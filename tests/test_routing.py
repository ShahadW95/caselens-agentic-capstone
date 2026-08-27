"""Offline A1 routing, ownership, audit, and budget tests."""

from __future__ import annotations

import pytest

from caselens.adapters import create_development_fake_adapters
from caselens.contracts import (
    CaseQuery,
    InteractionMode,
    SpecialistRole,
    WorkflowStatus,
)
from caselens.graph import create_case_graph, run_routing_skeleton
from caselens.state import (
    BudgetExceeded,
    StateOwner,
    StateOwnershipError,
    consume_retry,
    new_session,
    owned_update,
)
from caselens.supervisor import EXPLAIN_JUDGMENT_DISPLAY_LABEL


def _query(mode: InteractionMode, **updates: object) -> CaseQuery:
    values: dict[str, object] = {
        "session_id": f"session.test.{mode.value.lower()}",
        "mode": mode,
        "language": "en",
    }
    if mode is InteractionMode.ASK_CASE:
        values["user_query"] = "What does the cited case record establish?"
    elif mode is InteractionMode.CHECK_CLAIM:
        values["selected_claim_id"] = "claim.test.001"
    elif mode is InteractionMode.EXPLAIN_VERDICT:
        values["user_query"] = "Why did the court impose this judgment?"
    elif mode is InteractionMode.WHAT_IF:
        values["selected_event_id"] = "event.test.001"
        values["allowed_change_id"] = "change.test.001"
    values.update(updates)
    return CaseQuery(**values)


@pytest.mark.parametrize(
    ("mode", "roles"),
    [
        (InteractionMode.ASK_CASE, (SpecialistRole.EVIDENCE,)),
        (InteractionMode.VIEW_TIMELINE, (SpecialistRole.TIMELINE_ANALYSIS,)),
        (InteractionMode.CHECK_CLAIM, (SpecialistRole.EVIDENCE,)),
        (
            InteractionMode.EXPLAIN_VERDICT,
            (SpecialistRole.EVIDENCE, SpecialistRole.LEGAL),
        ),
        (InteractionMode.WHAT_IF, (SpecialistRole.TIMELINE_ANALYSIS,)),
    ],
)
def test_each_mode_selects_only_its_required_specialists(
    mode: InteractionMode, roles: tuple[SpecialistRole, ...]
) -> None:
    state = run_routing_skeleton(
        _query(mode), create_development_fake_adapters()
    )

    assert state.status is WorkflowStatus.COMPLETED
    assert tuple(task.role for task in state.delegation_tasks) == roles
    assert state.specialist_call_count == len(roles)


def test_explain_judgment_uses_default_question_and_joins_findings() -> None:
    state = run_routing_skeleton(
        _query(InteractionMode.EXPLAIN_VERDICT, user_query=""),
        create_development_fake_adapters(),
    )

    assert state.user_query == "Explain the guilty plea and judgment in this case."
    assert InteractionMode.EXPLAIN_VERDICT.value == "EXPLAIN_VERDICT"
    assert EXPLAIN_JUDGMENT_DISPLAY_LABEL == "اشرح الحكم | Explain the Judgment"
    assert state.evidence_finding is not None
    assert state.legal_finding is not None
    assert [event.phase for event in state.audit_events] == [
        "validation",
        "route",
        "delegation",
        "delegation",
        "join",
        "completion",
    ]


@pytest.mark.parametrize(
    "query",
    [
        _query(InteractionMode.ASK_CASE, user_query=""),
        _query(InteractionMode.CHECK_CLAIM, selected_claim_id=None),
        _query(InteractionMode.CHECK_CLAIM, selected_claim_id="not-a-claim"),
        _query(InteractionMode.WHAT_IF, allowed_change_id=None),
    ],
)
def test_invalid_mode_input_returns_safe_clarification(query: CaseQuery) -> None:
    state = run_routing_skeleton(query, create_development_fake_adapters())

    assert state.status is WorkflowStatus.NEEDS_CLARIFICATION
    assert len(state.validation_errors) == 1
    assert [event.phase for event in state.audit_events] == [
        "validation",
        "error",
        "completion",
    ]
    assert state.specialist_call_count == 0


def test_what_if_adds_evidence_only_when_plan_requires_it() -> None:
    query = _query(InteractionMode.WHAT_IF)
    ordinary = run_routing_skeleton(query, create_development_fake_adapters())
    required = run_routing_skeleton(
        query,
        create_development_fake_adapters(),
        require_what_if_evidence=True,
    )

    assert tuple(task.role for task in ordinary.delegation_tasks) == (
        SpecialistRole.TIMELINE_ANALYSIS,
    )
    assert tuple(task.role for task in required.delegation_tasks) == (
        SpecialistRole.EVIDENCE,
        SpecialistRole.TIMELINE_ANALYSIS,
    )
    assert required.delegation_tasks[1].dependency_task_ids == (
        required.delegation_tasks[0].task_id,
    )


def test_state_ownership_rejects_cross_role_write() -> None:
    state = new_session(_query(InteractionMode.ASK_CASE))

    with pytest.raises(StateOwnershipError, match="EVIDENCE cannot update: status"):
        owned_update(state, StateOwner.EVIDENCE, status=WorkflowStatus.COMPLETED)


def test_turn_and_specialist_call_budgets_stop_safely() -> None:
    query = _query(InteractionMode.EXPLAIN_VERDICT)
    no_turns = new_session(query).model_copy(update={"turn_count": 4})
    turn_stop = run_routing_skeleton(
        query, create_development_fake_adapters(), state=no_turns
    )
    one_call = new_session(query, specialist_call_budget=1)
    call_stop = run_routing_skeleton(
        query, create_development_fake_adapters(), state=one_call
    )

    assert turn_stop.status is WorkflowStatus.INSUFFICIENT_OR_ESCALATED
    assert turn_stop.specialist_call_count == 0
    assert call_stop.status is WorkflowStatus.INSUFFICIENT_OR_ESCALATED
    assert call_stop.specialist_call_count == 1


def test_graph_step_and_retry_budgets_are_enforced() -> None:
    query = _query(InteractionMode.ASK_CASE)
    state = new_session(query, graph_step_budget=1, retry_budget=1)
    stopped = run_routing_skeleton(
        query, create_development_fake_adapters(), state=state
    )
    retried = consume_retry(new_session(query, retry_budget=1), "adapter")

    assert stopped.status is WorkflowStatus.INSUFFICIENT_OR_ESCALATED
    with pytest.raises(BudgetExceeded, match="retry budget"):
        consume_retry(retried, "structured_output")


def test_state_has_no_raw_reasoning_or_model_payload_field() -> None:
    field_names = set(type(new_session(_query(InteractionMode.ASK_CASE))).model_fields)

    assert not field_names.intersection(
        {"chain_of_thought", "reasoning", "raw_prompt", "raw_model_payload"}
    )


def test_specialists_are_invoked_only_by_the_coordinator() -> None:
    adapters = create_development_fake_adapters()
    state = run_routing_skeleton(_query(InteractionMode.EXPLAIN_VERDICT), adapters)

    # The v1 specialist objects expose execute only; they receive typed task/state views,
    # and hold no references to peer specialists.
    assert "evidence" not in vars(adapters.legal)
    assert "legal" not in vars(adapters.evidence)
    assert state.specialist_call_count == 2


def test_a2_graph_exposes_explicit_workflow_nodes() -> None:
    graph = create_case_graph(create_development_fake_adapters())

    assert {
        "validate_request",
        "supervisor_plan",
        "explain_evidence",
        "explain_legal",
        "join_findings",
        "build_draft",
        "editorial_review",
        "bounded_correction",
        "final_validation",
        "complete",
        "safe_stop",
    }.issubset(graph.get_graph().nodes)
