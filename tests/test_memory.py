"""Offline tests for safe, resettable short-term memory."""

from __future__ import annotations

import pytest

from caselens.adapters import FakeEvidenceSpecialist
from caselens.contracts import (
    CaseQuery,
    DelegationTask,
    InteractionMode,
    MessageRole,
    SpecialistRole,
    SpecialistStateView,
)
from caselens.memory import (
    new_memory,
    remember_final_answer,
    remember_finding,
    remember_query,
    reset_memory,
    resolve_follow_up,
)


def test_follow_up_resolves_selected_id_and_uses_only_safe_summaries() -> None:
    first = CaseQuery(
        session_id="session.memory.001",
        mode=InteractionMode.CHECK_CLAIM,
        language="en",
        user_query="Check that claim.",
        selected_claim_id="claim.test.001",
    )
    memory = remember_query(new_memory(first.session_id, "en"), first)
    task = DelegationTask(
        task_id="task.memory.evidence",
        role=SpecialistRole.EVIDENCE,
        objective="Check cited evidence.",
        mode=first.mode,
        language="en",
    )
    finding = FakeEvidenceSpecialist().execute(
        task, SpecialistStateView(query=first)
    )
    memory = remember_finding(memory, finding)
    memory = remember_final_answer(memory, "The cited fixture supports the result.")
    follow_up = CaseQuery(
        session_id=first.session_id,
        mode=InteractionMode.CHECK_CLAIM,
        language="en",
        user_query="Why was that argument rejected?",
    )

    resolved = resolve_follow_up(follow_up, memory)

    assert resolved.query.selected_claim_id == "claim.test.001"
    assert resolved.safe_context == memory.finding_summaries
    assert tuple(message.role for message in memory.messages) == (
        MessageRole.USER,
        MessageRole.ASSISTANT,
    )
    assert set(type(memory).model_fields) == {
        "session_id",
        "case_id",
        "language",
        "last_mode",
        "selected_claim_id",
        "selected_event_id",
        "allowed_change_id",
        "messages",
        "finding_summaries",
    }


def test_memory_rejects_raw_reasoning_markers() -> None:
    memory = new_memory("session.memory.safe", "en")

    with pytest.raises(ValueError, match="raw reasoning"):
        remember_final_answer(memory, "raw_model_payload: private")


def test_reset_clears_memory_and_selected_ids() -> None:
    query = CaseQuery(
        session_id="session.memory.old",
        mode=InteractionMode.WHAT_IF,
        selected_event_id="event.test.001",
        allowed_change_id="change.test.001",
    )
    populated = remember_query(new_memory(query.session_id), query)

    reset = reset_memory(populated, new_session_id="session.memory.new")

    assert reset.session_id == "session.memory.new"
    assert reset.messages == ()
    assert reset.finding_summaries == ()
    assert reset.selected_claim_id is None
    assert reset.selected_event_id is None
    assert reset.allowed_change_id is None
