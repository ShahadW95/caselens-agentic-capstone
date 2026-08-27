from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from caselens.contracts import (  # noqa: E402
    CaseQuery,
    ConfidenceLabel,
    CounterfactualFinding,
    DelegationTask,
    EvidenceFinding,
    InteractionMode,
    LegalFinding,
    MVP_CASE_ID,
    ModelRequest,
    ModelResponse,
    SourceTier,
    SpecialistRole,
    SpecialistStateView,
    TimelineFinding,
)
from caselens.rag.chunking import Chunk  # noqa: E402
from caselens.rag.index import DeterministicFakeEmbeddingClient, IndexBundle, build_index, load_index  # noqa: E402
from caselens.rag.index import _document_hashes  # noqa: E402
from caselens.rag.loaders import CASE_ID_TO_FOLDER, load_knowledge_documents  # noqa: E402
from caselens.rag.chunking import chunk_documents  # noqa: E402
from caselens.specialists import SpecialistError, citation_from_manifest_source  # noqa: E402
from caselens.specialists.evidence import EvidenceSpecialist  # noqa: E402
from caselens.specialists.legal import LegalSpecialist  # noqa: E402
from caselens.specialists.timeline_analysis import TimelineAnalysisSpecialist  # noqa: E402
from caselens.services.case_loader import load_case_pack  # noqa: E402


# ---------------------------------------------------------------------------
# Shared fixtures / fakes
# ---------------------------------------------------------------------------


class ScriptedModel:
    """Test-only model boundary: pop one scripted outcome per generate() call.

    Each entry is either a response text (str) or an Exception instance to raise.
    """

    def __init__(self, script: list[str | Exception]) -> None:
        self._script = list(script)
        self.calls = 0
        self.requests: list[ModelRequest] = []

    def generate(self, request: ModelRequest) -> ModelResponse:
        self.calls += 1
        self.requests.append(request)
        if not self._script:
            raise AssertionError("ScriptedModel ran out of scripted responses")
        outcome = self._script.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return ModelResponse(request_id=request.request_id, text=outcome)


def _task(role: SpecialistRole, mode: InteractionMode, task_id: str = "task.test.1") -> DelegationTask:
    return DelegationTask(task_id=task_id, role=role, objective="Exercise the specialist.", mode=mode, language="en")


def _state(mode: InteractionMode, **query_kwargs) -> SpecialistStateView:
    return SpecialistStateView(
        query=CaseQuery(session_id="session.test.1", mode=mode, language="en", **query_kwargs)
    )


@pytest.fixture(scope="module")
def real_index() -> IndexBundle:
    docs = load_knowledge_documents(MVP_CASE_ID)
    chunks = chunk_documents(docs)
    client = DeterministicFakeEmbeddingClient(dimensions=768)
    return load_index(
        case_folder=CASE_ID_TO_FOLDER[MVP_CASE_ID],
        expected_document_hashes=_document_hashes(chunks),
        expected_dimensions=768,
    )


@pytest.fixture(scope="module")
def embedding_client() -> DeterministicFakeEmbeddingClient:
    return DeterministicFakeEmbeddingClient(dimensions=768)


def _empty_citation_index() -> tuple[IndexBundle, DeterministicFakeEmbeddingClient]:
    """A tiny index whose only chunk cites nothing, to force a zero-citation path."""

    chunk = Chunk(
        chunk_id="chunk.uncited.001",
        document_id="doc.uncited.001",
        file_path="knowledge_base/case_001/uncited.md",
        heading="Uncited section",
        text="This section makes a claim without citing any source at all.",
        source_type="TEAM_DIGEST_OVERVIEW",
        source_tier=SourceTier.A,
        jurisdiction="Fixture jurisdiction",
        original_source_urls=("https://example.invalid/uncited",),
        cited_source_ids=(),
    )
    client = DeterministicFakeEmbeddingClient(dimensions=8)
    bundle = build_index(MVP_CASE_ID, (chunk,), client)
    return bundle, client


SUPPORTED_CLAIM = "CLAIM_SEC_RECEIVED_COMPLAINTS"
CONTRADICTED_CLAIM = "CLAIM_MADOFF_STOLE_65B_CASH"
WHAT_IF_EVENT = "EVT_SCHEME_OPERATES_FOR_DECADES"
WHAT_IF_CHANGE = "CHG_INDEPENDENT_VERIFICATION_AFTER_COMPLAINT"


# ---------------------------------------------------------------------------
# EvidenceSpecialist
# ---------------------------------------------------------------------------


def test_evidence_check_claim_happy_path_no_model_call(real_index, embedding_client) -> None:
    model = ScriptedModel([])
    specialist = EvidenceSpecialist(model, embedding_client, real_index)
    result = specialist.execute(
        _task(SpecialistRole.EVIDENCE, InteractionMode.CHECK_CLAIM),
        _state(InteractionMode.CHECK_CLAIM, selected_claim_id=SUPPORTED_CLAIM),
    )
    assert isinstance(result, EvidenceFinding)
    assert model.calls == 0  # deterministic tool output needs no interpretation
    assert result.established_facts and not result.disputed_items and not result.unknowns


def test_evidence_check_claim_separates_contradicted_into_disputed(real_index, embedding_client) -> None:
    specialist = EvidenceSpecialist(ScriptedModel([]), embedding_client, real_index)
    result = specialist.execute(
        _task(SpecialistRole.EVIDENCE, InteractionMode.CHECK_CLAIM),
        _state(InteractionMode.CHECK_CLAIM, selected_claim_id=CONTRADICTED_CLAIM),
    )
    assert result.disputed_items and not result.established_facts
    kinds = {a.amount_kind.value for a in result.financial_amounts}
    assert {"FICTITIOUS_STATEMENT_BALANCE", "ESTIMATED_PRINCIPAL_LOSS"}.issubset(kinds)


def test_evidence_check_claim_missing_selection_is_rejected(real_index, embedding_client) -> None:
    specialist = EvidenceSpecialist(ScriptedModel([]), embedding_client, real_index)
    with pytest.raises(SpecialistError) as excinfo:
        specialist.execute(_task(SpecialistRole.EVIDENCE, InteractionMode.CHECK_CLAIM), _state(InteractionMode.CHECK_CLAIM))
    assert excinfo.value.code == "MISSING_CLAIM_SELECTION"


def test_evidence_ask_case_happy_path_calls_model_once(real_index, embedding_client) -> None:
    model = ScriptedModel(["SUMMARY: A grounded one-sentence answer."])
    specialist = EvidenceSpecialist(model, embedding_client, real_index)
    result = specialist.execute(
        _task(SpecialistRole.EVIDENCE, InteractionMode.ASK_CASE),
        _state(InteractionMode.ASK_CASE, user_query="Was Madoff a government official?"),
    )
    assert isinstance(result, EvidenceFinding)
    assert model.calls == 1
    assert result.summary == "A grounded one-sentence answer."
    assert result.citations


def test_evidence_ask_case_missing_query_is_rejected(real_index, embedding_client) -> None:
    specialist = EvidenceSpecialist(ScriptedModel([]), embedding_client, real_index)
    with pytest.raises(SpecialistError) as excinfo:
        specialist.execute(_task(SpecialistRole.EVIDENCE, InteractionMode.ASK_CASE), _state(InteractionMode.ASK_CASE, user_query=""))
    assert excinfo.value.code == "MISSING_QUERY_TEXT"


def test_evidence_ask_case_zero_citable_chunks_is_insufficient() -> None:
    bundle, client = _empty_citation_index()
    specialist = EvidenceSpecialist(ScriptedModel([]), client, bundle)
    with pytest.raises(SpecialistError) as excinfo:
        specialist.execute(
            _task(SpecialistRole.EVIDENCE, InteractionMode.ASK_CASE),
            _state(InteractionMode.ASK_CASE, user_query="Anything at all"),
        )
    assert excinfo.value.code == "INSUFFICIENT_EVIDENCE"


def test_evidence_ask_case_malformed_response_triggers_one_repair(real_index, embedding_client) -> None:
    model = ScriptedModel(["not the expected format", "SUMMARY: repaired answer."])
    specialist = EvidenceSpecialist(model, embedding_client, real_index)
    result = specialist.execute(
        _task(SpecialistRole.EVIDENCE, InteractionMode.ASK_CASE),
        _state(InteractionMode.ASK_CASE, user_query="Was Madoff a government official?"),
    )
    assert model.calls == 2
    assert result.summary == "repaired answer."
    assert result.confidence == ConfidenceLabel.MEDIUM


def test_evidence_ask_case_repeated_malformed_response_falls_back_without_raising(real_index, embedding_client) -> None:
    model = ScriptedModel(["still wrong", "still wrong again"])
    specialist = EvidenceSpecialist(model, embedding_client, real_index)
    result = specialist.execute(
        _task(SpecialistRole.EVIDENCE, InteractionMode.ASK_CASE),
        _state(InteractionMode.ASK_CASE, user_query="Was Madoff a government official?"),
    )
    assert model.calls == 2
    assert result.confidence == ConfidenceLabel.LOW
    assert result.citations  # deterministic facts survive a total model failure


def test_evidence_ask_case_model_exception_is_handled_safely(real_index, embedding_client) -> None:
    model = ScriptedModel([RuntimeError("simulated provider outage"), RuntimeError("simulated outage again")])
    specialist = EvidenceSpecialist(model, embedding_client, real_index)
    result = specialist.execute(
        _task(SpecialistRole.EVIDENCE, InteractionMode.ASK_CASE),
        _state(InteractionMode.ASK_CASE, user_query="Was Madoff a government official?"),
    )
    assert model.calls == 2
    assert result.confidence == ConfidenceLabel.LOW


def test_evidence_wrong_role_is_rejected(real_index, embedding_client) -> None:
    specialist = EvidenceSpecialist(ScriptedModel([]), embedding_client, real_index)
    with pytest.raises(SpecialistError) as excinfo:
        specialist.execute(
            _task(SpecialistRole.LEGAL, InteractionMode.ASK_CASE), _state(InteractionMode.ASK_CASE, user_query="x")
        )
    assert excinfo.value.code == "WRONG_ROLE"


def test_evidence_does_not_handle_other_modes(real_index, embedding_client) -> None:
    specialist = EvidenceSpecialist(ScriptedModel([]), embedding_client, real_index)
    for mode in (InteractionMode.VIEW_TIMELINE, InteractionMode.EXPLAIN_VERDICT, InteractionMode.WHAT_IF):
        with pytest.raises(SpecialistError) as excinfo:
            specialist.execute(_task(SpecialistRole.EVIDENCE, mode), _state(mode))
        assert excinfo.value.code == "UNSUPPORTED_MODE"


# ---------------------------------------------------------------------------
# LegalSpecialist
# ---------------------------------------------------------------------------


def test_legal_explain_verdict_happy_path(real_index, embedding_client) -> None:
    model = ScriptedModel(["EXPLANATION: A grounded plain-language explanation."])
    specialist = LegalSpecialist(model, embedding_client, real_index)
    result = specialist.execute(
        _task(SpecialistRole.LEGAL, InteractionMode.EXPLAIN_VERDICT),
        _state(InteractionMode.EXPLAIN_VERDICT, user_query="Explain the plea and sentence"),
    )
    assert isinstance(result, LegalFinding)
    assert model.calls == 1
    assert result.explanation == "A grounded plain-language explanation."
    assert len(result.proceeding_records) == 4
    assert "not legal advice" in result.educational_disclaimer.lower()


def test_legal_default_query_used_when_user_query_blank(real_index, embedding_client) -> None:
    model = ScriptedModel(["EXPLANATION: fine."])
    specialist = LegalSpecialist(model, embedding_client, real_index)
    result = specialist.execute(
        _task(SpecialistRole.LEGAL, InteractionMode.EXPLAIN_VERDICT), _state(InteractionMode.EXPLAIN_VERDICT)
    )
    assert isinstance(result, LegalFinding)
    assert model.calls == 1


def test_legal_malformed_response_triggers_one_repair(real_index, embedding_client) -> None:
    model = ScriptedModel(["nope", "EXPLANATION: repaired."])
    specialist = LegalSpecialist(model, embedding_client, real_index)
    result = specialist.execute(
        _task(SpecialistRole.LEGAL, InteractionMode.EXPLAIN_VERDICT), _state(InteractionMode.EXPLAIN_VERDICT)
    )
    assert model.calls == 2
    assert result.explanation == "repaired."
    assert result.confidence == ConfidenceLabel.MEDIUM


def test_legal_module_never_imports_the_counterfactual_tool() -> None:
    import ast

    source = (
        Path(__file__).resolve().parents[1] / "src" / "caselens" / "specialists" / "legal.py"
    ).read_text()
    imported_names = {
        alias.name
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    assert "simulate_counterfactual" not in imported_names
    assert not any("counterfactual" in (node.module or "") for node in ast.walk(ast.parse(source)) if isinstance(node, ast.ImportFrom))


def test_legal_does_not_handle_other_modes(real_index, embedding_client) -> None:
    specialist = LegalSpecialist(ScriptedModel([]), embedding_client, real_index)
    for mode in (InteractionMode.ASK_CASE, InteractionMode.CHECK_CLAIM, InteractionMode.VIEW_TIMELINE, InteractionMode.WHAT_IF):
        with pytest.raises(SpecialistError) as excinfo:
            specialist.execute(_task(SpecialistRole.LEGAL, mode), _state(mode))
        assert excinfo.value.code == "UNSUPPORTED_MODE"


# ---------------------------------------------------------------------------
# TimelineAnalysisSpecialist
# ---------------------------------------------------------------------------


def test_timeline_view_happy_path_uses_only_the_timeline_tool() -> None:
    specialist = TimelineAnalysisSpecialist()
    result = specialist.execute(
        _task(SpecialistRole.TIMELINE_ANALYSIS, InteractionMode.VIEW_TIMELINE), _state(InteractionMode.VIEW_TIMELINE)
    )
    assert isinstance(result, TimelineFinding)
    assert len(result.events) == 11  # 12 curated events minus the one with no date anchor at all
    assert all(e.citation_ids for e in result.events)


def test_what_if_happy_path_uses_only_the_counterfactual_tool() -> None:
    specialist = TimelineAnalysisSpecialist()
    result = specialist.execute(
        _task(SpecialistRole.TIMELINE_ANALYSIS, InteractionMode.WHAT_IF),
        _state(InteractionMode.WHAT_IF, selected_event_id=WHAT_IF_EVENT, allowed_change_id=WHAT_IF_CHANGE),
    )
    assert isinstance(result, CounterfactualFinding)
    assert "hypothetical" in result.mandatory_hypothetical_disclaimer.lower()
    assert result.citations


def test_what_if_missing_selection_is_rejected() -> None:
    specialist = TimelineAnalysisSpecialist()
    with pytest.raises(SpecialistError) as excinfo:
        specialist.execute(_task(SpecialistRole.TIMELINE_ANALYSIS, InteractionMode.WHAT_IF), _state(InteractionMode.WHAT_IF))
    assert excinfo.value.code == "MISSING_WHAT_IF_SELECTION"


def test_what_if_unknown_change_propagates_as_specialist_error() -> None:
    specialist = TimelineAnalysisSpecialist()
    with pytest.raises(SpecialistError) as excinfo:
        specialist.execute(
            _task(SpecialistRole.TIMELINE_ANALYSIS, InteractionMode.WHAT_IF),
            _state(InteractionMode.WHAT_IF, selected_event_id=WHAT_IF_EVENT, allowed_change_id="CHG_DOES_NOT_EXIST"),
        )
    assert excinfo.value.code == "TOOL_FAILURE"


def test_timeline_analysis_does_not_handle_other_modes() -> None:
    specialist = TimelineAnalysisSpecialist()
    for mode in (InteractionMode.ASK_CASE, InteractionMode.CHECK_CLAIM, InteractionMode.EXPLAIN_VERDICT):
        with pytest.raises(SpecialistError) as excinfo:
            specialist.execute(_task(SpecialistRole.TIMELINE_ANALYSIS, mode), _state(mode))
        assert excinfo.value.code == "UNSUPPORTED_MODE"


def test_timeline_analysis_wrong_role_is_rejected() -> None:
    specialist = TimelineAnalysisSpecialist()
    with pytest.raises(SpecialistError) as excinfo:
        specialist.execute(_task(SpecialistRole.EVIDENCE, InteractionMode.VIEW_TIMELINE), _state(InteractionMode.VIEW_TIMELINE))
    assert excinfo.value.code == "WRONG_ROLE"


# ---------------------------------------------------------------------------
# Shared helpers: unknown source ID, contract validation
# ---------------------------------------------------------------------------


def test_citation_from_manifest_source_rejects_unknown_id() -> None:
    pack = load_case_pack(MVP_CASE_ID)
    manifest_by_id = {s.source_id: s for s in pack.source_manifest.sources}
    with pytest.raises(SpecialistError) as excinfo:
        citation_from_manifest_source("SRC_DOES_NOT_EXIST", manifest_by_id)
    assert excinfo.value.code == "UNKNOWN_SOURCE_ID"


def test_all_specialist_outputs_are_the_frozen_contract_types(real_index, embedding_client) -> None:
    evidence = EvidenceSpecialist(ScriptedModel([]), embedding_client, real_index).execute(
        _task(SpecialistRole.EVIDENCE, InteractionMode.CHECK_CLAIM),
        _state(InteractionMode.CHECK_CLAIM, selected_claim_id=SUPPORTED_CLAIM),
    )
    legal = LegalSpecialist(ScriptedModel(["EXPLANATION: ok."]), embedding_client, real_index).execute(
        _task(SpecialistRole.LEGAL, InteractionMode.EXPLAIN_VERDICT), _state(InteractionMode.EXPLAIN_VERDICT)
    )
    timeline = TimelineAnalysisSpecialist().execute(
        _task(SpecialistRole.TIMELINE_ANALYSIS, InteractionMode.VIEW_TIMELINE), _state(InteractionMode.VIEW_TIMELINE)
    )
    counterfactual = TimelineAnalysisSpecialist().execute(
        _task(SpecialistRole.TIMELINE_ANALYSIS, InteractionMode.WHAT_IF),
        _state(InteractionMode.WHAT_IF, selected_event_id=WHAT_IF_EVENT, allowed_change_id=WHAT_IF_CHANGE),
    )
    assert isinstance(evidence, EvidenceFinding)
    assert isinstance(legal, LegalFinding)
    assert isinstance(timeline, TimelineFinding)
    assert isinstance(counterfactual, CounterfactualFinding)
