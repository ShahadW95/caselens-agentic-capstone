"""Deterministic, allowlisted loader and validator for curated case packs.

This module defines Track B's internal representation of a curated case pack
(``case_metadata.json``, ``timeline.json``, ``claims.json``, ``evidence.json``,
``financial_amounts.json``, ``causal_graph.json``, ``source_manifest.json``)
and loads it into strict Pydantic structures. It reuses the frozen v1
contracts (``ProceedingRecord``, shared enums, ``StableId``/``NonEmptyText``)
wherever the raw case-pack data matches them exactly, and defines local models
only where the pack needs fields the runtime contracts do not carry yet (for
example, retrieval citations do not exist until the RAG layer in B2 attaches
them). Nothing here edits ``contracts.py`` or ``protocols.py``.
"""

from __future__ import annotations

import json
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, AnyHttpUrl, model_validator

from ..contracts import (
    AmountKind,
    ClaimStatus,
    ConfidenceLabel,
    MVP_CASE_ID,
    NonEmptyText,
    ProceedingRecord,
    ProceedingType,
    SourceTier,
    StableId,
    TimelineTrack,
)

__all__ = [
    "CaseLoaderError",
    "CasePack",
    "CaseMetadata",
    "TimelineEventRecord",
    "ClaimRecord",
    "EvidenceRecord",
    "FinancialAmountRecord",
    "CausalGraph",
    "CausalNode",
    "CausalEdge",
    "AllowedChange",
    "SourceManifest",
    "SourceManifestEntry",
    "load_case_pack",
]

# ---------------------------------------------------------------------------
# Allowlist: never accept an arbitrary case ID or path from a caller.
# ---------------------------------------------------------------------------

CASE_ID_TO_FOLDER: dict[str, str] = {MVP_CASE_ID: "case_001"}

DEFAULT_DATA_ROOT = Path(__file__).resolve().parents[3] / "data" / "cases"


class CaseLoaderError(Exception):
    """Structured, user-safe error raised for any case-pack loading failure."""

    def __init__(self, code: str, user_message: str, *, recoverable: bool = False) -> None:
        self.code = code
        self.user_message = user_message
        self.recoverable = recoverable
        super().__init__(f"[{code}] {user_message}")

    def to_safe_error_fields(self) -> dict[str, object]:
        """Field values compatible with the frozen ``contracts.SafeError`` shape."""

        return {
            "error_id": f"error.case_loader.{self.code.lower()}",
            "code": self.code,
            "user_message": self.user_message,
            "recoverable": self.recoverable,
            "retry_allowed": False,
        }


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


# ---------------------------------------------------------------------------
# source_manifest.json
# ---------------------------------------------------------------------------


class SourceManifestEntry(_StrictModel):
    source_id: StableId
    title: NonEmptyText
    publisher: NonEmptyText
    source_type: NonEmptyText
    source_tier: SourceTier
    url: AnyHttpUrl
    use: NonEmptyText
    language: NonEmptyText
    published_date: date | None = Field(default=None, alias="date")


class SourceManifest(_StrictModel):
    case_id: Literal[MVP_CASE_ID] = MVP_CASE_ID
    case_title: NonEmptyText
    docket: NonEmptyText
    jurisdiction: NonEmptyText
    case_status: NonEmptyText
    source_pack_cutoff: date
    manifest_version: NonEmptyText
    last_reviewed: date
    sources: tuple[SourceManifestEntry, ...] = Field(min_length=1)
    excluded_categories: tuple[NonEmptyText, ...] = ()
    notes: tuple[NonEmptyText, ...] = ()


# ---------------------------------------------------------------------------
# case_metadata.json
# ---------------------------------------------------------------------------


class CaseMetadata(_StrictModel):
    case_id: Literal[MVP_CASE_ID] = MVP_CASE_ID
    display_title: NonEmptyText
    jurisdiction: NonEmptyText
    court: NonEmptyText
    case_status: NonEmptyText
    final_status_source_ids: tuple[StableId, ...] = Field(min_length=1)
    key_dates: dict[str, date] = Field(default_factory=dict)
    synopsis: NonEmptyText
    legal_outcome_summary: NonEmptyText
    dataset_version: NonEmptyText
    last_reviewed: date
    editorial_warnings: tuple[NonEmptyText, ...] = ()
    scope_exclusions: tuple[NonEmptyText, ...] = ()
    proceedings: tuple[ProceedingRecord, ...] = Field(min_length=1)


# ---------------------------------------------------------------------------
# timeline.json
# ---------------------------------------------------------------------------


class DatePrecision(str, Enum):
    EXACT = "EXACT"
    MONTH = "MONTH"
    YEAR = "YEAR"
    ERA_NO_EXACT_DATE = "ERA_NO_EXACT_DATE"
    ONGOING_NO_SINGLE_DATE = "ONGOING_NO_SINGLE_DATE"


class TimelineEventRecord(_StrictModel):
    event_id: StableId
    title: NonEmptyText
    summary: NonEmptyText
    track: TimelineTrack
    date_precision: DatePrecision
    event_date: date | None = None
    date_label: NonEmptyText
    start_date: date | None = None
    end_date: date | None = None
    actor_ids: tuple[StableId, ...] = ()
    related_claim_ids: tuple[StableId, ...] = ()
    evidence_ids: tuple[StableId, ...] = Field(min_length=1)
    source_ids: tuple[StableId, ...] = Field(min_length=1)
    certainty: ConfidenceLabel = ConfidenceLabel.HIGH
    fact_classification: ClaimStatus = ClaimStatus.ESTABLISHED

    @model_validator(mode="after")
    def date_fields_are_consistent(self) -> "TimelineEventRecord":
        if self.date_precision is DatePrecision.EXACT:
            if self.event_date is None:
                raise ValueError("EXACT date_precision requires event_date")
        elif self.event_date is not None:
            raise ValueError("event_date must be null unless date_precision is EXACT")
        if self.start_date is not None and self.end_date is not None:
            if self.start_date > self.end_date:
                raise ValueError("start_date must not be after end_date")
        return self


# ---------------------------------------------------------------------------
# claims.json
# ---------------------------------------------------------------------------

ClaimSupportStatus = Literal[
    "SUPPORTED", "CONTRADICTED", "PARTIALLY_SUPPORTED", "INSUFFICIENT_EVIDENCE"
]


class ClaimRecord(_StrictModel):
    claim_id: StableId
    claim_text: NonEmptyText
    speaker_or_party: NonEmptyText = "unknown"
    context: NonEmptyText
    status: ClaimStatus
    supporting_evidence_ids: tuple[StableId, ...] = ()
    contradicting_evidence_ids: tuple[StableId, ...] = ()
    supporting_source_ids: tuple[StableId, ...] = Field(min_length=1)
    court_treatment: NonEmptyText | None = None
    explanation: NonEmptyText
    related_financial_amount_ids: tuple[StableId, ...] = ()

    @model_validator(mode="after")
    def status_is_a_deterministic_claim_status(self) -> "ClaimRecord":
        allowed = {
            ClaimStatus.SUPPORTED,
            ClaimStatus.CONTRADICTED,
            ClaimStatus.PARTIALLY_SUPPORTED,
            ClaimStatus.INSUFFICIENT_EVIDENCE,
        }
        if self.status not in allowed:
            raise ValueError(
                "claim status must be one of SUPPORTED, CONTRADICTED, "
                "PARTIALLY_SUPPORTED, or INSUFFICIENT_EVIDENCE"
            )
        if self.status is ClaimStatus.SUPPORTED and not self.supporting_evidence_ids:
            raise ValueError("SUPPORTED claims require supporting_evidence_ids")
        if self.status is ClaimStatus.CONTRADICTED and not self.contradicting_evidence_ids:
            raise ValueError("CONTRADICTED claims require contradicting_evidence_ids")
        if self.status is ClaimStatus.PARTIALLY_SUPPORTED and not (
            self.supporting_evidence_ids and self.contradicting_evidence_ids
        ):
            raise ValueError(
                "PARTIALLY_SUPPORTED claims require both supporting and "
                "contradicting evidence ids"
            )
        return self


# ---------------------------------------------------------------------------
# evidence.json
# ---------------------------------------------------------------------------


class EvidenceRecord(_StrictModel):
    evidence_id: StableId
    label: NonEmptyText
    evidence_type: NonEmptyText
    introduced_or_reported_by: NonEmptyText
    supporting_source_ids: tuple[StableId, ...] = Field(min_length=1)
    related_claim_ids: tuple[StableId, ...] = ()
    related_event_ids: tuple[StableId, ...] = ()
    court_treatment_note: NonEmptyText | None = None
    limitations: tuple[NonEmptyText, ...] = ()
    disputes: tuple[NonEmptyText, ...] = ()


# ---------------------------------------------------------------------------
# financial_amounts.json
# ---------------------------------------------------------------------------


class FinancialAmountRecord(_StrictModel):
    amount_id: StableId
    amount_kind: AmountKind
    currency: NonEmptyText
    value_or_range: NonEmptyText
    as_of_date: date
    source_ids: tuple[StableId, ...] = Field(min_length=1)
    measurement_note: NonEmptyText
    proceeding_type: ProceedingType


# ---------------------------------------------------------------------------
# causal_graph.json
# ---------------------------------------------------------------------------

CausalNodeType = Literal["EVENT", "EVIDENCE", "CLAIM", "CONDITION"]
CausalEdgeType = Literal["ENABLES", "PRECEDES", "CONTRIBUTES_TO"]


class CausalNode(_StrictModel):
    node_id: StableId
    node_type: CausalNodeType
    reference_id: StableId
    label: NonEmptyText
    source_ids: tuple[StableId, ...] = Field(min_length=1)


class CausalEdge(_StrictModel):
    edge_id: StableId
    from_node_id: StableId
    to_node_id: StableId
    edge_type: CausalEdgeType
    rationale: NonEmptyText
    source_ids: tuple[StableId, ...] = Field(min_length=1)


class AllowedChangeDirectEffect(_StrictModel):
    node_id: StableId
    description: NonEmptyText


class UnchangedFact(_StrictModel):
    text: NonEmptyText
    source_ids: tuple[StableId, ...] = Field(min_length=1)


class AllowedChange(_StrictModel):
    change_id: StableId
    event_id: StableId
    target_node_id: StableId
    label: NonEmptyText
    description: NonEmptyText
    direct_effects: tuple[AllowedChangeDirectEffect, ...] = Field(min_length=1)
    downstream_possible_effects: tuple[NonEmptyText, ...] = Field(min_length=1)
    unchanged_facts: tuple[UnchangedFact, ...] = Field(min_length=1)
    unknowns: tuple[NonEmptyText, ...] = Field(min_length=1)
    mandatory_hypothetical_disclaimer: NonEmptyText

    @model_validator(mode="after")
    def disclaimer_identifies_hypothetical(self) -> "AllowedChange":
        text = self.mandatory_hypothetical_disclaimer.lower()
        if "hypothetical" not in text and "افتراضي" not in text:
            raise ValueError(
                "mandatory_hypothetical_disclaimer must identify the output as hypothetical"
            )
        return self


class CausalGraph(_StrictModel):
    nodes: tuple[CausalNode, ...] = Field(min_length=1)
    edges: tuple[CausalEdge, ...] = ()
    allowed_changes: tuple[AllowedChange, ...] = Field(min_length=1)


# ---------------------------------------------------------------------------
# Aggregate case pack
# ---------------------------------------------------------------------------


class CasePack(_StrictModel):
    case_metadata: CaseMetadata
    timeline: tuple[TimelineEventRecord, ...]
    claims: tuple[ClaimRecord, ...]
    evidence: tuple[EvidenceRecord, ...]
    financial_amounts: tuple[FinancialAmountRecord, ...]
    causal_graph: CausalGraph
    source_manifest: SourceManifest


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

_FILES = (
    "case_metadata.json",
    "timeline.json",
    "claims.json",
    "evidence.json",
    "financial_amounts.json",
    "causal_graph.json",
    "source_manifest.json",
)


def _read_json(case_dir: Path, filename: str) -> object:
    path = case_dir / filename
    if not path.exists():
        raise CaseLoaderError("MISSING_FILE", f"Required case file '{filename}' was not found.")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CaseLoaderError(
            "MALFORMED_JSON", f"Case file '{filename}' is not valid JSON."
        ) from exc


def _parse(model: type[BaseModel], raw: object, filename: str) -> BaseModel:
    try:
        return model.model_validate(raw)
    except Exception as exc:  # noqa: BLE001 - normalized into a safe error below
        raise CaseLoaderError(
            "SCHEMA_VALIDATION_FAILED", f"Case file '{filename}' failed schema validation: {exc}"
        ) from exc


def _parse_list(model: type[BaseModel], raw: object, filename: str) -> tuple[BaseModel, ...]:
    if not isinstance(raw, list):
        raise CaseLoaderError("SCHEMA_VALIDATION_FAILED", f"Case file '{filename}' must be a JSON array.")
    items: list[BaseModel] = []
    for index, entry in enumerate(raw):
        try:
            items.append(model.model_validate(entry))
        except Exception as exc:  # noqa: BLE001 - normalized into a safe error below
            raise CaseLoaderError(
                "SCHEMA_VALIDATION_FAILED",
                f"Case file '{filename}' entry {index} failed schema validation: {exc}",
            ) from exc
    return tuple(items)


def _check_unique(ids: list[str], kind: str) -> None:
    seen: set[str] = set()
    for item_id in ids:
        if item_id in seen:
            raise CaseLoaderError("DUPLICATE_ID", f"Duplicate {kind} id '{item_id}'.")
        seen.add(item_id)


def _check_subset(used: set[str], known: set[str], kind: str) -> None:
    missing = used - known
    if missing:
        example = sorted(missing)[0]
        raise CaseLoaderError(
            "DANGLING_REFERENCE_ID", f"Reference to unknown {kind} id '{example}'."
        )


def load_case_pack(case_id: str, *, case_dir: Path | None = None) -> CasePack:
    """Load and fully validate a curated, allowlisted case pack.

    ``case_dir`` overrides the physical directory for the already-allowlisted
    case (used by tests to point at a fixture); it never widens which case
    IDs are accepted.
    """

    if case_id not in CASE_ID_TO_FOLDER:
        raise CaseLoaderError(
            "UNSUPPORTED_CASE", f"Case '{case_id}' is not part of the curated case library."
        )
    resolved_dir = case_dir if case_dir is not None else DEFAULT_DATA_ROOT / CASE_ID_TO_FOLDER[case_id]
    if not resolved_dir.is_dir():
        raise CaseLoaderError("MISSING_FILE", "The case pack directory was not found.")

    raw: dict[str, object] = {name: _read_json(resolved_dir, name) for name in _FILES}

    case_metadata = _parse(CaseMetadata, raw["case_metadata.json"], "case_metadata.json")
    timeline = _parse_list(TimelineEventRecord, raw["timeline.json"], "timeline.json")
    claims = _parse_list(ClaimRecord, raw["claims.json"], "claims.json")
    evidence = _parse_list(EvidenceRecord, raw["evidence.json"], "evidence.json")
    financial_amounts = _parse_list(
        FinancialAmountRecord, raw["financial_amounts.json"], "financial_amounts.json"
    )
    causal_graph_raw = raw["causal_graph.json"]
    if not isinstance(causal_graph_raw, dict):
        raise CaseLoaderError(
            "SCHEMA_VALIDATION_FAILED", "Case file 'causal_graph.json' must be a JSON object."
        )
    causal_graph = _parse(CausalGraph, causal_graph_raw, "causal_graph.json")
    source_manifest = _parse(SourceManifest, raw["source_manifest.json"], "source_manifest.json")

    # -- Uniqueness -----------------------------------------------------
    _check_unique([p.proceeding_id for p in case_metadata.proceedings], "proceeding")
    _check_unique([e.event_id for e in timeline], "timeline event")
    _check_unique([c.claim_id for c in claims], "claim")
    _check_unique([e.evidence_id for e in evidence], "evidence")
    _check_unique([f.amount_id for f in financial_amounts], "financial amount")
    _check_unique([n.node_id for n in causal_graph.nodes], "causal node")
    _check_unique([e.edge_id for e in causal_graph.edges], "causal edge")
    _check_unique([c.change_id for c in causal_graph.allowed_changes], "allowed change")
    _check_unique([s.source_id for s in source_manifest.sources], "source")

    # -- Known ID sets ----------------------------------------------------
    known_sources = {s.source_id for s in source_manifest.sources}
    known_events = {e.event_id for e in timeline}
    known_claims = {c.claim_id for c in claims}
    known_evidence = {e.evidence_id for e in evidence}
    known_amounts = {f.amount_id for f in financial_amounts}
    known_nodes = {n.node_id for n in causal_graph.nodes}

    # -- Source ID references resolve to the manifest --------------------
    used_source_ids: set[str] = set(case_metadata.final_status_source_ids)
    for proceeding in case_metadata.proceedings:
        used_source_ids.update(proceeding.source_ids)
    for event in timeline:
        used_source_ids.update(event.source_ids)
    for claim in claims:
        used_source_ids.update(claim.supporting_source_ids)
    for item in evidence:
        used_source_ids.update(item.supporting_source_ids)
    for amount in financial_amounts:
        used_source_ids.update(amount.source_ids)
    for node in causal_graph.nodes:
        used_source_ids.update(node.source_ids)
    for edge in causal_graph.edges:
        used_source_ids.update(edge.source_ids)
    for change in causal_graph.allowed_changes:
        for fact in change.unchanged_facts:
            used_source_ids.update(fact.source_ids)
    _check_subset(used_source_ids, known_sources, "source")

    # -- Cross-collection references --------------------------------------
    for event in timeline:
        _check_subset(set(event.related_claim_ids), known_claims, "claim")
        _check_subset(set(event.evidence_ids), known_evidence, "evidence")
    for claim in claims:
        _check_subset(set(claim.supporting_evidence_ids), known_evidence, "evidence")
        _check_subset(set(claim.contradicting_evidence_ids), known_evidence, "evidence")
        _check_subset(set(claim.related_financial_amount_ids), known_amounts, "financial amount")
    for item in evidence:
        _check_subset(set(item.related_claim_ids), known_claims, "claim")
        _check_subset(set(item.related_event_ids), known_events, "timeline event")

    # -- Causal graph structural checks -----------------------------------
    reference_pool = known_events | known_evidence | known_claims
    for node in causal_graph.nodes:
        pool = {
            "EVENT": known_events,
            "EVIDENCE": known_evidence,
            "CLAIM": known_claims,
            "CONDITION": reference_pool,
        }[node.node_type]
        if node.reference_id not in pool:
            raise CaseLoaderError(
                "DANGLING_REFERENCE_ID",
                f"Causal node '{node.node_id}' references unknown {node.node_type} id "
                f"'{node.reference_id}'.",
            )

    adjacency: dict[str, list[str]] = {node_id: [] for node_id in known_nodes}
    for edge in causal_graph.edges:
        if edge.from_node_id not in known_nodes or edge.to_node_id not in known_nodes:
            raise CaseLoaderError(
                "DANGLING_CAUSAL_NODE",
                f"Causal edge '{edge.edge_id}' references a node outside the graph.",
            )
        adjacency[edge.from_node_id].append(edge.to_node_id)

    _reject_cycles(adjacency)

    for change in causal_graph.allowed_changes:
        if change.event_id not in known_events:
            raise CaseLoaderError(
                "DANGLING_REFERENCE_ID",
                f"Allowed change '{change.change_id}' anchors to an unknown event.",
            )
        if change.target_node_id not in known_nodes:
            raise CaseLoaderError(
                "NON_ALLOWLISTED_CHANGE_TARGET",
                f"Allowed change '{change.change_id}' targets an unknown node.",
            )
        for effect in change.direct_effects:
            if effect.node_id not in known_nodes:
                raise CaseLoaderError(
                    "NON_ALLOWLISTED_CHANGE_TARGET",
                    f"Allowed change '{change.change_id}' has a direct effect on an unknown node.",
                )

    # -- Final status is authoritative (at least one Tier A source) ------
    tier_by_source = {s.source_id: s.source_tier for s in source_manifest.sources}
    if not any(
        tier_by_source.get(sid) is SourceTier.A for sid in case_metadata.final_status_source_ids
    ):
        raise CaseLoaderError(
            "FINAL_STATUS_NOT_AUTHORITATIVE",
            "The case's final status must be supported by at least one Tier A source.",
        )

    return CasePack(
        case_metadata=case_metadata,
        timeline=tuple(sorted(timeline, key=_timeline_sort_key)),
        claims=tuple(sorted(claims, key=lambda c: c.claim_id)),
        evidence=tuple(sorted(evidence, key=lambda e: e.evidence_id)),
        financial_amounts=tuple(sorted(financial_amounts, key=lambda f: f.amount_id)),
        causal_graph=causal_graph,
        source_manifest=source_manifest,
    )


def _timeline_sort_key(event: TimelineEventRecord) -> tuple[date, str]:
    anchor = event.event_date or event.start_date or date.max
    return (anchor, event.event_id)


def _reject_cycles(adjacency: dict[str, list[str]]) -> None:
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {node_id: WHITE for node_id in adjacency}

    def visit(node_id: str) -> None:
        color[node_id] = GRAY
        for neighbour in adjacency[node_id]:
            if color[neighbour] == GRAY:
                raise CaseLoaderError(
                    "CAUSAL_GRAPH_CYCLE", "The causal graph must not contain a cycle."
                )
            if color[neighbour] == WHITE:
                visit(neighbour)
        color[node_id] = BLACK

    for node_id in adjacency:
        if color[node_id] == WHITE:
            visit(node_id)
