"""Build a strict research brief while preserving finding status and citations."""

from __future__ import annotations

from collections.abc import Iterable

from ..contracts import (
    CaseResearchBrief,
    ConfidenceLabel,
    CounterfactualFinding,
    EvidenceFinding,
    LegalFinding,
    SourceCitation,
    TimelineFinding,
)
from ..state import CaseLensState

_CONFIDENCE_ORDER = {
    ConfidenceLabel.LOW: 0,
    ConfidenceLabel.MEDIUM: 1,
    ConfidenceLabel.HIGH: 2,
}


def build_case_research_brief(state: CaseLensState) -> CaseResearchBrief:
    """Join present specialist findings without relabeling their statements."""

    findings = tuple(
        finding
        for finding in (
            state.evidence_finding,
            state.legal_finding,
            state.timeline_finding,
            state.counterfactual_finding,
        )
        if finding is not None
    )
    if not findings:
        raise ValueError("a draft requires at least one specialist finding")

    evidence = state.evidence_finding
    legal = state.legal_finding
    timeline = state.timeline_finding
    counterfactual = state.counterfactual_finding
    citations = _unique_citations(
        citation for finding in findings for citation in finding.citations
    )
    if not citations:
        raise ValueError("a draft requires cited specialist findings")

    answer_parts = tuple(
        part
        for part in (
            evidence.summary if evidence else None,
            legal.explanation if legal else None,
            timeline.summary if timeline else None,
            counterfactual.changed_assumption if counterfactual else None,
        )
        if part
    )
    categorized = tuple(
        finding for finding in (evidence, legal) if finding is not None
    )
    confidences = tuple(finding.confidence for finding in findings)
    return CaseResearchBrief(
        brief_id=f"brief.{state.session_id}.{state.turn_count}",
        session_id=state.session_id,
        mode=state.mode,
        language=state.language,
        concise_answer=" ".join(answer_parts),
        established_facts=tuple(
            statement
            for finding in categorized
            for statement in finding.established_facts
        ),
        allegations=tuple(
            statement for finding in categorized for statement in finding.allegations
        ),
        disputed_items=tuple(
            statement
            for finding in categorized
            for statement in finding.disputed_items
        ),
        unknowns=tuple(
            statement for finding in categorized for statement in finding.unknowns
        ),
        legal_explanation=legal.explanation if legal else None,
        timeline_events=timeline.events if timeline else (),
        counterfactual=counterfactual,
        financial_amounts=evidence.financial_amounts if evidence else (),
        proceeding_records=legal.proceeding_records if legal else (),
        citations=citations,
        confidence=min(confidences, key=_CONFIDENCE_ORDER.__getitem__),
        limitations=(
            "Development adapters provide fictional fixtures until real v1 adapters are injected."
            if state.language == "en"
            else "توفر محولات التطوير بيانات اختبار خيالية حتى حقن محولات v1 الحقيقية.",
        ),
        educational_disclaimer=(
            "Educational case research only; not legal advice or a prediction."
            if state.language == "en"
            else "بحث تعليمي في القضية فقط، وليس استشارة قانونية أو تنبؤًا."
        ),
    )


def _unique_citations(citations: Iterable[SourceCitation]) -> tuple[SourceCitation, ...]:
    unique: dict[str, SourceCitation] = {}
    for citation in citations:
        unique.setdefault(citation.citation_id, citation)
    return tuple(unique.values())
