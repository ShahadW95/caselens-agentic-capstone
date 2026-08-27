"""Tool 2 — check_claim_support: deterministic claim verification over the curated claim/evidence map."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..contracts import AmountKind, MVP_CASE_ID, NonEmptyText, StableId
from ..services.case_loader import CaseLoaderError, load_case_pack
from . import ToolError, ToolSpec, register_tool

__all__ = [
    "CheckClaimSupportRequest",
    "FinancialAmountSummary",
    "CheckClaimSupportResult",
    "check_claim_support",
]

# Deterministic, approved keyword -> claim_id mapping. This is the only path
# by which free-text user input may be matched to a curated claim; anything
# that does not match returns insufficient_evidence rather than guessing.
_KEYWORD_TO_CLAIM_ID: tuple[tuple[tuple[str, ...], str], ...] = (
    (("65 billion", "$65b", "usd 65", "65b cash"), "CLAIM_MADOFF_STOLE_65B_CASH"),
    (("government official", "government employee"), "CLAIM_MADOFF_GOV_OFFICIAL"),
    (("received complaints", "verification opportunit"), "CLAIM_SEC_RECEIVED_COMPLAINTS"),
    (("sec was corrupt", "sec bribed", "bribery"), "CLAIM_SEC_WAS_CORRUPT"),
    (("acted alone", "acted completely alone", "by himself"), "CLAIM_MADOFF_ACTED_ALONE"),
    (("jury verdict", "jury trial", "convicted at trial"), "CLAIM_ONLY_11_FELONY_COUNTS_NO_TRIAL"),
    (("case is still open", "case still unresolved", "still being litigated"), "CLAIM_CRIMINAL_CASE_STILL_OPEN"),
)


def _match_claim_id(user_claim_text: str) -> str | None:
    lowered = user_claim_text.lower()
    for keywords, claim_id in _KEYWORD_TO_CLAIM_ID:
        if any(keyword in lowered for keyword in keywords):
            return claim_id
    return None


class CheckClaimSupportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    case_id: str
    claim_id: StableId | None = None
    user_claim_text: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def exactly_one_claim_reference(self) -> "CheckClaimSupportRequest":
        if (self.claim_id is None) == (self.user_claim_text is None):
            raise ValueError("exactly one of claim_id or user_claim_text must be provided")
        return self


class FinancialAmountSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    amount_id: StableId
    amount_kind: AmountKind
    currency: NonEmptyText
    value_or_range: NonEmptyText
    as_of_date: date
    source_ids: tuple[StableId, ...]
    measurement_note: NonEmptyText


class CheckClaimSupportResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    status: str  # supported | contradicted | partially_supported | insufficient_evidence
    claim_id: StableId | None
    normalized_claim_text: NonEmptyText
    supporting_evidence_ids: tuple[StableId, ...]
    contradicting_evidence_ids: tuple[StableId, ...]
    supporting_source_ids: tuple[StableId, ...]
    court_treatment: NonEmptyText | None
    explanation: NonEmptyText
    financial_amounts: tuple[FinancialAmountSummary, ...]


def check_claim_support(request: CheckClaimSupportRequest) -> CheckClaimSupportResult:
    if request.case_id != MVP_CASE_ID:
        raise ToolError("UNSUPPORTED_CASE", f"Case '{request.case_id}' is not part of the curated case library.")

    try:
        pack = load_case_pack(request.case_id)
    except CaseLoaderError as exc:
        raise ToolError("CASE_DATA_UNAVAILABLE", exc.user_message) from exc

    claims_by_id = {c.claim_id: c for c in pack.claims}
    amounts_by_id = {a.amount_id: a for a in pack.financial_amounts}

    if request.claim_id is not None:
        claim = claims_by_id.get(request.claim_id)
        if claim is None:
            raise ToolError("UNKNOWN_CLAIM_ID", f"'{request.claim_id}' is not a known claim id in this case pack.")
    else:
        matched_id = _match_claim_id(request.user_claim_text or "")
        claim = claims_by_id.get(matched_id) if matched_id else None
        if claim is None:
            return CheckClaimSupportResult(
                status="insufficient_evidence",
                claim_id=None,
                normalized_claim_text=(request.user_claim_text or "").strip(),
                supporting_evidence_ids=(),
                contradicting_evidence_ids=(),
                supporting_source_ids=(),
                court_treatment=None,
                explanation=(
                    "This claim could not be matched to a curated claim in this case pack. "
                    "Try selecting one of the known claims instead of free text."
                ),
                financial_amounts=(),
            )

    financial_amounts = tuple(
        FinancialAmountSummary(
            amount_id=a.amount_id,
            amount_kind=a.amount_kind,
            currency=a.currency,
            value_or_range=a.value_or_range,
            as_of_date=a.as_of_date,
            source_ids=a.source_ids,
            measurement_note=a.measurement_note,
        )
        for aid in claim.related_financial_amount_ids
        if (a := amounts_by_id.get(aid)) is not None
    )

    return CheckClaimSupportResult(
        status=claim.status.value.lower(),
        claim_id=claim.claim_id,
        normalized_claim_text=claim.claim_text,
        supporting_evidence_ids=claim.supporting_evidence_ids,
        contradicting_evidence_ids=claim.contradicting_evidence_ids,
        supporting_source_ids=claim.supporting_source_ids,
        court_treatment=claim.court_treatment,
        explanation=claim.explanation,
        financial_amounts=financial_amounts,
    )


register_tool(
    ToolSpec(
        name="check_claim_support",
        description="Deterministically check a curated claim's support status against the case's evidence map.",
        permission_category="read_case_data",
        input_schema=CheckClaimSupportRequest.model_json_schema(),
        result_schema=CheckClaimSupportResult.model_json_schema(),
    )
)
