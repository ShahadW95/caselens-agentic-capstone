"""Typed orchestration state, ownership rules, reducers, and budgets."""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from .contracts import (
    MVP_CASE_ID,
    AuditEvent,
    CaseQuery,
    CaseResearchBrief,
    CounterfactualFinding,
    DelegationPlan,
    DelegationTask,
    EvidenceFinding,
    InteractionMode,
    LanguageCode,
    LegalFinding,
    ProceedingStatus,
    RetrievalPlan,
    ReviewResult,
    SafeError,
    SafeMessage,
    StableId,
    TimelineFinding,
    WorkflowStatus,
)


class StateOwner(str, Enum):
    INPUT = "INPUT"
    MEMORY = "MEMORY"
    SUPERVISOR = "SUPERVISOR"
    RETRIEVAL = "RETRIEVAL"
    EVIDENCE = "EVIDENCE"
    LEGAL = "LEGAL"
    TIMELINE = "TIMELINE"
    REVIEWER = "REVIEWER"


class RetryCounters(BaseModel):
    """Bounded retry counters; A1 exposes enforcement but performs no retries."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    structured_output: int = Field(default=0, ge=0)
    adapter: int = Field(default=0, ge=0)

    @property
    def total(self) -> int:
        return self.structured_output + self.adapter


class CaseLensState(BaseModel):
    """Immutable shared state; changes pass through owned updates or reducers."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    session_id: StableId
    case_id: Literal[MVP_CASE_ID] = MVP_CASE_ID
    case_status: ProceedingStatus = ProceedingStatus.CLOSED_FINAL
    mode: InteractionMode | None = None
    language: LanguageCode = "ar"
    user_query: str = ""
    selected_claim_id: StableId | None = None
    selected_event_id: StableId | None = None
    hypothetical_change: StableId | None = None

    turn_count: int = Field(default=0, ge=0)
    max_turns: int = Field(default=4, ge=1)
    specialist_call_count: int = Field(default=0, ge=0)
    specialist_call_budget: int = Field(default=3, ge=1)
    retry_counters: RetryCounters = Field(default_factory=RetryCounters)
    retry_budget: int = Field(default=1, ge=0)
    graph_step_count: int = Field(default=0, ge=0)
    graph_step_budget: int = Field(default=12, ge=1)

    short_term_messages: tuple[SafeMessage, ...] = ()
    plan: DelegationPlan | None = None
    delegation_tasks: tuple[DelegationTask, ...] = ()
    retrieval_plans: tuple[RetrievalPlan, ...] = ()
    retrieval_rounds: int = Field(default=0, ge=0, le=2)
    retrieved_chunk_refs: tuple[StableId, ...] = ()

    evidence_finding: EvidenceFinding | None = None
    legal_finding: LegalFinding | None = None
    timeline_finding: TimelineFinding | None = None
    counterfactual_finding: CounterfactualFinding | None = None
    draft_brief: CaseResearchBrief | None = None
    review_result: ReviewResult | None = None
    final_brief: CaseResearchBrief | None = None

    validation_errors: tuple[SafeError, ...] = ()
    audit_events: tuple[AuditEvent, ...] = ()
    status: WorkflowStatus = WorkflowStatus.INITIALIZED
    completion_reason: str | None = None


_OWNED_FIELDS: dict[StateOwner, frozenset[str]] = {
    StateOwner.INPUT: frozenset(
        {
            "mode",
            "language",
            "user_query",
            "selected_claim_id",
            "selected_event_id",
            "hypothetical_change",
        }
    ),
    StateOwner.MEMORY: frozenset({"short_term_messages"}),
    StateOwner.SUPERVISOR: frozenset(
        {
            "plan",
            "delegation_tasks",
            "status",
            "completion_reason",
            "turn_count",
            "specialist_call_count",
            "retry_counters",
            "graph_step_count",
        }
    ),
    StateOwner.RETRIEVAL: frozenset({"retrieval_plans", "retrieval_rounds"}),
    StateOwner.EVIDENCE: frozenset({"evidence_finding"}),
    StateOwner.LEGAL: frozenset({"legal_finding"}),
    StateOwner.TIMELINE: frozenset(
        {"timeline_finding", "counterfactual_finding"}
    ),
    StateOwner.REVIEWER: frozenset(
        {"draft_brief", "review_result", "final_brief"}
    ),
}


class StateOwnershipError(ValueError):
    """Raised when a component attempts to write another owner's field."""


class BudgetExceeded(RuntimeError):
    """Raised before a bounded orchestration operation would exceed its limit."""


def new_session(
    query: CaseQuery,
    *,
    max_turns: int = 4,
    specialist_call_budget: int = 3,
    retry_budget: int = 1,
    graph_step_budget: int = 12,
) -> CaseLensState:
    """Create a clean session using the caller-supplied stable session ID."""

    return CaseLensState(
        session_id=query.session_id,
        mode=query.mode,
        language=query.language,
        user_query=query.user_query,
        selected_claim_id=query.selected_claim_id,
        selected_event_id=query.selected_event_id,
        hypothetical_change=query.allowed_change_id,
        max_turns=max_turns,
        specialist_call_budget=specialist_call_budget,
        retry_budget=retry_budget,
        graph_step_budget=graph_step_budget,
    )


def owned_update(
    state: CaseLensState, owner: StateOwner, **updates: Any
) -> CaseLensState:
    """Apply an immutable update only when every field belongs to the writer."""

    disallowed = set(updates).difference(_OWNED_FIELDS[owner])
    if disallowed:
        names = ", ".join(sorted(disallowed))
        raise StateOwnershipError(f"{owner.value} cannot update: {names}")
    return state.model_copy(update=updates)


def append_messages(
    state: CaseLensState, *messages: SafeMessage
) -> CaseLensState:
    return owned_update(
        state,
        StateOwner.MEMORY,
        short_term_messages=state.short_term_messages + tuple(messages),
    )


def append_errors(state: CaseLensState, *errors: SafeError) -> CaseLensState:
    return state.model_copy(
        update={"validation_errors": state.validation_errors + tuple(errors)}
    )


def append_audit_events(
    state: CaseLensState, *events: AuditEvent
) -> CaseLensState:
    return state.model_copy(update={"audit_events": state.audit_events + tuple(events)})


def append_retrieved_chunk_refs(
    state: CaseLensState, *chunk_refs: StableId
) -> CaseLensState:
    return state.model_copy(
        update={"retrieved_chunk_refs": state.retrieved_chunk_refs + tuple(chunk_refs)}
    )


def consume_turn(state: CaseLensState) -> CaseLensState:
    if state.turn_count >= state.max_turns:
        raise BudgetExceeded("turn budget exhausted")
    return owned_update(
        state, StateOwner.SUPERVISOR, turn_count=state.turn_count + 1
    )


def consume_specialist_call(state: CaseLensState) -> CaseLensState:
    if state.specialist_call_count >= state.specialist_call_budget:
        raise BudgetExceeded("specialist-call budget exhausted")
    return owned_update(
        state,
        StateOwner.SUPERVISOR,
        specialist_call_count=state.specialist_call_count + 1,
    )


def consume_graph_step(state: CaseLensState) -> CaseLensState:
    if state.graph_step_count >= state.graph_step_budget:
        raise BudgetExceeded("graph-step budget exhausted")
    return owned_update(
        state,
        StateOwner.SUPERVISOR,
        graph_step_count=state.graph_step_count + 1,
    )


def consume_retry(state: CaseLensState, kind: Literal["structured_output", "adapter"]) -> CaseLensState:
    if state.retry_counters.total >= state.retry_budget:
        raise BudgetExceeded("retry budget exhausted")
    counters = state.retry_counters.model_copy(
        update={kind: getattr(state.retry_counters, kind) + 1}
    )
    return owned_update(state, StateOwner.SUPERVISOR, retry_counters=counters)
