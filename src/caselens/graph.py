"""A1 routing compatibility plus the complete A2 LangGraph workflow."""

from __future__ import annotations

from typing import Literal, Protocol, TypedDict

from langgraph.errors import GraphRecursionError
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, ConfigDict, Field

from .contracts import (
    AuditEventType,
    CaseQuery,
    CaseResearchBrief,
    CounterfactualFinding,
    DelegationTask,
    EvidenceFinding,
    InteractionMode,
    LegalFinding,
    ReviewContext,
    ReviewResult,
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
    ReviewerProtocol,
    TimelineAnalysisSpecialistProtocol,
)
from .state import (
    BudgetExceeded,
    CaseLensState,
    StateOwner,
    append_audit_events,
    append_errors,
    consume_graph_step,
    consume_retry,
    consume_specialist_call,
    consume_turn,
    new_session,
    owned_update,
)
from .reviewer import (
    repair_draft,
    reviewer_preserves_evidence,
    validate_editorial_integrity,
)
from .services.result_builder import build_case_research_brief
from .supervisor import audit_event, build_delegation_plan, validate_route


class RoutingAdapters(Protocol):
    evidence: EvidenceSpecialistProtocol
    legal: LegalSpecialistProtocol
    timeline_analysis: TimelineAnalysisSpecialistProtocol
    reviewer: ReviewerProtocol


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


Finding = EvidenceFinding | LegalFinding | TimelineFinding | CounterfactualFinding


class SpecialistExecution(BaseModel):
    """Internal validated result from one bounded specialist node."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    task: DelegationTask
    finding: Finding | None = None
    attempts: int = Field(default=1, ge=1, le=2)
    repaired: bool = False
    error_code: str | None = None
    error_message: str | None = None


class _GraphState(TypedDict, total=False):
    query: CaseQuery
    case_state: CaseLensState
    require_what_if_evidence: bool
    repair_task_id: str | None
    evidence_execution: SpecialistExecution
    legal_execution: SpecialistExecution
    timeline_execution: SpecialistExecution
    stop_code: str
    stop_message: str
    stop_status: WorkflowStatus


def _stop_update(
    code: str,
    message: str,
    status: WorkflowStatus,
) -> dict[str, object]:
    return {
        "stop_code": code,
        "stop_message": message,
        "stop_status": status,
    }


def _validate_request_node(graph_state: _GraphState) -> dict[str, object]:
    state = graph_state["case_state"]
    query = graph_state["query"]
    try:
        state = consume_turn(consume_graph_step(state))
    except BudgetExceeded as exc:
        return {
            "case_state": state,
            **_stop_update(
                "BUDGET_EXHAUSTED",
                str(exc),
                WorkflowStatus.INSUFFICIENT_OR_ESCALATED,
            ),
        }
    state = owned_update(
        state, StateOwner.SUPERVISOR, status=WorkflowStatus.VALIDATING
    )
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
        return {
            "case_state": state,
            **_stop_update(
                validation.error.code,
                validation.error.user_message,
                WorkflowStatus.NEEDS_CLARIFICATION,
            ),
        }
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
    return {"case_state": state, "query": query}


def _route_after_validation(graph_state: _GraphState) -> str:
    return "stop" if "stop_code" in graph_state else "plan"


def _plan_node(graph_state: _GraphState) -> dict[str, object]:
    state = graph_state["case_state"]
    query = graph_state["query"]
    try:
        state = consume_graph_step(state)
        plan = build_delegation_plan(
            query,
            require_what_if_evidence=graph_state.get(
                "require_what_if_evidence", False
            ),
        )
        remaining_calls = state.specialist_call_budget - state.specialist_call_count
        if len(plan.tasks) > remaining_calls:
            raise BudgetExceeded("specialist-call budget cannot satisfy the plan")
        remaining_steps = state.graph_step_budget - state.graph_step_count
        minimum_steps = len(plan.tasks) + 5
        if minimum_steps > remaining_steps:
            raise BudgetExceeded("graph-step budget cannot satisfy the plan")
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
        repair_task_id = None
        if (
            state.retry_counters.total < state.retry_budget
            and remaining_calls > len(plan.tasks)
            and remaining_steps > minimum_steps
        ):
            repair_task_id = plan.tasks[0].task_id
        return {"case_state": state, "repair_task_id": repair_task_id}
    except BudgetExceeded as exc:
        return {
            "case_state": state,
            **_stop_update(
                "BUDGET_EXHAUSTED",
                str(exc),
                WorkflowStatus.INSUFFICIENT_OR_ESCALATED,
            ),
        }


def _route_after_plan(graph_state: _GraphState) -> str | list[str]:
    if "stop_code" in graph_state:
        return "stop"
    mode = graph_state["query"].mode
    if mode in (InteractionMode.ASK_CASE, InteractionMode.CHECK_CLAIM):
        return "evidence_single"
    if mode is InteractionMode.EXPLAIN_VERDICT:
        return ["explain_evidence", "explain_legal"]
    if (
        mode is InteractionMode.WHAT_IF
        and graph_state.get("require_what_if_evidence", False)
    ):
        return "what_if_evidence"
    return "timeline_single"


def _completed_execution_ids(graph_state: _GraphState) -> tuple[str, ...]:
    return tuple(
        execution.task.task_id
        for key in (
            "evidence_execution",
            "legal_execution",
            "timeline_execution",
        )
        if (execution := graph_state.get(key)) is not None
        and execution.finding is not None
        and execution.error_code is None
    )


def _invoke_specialist(
    *,
    task: DelegationTask,
    graph_state: _GraphState,
    adapters: RoutingAdapters,
) -> SpecialistExecution:
    query = graph_state["query"]
    view = SpecialistStateView(
        query=query,
        safe_messages=graph_state["case_state"].short_term_messages,
        completed_task_ids=_completed_execution_ids(graph_state),
        retrieved_chunk_refs=graph_state["case_state"].retrieved_chunk_refs,
    )
    allow_repair = graph_state.get("repair_task_id") == task.task_id
    attempts = 0
    while attempts < (2 if allow_repair else 1):
        attempts += 1
        try:
            if task.role is SpecialistRole.EVIDENCE:
                finding = adapters.evidence.execute(task, view)
                valid = isinstance(finding, EvidenceFinding)
            elif task.role is SpecialistRole.LEGAL:
                finding = adapters.legal.execute(task, view)
                valid = isinstance(finding, LegalFinding)
            else:
                finding = adapters.timeline_analysis.execute(task, view)
                valid = (
                    isinstance(finding, CounterfactualFinding)
                    if query.mode is InteractionMode.WHAT_IF
                    else isinstance(finding, TimelineFinding)
                )
        except Exception:
            return SpecialistExecution(
                task=task,
                attempts=attempts,
                error_code="ADAPTER_FAILURE",
                error_message="The selected specialist failed safely.",
            )
        if valid:
            return SpecialistExecution(
                task=task,
                finding=finding,
                attempts=attempts,
                repaired=attempts == 2,
            )
    return SpecialistExecution(
        task=task,
        attempts=attempts,
        error_code="MALFORMED_ADAPTER_OUTPUT",
        error_message="The specialist returned an invalid structured result twice.",
    )


def _specialist_node(
    graph_state: _GraphState,
    adapters: RoutingAdapters,
    role: SpecialistRole,
    output_key: Literal[
        "evidence_execution", "legal_execution", "timeline_execution"
    ],
) -> dict[str, object]:
    plan = graph_state["case_state"].plan
    assert plan is not None
    task = next(task for task in plan.tasks if task.role is role)
    return {
        output_key: _invoke_specialist(
            task=task,
            graph_state=graph_state,
            adapters=adapters,
        )
    }


def _ordered_executions(graph_state: _GraphState) -> tuple[SpecialistExecution, ...]:
    plan = graph_state["case_state"].plan
    assert plan is not None
    by_task_id = {
        execution.task.task_id: execution
        for key in (
            "evidence_execution",
            "legal_execution",
            "timeline_execution",
        )
        if (execution := graph_state.get(key)) is not None
    }
    return tuple(by_task_id[task.task_id] for task in plan.tasks)


def _append_execution_trace(
    state: CaseLensState, execution: SpecialistExecution
) -> CaseLensState:
    task = execution.task
    state = _append_event(
        state,
        AuditEventType.DELEGATION,
        "delegation",
        WorkflowStatus.RUNNING,
        task.role.value,
        f"Delegated and validated task {task.task_id}.",
    )
    if execution.repaired:
        state = _append_event(
            state,
            AuditEventType.VALIDATION,
            "structured_repair",
            WorkflowStatus.RUNNING,
            task.role.value,
            "One bounded structured-output repair succeeded.",
        )
    finding = execution.finding
    citation_count = len(finding.citations) if finding is not None else 0
    if task.mode is InteractionMode.CHECK_CLAIM:
        event_type = AuditEventType.TOOL
        phase = "tool:check_claim_support"
        summary = "Claim-support tool intent completed through the injected adapter."
    elif task.mode is InteractionMode.VIEW_TIMELINE:
        event_type = AuditEventType.TOOL
        phase = "tool:query_case_timeline"
        summary = "Timeline tool intent completed through the injected adapter."
    elif (
        task.mode is InteractionMode.WHAT_IF
        and task.role is SpecialistRole.TIMELINE_ANALYSIS
    ):
        event_type = AuditEventType.TOOL
        phase = "tool:simulate_counterfactual"
        summary = "Counterfactual tool intent completed through the injected adapter."
    else:
        event_type = AuditEventType.RETRIEVAL
        phase = "retrieval"
        summary = (
            f"Injected adapter returned {citation_count} validated citation reference(s); "
            "development fakes perform no live retrieval."
        )
    return _append_event(
        state,
        event_type,
        phase,
        WorkflowStatus.RUNNING,
        task.role.value,
        summary,
    )


def _join_node(graph_state: _GraphState) -> dict[str, object]:
    state = graph_state["case_state"]
    try:
        executions = _ordered_executions(graph_state)
        tasks = list(state.delegation_tasks)
        for execution in executions:
            for _ in range(execution.attempts):
                state = consume_specialist_call(consume_graph_step(state))
            if execution.repaired:
                state = consume_retry(state, "structured_output")
            state = _append_execution_trace(state, execution)
            index = next(
                index
                for index, task in enumerate(tasks)
                if task.task_id == execution.task.task_id
            )
            if execution.error_code is not None:
                tasks[index] = tasks[index].model_copy(
                    update={"status": TaskStatus.BLOCKED}
                )
                state = owned_update(
                    state, StateOwner.SUPERVISOR, delegation_tasks=tuple(tasks)
                )
                return {
                    "case_state": state,
                    **_stop_update(
                        execution.error_code,
                        execution.error_message or "A specialist failed safely.",
                        WorkflowStatus.FAILED,
                    ),
                }
            finding = execution.finding
            assert finding is not None
            if isinstance(finding, EvidenceFinding):
                state = owned_update(
                    state, StateOwner.EVIDENCE, evidence_finding=finding
                )
            elif isinstance(finding, LegalFinding):
                state = owned_update(state, StateOwner.LEGAL, legal_finding=finding)
            elif isinstance(finding, TimelineFinding):
                state = owned_update(
                    state, StateOwner.TIMELINE, timeline_finding=finding
                )
            else:
                state = owned_update(
                    state, StateOwner.TIMELINE, counterfactual_finding=finding
                )
            tasks[index] = tasks[index].model_copy(update={"status": TaskStatus.COMPLETE})
        state = owned_update(
            state, StateOwner.SUPERVISOR, delegation_tasks=tuple(tasks)
        )
        state = consume_graph_step(state)
        state = _append_event(
            state,
            AuditEventType.ROUTE,
            "join",
            WorkflowStatus.RUNNING,
            "CASE_DIRECTOR",
            "All selected validated findings joined in plan order.",
        )
        return {"case_state": state}
    except BudgetExceeded as exc:
        return {
            "case_state": state,
            **_stop_update(
                "BUDGET_EXHAUSTED",
                str(exc),
                WorkflowStatus.INSUFFICIENT_OR_ESCALATED,
            ),
        }


def _route_after_join(graph_state: _GraphState) -> str:
    return "stop" if "stop_code" in graph_state else "build_draft"


def _build_draft_node(graph_state: _GraphState) -> dict[str, object]:
    state = graph_state["case_state"]
    try:
        state = consume_graph_step(state)
        draft = build_case_research_brief(state)
        state = owned_update(state, StateOwner.REVIEWER, draft_brief=draft)
        return {"case_state": state}
    except BudgetExceeded as exc:
        return {
            "case_state": state,
            **_stop_update(
                "BUDGET_EXHAUSTED",
                str(exc),
                WorkflowStatus.INSUFFICIENT_OR_ESCALATED,
            ),
        }
    except ValueError:
        return {
            "case_state": state,
            **_stop_update(
                "DRAFT_BUILD_FAILED",
                "The validated findings could not form a safe draft brief.",
                WorkflowStatus.FAILED,
            ),
        }


def _review_node(
    graph_state: _GraphState, adapters: RoutingAdapters
) -> dict[str, object]:
    state = graph_state["case_state"]
    draft = state.draft_brief
    assert draft is not None
    try:
        state = consume_graph_step(state)
    except BudgetExceeded as exc:
        return {
            "case_state": state,
            **_stop_update(
                "BUDGET_EXHAUSTED",
                str(exc),
                WorkflowStatus.INSUFFICIENT_OR_ESCALATED,
            ),
        }
    state = owned_update(
        state, StateOwner.SUPERVISOR, status=WorkflowStatus.REVIEWING
    )
    local_defect = validate_editorial_integrity(draft)
    attempts = 0
    if local_defect is not None:
        result = ReviewResult(
            review_id=f"review.{state.session_id}.{state.review_attempt_count + 1}",
            approved=False,
            defects=(local_defect,),
        )
    else:
        context = ReviewContext(
            evidence_finding=state.evidence_finding,
            legal_finding=state.legal_finding,
            timeline_finding=state.timeline_finding,
            counterfactual_finding=state.counterfactual_finding,
        )
        candidate: object = None
        while attempts < 2:
            attempts += 1
            try:
                candidate = adapters.reviewer.review(draft, context)
            except Exception:
                return {
                    "case_state": state,
                    **_stop_update(
                        "REVIEWER_FAILURE",
                        "Editorial review failed safely.",
                        WorkflowStatus.FAILED,
                    ),
                }
            if isinstance(candidate, ReviewResult):
                result = candidate
                break
            if attempts == 1:
                try:
                    state = consume_retry(state, "structured_output")
                except BudgetExceeded:
                    break
        if not isinstance(candidate, ReviewResult):
            return {
                "case_state": state,
                **_stop_update(
                    "MALFORMED_REVIEW_OUTPUT",
                    "Editorial review returned invalid structured output twice.",
                    WorkflowStatus.FAILED,
                ),
            }
    state = owned_update(
        state,
        StateOwner.REVIEWER,
        review_result=result,
        review_attempt_count=state.review_attempt_count + max(attempts, 1),
    )
    state = _append_event(
        state,
        AuditEventType.REVIEW,
        "review",
        WorkflowStatus.REVIEWING,
        "EDITORIAL_INTEGRITY_REVIEWER",
        "Editorial review approved the draft."
        if result.approved
        else "Editorial review returned one structured defect.",
    )
    if not result.approved and state.correction_count >= 1:
        return {
            "case_state": state,
            **_stop_update(
                "SECOND_REVIEW_DEFECT",
                "The draft remained defective after the one allowed correction.",
                WorkflowStatus.INSUFFICIENT_OR_ESCALATED,
            ),
        }
    return {"case_state": state}


def _route_after_review(graph_state: _GraphState) -> str:
    if "stop_code" in graph_state:
        return "stop"
    result = graph_state["case_state"].review_result
    assert result is not None
    return "final_validation" if result.approved else "correction"


def _correction_node(graph_state: _GraphState) -> dict[str, object]:
    state = graph_state["case_state"]
    assert state.draft_brief is not None
    assert state.review_result is not None
    defect = state.review_result.defects[0]
    try:
        state = consume_graph_step(state)
        repaired = repair_draft(state.draft_brief, defect)
    except BudgetExceeded as exc:
        return {
            "case_state": state,
            **_stop_update(
                "BUDGET_EXHAUSTED",
                str(exc),
                WorkflowStatus.INSUFFICIENT_OR_ESCALATED,
            ),
        }
    except ValueError:
        return {
            "case_state": state,
            **_stop_update(
                "UNCORRECTABLE_REVIEW_DEFECT",
                "The defect cannot be corrected without new evidence.",
                WorkflowStatus.INSUFFICIENT_OR_ESCALATED,
            ),
        }
    state = owned_update(
        state,
        StateOwner.REVIEWER,
        draft_brief=repaired,
        review_result=None,
        correction_count=state.correction_count + 1,
    )
    state = _append_event(
        state,
        AuditEventType.REVIEW,
        "correction",
        WorkflowStatus.REVIEWING,
        "CASE_DIRECTOR",
        "Applied the one allowed bounded editorial correction.",
    )
    return {"case_state": state}


def _final_validation_node(graph_state: _GraphState) -> dict[str, object]:
    state = graph_state["case_state"]
    result = state.review_result
    try:
        state = consume_graph_step(state)
        if result is None or not result.approved or result.final_brief is None:
            raise ValueError("approved review did not provide a final brief")
        final_brief = CaseResearchBrief.model_validate(
            result.final_brief.model_dump(mode="python")
        )
        defect = validate_editorial_integrity(final_brief)
        if defect is not None:
            raise ValueError("final brief failed deterministic editorial validation")
        if state.draft_brief is None or not reviewer_preserves_evidence(
            state.draft_brief, final_brief
        ):
            raise ValueError("reviewer changed protected evidence fields")
        state = owned_update(
            state, StateOwner.REVIEWER, final_brief=final_brief
        )
        state = _append_event(
            state,
            AuditEventType.VALIDATION,
            "final_validation",
            WorkflowStatus.REVIEWING,
            "CASE_DIRECTOR",
            "The reviewed final brief passed strict contract validation.",
        )
        return {"case_state": state}
    except BudgetExceeded as exc:
        return {
            "case_state": state,
            **_stop_update(
                "BUDGET_EXHAUSTED",
                str(exc),
                WorkflowStatus.INSUFFICIENT_OR_ESCALATED,
            ),
        }
    except ValueError:
        return {
            "case_state": state,
            **_stop_update(
                "FINAL_VALIDATION_FAILED",
                "The reviewed brief failed final contract or evidence validation.",
                WorkflowStatus.FAILED,
            ),
        }


def _route_after_final_validation(graph_state: _GraphState) -> str:
    return "stop" if "stop_code" in graph_state else "complete"


def _complete_node(graph_state: _GraphState) -> dict[str, object]:
    state = graph_state["case_state"]
    try:
        state = consume_graph_step(state)
    except BudgetExceeded as exc:
        return {
            "case_state": _safe_stop(
                state,
                code="BUDGET_EXHAUSTED",
                message=str(exc),
                status=WorkflowStatus.INSUFFICIENT_OR_ESCALATED,
            )
        }
    state = owned_update(
        state,
        StateOwner.SUPERVISOR,
        status=WorkflowStatus.COMPLETED,
        completion_reason="REVIEWED_FINAL_BRIEF",
    )
    state = _append_event(
        state,
        AuditEventType.COMPLETION,
        "completion",
        WorkflowStatus.COMPLETED,
        "CASE_DIRECTOR",
        "Reviewed final brief completed.",
    )
    return {"case_state": state}


def _stop_node(graph_state: _GraphState) -> dict[str, object]:
    state = _safe_stop(
        graph_state["case_state"],
        code=graph_state.get("stop_code", "WORKFLOW_STOPPED"),
        message=graph_state.get("stop_message", "The workflow stopped safely."),
        status=graph_state.get("stop_status", WorkflowStatus.FAILED),
    )
    return {"case_state": state}


def create_case_graph(adapters: RoutingAdapters):
    """Compile the A2 workflow around injected v1 protocol implementations."""

    graph = StateGraph(_GraphState)
    graph.add_node("validate_request", _validate_request_node)
    graph.add_node("supervisor_plan", _plan_node)
    graph.add_node(
        "evidence_single",
        lambda state: _specialist_node(
            state, adapters, SpecialistRole.EVIDENCE, "evidence_execution"
        ),
    )
    graph.add_node(
        "timeline_single",
        lambda state: _specialist_node(
            state,
            adapters,
            SpecialistRole.TIMELINE_ANALYSIS,
            "timeline_execution",
        ),
    )
    graph.add_node(
        "explain_evidence",
        lambda state: _specialist_node(
            state, adapters, SpecialistRole.EVIDENCE, "evidence_execution"
        ),
    )
    graph.add_node(
        "explain_legal",
        lambda state: _specialist_node(
            state, adapters, SpecialistRole.LEGAL, "legal_execution"
        ),
    )
    graph.add_node(
        "what_if_evidence",
        lambda state: _specialist_node(
            state, adapters, SpecialistRole.EVIDENCE, "evidence_execution"
        ),
    )
    graph.add_node(
        "what_if_timeline",
        lambda state: _specialist_node(
            state,
            adapters,
            SpecialistRole.TIMELINE_ANALYSIS,
            "timeline_execution",
        ),
    )
    graph.add_node("join_findings", _join_node)
    graph.add_node("build_draft", _build_draft_node)
    graph.add_node("editorial_review", lambda state: _review_node(state, adapters))
    graph.add_node("bounded_correction", _correction_node)
    graph.add_node("final_validation", _final_validation_node)
    graph.add_node("complete", _complete_node)
    graph.add_node("safe_stop", _stop_node)

    graph.add_edge(START, "validate_request")
    graph.add_conditional_edges(
        "validate_request",
        _route_after_validation,
        {"plan": "supervisor_plan", "stop": "safe_stop"},
    )
    graph.add_conditional_edges(
        "supervisor_plan",
        _route_after_plan,
        {
            "stop": "safe_stop",
            "evidence_single": "evidence_single",
            "timeline_single": "timeline_single",
            "explain_evidence": "explain_evidence",
            "explain_legal": "explain_legal",
            "what_if_evidence": "what_if_evidence",
        },
    )
    graph.add_edge("evidence_single", "join_findings")
    graph.add_edge("timeline_single", "join_findings")
    graph.add_edge(["explain_evidence", "explain_legal"], "join_findings")
    graph.add_edge("what_if_evidence", "what_if_timeline")
    graph.add_edge("what_if_timeline", "join_findings")
    graph.add_conditional_edges(
        "join_findings",
        _route_after_join,
        {"build_draft": "build_draft", "stop": "safe_stop"},
    )
    graph.add_edge("build_draft", "editorial_review")
    graph.add_conditional_edges(
        "editorial_review",
        _route_after_review,
        {
            "final_validation": "final_validation",
            "correction": "bounded_correction",
            "stop": "safe_stop",
        },
    )
    graph.add_edge("bounded_correction", "editorial_review")
    graph.add_conditional_edges(
        "final_validation",
        _route_after_final_validation,
        {"complete": "complete", "stop": "safe_stop"},
    )
    graph.add_edge("complete", END)
    graph.add_edge("safe_stop", END)
    return graph.compile()


def run_case_query(
    query: CaseQuery,
    adapters: RoutingAdapters,
    *,
    state: CaseLensState | None = None,
    require_what_if_evidence: bool = False,
) -> CaseLensState:
    """Headless A2 service entry point for Streamlit and offline tests."""

    state = state or new_session(query)
    if state.session_id != query.session_id:
        raise ValueError("query and state session IDs must match")
    if state.status is WorkflowStatus.COMPLETED and state.final_brief is not None:
        return state
    workflow = create_case_graph(adapters)
    try:
        result = workflow.invoke(
            {
                "query": query,
                "case_state": state,
                "require_what_if_evidence": require_what_if_evidence,
            },
            config={"recursion_limit": max(25, state.graph_step_budget * 3)},
        )
    except GraphRecursionError:
        return _safe_stop(
            state,
            code="GRAPH_RECURSION_LIMIT",
            message="The workflow exceeded its bounded graph execution limit.",
            status=WorkflowStatus.INSUFFICIENT_OR_ESCALATED,
        )
    return result["case_state"]
