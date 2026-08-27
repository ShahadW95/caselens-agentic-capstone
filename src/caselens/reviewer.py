"""Deterministic editorial checks and one bounded draft correction."""

from __future__ import annotations

from .contracts import (
    CaseResearchBrief,
    ReviewDefect,
    ReviewDefectCode,
)

_DISCLAIMER_EN = "Educational case research only; not legal advice or a prediction."
_DISCLAIMER_AR = "بحث تعليمي في القضية فقط، وليس استشارة قانونية أو تنبؤًا."
_UNSAFE_PHRASES = ("you should", "we advise", "diagnosis", "guaranteed outcome")


def validate_editorial_integrity(brief: CaseResearchBrief) -> ReviewDefect | None:
    """Return one safe structured defect, never hidden review reasoning."""

    known_citations = {citation.citation_id for citation in brief.citations}
    statements = (
        brief.established_facts
        + brief.allegations
        + brief.disputed_items
        + brief.unknowns
    )
    if any(
        not statement.citation_ids
        or not set(statement.citation_ids).issubset(known_citations)
        for statement in statements
    ):
        return _defect(
            ReviewDefectCode.MISSING_CITATION,
            "statements",
            "A finding is missing a known citation reference.",
        )
    disclaimer = brief.educational_disclaimer.lower()
    if "legal advice" not in disclaimer and "استشارة قانونية" not in disclaimer:
        return _defect(
            ReviewDefectCode.DISCLAIMER_MISSING,
            "educational_disclaimer",
            "The educational and not-legal-advice disclaimer is missing.",
        )
    public_text = " ".join(
        item
        for item in (brief.concise_answer, brief.legal_explanation or "")
        if item
    ).lower()
    if any(phrase in public_text for phrase in _UNSAFE_PHRASES):
        return _defect(
            ReviewDefectCode.UNSAFE_CONTENT,
            "concise_answer",
            "The draft contains advice, diagnosis, or certainty language.",
        )
    if brief.counterfactual is not None:
        marker = brief.counterfactual.mandatory_hypothetical_disclaimer.lower()
        if "hypothetical" not in marker and "افتراضي" not in marker:
            return _defect(
                ReviewDefectCode.COUNTERFACTUAL_CERTAINTY,
                "counterfactual.mandatory_hypothetical_disclaimer",
                "The counterfactual is not clearly identified as hypothetical.",
            )
    return None


def repair_draft(
    draft: CaseResearchBrief, defect: ReviewDefect
) -> CaseResearchBrief:
    """Apply one bounded correction without adding facts or citations."""

    if defect.code is ReviewDefectCode.UNSAFE_CONTENT:
        return draft.model_copy(
            update={
                "concise_answer": (
                    "The cited record supports only the bounded educational findings "
                    "listed in this brief."
                    if draft.language == "en"
                    else "يدعم السجل المستشهد به النتائج التعليمية المحدودة الواردة في هذا الملخص فقط."
                )
            }
        )
    if defect.code is ReviewDefectCode.DISCLAIMER_MISSING:
        return draft.model_copy(
            update={
                "educational_disclaimer": (
                    _DISCLAIMER_EN if draft.language == "en" else _DISCLAIMER_AR
                )
            }
        )
    if defect.code is ReviewDefectCode.COUNTERFACTUAL_CERTAINTY and draft.counterfactual:
        counterfactual = draft.counterfactual.model_copy(
            update={
                "mandatory_hypothetical_disclaimer": (
                    "This is a bounded hypothetical, not a prediction."
                    if draft.language == "en"
                    else "هذا تحليل افتراضي محدود وليس تنبؤًا."
                )
            }
        )
        return draft.model_copy(update={"counterfactual": counterfactual})
    raise ValueError("the structured defect cannot be corrected without new evidence")


def reviewer_preserves_evidence(
    draft: CaseResearchBrief, final_brief: CaseResearchBrief
) -> bool:
    """Ensure Editorial review changed no sourced fact or finding collection."""

    protected_fields = (
        "established_facts",
        "allegations",
        "disputed_items",
        "unknowns",
        "timeline_events",
        "counterfactual",
        "financial_amounts",
        "proceeding_records",
        "citations",
    )
    return all(
        getattr(final_brief, field_name) == getattr(draft, field_name)
        for field_name in protected_fields
    )


def _defect(
    code: ReviewDefectCode, field_path: str, description: str
) -> ReviewDefect:
    return ReviewDefect(
        defect_id=f"defect.editorial.{code.value.lower()}",
        code=code,
        field_path=field_path,
        description=description,
        responsible_role="CASE_DIRECTOR",
    )
