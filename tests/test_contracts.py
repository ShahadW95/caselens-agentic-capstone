from __future__ import annotations

import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import caselens
import caselens.contracts as contract_module
from caselens.adapters import create_development_fake_adapters
from caselens.config import RuntimeConfig
from caselens.contracts import (
    CaseQuery,
    CaseResearchBrief,
    ClaimStatus,
    ConfidenceLabel,
    CounterfactualFinding,
    DelegationTask,
    EvidenceFinding,
    FindingStatement,
    InteractionMode,
    MVP_CASE_ID,
    ProceedingRecord,
    ProceedingStatus,
    ProceedingType,
    ReviewContext,
    SourceCitation,
    SourceTier,
    SpecialistRole,
    SpecialistStateView,
)
from caselens.protocols import (
    EvidenceSpecialistProtocol,
    LegalSpecialistProtocol,
    ReviewerProtocol,
    TimelineAnalysisSpecialistProtocol,
)


def citation() -> SourceCitation:
    return SourceCitation(
        citation_id="cit.test.001",
        source_id="source.test.001",
        document_id="document.test.001",
        chunk_id="chunk.test.001",
        title="Test source",
        heading="Test heading",
        source_type="official_record",
        source_tier=SourceTier.A,
        original_url="https://example.invalid/source",
    )


def fact(status: ClaimStatus = ClaimStatus.ESTABLISHED) -> FindingStatement:
    return FindingStatement(
        statement_id="statement.test.001",
        text="A fixture statement.",
        status=status,
        citation_ids=("cit.test.001",),
    )


def task(role: SpecialistRole, mode: InteractionMode) -> DelegationTask:
    return DelegationTask(
        task_id=f"task.test.{role.value.lower()}",
        role=role,
        objective="Exercise protocol compatibility.",
        mode=mode,
        language="en",
    )


def state(mode: InteractionMode) -> SpecialistStateView:
    return SpecialistStateView(
        query=CaseQuery(
            session_id="session.test.001",
            mode=mode,
            language="en",
            user_query="Fixture question",
            selected_event_id="event.test.001" if mode is InteractionMode.WHAT_IF else None,
            allowed_change_id="change.test.001" if mode is InteractionMode.WHAT_IF else None,
        )
    )


def test_import_smoke_and_contract_version() -> None:
    assert caselens.CONTRACT_VERSION == "v1"
    assert MVP_CASE_ID == "US_SDNY_09CR00213_DC"


def test_contracts_have_no_raw_reasoning_or_prompt_fields() -> None:
    forbidden = {"chain_of_thought", "raw_reasoning", "reasoning", "raw_prompt"}
    contract_types = (
        item
        for item in vars(contract_module).values()
        if isinstance(item, type)
        and issubclass(item, BaseModel)
        and item is not BaseModel
    )
    for contract_type in contract_types:
        assert forbidden.isdisjoint(contract_type.model_fields)


def test_enum_and_confidence_validation() -> None:
    with pytest.raises(ValidationError):
        CaseQuery(
            session_id="session.test.001",
            mode="FREE_CHAT",
            language="en",
        )
    with pytest.raises(ValidationError):
        EvidenceFinding(
            finding_id="finding.test.001",
            task_id="task.test.001",
            summary="Invalid confidence fixture.",
            citations=(citation(),),
            confidence="CERTAIN",
        )


def test_findings_require_citations() -> None:
    with pytest.raises(ValidationError):
        EvidenceFinding(
            finding_id="finding.test.001",
            task_id="task.test.001",
            summary="Missing citation fixture.",
            confidence=ConfidenceLabel.LOW,
        )


def test_allegation_cannot_be_labeled_as_established_fact() -> None:
    with pytest.raises(ValidationError):
        EvidenceFinding(
            finding_id="finding.test.001",
            task_id="task.test.001",
            summary="Status mixing fixture.",
            established_facts=(fact(ClaimStatus.ALLEGED),),
            citations=(citation(),),
            confidence=ConfidenceLabel.LOW,
        )


def test_proceeding_statuses_cannot_be_mixed() -> None:
    with pytest.raises(ValidationError):
        ProceedingRecord(
            proceeding_id="proceeding.test.001",
            proceeding_type=ProceedingType.CRIMINAL_CASE,
            status=ProceedingStatus.ONGOING_RECOVERY,
            status_as_of=date(2026, 2, 27),
            source_ids=("source.test.001",),
            status_note="Invalid mixed status.",
        )


def test_counterfactual_requires_unknowns_and_hypothetical_disclaimer() -> None:
    base = {
        "finding_id": "finding.test.counterfactual",
        "task_id": "task.test.timeline",
        "event_id": "event.test.001",
        "allowed_change_id": "change.test.001",
        "changed_assumption": "A bounded change.",
        "directly_affected_nodes": ("node.test.001",),
        "downstream_possible_effects": ("An effect may occur.",),
        "unchanged_facts": (fact(),),
        "confidence": ConfidenceLabel.LOW,
        "citations": (citation(),),
    }
    with pytest.raises(ValidationError):
        CounterfactualFinding(
            **base,
            unknowns=(),
            mandatory_hypothetical_disclaimer="A disclaimer without the marker.",
        )


def test_final_brief_rejects_allegation_in_fact_section() -> None:
    with pytest.raises(ValidationError):
        CaseResearchBrief(
            brief_id="brief.test.001",
            session_id="session.test.001",
            mode=InteractionMode.ASK_CASE,
            language="en",
            concise_answer="A test answer.",
            established_facts=(fact(ClaimStatus.ALLEGED),),
            citations=(citation(),),
            confidence=ConfidenceLabel.LOW,
            limitations=("Fixture only.",),
            educational_disclaimer="Educational research only; not legal advice.",
        )


def test_fake_adapters_match_runtime_protocols() -> None:
    adapters = create_development_fake_adapters()
    assert isinstance(adapters.evidence, EvidenceSpecialistProtocol)
    assert isinstance(adapters.legal, LegalSpecialistProtocol)
    assert isinstance(adapters.timeline_analysis, TimelineAnalysisSpecialistProtocol)
    assert isinstance(adapters.reviewer, ReviewerProtocol)

    evidence = adapters.evidence.execute(
        task(SpecialistRole.EVIDENCE, InteractionMode.ASK_CASE),
        state(InteractionMode.ASK_CASE),
    )
    legal = adapters.legal.execute(
        task(SpecialistRole.LEGAL, InteractionMode.EXPLAIN_VERDICT),
        state(InteractionMode.EXPLAIN_VERDICT),
    )
    timeline = adapters.timeline_analysis.execute(
        task(SpecialistRole.TIMELINE_ANALYSIS, InteractionMode.VIEW_TIMELINE),
        state(InteractionMode.VIEW_TIMELINE),
    )
    counterfactual = adapters.timeline_analysis.execute(
        task(SpecialistRole.TIMELINE_ANALYSIS, InteractionMode.WHAT_IF),
        state(InteractionMode.WHAT_IF),
    )
    assert evidence.citations and legal.citations and timeline.citations
    assert isinstance(counterfactual, CounterfactualFinding)


def test_fake_reviewer_approves_valid_brief() -> None:
    adapters = create_development_fake_adapters()
    draft = CaseResearchBrief(
        brief_id="brief.test.001",
        session_id="session.test.001",
        mode=InteractionMode.ASK_CASE,
        language="en",
        concise_answer="A fixture answer.",
        established_facts=(fact(),),
        citations=(citation(),),
        confidence=ConfidenceLabel.LOW,
        limitations=("Fixture only.",),
        educational_disclaimer="Educational research only; not legal advice.",
    )
    result = adapters.reviewer.review(draft, ReviewContext())
    assert result.approved and result.final_brief == draft


def test_environment_sample_is_safe_and_env_is_ignored() -> None:
    root = Path(__file__).resolve().parents[1]
    gitignore = (root / ".gitignore").read_text(encoding="utf-8")
    sample = (root / ".env.example").read_text(encoding="utf-8")
    assert ".env\n" in gitignore
    assert sample.splitlines()[0] == "GEMINI_API_KEY="
    assert "gemini-3.7-flash" in sample
    assert "gemini-embedding-2" in sample
    assert "768" in sample
    assert subprocess.run(
        ["git", "check-ignore", "-q", ".env"],
        cwd=root,
        check=False,
    ).returncode == 0
    assert subprocess.run(
        ["git", "check-ignore", "-q", ".streamlit/secrets.toml"],
        cwd=root,
        check=False,
    ).returncode == 0


def test_config_is_keyless_by_default_and_never_repr_leaks_key() -> None:
    config = RuntimeConfig.from_sources(environ={}, streamlit_secrets={})
    assert not config.provider_configured

    configured = RuntimeConfig.from_sources(
        environ={"GEMINI_API_KEY": "fixture-secret-do-not-use"},
        streamlit_secrets={},
    )
    assert configured.provider_configured
    assert "fixture-secret-do-not-use" not in repr(configured)
