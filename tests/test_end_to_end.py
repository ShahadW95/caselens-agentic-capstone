"""Offline acceptance evidence for the complete A2 LangGraph workflow."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from caselens.adapters import (
    FakeEvidenceSpecialist,
    FakeLegalSpecialist,
    FakeReviewer,
    FakeTimelineAnalysisSpecialist,
)
from caselens.contracts import (
    CaseQuery,
    ClaimStatus,
    ConfidenceLabel,
    DelegationTask,
    EvidenceFinding,
    FindingStatement,
    InteractionMode,
    ReviewContext,
    ReviewDefect,
    ReviewDefectCode,
    ReviewResult,
    SourceCitation,
    SourceTier,
    SpecialistStateView,
    WorkflowStatus,
)
from caselens.graph import run_case_query
from caselens.state import new_session


@dataclass(frozen=True)
class AdapterBundle:
    evidence: object
    legal: object
    timeline_analysis: object
    reviewer: object


def _adapters(
    *, evidence: object | None = None, reviewer: object | None = None
) -> AdapterBundle:
    return AdapterBundle(
        evidence=evidence or FakeEvidenceSpecialist(),
        legal=FakeLegalSpecialist(),
        timeline_analysis=FakeTimelineAnalysisSpecialist(),
        reviewer=reviewer or FakeReviewer(),
    )


def _query(mode: InteractionMode, suffix: str = "complete") -> CaseQuery:
    values: dict[str, object] = {
        "session_id": f"session.a2.{mode.value.lower()}.{suffix}",
        "mode": mode,
        "language": "en",
    }
    if mode is InteractionMode.ASK_CASE:
        values["user_query"] = "What does the cited case record establish?"
    elif mode is InteractionMode.CHECK_CLAIM:
        values["selected_claim_id"] = "claim.a2.001"
    elif mode is InteractionMode.EXPLAIN_VERDICT:
        values["user_query"] = "Explain the guilty plea and judgment."
    elif mode is InteractionMode.WHAT_IF:
        values["selected_event_id"] = "event.a2.001"
        values["allowed_change_id"] = "change.a2.001"
    return CaseQuery(**values)


@pytest.mark.parametrize("mode", tuple(InteractionMode))
def test_complete_path_for_all_five_modes(mode: InteractionMode) -> None:
    state = run_case_query(_query(mode), _adapters())

    assert state.status is WorkflowStatus.COMPLETED
    assert state.final_brief is not None
    assert state.review_result is not None and state.review_result.approved
    assert state.audit_events[-1].phase == "completion"


def test_explain_judgment_parallel_findings_join_into_final_brief() -> None:
    state = run_case_query(_query(InteractionMode.EXPLAIN_VERDICT), _adapters())

    assert state.evidence_finding is not None
    assert state.legal_finding is not None
    assert state.final_brief is not None
    assert state.final_brief.legal_explanation == state.legal_finding.explanation
    assert tuple(task.dependency_task_ids for task in state.delegation_tasks) == (
        (),
        (),
    )
    phases = [event.phase for event in state.audit_events]
    assert phases.index("join") > max(
        index for index, phase in enumerate(phases) if phase == "delegation"
    )


def test_citations_and_status_categories_reach_final_brief_unchanged() -> None:
    state = run_case_query(_query(InteractionMode.ASK_CASE), _adapters())

    assert state.evidence_finding is not None and state.final_brief is not None
    assert state.final_brief.citations == state.evidence_finding.citations
    assert (
        state.final_brief.established_facts
        == state.evidence_finding.established_facts
    )


class InsufficientEvidence:
    def execute(
        self, task: DelegationTask, state_view: SpecialistStateView
    ) -> EvidenceFinding:
        del state_view
        citation = SourceCitation(
            citation_id="cit.insufficient.001",
            source_id="source.insufficient.001",
            document_id="document.insufficient.001",
            chunk_id="chunk.insufficient.001",
            title="Insufficient fixture",
            heading="Unknown claim",
            source_type="fictional_fixture",
            source_tier=SourceTier.A,
            original_url="https://example.invalid/insufficient",
        )
        unknown = FindingStatement(
            statement_id="statement.insufficient.001",
            text="The curated fixture does not establish this claim.",
            status=ClaimStatus.INSUFFICIENT_EVIDENCE,
            citation_ids=(citation.citation_id,),
        )
        return EvidenceFinding(
            finding_id="finding.insufficient.001",
            task_id=task.task_id,
            summary="Evidence is insufficient for the selected claim.",
            unknowns=(unknown,),
            citations=(citation,),
            confidence=ConfidenceLabel.LOW,
        )


def test_unsupported_claim_is_labeled_insufficient_not_promoted_to_fact() -> None:
    state = run_case_query(
        _query(InteractionMode.CHECK_CLAIM, "unsupported"),
        _adapters(evidence=InsufficientEvidence()),
    )

    assert state.status is WorkflowStatus.COMPLETED
    assert state.final_brief is not None
    assert state.final_brief.established_facts == ()
    assert state.final_brief.unknowns[0].status is ClaimStatus.INSUFFICIENT_EVIDENCE


class OneDefectReviewer:
    def __init__(self, *, always_reject: bool = False) -> None:
        self.calls = 0
        self.always_reject = always_reject

    def review(self, draft, context: ReviewContext) -> ReviewResult:
        del context
        self.calls += 1
        if self.calls == 1 or self.always_reject:
            return ReviewResult(
                review_id=f"review.defect.{self.calls}",
                approved=False,
                defects=(
                    ReviewDefect(
                        defect_id=f"defect.unsafe.{self.calls}",
                        code=ReviewDefectCode.UNSAFE_CONTENT,
                        field_path="concise_answer",
                        description="Replace unsafe certainty language.",
                        responsible_role="CASE_DIRECTOR",
                    ),
                ),
            )
        return ReviewResult(
            review_id=f"review.approved.{self.calls}",
            approved=True,
            final_brief=draft,
        )


def test_one_review_defect_is_corrected_once() -> None:
    reviewer = OneDefectReviewer()
    state = run_case_query(
        _query(InteractionMode.ASK_CASE, "one-defect"),
        _adapters(reviewer=reviewer),
    )

    assert state.status is WorkflowStatus.COMPLETED
    assert state.correction_count == 1
    assert state.review_attempt_count == 2
    assert reviewer.calls == 2
    assert "correction" in [event.phase for event in state.audit_events]


def test_second_review_defect_stops_as_insufficient() -> None:
    reviewer = OneDefectReviewer(always_reject=True)
    state = run_case_query(
        _query(InteractionMode.ASK_CASE, "two-defects"),
        _adapters(reviewer=reviewer),
    )

    assert state.status is WorkflowStatus.INSUFFICIENT_OR_ESCALATED
    assert state.correction_count == 1
    assert state.final_brief is None
    assert state.completion_reason == "SECOND_REVIEW_DEFECT"
    assert reviewer.calls == 2


class FactAddingReviewer:
    def review(self, draft, context: ReviewContext) -> ReviewResult:
        del context
        added = FindingStatement(
            statement_id="statement.reviewer.added",
            text="A reviewer must not add this otherwise valid-looking fact.",
            status=ClaimStatus.ESTABLISHED,
            citation_ids=(draft.citations[0].citation_id,),
        )
        changed = draft.model_copy(
            update={"established_facts": draft.established_facts + (added,)}
        )
        return ReviewResult(
            review_id="review.added.fact",
            approved=True,
            final_brief=changed,
        )


def test_reviewer_cannot_add_new_facts() -> None:
    state = run_case_query(
        _query(InteractionMode.ASK_CASE, "reviewer-fact"),
        _adapters(reviewer=FactAddingReviewer()),
    )

    assert state.status is WorkflowStatus.FAILED
    assert state.completion_reason == "FINAL_VALIDATION_FAILED"
    assert state.final_brief is None


class RaisingEvidence:
    def execute(self, task: DelegationTask, state_view: SpecialistStateView) -> object:
        del task, state_view
        raise RuntimeError("private provider detail must not escape")


def test_adapter_exception_becomes_safe_failure() -> None:
    state = run_case_query(
        _query(InteractionMode.ASK_CASE, "adapter-error"),
        _adapters(evidence=RaisingEvidence()),
    )

    assert state.status is WorkflowStatus.FAILED
    assert state.completion_reason == "ADAPTER_FAILURE"
    serialized = state.model_dump_json()
    assert "private provider detail" not in serialized


class MalformedThenValidEvidence:
    def __init__(self, *, always_malformed: bool = False) -> None:
        self.calls = 0
        self.always_malformed = always_malformed

    def execute(self, task: DelegationTask, state_view: SpecialistStateView) -> object:
        self.calls += 1
        if self.calls == 1 or self.always_malformed:
            return {"invalid": "untyped payload"}
        return FakeEvidenceSpecialist().execute(task, state_view)


def test_malformed_output_gets_one_structured_repair() -> None:
    evidence = MalformedThenValidEvidence()
    state = run_case_query(
        _query(InteractionMode.ASK_CASE, "malformed-once"),
        _adapters(evidence=evidence),
    )

    assert state.status is WorkflowStatus.COMPLETED
    assert evidence.calls == 2
    assert state.retry_counters.structured_output == 1
    assert state.specialist_call_count == 2
    assert "structured_repair" in [event.phase for event in state.audit_events]


def test_second_malformed_output_stops_safely() -> None:
    evidence = MalformedThenValidEvidence(always_malformed=True)
    state = run_case_query(
        _query(InteractionMode.ASK_CASE, "malformed-twice"),
        _adapters(evidence=evidence),
    )

    assert state.status is WorkflowStatus.FAILED
    assert state.completion_reason == "MALFORMED_ADAPTER_OUTPUT"
    assert evidence.calls == 2


def test_graph_step_budget_stops_before_overrun() -> None:
    query = _query(InteractionMode.ASK_CASE, "step-budget")
    constrained = new_session(query, graph_step_budget=7)
    state = run_case_query(query, _adapters(), state=constrained)

    assert state.status is WorkflowStatus.INSUFFICIENT_OR_ESCALATED
    assert state.graph_step_count <= state.graph_step_budget
    assert state.final_brief is None


def test_invalid_input_stops_for_clarification_before_specialists() -> None:
    query = CaseQuery(
        session_id="session.a2.invalid",
        mode=InteractionMode.ASK_CASE,
        user_query="",
    )
    state = run_case_query(query, _adapters())

    assert state.status is WorkflowStatus.NEEDS_CLARIFICATION
    assert state.specialist_call_count == 0
    assert state.final_brief is None


class DependencyAwareTimeline(FakeTimelineAnalysisSpecialist):
    def __init__(self) -> None:
        self.completed_task_ids: tuple[str, ...] = ()

    def execute(self, task: DelegationTask, state_view: SpecialistStateView):
        self.completed_task_ids = state_view.completed_task_ids
        return super().execute(task, state_view)


def test_evidence_required_what_if_runs_dependency_before_timeline() -> None:
    timeline = DependencyAwareTimeline()
    adapters = AdapterBundle(
        evidence=FakeEvidenceSpecialist(),
        legal=FakeLegalSpecialist(),
        timeline_analysis=timeline,
        reviewer=FakeReviewer(),
    )
    state = run_case_query(
        _query(InteractionMode.WHAT_IF, "dependency"),
        adapters,
        require_what_if_evidence=True,
    )

    assert state.status is WorkflowStatus.COMPLETED
    assert timeline.completed_task_ids == (state.delegation_tasks[0].task_id,)
    assert state.delegation_tasks[1].dependency_task_ids == (
        state.delegation_tasks[0].task_id,
    )


class CountingEvidence(FakeEvidenceSpecialist):
    def __init__(self) -> None:
        self.calls = 0

    def execute(
        self, task: DelegationTask, state_view: SpecialistStateView
    ) -> EvidenceFinding:
        self.calls += 1
        return super().execute(task, state_view)


def test_completed_state_is_idempotent_and_does_not_call_specialist_again() -> None:
    evidence = CountingEvidence()
    query = _query(InteractionMode.ASK_CASE, "idempotent")
    first = run_case_query(query, _adapters(evidence=evidence))
    second = run_case_query(query, _adapters(evidence=evidence), state=first)

    assert second is first
    assert evidence.calls == 1


def test_safe_trace_has_tool_status_without_raw_reasoning() -> None:
    state = run_case_query(_query(InteractionMode.CHECK_CLAIM, "trace"), _adapters())
    serialized = state.model_dump_json().lower()

    assert "tool:check_claim_support" in [event.phase for event in state.audit_events]
    assert "chain_of_thought" not in serialized
    assert "raw_prompt" not in serialized
    assert "raw_model_payload" not in serialized
