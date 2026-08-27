"""Deterministic A1 request validation and Supervisor planning boundary."""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict

from .contracts import (
    AuditEvent,
    AuditEventType,
    CaseQuery,
    DelegationPlan,
    DelegationTask,
    InteractionMode,
    SafeError,
    SpecialistRole,
    WorkflowStatus,
)


class RouteValidation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    accepted: bool
    query: CaseQuery
    error: SafeError | None = None


_CLAIM_ID = re.compile(r"^claim[._:-][A-Za-z0-9][A-Za-z0-9._:-]*$")
EXPLAIN_JUDGMENT_DISPLAY_LABEL = "اشرح الحكم | Explain the Judgment"
_DEFAULT_JUDGMENT_QUESTION = {
    "ar": "اشرح الإقرار بالذنب والحكم الصادر في القضية.",
    "en": "Explain the guilty plea and judgment in this case.",
}


def _clarification(query: CaseQuery, code: str, message: str) -> RouteValidation:
    return RouteValidation(
        accepted=False,
        query=query,
        error=SafeError(
            error_id=f"error.{query.session_id}.{code.lower()}",
            code=code,
            user_message=message,
            recoverable=True,
        ),
    )


def validate_route(query: CaseQuery) -> RouteValidation:
    if query.mode is InteractionMode.ASK_CASE and not query.user_query.strip():
        return _clarification(query, "QUESTION_REQUIRED", "Please enter a case question.")
    if query.mode is InteractionMode.CHECK_CLAIM and (
        query.selected_claim_id is None
        or _CLAIM_ID.fullmatch(query.selected_claim_id) is None
    ):
        return _clarification(
            query,
            "CLAIM_ID_REQUIRED",
            "Select a valid case claim before checking support.",
        )
    if query.mode is InteractionMode.EXPLAIN_VERDICT and not query.user_query.strip():
        query = query.model_copy(
            update={"user_query": _DEFAULT_JUDGMENT_QUESTION[query.language]}
        )
    if query.mode is InteractionMode.WHAT_IF and (
        query.selected_event_id is None or query.allowed_change_id is None
    ):
        return _clarification(
            query,
            "WHAT_IF_SELECTION_REQUIRED",
            "Select both a case event and an allowed change.",
        )
    return RouteValidation(accepted=True, query=query)


def _task(
    query: CaseQuery,
    role: SpecialistRole,
    suffix: str,
    objective: str,
) -> DelegationTask:
    return DelegationTask(
        task_id=f"task.{query.session_id}.{suffix}",
        role=role,
        objective=objective,
        mode=query.mode,
        language=query.language,
    )


def build_delegation_plan(
    query: CaseQuery, *, require_what_if_evidence: bool = False
) -> DelegationPlan:
    if query.mode is InteractionMode.ASK_CASE:
        tasks = (
            _task(query, SpecialistRole.EVIDENCE, "evidence", "Answer from cited case evidence."),
        )
    elif query.mode is InteractionMode.VIEW_TIMELINE:
        tasks = (
            _task(
                query,
                SpecialistRole.TIMELINE_ANALYSIS,
                "timeline",
                "Return the requested case timeline using optional filters.",
            ),
        )
    elif query.mode is InteractionMode.CHECK_CLAIM:
        tasks = (
            _task(
                query,
                SpecialistRole.EVIDENCE,
                "claim",
                "Validate the selected claim with check_claim_support tool intent.",
            ),
        )
    elif query.mode is InteractionMode.EXPLAIN_VERDICT:
        tasks = (
            _task(
                query,
                SpecialistRole.EVIDENCE,
                "judgment_evidence",
                "Establish the cited plea, sentencing, and judgment facts.",
            ),
            _task(
                query,
                SpecialistRole.LEGAL,
                "judgment_legal",
                "Explain the guilty plea and judgment for educational use.",
            ),
        )
    else:
        timeline = _task(
            query,
            SpecialistRole.TIMELINE_ANALYSIS,
            "what_if",
            "Simulate only the selected event and allowed change.",
        )
        tasks = (timeline,)
        if require_what_if_evidence:
            evidence = _task(
                query,
                SpecialistRole.EVIDENCE,
                "what_if_evidence",
                "Validate unchanged factual premises required by the plan.",
            )
            timeline = timeline.model_copy(
                update={"dependency_task_ids": (evidence.task_id,)}
            )
            tasks = (
                evidence,
                timeline,
            )
    return DelegationPlan(
        plan_id=f"plan.{query.session_id}.{query.mode.value.lower()}",
        mode=query.mode,
        tasks=tasks,
        completion_condition="All selected independent tasks complete, then the Supervisor joins them.",
    )


def audit_event(
    *,
    session_id: str,
    sequence: int,
    event_type: AuditEventType,
    phase: str,
    status: WorkflowStatus,
    actor: str,
    safe_summary: str,
) -> AuditEvent:
    return AuditEvent(
        event_id=f"audit.{session_id}.{sequence}",
        event_type=event_type,
        phase=phase,
        status=status,
        actor=actor,
        safe_summary=safe_summary,
    )
