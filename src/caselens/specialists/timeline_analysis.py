"""Timeline & What-If Specialist — handles VIEW_TIMELINE and WHAT_IF.

Fully deterministic: both tool 1 (``query_case_timeline``) and tool 3
(``simulate_counterfactual``) already return complete, sourced structured
data, so this specialist never calls the model boundary — there is nothing
for interpretation to add that the curated data doesn't already state, and
skipping the call keeps a bounded hypothetical from ever picking up
model-invented certainty.
"""

from __future__ import annotations

from ..contracts import (
    ClaimStatus,
    ConfidenceLabel,
    CounterfactualFinding,
    DelegationTask,
    FindingStatement,
    InteractionMode,
    MVP_CASE_ID,
    SpecialistRole,
    SpecialistStateView,
    TimelineEvent,
    TimelineFinding,
)
from ..services.case_loader import CaseLoaderError, load_case_pack
from ..tools import ToolError
from ..tools.counterfactual import SimulateCounterfactualRequest, simulate_counterfactual
from ..tools.timeline import QueryCaseTimelineRequest, query_case_timeline
from . import SpecialistError, citation_from_manifest_source

__all__ = ["TimelineAnalysisSpecialist"]


class TimelineAnalysisSpecialist:
    """Real Timeline & What-If Specialist behind ``TimelineAnalysisSpecialistProtocol``."""

    def execute(
        self, task: DelegationTask, state_view: SpecialistStateView
    ) -> TimelineFinding | CounterfactualFinding:
        if task.role is not SpecialistRole.TIMELINE_ANALYSIS:
            raise SpecialistError("WRONG_ROLE", "This specialist only accepts TIMELINE_AND_WHAT_IF tasks.")
        if state_view.query.case_id != MVP_CASE_ID:
            raise SpecialistError("UNSUPPORTED_CASE", "Only the curated MVP case is supported.")

        if task.mode is InteractionMode.VIEW_TIMELINE:
            return self._execute_view_timeline(task, state_view)
        if task.mode is InteractionMode.WHAT_IF:
            return self._execute_what_if(task, state_view)
        raise SpecialistError(
            "UNSUPPORTED_MODE", f"TimelineAnalysisSpecialist does not handle mode '{task.mode.value}'."
        )

    # -- VIEW_TIMELINE: tool 1 only ----------------------------------------

    def _execute_view_timeline(self, task: DelegationTask, state_view: SpecialistStateView) -> TimelineFinding:
        del state_view  # no free-text filtering in this checkpoint; full curated timeline
        try:
            result = query_case_timeline(QueryCaseTimelineRequest(case_id=MVP_CASE_ID), query_id=f"q.{task.task_id}")
        except ToolError as exc:
            raise SpecialistError("TOOL_FAILURE", exc.user_message) from exc

        if result.status == "empty":
            raise SpecialistError("NO_EVENTS_FOUND", "The timeline query returned no events.")

        try:
            pack = load_case_pack(MVP_CASE_ID)
        except CaseLoaderError as exc:
            raise SpecialistError("CASE_DATA_UNAVAILABLE", exc.user_message) from exc
        manifest_by_id = {s.source_id: s for s in pack.source_manifest.sources}

        all_citations = []
        events = []
        skipped_no_date = 0
        for summary in result.events:
            # The frozen TimelineEvent contract requires exactly one event_date;
            # use the earliest known real boundary rather than inventing one.
            effective_date = summary.event_date or summary.start_date or summary.end_date
            if effective_date is None:
                skipped_no_date += 1
                continue
            event_citations = tuple(citation_from_manifest_source(sid, manifest_by_id) for sid in summary.source_ids)
            all_citations.extend(event_citations)
            events.append(
                TimelineEvent(
                    event_id=summary.event_id,
                    event_date=effective_date,
                    title=summary.title,
                    summary=f"{summary.summary} (as of: {summary.date_label})",
                    track=summary.track,
                    evidence_ids=summary.evidence_ids,
                    source_ids=summary.source_ids,
                    citation_ids=tuple(c.citation_id for c in event_citations),
                )
            )

        if not events:
            raise SpecialistError(
                "NO_DATABLE_EVENTS", "No returned timeline events carry any usable date anchor."
            )

        finding_summary = result.summary
        if skipped_no_date:
            finding_summary += (
                f" {skipped_no_date} event(s) with no date anchor at all are omitted from this dated view."
            )

        return TimelineFinding(
            finding_id=f"finding.{task.task_id}",
            task_id=task.task_id,
            summary=finding_summary,
            events=tuple(events),
            citations=tuple(all_citations),
            confidence=ConfidenceLabel.HIGH,
        )

    # -- WHAT_IF: tool 3 only -----------------------------------------------

    def _execute_what_if(self, task: DelegationTask, state_view: SpecialistStateView) -> CounterfactualFinding:
        event_id = state_view.query.selected_event_id
        allowed_change_id = state_view.query.allowed_change_id
        if event_id is None or allowed_change_id is None:
            raise SpecialistError(
                "MISSING_WHAT_IF_SELECTION", "WHAT_IF requires both selected_event_id and allowed_change_id."
            )

        try:
            result = simulate_counterfactual(
                SimulateCounterfactualRequest(
                    case_id=MVP_CASE_ID, event_id=event_id, allowed_change_id=allowed_change_id
                )
            )
        except ToolError as exc:
            raise SpecialistError("TOOL_FAILURE", exc.user_message) from exc

        try:
            pack = load_case_pack(MVP_CASE_ID)
        except CaseLoaderError as exc:
            raise SpecialistError("CASE_DATA_UNAVAILABLE", exc.user_message) from exc
        manifest_by_id = {s.source_id: s for s in pack.source_manifest.sources}

        all_citations = {}
        for sid in result.source_ids:
            citation = citation_from_manifest_source(sid, manifest_by_id)
            all_citations[citation.citation_id] = citation

        unchanged_facts = []
        for index, fact in enumerate(result.unchanged_facts):
            fact_citations = tuple(citation_from_manifest_source(sid, manifest_by_id) for sid in fact.source_ids)
            for c in fact_citations:
                all_citations[c.citation_id] = c
            unchanged_facts.append(
                FindingStatement(
                    statement_id=f"statement.{task.task_id}.{index}",
                    text=fact.text,
                    status=ClaimStatus.ESTABLISHED,
                    citation_ids=tuple(c.citation_id for c in fact_citations),
                )
            )

        return CounterfactualFinding(
            finding_id=f"finding.{task.task_id}",
            task_id=task.task_id,
            event_id=result.event_id,
            allowed_change_id=result.allowed_change_id,
            changed_assumption=result.changed_assumption,
            directly_affected_nodes=result.directly_affected_nodes,
            downstream_possible_effects=result.downstream_possible_effects,
            unchanged_facts=tuple(unchanged_facts),
            unknowns=result.unknowns,
            confidence=result.confidence_label,
            mandatory_hypothetical_disclaimer=result.mandatory_hypothetical_disclaimer,
            citations=tuple(all_citations.values()),
        )
