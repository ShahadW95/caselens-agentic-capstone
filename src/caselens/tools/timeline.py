"""Tool 1 — query_case_timeline: deterministic, filtered timeline lookups."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..contracts import MVP_CASE_ID, NonEmptyText, StableId, TimelineTrack
from ..services.case_loader import CaseLoaderError, TimelineEventRecord, load_case_pack
from . import ToolError, ToolSpec, register_tool

__all__ = [
    "QueryCaseTimelineRequest",
    "TimelineEventSummary",
    "QueryCaseTimelineResult",
    "query_case_timeline",
]


class QueryCaseTimelineRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    case_id: str
    start_date: date | None = None
    end_date: date | None = None
    track: TimelineTrack | None = None
    related_id: StableId | None = None
    limit: int = Field(default=20, ge=1, le=100)

    @model_validator(mode="after")
    def date_range_is_ordered(self) -> "QueryCaseTimelineRequest":
        if self.start_date is not None and self.end_date is not None and self.start_date > self.end_date:
            raise ValueError("start_date must not be after end_date")
        return self


class TimelineEventSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    event_id: StableId
    title: NonEmptyText
    summary: NonEmptyText
    track: TimelineTrack
    date_label: NonEmptyText
    event_date: date | None
    evidence_ids: tuple[StableId, ...]
    source_ids: tuple[StableId, ...]


class QueryCaseTimelineResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    status: str  # "ok" | "empty"
    query_id: StableId
    events: tuple[TimelineEventSummary, ...]
    applied_filters: dict[str, object]
    result_count: int
    summary: NonEmptyText
    empty_result_reason: NonEmptyText | None = None


def _event_effective_range(event: TimelineEventRecord) -> tuple[date, date]:
    # Fall back to the *other known* bound rather than date.min/date.max: an
    # event with only an end_date (e.g. "ongoing as of X") is anchored at X
    # for filtering purposes, not treated as spanning from the dawn of time.
    start = event.start_date or event.event_date or event.end_date or date.min
    end = event.end_date or event.event_date or event.start_date or date.max
    return start, end


def query_case_timeline(request: QueryCaseTimelineRequest, *, query_id: StableId) -> QueryCaseTimelineResult:
    if request.case_id != MVP_CASE_ID:
        raise ToolError("UNSUPPORTED_CASE", f"Case '{request.case_id}' is not part of the curated case library.")

    try:
        pack = load_case_pack(request.case_id)
    except CaseLoaderError as exc:
        raise ToolError("CASE_DATA_UNAVAILABLE", exc.user_message) from exc

    known_claims = {c.claim_id for c in pack.claims}
    known_evidence = {e.evidence_id for e in pack.evidence}
    if request.related_id is not None and request.related_id not in (known_claims | known_evidence):
        raise ToolError(
            "UNKNOWN_ID", f"'{request.related_id}' is not a known claim or evidence id in this case pack."
        )

    filter_start = request.start_date or date.min
    filter_end = request.end_date or date.max

    date_filter_requested = request.start_date is not None or request.end_date is not None

    matched: list[TimelineEventRecord] = []
    for event in pack.timeline:
        has_any_date_info = (
            event.event_date is not None or event.start_date is not None or event.end_date is not None
        )
        if date_filter_requested and not has_any_date_info:
            # An event with no date information at all cannot be affirmatively
            # said to fall inside a requested range; exclude rather than guess.
            continue
        event_start, event_end = _event_effective_range(event)
        if event_end < filter_start or event_start > filter_end:
            continue
        if request.track is not None and event.track != request.track:
            continue
        if request.related_id is not None and request.related_id not in (
            set(event.related_claim_ids) | set(event.evidence_ids)
        ):
            continue
        matched.append(event)

    limited = matched[: request.limit]

    applied_filters: dict[str, object] = {
        "start_date": request.start_date.isoformat() if request.start_date else None,
        "end_date": request.end_date.isoformat() if request.end_date else None,
        "track": request.track.value if request.track else None,
        "related_id": request.related_id,
        "limit": request.limit,
    }

    if not limited:
        return QueryCaseTimelineResult(
            status="empty",
            query_id=query_id,
            events=(),
            applied_filters=applied_filters,
            result_count=0,
            summary="No timeline events matched the given filters.",
            empty_result_reason="No curated timeline event satisfies the requested date range/track/related-id filters.",
        )

    summaries = tuple(
        TimelineEventSummary(
            event_id=e.event_id,
            title=e.title,
            summary=e.summary,
            track=e.track,
            date_label=e.date_label,
            event_date=e.event_date,
            evidence_ids=e.evidence_ids,
            source_ids=e.source_ids,
        )
        for e in limited
    )
    return QueryCaseTimelineResult(
        status="ok",
        query_id=query_id,
        events=summaries,
        applied_filters=applied_filters,
        result_count=len(summaries),
        summary=f"{len(summaries)} of {len(matched)} matching timeline event(s) returned (limit={request.limit}).",
    )


register_tool(
    ToolSpec(
        name="query_case_timeline",
        description="Return a deterministically ordered, filtered slice of the curated case timeline.",
        permission_category="read_case_data",
        input_schema=QueryCaseTimelineRequest.model_json_schema(),
        result_schema=QueryCaseTimelineResult.model_json_schema(),
    )
)
