"""A1 fake-backed routing skeleton; A2 adds the full LangGraph review workflow."""

from __future__ import annotations

from typing import Protocol

from .contracts import (
    AuditEventType,
    CaseQuery,
    CounterfactualFinding,
    EvidenceFinding,
    LegalFinding,
    SafeError,
    SpecialistRole,
    SpecialistStateView,
    TaskStatus,
    TimelineFinding,
    WorkflowStatus,
)
from .protocols import (
    EvidenceSpecialistProtocol,
    LegalSpecialistProtocol,
    TimelineAnalysisSpecialistProtocol,
)
from .state import (
    BudgetExceeded,
    CaseLensState,
    StateOwner,
    append_audit_events,
    append_errors,
    consume_graph_step,
    consume_specialist_call,
    consume_turn,
    new_session,
    owned_update,
)
from .supervisor import audit_event, build_delegation_plan, validate_route


class RoutingAdapters(Protocol):
    evidence: EvidenceSpecialistProtocol
    legal: LegalSpecialistProtocol
    timeline_analysis: TimelineAnalysisSpecialistProtocol


def _append_event(
    state: CaseLensState,
    event_type: AuditEventType,
    phase: str,
    status: WorkflowStatus,
    actor: str,
    summary: str,
) -> CaseLensState:
    event = audit_event(
        session_id=state.session_id,
        sequence=len(state.audit_events) + 1,
        event_type=event_type,
        phase=phase,
        status=status,
        actor=actor,
        safe_summary=summary,
    )
    return append_audit_events(state, event)


def _safe_stop(
    state: CaseLensState,
    *,
    code: str,
    message: str,
    status: WorkflowStatus,
) -> CaseLensState:
    error = SafeError(
        error_id=f"error.{state.session_id}.{len(state.validation_errors) + 1}",
        code=code,
        user_message=message,
        recoverable=status is WorkflowStatus.NEEDS_CLARIFICATION,
    )
    state = append_errors(state, error)
    state = owned_update(
        state,
        StateOwner.SUPERVISOR,
        status=status,
        completion_reason=code,
    )
    state = _append_event(
        state, AuditEventType.ERROR, "error", status, "CASE_DIRECTOR", message
    )
    return _append_event(
        state,
        AuditEventType.COMPLETION,
        "completion",
        status,
        "CASE_DIRECTOR",
        "Routing stopped safely.",
    )


def _execute_task(
    state: CaseLensState,
    task_index: int,
    adapters: RoutingAdapters,
    query: CaseQuery,
) -> CaseLensState:
    task = state.delegation_tasks[task_index]
    state = consume_specialist_call(consume_graph_step(state))
    state = _append_event(
        state,
        AuditEventType.DELEGATION,
        "delegation",
        WorkflowStatus.RUNNING,
        task.role.value,
        f"Delegated task {task.task_id}.",
    )
    completed_ids = tuple(
        item.task_id
        for item in state.delegation_tasks
        if item.status is TaskStatus.COMPLETE
    )
    view = SpecialistStateView(
        query=query,
        safe_messages=state.short_term_messages,
        completed_task_ids=completed_ids,
        retrieved_chunk_refs=state.retrieved_chunk_refs,
    )
    if task.role is SpecialistRole.EVIDENCE:
        finding = adapters.evidence.execute(task, view)
        if not isinstance(finding, EvidenceFinding):
            raise TypeError("evidence adapter returned the wrong contract")
        state = owned_update(state, StateOwner.EVIDENCE, evidence_finding=finding)
    elif task.role is SpecialistRole.LEGAL:
        finding = adapters.legal.execute(task, view)
        if not isinstance(finding, LegalFinding):
            raise TypeError("legal adapter returned the wrong contract")
        state = owned_update(state, StateOwner.LEGAL, legal_finding=finding)
    else:
        finding = adapters.timeline_analysis.execute(task, view)
        if isinstance(finding, TimelineFinding):
            state = owned_update(state, StateOwner.TIMELINE, timeline_finding=finding)
        elif isinstance(finding, CounterfactualFinding):
            state = owned_update(
                state, StateOwner.TIMELINE, counterfactual_finding=finding
            )
        else:
            raise TypeError("timeline adapter returned the wrong contract")
    tasks = list(state.delegation_tasks)
    tasks[task_index] = task.model_copy(update={"status": TaskStatus.COMPLETE})
    return owned_update(state, StateOwner.SUPERVISOR, delegation_tasks=tuple(tasks))


def run_routing_skeleton(
    query: CaseQuery,
    adapters: RoutingAdapters,
    *,
    state: CaseLensState | None = None,
    require_what_if_evidence: bool = False,
) -> CaseLensState:
    """Validate, plan, delegate through injected fakes, join, and stop at A1."""

    state = state or new_session(query)
    if state.session_id != query.session_id:
        raise ValueError("query and state session IDs must match")
    try:
        state = consume_turn(consume_graph_step(state))
    except BudgetExceeded as exc:
        return _safe_stop(
            state,
            code="BUDGET_EXHAUSTED",
            message=str(exc),
            status=WorkflowStatus.INSUFFICIENT_OR_ESCALATED,
        )
    state = owned_update(state, StateOwner.SUPERVISOR, status=WorkflowStatus.VALIDATING)
    state = _append_event(
        state,
        AuditEventType.VALIDATION,
        "validation",
        WorkflowStatus.VALIDATING,
        "CASE_DIRECTOR",
        "Mode-specific input validation completed.",
    )
    validation = validate_route(query)
    if not validation.accepted:
        assert validation.error is not None
        return _safe_stop(
            state,
            code=validation.error.code,
            message=validation.error.user_message,
            status=WorkflowStatus.NEEDS_CLARIFICATION,
        )
    query = validation.query
    state = owned_update(
        state,
        StateOwner.INPUT,
        mode=query.mode,
        language=query.language,
        user_query=query.user_query,
        selected_claim_id=query.selected_claim_id,
        selected_event_id=query.selected_event_id,
        hypothetical_change=query.allowed_change_id,
    )
    try:
        state = consume_graph_step(state)
        plan = build_delegation_plan(
            query, require_what_if_evidence=require_what_if_evidence
        )
        state = owned_update(
            state,
            StateOwner.SUPERVISOR,
            plan=plan,
            delegation_tasks=plan.tasks,
            status=WorkflowStatus.RUNNING,
        )
        state = _append_event(
            state,
            AuditEventType.ROUTE,
            "route",
            WorkflowStatus.PLANNING,
            "CASE_DIRECTOR",
            f"Selected {len(plan.tasks)} bounded specialist task(s).",
        )
        while any(task.status is TaskStatus.PENDING for task in state.delegation_tasks):
            completed = {
                task.task_id
                for task in state.delegation_tasks
                if task.status is TaskStatus.COMPLETE
            }
            ready = [
                index
                for index, task in enumerate(state.delegation_tasks)
                if task.status is TaskStatus.PENDING
                and set(task.dependency_task_ids).issubset(completed)
            ]
            if not ready:
                raise RuntimeError("delegation dependencies cannot make progress")
            for index in ready:
                state = _execute_task(state, index, adapters, query)
        state = consume_graph_step(state)
        state = _append_event(
            state,
            AuditEventType.ROUTE,
            "join",
            WorkflowStatus.RUNNING,
            "CASE_DIRECTOR",
            "All selected specialist findings joined.",
        )
        state = consume_graph_step(state)
        state = owned_update(
            state,
            StateOwner.SUPERVISOR,
            status=WorkflowStatus.COMPLETED,
            completion_reason="A1_ROUTING_SKELETON_COMPLETE",
        )
        return _append_event(
            state,
            AuditEventType.COMPLETION,
            "completion",
            WorkflowStatus.COMPLETED,
            "CASE_DIRECTOR",
            "A1 routing skeleton completed without final review.",
        )
    except BudgetExceeded as exc:
        return _safe_stop(
            state,
            code="BUDGET_EXHAUSTED",
            message=str(exc),
            status=WorkflowStatus.INSUFFICIENT_OR_ESCALATED,
        )
    except (RuntimeError, TypeError, ValueError) as exc:
        return _safe_stop(
            state,
            code="ROUTING_FAILED",
            message=f"The bounded routing skeleton could not complete: {exc}",
            status=WorkflowStatus.FAILED,
        )
