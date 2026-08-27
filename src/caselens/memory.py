"""Safe, session-scoped short-term memory for follow-up resolution."""

from __future__ import annotations

from typing import Literal, Self
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, model_validator

from .contracts import (
    MVP_CASE_ID,
    CaseQuery,
    CounterfactualFinding,
    EvidenceFinding,
    LanguageCode,
    LegalFinding,
    InteractionMode,
    MessageRole,
    SafeMessage,
    SpecialistRole,
    StableId,
    TimelineFinding,
)


class FindingSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    finding_id: StableId
    role: SpecialistRole
    summary: str


class SessionMemory(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    session_id: StableId
    case_id: Literal[MVP_CASE_ID] = MVP_CASE_ID
    language: LanguageCode = "ar"
    last_mode: InteractionMode | None = None
    selected_claim_id: StableId | None = None
    selected_event_id: StableId | None = None
    allowed_change_id: StableId | None = None
    messages: tuple[SafeMessage, ...] = ()
    finding_summaries: tuple[FindingSummary, ...] = ()

    @model_validator(mode="after")
    def excludes_raw_reasoning_and_payloads(self) -> Self:
        for message in self.messages:
            _safe_text(message.content)
        for finding in self.finding_summaries:
            _safe_text(finding.summary)
        return self


class FollowUpResolution(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    query: CaseQuery
    safe_context: tuple[FindingSummary, ...] = ()


_FORBIDDEN_MARKERS = (
    "chain_of_thought",
    "chain-of-thought",
    "raw_prompt",
    "raw_model_payload",
    "system prompt",
)


def _safe_text(text: str) -> str:
    normalized = text.strip()
    if not normalized:
        raise ValueError("safe memory text cannot be empty")
    lowered = normalized.lower()
    if any(marker in lowered for marker in _FORBIDDEN_MARKERS):
        raise ValueError("raw reasoning, prompts, and model payloads are not memory")
    return normalized


def new_memory(session_id: StableId, language: LanguageCode = "ar") -> SessionMemory:
    return SessionMemory(session_id=session_id, language=language)


def remember_query(memory: SessionMemory, query: CaseQuery) -> SessionMemory:
    if query.session_id != memory.session_id:
        raise ValueError("query and memory session IDs must match")
    messages = memory.messages
    if query.user_query.strip():
        messages += (
            SafeMessage(
                message_id=f"message.{memory.session_id}.{len(messages) + 1}",
                role=MessageRole.USER,
                language=query.language,
                content=_safe_text(query.user_query),
            ),
        )
    return memory.model_copy(
        update={
            "language": query.language,
            "last_mode": query.mode,
            "selected_claim_id": query.selected_claim_id or memory.selected_claim_id,
            "selected_event_id": query.selected_event_id or memory.selected_event_id,
            "allowed_change_id": query.allowed_change_id or memory.allowed_change_id,
            "messages": messages,
        }
    )


def remember_final_answer(
    memory: SessionMemory, content: str, *, language: LanguageCode | None = None
) -> SessionMemory:
    message = SafeMessage(
        message_id=f"message.{memory.session_id}.{len(memory.messages) + 1}",
        role=MessageRole.ASSISTANT,
        language=language or memory.language,
        content=_safe_text(content),
    )
    return memory.model_copy(update={"messages": memory.messages + (message,)})


def remember_finding(
    memory: SessionMemory,
    finding: EvidenceFinding | LegalFinding | TimelineFinding | CounterfactualFinding,
) -> SessionMemory:
    if isinstance(finding, EvidenceFinding):
        role = SpecialistRole.EVIDENCE
        text = finding.summary
    elif isinstance(finding, LegalFinding):
        role = SpecialistRole.LEGAL
        text = finding.explanation
    elif isinstance(finding, TimelineFinding):
        role = SpecialistRole.TIMELINE_ANALYSIS
        text = finding.summary
    else:
        role = SpecialistRole.TIMELINE_ANALYSIS
        text = finding.changed_assumption
    item = FindingSummary(
        finding_id=finding.finding_id,
        role=role,
        summary=_safe_text(text),
    )
    return memory.model_copy(
        update={"finding_summaries": memory.finding_summaries + (item,)}
    )


def resolve_follow_up(query: CaseQuery, memory: SessionMemory) -> FollowUpResolution:
    if query.session_id != memory.session_id:
        raise ValueError("query and memory session IDs must match")
    resolved = query.model_copy(
        update={
            "selected_claim_id": query.selected_claim_id or memory.selected_claim_id,
            "selected_event_id": query.selected_event_id or memory.selected_event_id,
            "allowed_change_id": query.allowed_change_id or memory.allowed_change_id,
        }
    )
    return FollowUpResolution(query=resolved, safe_context=memory.finding_summaries[-3:])


def reset_memory(
    memory: SessionMemory, *, new_session_id: StableId | None = None
) -> SessionMemory:
    return SessionMemory(
        session_id=new_session_id or f"session.{uuid4().hex}",
        language=memory.language,
    )
