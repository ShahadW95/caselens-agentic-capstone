"""Strict v1 integration contracts shared by both implementation tracks."""

from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from typing import Annotated, Literal, Self

from pydantic import (
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)

CONTRACT_VERSION = "v1"
MVP_CASE_ID = "US_SDNY_09CR00213_DC"

NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
StableId = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=3, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$"),
]
LanguageCode = Literal["ar", "en"]


class ContractModel(BaseModel):
    """Base configuration for boundary objects."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class InteractionMode(str, Enum):
    ASK_CASE = "ASK_CASE"
    VIEW_TIMELINE = "VIEW_TIMELINE"
    CHECK_CLAIM = "CHECK_CLAIM"
    EXPLAIN_VERDICT = "EXPLAIN_VERDICT"
    WHAT_IF = "WHAT_IF"


class WorkflowStatus(str, Enum):
    INITIALIZED = "INITIALIZED"
    VALIDATING = "VALIDATING"
    PLANNING = "PLANNING"
    RUNNING = "RUNNING"
    REVIEWING = "REVIEWING"
    COMPLETED = "COMPLETED"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    INSUFFICIENT_OR_ESCALATED = "INSUFFICIENT_OR_ESCALATED"
    FAILED = "FAILED"


class SourceTier(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class ClaimStatus(str, Enum):
    ESTABLISHED = "ESTABLISHED"
    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    ALLEGED = "ALLEGED"
    DISPUTED = "DISPUTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    UNKNOWN = "UNKNOWN"


class ConfidenceLabel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class AmountKind(str, Enum):
    FICTITIOUS_STATEMENT_BALANCE = "FICTITIOUS_STATEMENT_BALANCE"
    ESTIMATED_PRINCIPAL_LOSS = "ESTIMATED_PRINCIPAL_LOSS"
    FORFEITURE_ORDER = "FORFEITURE_ORDER"
    RECOVERY = "RECOVERY"
    DISTRIBUTION = "DISTRIBUTION"


class ProceedingType(str, Enum):
    CRIMINAL_CASE = "CRIMINAL_CASE"
    SEC_ENFORCEMENT = "SEC_ENFORCEMENT"
    SIPA_LIQUIDATION = "SIPA_LIQUIDATION"
    DOJ_VICTIM_FUND = "DOJ_VICTIM_FUND"


class ProceedingStatus(str, Enum):
    CLOSED_FINAL = "CLOSED_FINAL"
    ONGOING_ENFORCEMENT = "ONGOING_ENFORCEMENT"
    ONGOING_RECOVERY = "ONGOING_RECOVERY"
    DISTRIBUTION_COMPLETE = "DISTRIBUTION_COMPLETE"
    ADMINISTRATION_CLOSED = "ADMINISTRATION_CLOSED"


class MessageRole(str, Enum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"


class SpecialistRole(str, Enum):
    EVIDENCE = "SOURCE_AND_EVIDENCE"
    LEGAL = "LEGAL_EXPLANATION"
    TIMELINE_ANALYSIS = "TIMELINE_AND_WHAT_IF"


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETE = "COMPLETE"
    BLOCKED = "BLOCKED"
    INSUFFICIENT = "INSUFFICIENT"


class TimelineTrack(str, Enum):
    SCHEME = "SCHEME"
    REGULATORY = "REGULATORY"
    CRIMINAL = "CRIMINAL"
    RECOVERY = "RECOVERY"


class ReviewDefectCode(str, Enum):
    MISSING_CITATION = "MISSING_CITATION"
    STATUS_MISLABEL = "STATUS_MISLABEL"
    AMOUNT_KIND_MISSING = "AMOUNT_KIND_MISSING"
    COUNTERFACTUAL_CERTAINTY = "COUNTERFACTUAL_CERTAINTY"
    DISCLAIMER_MISSING = "DISCLAIMER_MISSING"
    UNSAFE_CONTENT = "UNSAFE_CONTENT"


class AuditEventType(str, Enum):
    VALIDATION = "VALIDATION"
    ROUTE = "ROUTE"
    DELEGATION = "DELEGATION"
    RETRIEVAL = "RETRIEVAL"
    TOOL = "TOOL"
    REVIEW = "REVIEW"
    ERROR = "ERROR"
    COMPLETION = "COMPLETION"


class FinancialAmount(ContractModel):
    amount_id: StableId
    amount_kind: AmountKind
    currency: Annotated[str, StringConstraints(to_upper=True, pattern=r"^[A-Z]{3}$")]
    value_or_range: NonEmptyText
    as_of_date: date
    source_ids: tuple[StableId, ...] = Field(min_length=1)
    measurement_note: NonEmptyText


class ProceedingRecord(ContractModel):
    proceeding_id: StableId
    case_id: Literal[MVP_CASE_ID] = MVP_CASE_ID
    proceeding_type: ProceedingType
    status: ProceedingStatus
    status_as_of: date
    source_ids: tuple[StableId, ...] = Field(min_length=1)
    status_note: NonEmptyText

    @model_validator(mode="after")
    def status_matches_proceeding(self) -> Self:
        allowed = {
            ProceedingType.CRIMINAL_CASE: {ProceedingStatus.CLOSED_FINAL},
            ProceedingType.SEC_ENFORCEMENT: {
                ProceedingStatus.CLOSED_FINAL,
                ProceedingStatus.ONGOING_ENFORCEMENT,
            },
            ProceedingType.SIPA_LIQUIDATION: {
                ProceedingStatus.ONGOING_RECOVERY,
                ProceedingStatus.ADMINISTRATION_CLOSED,
            },
            ProceedingType.DOJ_VICTIM_FUND: {
                ProceedingStatus.ONGOING_RECOVERY,
                ProceedingStatus.DISTRIBUTION_COMPLETE,
            },
        }
        if self.status not in allowed[self.proceeding_type]:
            raise ValueError("proceeding status is incompatible with proceeding type")
        return self


class CaseQuery(ContractModel):
    session_id: StableId
    case_id: Literal[MVP_CASE_ID] = MVP_CASE_ID
    mode: InteractionMode
    language: LanguageCode = "ar"
    user_query: str = ""
    selected_claim_id: StableId | None = None
    selected_event_id: StableId | None = None
    allowed_change_id: StableId | None = None


class SafeMessage(ContractModel):
    message_id: StableId
    role: MessageRole
    language: LanguageCode
    content: NonEmptyText
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DelegationTask(ContractModel):
    task_id: StableId
    role: SpecialistRole
    objective: NonEmptyText
    case_id: Literal[MVP_CASE_ID] = MVP_CASE_ID
    mode: InteractionMode
    language: LanguageCode
    dependency_task_ids: tuple[StableId, ...] = ()
    status: TaskStatus = TaskStatus.PENDING

    @model_validator(mode="after")
    def cannot_depend_on_self(self) -> Self:
        if self.task_id in self.dependency_task_ids:
            raise ValueError("a delegation task cannot depend on itself")
        return self


class DelegationPlan(ContractModel):
    plan_id: StableId
    case_id: Literal[MVP_CASE_ID] = MVP_CASE_ID
    mode: InteractionMode
    tasks: tuple[DelegationTask, ...] = Field(min_length=1, max_length=3)
    completion_condition: NonEmptyText

    @model_validator(mode="after")
    def task_ids_are_unique_and_local(self) -> Self:
        task_ids = [task.task_id for task in self.tasks]
        if len(task_ids) != len(set(task_ids)):
            raise ValueError("delegation task IDs must be unique")
        known = set(task_ids)
        if any(not set(task.dependency_task_ids).issubset(known) for task in self.tasks):
            raise ValueError("task dependencies must refer to tasks in the same plan")
        return self


class SourceCitation(ContractModel):
    citation_id: StableId
    source_id: StableId
    document_id: StableId
    chunk_id: StableId
    title: NonEmptyText
    heading: NonEmptyText
    source_type: NonEmptyText
    source_tier: SourceTier
    original_url: AnyHttpUrl | None = None


class RetrievalPlan(ContractModel):
    retrieval_id: StableId
    task_id: StableId
    case_id: Literal[MVP_CASE_ID] = MVP_CASE_ID
    query: NonEmptyText
    permitted_source_types: tuple[NonEmptyText, ...] = ()
    permitted_source_tiers: tuple[SourceTier, ...] = (
        SourceTier.A,
        SourceTier.B,
    )
    top_k: int = Field(default=5, ge=1, le=10)
    round_number: int = Field(default=1, ge=1, le=2)


class RetrievedChunk(ContractModel):
    chunk_id: StableId
    document_id: StableId
    file_path: NonEmptyText
    heading: NonEmptyText
    excerpt: NonEmptyText
    similarity_score: float = Field(ge=0.0, le=1.0)
    source_type: NonEmptyText
    source_tier: SourceTier
    jurisdiction: NonEmptyText
    original_source_urls: tuple[AnyHttpUrl, ...] = Field(min_length=1)


class EvidenceAssessment(ContractModel):
    assessment_id: StableId
    retrieval_id: StableId
    sufficient: bool
    rationale: NonEmptyText
    relevant_chunk_ids: tuple[StableId, ...]
    missing_information: tuple[NonEmptyText, ...] = ()
    may_reformulate: bool = False

    @model_validator(mode="after")
    def reformulation_requires_insufficiency(self) -> Self:
        if self.sufficient and self.may_reformulate:
            raise ValueError("sufficient evidence must not trigger reformulation")
        return self


class FindingStatement(ContractModel):
    statement_id: StableId
    text: NonEmptyText
    status: ClaimStatus
    citation_ids: tuple[StableId, ...] = Field(min_length=1)


class EvidenceFinding(ContractModel):
    finding_id: StableId
    task_id: StableId
    case_id: Literal[MVP_CASE_ID] = MVP_CASE_ID
    summary: NonEmptyText
    established_facts: tuple[FindingStatement, ...] = ()
    allegations: tuple[FindingStatement, ...] = ()
    disputed_items: tuple[FindingStatement, ...] = ()
    unknowns: tuple[FindingStatement, ...] = ()
    financial_amounts: tuple[FinancialAmount, ...] = ()
    citations: tuple[SourceCitation, ...] = Field(min_length=1)
    confidence: ConfidenceLabel

    @model_validator(mode="after")
    def validate_categories_and_citations(self) -> Self:
        _validate_finding_categories(self)
        return self


class LegalFinding(ContractModel):
    finding_id: StableId
    task_id: StableId
    case_id: Literal[MVP_CASE_ID] = MVP_CASE_ID
    explanation: NonEmptyText
    established_facts: tuple[FindingStatement, ...] = ()
    allegations: tuple[FindingStatement, ...] = ()
    disputed_items: tuple[FindingStatement, ...] = ()
    unknowns: tuple[FindingStatement, ...] = ()
    proceeding_records: tuple[ProceedingRecord, ...] = Field(min_length=1)
    citations: tuple[SourceCitation, ...] = Field(min_length=1)
    confidence: ConfidenceLabel
    educational_disclaimer: NonEmptyText

    @model_validator(mode="after")
    def validate_categories_and_citations(self) -> Self:
        _validate_finding_categories(self)
        return self


class TimelineEvent(ContractModel):
    event_id: StableId
    event_date: date
    title: NonEmptyText
    summary: NonEmptyText
    track: TimelineTrack
    actor_ids: tuple[StableId, ...] = ()
    evidence_ids: tuple[StableId, ...] = Field(min_length=1)
    source_ids: tuple[StableId, ...] = Field(min_length=1)
    citation_ids: tuple[StableId, ...] = Field(min_length=1)


class TimelineFinding(ContractModel):
    finding_id: StableId
    task_id: StableId
    case_id: Literal[MVP_CASE_ID] = MVP_CASE_ID
    summary: NonEmptyText
    events: tuple[TimelineEvent, ...] = Field(min_length=1)
    citations: tuple[SourceCitation, ...] = Field(min_length=1)
    confidence: ConfidenceLabel

    @model_validator(mode="after")
    def event_citations_exist(self) -> Self:
        known = {citation.citation_id for citation in self.citations}
        used = {item for event in self.events for item in event.citation_ids}
        if not used.issubset(known):
            raise ValueError("timeline events reference unknown citations")
        return self


class CounterfactualFinding(ContractModel):
    finding_id: StableId
    task_id: StableId
    case_id: Literal[MVP_CASE_ID] = MVP_CASE_ID
    event_id: StableId
    allowed_change_id: StableId
    changed_assumption: NonEmptyText
    directly_affected_nodes: tuple[StableId, ...] = Field(min_length=1)
    downstream_possible_effects: tuple[NonEmptyText, ...] = Field(min_length=1)
    unchanged_facts: tuple[FindingStatement, ...] = Field(min_length=1)
    unknowns: tuple[NonEmptyText, ...] = Field(min_length=1)
    confidence: ConfidenceLabel
    mandatory_hypothetical_disclaimer: NonEmptyText
    citations: tuple[SourceCitation, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def disclaimer_and_citations_are_safe(self) -> Self:
        disclaimer = self.mandatory_hypothetical_disclaimer.lower()
        if "hypothetical" not in disclaimer and "افتراضي" not in disclaimer:
            raise ValueError("counterfactual disclaimer must identify the output as hypothetical")
        known = {citation.citation_id for citation in self.citations}
        used = {item for fact in self.unchanged_facts for item in fact.citation_ids}
        if not used.issubset(known):
            raise ValueError("counterfactual facts reference unknown citations")
        return self


class ReviewDefect(ContractModel):
    defect_id: StableId
    code: ReviewDefectCode
    field_path: NonEmptyText
    description: NonEmptyText
    responsible_role: SpecialistRole | Literal["CASE_DIRECTOR"]


class AuditEvent(ContractModel):
    event_id: StableId
    event_type: AuditEventType
    phase: NonEmptyText
    status: WorkflowStatus
    actor: NonEmptyText
    safe_summary: NonEmptyText
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CaseResearchBrief(ContractModel):
    brief_id: StableId
    session_id: StableId
    case_id: Literal[MVP_CASE_ID] = MVP_CASE_ID
    mode: InteractionMode
    language: LanguageCode
    concise_answer: NonEmptyText
    established_facts: tuple[FindingStatement, ...] = ()
    allegations: tuple[FindingStatement, ...] = ()
    disputed_items: tuple[FindingStatement, ...] = ()
    unknowns: tuple[FindingStatement, ...] = ()
    legal_explanation: NonEmptyText | None = None
    timeline_events: tuple[TimelineEvent, ...] = ()
    counterfactual: CounterfactualFinding | None = None
    financial_amounts: tuple[FinancialAmount, ...] = ()
    proceeding_records: tuple[ProceedingRecord, ...] = ()
    citations: tuple[SourceCitation, ...] = Field(min_length=1)
    confidence: ConfidenceLabel
    limitations: tuple[NonEmptyText, ...] = Field(min_length=1)
    educational_disclaimer: NonEmptyText

    @model_validator(mode="after")
    def preserve_status_and_citations(self) -> Self:
        _validate_finding_categories(self)
        if "legal advice" not in self.educational_disclaimer.lower() and "استشارة قانونية" not in self.educational_disclaimer:
            raise ValueError("final brief must state that it is not legal advice")
        known = {citation.citation_id for citation in self.citations}
        statements = (
            self.established_facts
            + self.allegations
            + self.disputed_items
            + self.unknowns
        )
        used = {item for statement in statements for item in statement.citation_ids}
        if not used.issubset(known):
            raise ValueError("brief statements reference unknown citations")
        if self.counterfactual is not None:
            nested = {citation.citation_id for citation in self.counterfactual.citations}
            if not nested.issubset(known):
                raise ValueError("counterfactual citations must be included in brief citations")
        return self


class ReviewResult(ContractModel):
    review_id: StableId
    approved: bool
    defects: tuple[ReviewDefect, ...] = Field(default=(), max_length=1)
    final_brief: CaseResearchBrief | None = None

    @model_validator(mode="after")
    def approval_matches_result(self) -> Self:
        if self.approved and (self.defects or self.final_brief is None):
            raise ValueError("approved review requires a final brief and no defect")
        if not self.approved and len(self.defects) != 1:
            raise ValueError("rejected review requires exactly one structured defect")
        return self


class SafeError(ContractModel):
    error_id: StableId
    code: NonEmptyText
    user_message: NonEmptyText
    recoverable: bool
    retry_allowed: bool = False


class SpecialistStateView(ContractModel):
    query: CaseQuery
    safe_messages: tuple[SafeMessage, ...] = ()
    completed_task_ids: tuple[StableId, ...] = ()
    retrieved_chunk_refs: tuple[StableId, ...] = ()


class ReviewContext(ContractModel):
    evidence_finding: EvidenceFinding | None = None
    legal_finding: LegalFinding | None = None
    timeline_finding: TimelineFinding | None = None
    counterfactual_finding: CounterfactualFinding | None = None


class ModelRequest(ContractModel):
    request_id: StableId
    operation: NonEmptyText
    public_case_context: NonEmptyText
    user_question: NonEmptyText
    language: LanguageCode
    contains_private_profile: Literal[False] = False
    contains_secret: Literal[False] = False


class ModelResponse(ContractModel):
    request_id: StableId
    text: NonEmptyText
    model_id: Literal["gemini-3.7-flash"] = "gemini-3.7-flash"


def _validate_finding_categories(
    finding: EvidenceFinding | LegalFinding | CaseResearchBrief,
) -> None:
    category_statuses = {
        "established_facts": {ClaimStatus.ESTABLISHED, ClaimStatus.SUPPORTED},
        "allegations": {ClaimStatus.ALLEGED},
        "disputed_items": {
            ClaimStatus.CONTRADICTED,
            ClaimStatus.PARTIALLY_SUPPORTED,
            ClaimStatus.DISPUTED,
        },
        "unknowns": {ClaimStatus.INSUFFICIENT_EVIDENCE, ClaimStatus.UNKNOWN},
    }
    for field_name, allowed in category_statuses.items():
        statements = getattr(finding, field_name)
        if any(statement.status not in allowed for statement in statements):
            raise ValueError(f"{field_name} contains an incompatible claim status")

    known = {citation.citation_id for citation in finding.citations}
    used = {
        citation_id
        for field_name in category_statuses
        for statement in getattr(finding, field_name)
        for citation_id in statement.citation_ids
    }
    if not used.issubset(known):
        raise ValueError("finding statements reference unknown citations")
