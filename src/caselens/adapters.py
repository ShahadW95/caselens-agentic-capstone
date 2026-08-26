"""Deterministic development fakes implementing the frozen v1 protocols."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .contracts import (
    CaseResearchBrief,
    ClaimStatus,
    ConfidenceLabel,
    CounterfactualFinding,
    DelegationTask,
    EvidenceFinding,
    FindingStatement,
    LegalFinding,
    ProceedingRecord,
    ProceedingStatus,
    ProceedingType,
    ReviewContext,
    ReviewResult,
    SourceCitation,
    SourceTier,
    SpecialistStateView,
    TimelineEvent,
    TimelineFinding,
    TimelineTrack,
)
from .protocols import (
    EvidenceSpecialistProtocol,
    LegalSpecialistProtocol,
    ReviewerProtocol,
    TimelineAnalysisSpecialistProtocol,
)

FAKE_WARNING = (
    "DEVELOPMENT FAKE: fictional identifiers and content; never select in live mode."
)


def _citation() -> SourceCitation:
    return SourceCitation(
        citation_id="cit.fake.001",
        source_id="source.fake.001",
        document_id="document.fake.001",
        chunk_id="chunk.fake.001",
        title="Fictional contract fixture",
        heading="Development-only evidence",
        source_type="fictional_fixture",
        source_tier=SourceTier.A,
        original_url="https://example.invalid/caselens-fixture",
    )


def _statement(prefix: str = "fact") -> FindingStatement:
    return FindingStatement(
        statement_id=f"statement.fake.{prefix}",
        text="Fictional contract evidence used only for offline compatibility tests.",
        status=ClaimStatus.ESTABLISHED,
        citation_ids=("cit.fake.001",),
    )


class FakeEvidenceSpecialist:
    """Development-only deterministic Evidence Specialist."""

    def execute(
        self, task: DelegationTask, state_view: SpecialistStateView
    ) -> EvidenceFinding:
        del state_view
        return EvidenceFinding(
            finding_id="finding.fake.evidence",
            task_id=task.task_id,
            summary=FAKE_WARNING,
            established_facts=(_statement("evidence"),),
            citations=(_citation(),),
            confidence=ConfidenceLabel.HIGH,
        )


class FakeLegalSpecialist:
    """Development-only deterministic Legal Explanation Specialist."""

    def execute(
        self, task: DelegationTask, state_view: SpecialistStateView
    ) -> LegalFinding:
        del state_view
        return LegalFinding(
            finding_id="finding.fake.legal",
            task_id=task.task_id,
            explanation=FAKE_WARNING,
            established_facts=(_statement("legal"),),
            proceeding_records=(
                ProceedingRecord(
                    proceeding_id="proceeding.fake.criminal",
                    proceeding_type=ProceedingType.CRIMINAL_CASE,
                    status=ProceedingStatus.CLOSED_FINAL,
                    status_as_of=date(2009, 6, 29),
                    source_ids=("source.fake.001",),
                    status_note="Fictional fixture representing a closed proceeding.",
                ),
            ),
            citations=(_citation(),),
            confidence=ConfidenceLabel.HIGH,
            educational_disclaimer="Educational research only; not legal advice.",
        )


class FakeTimelineAnalysisSpecialist:
    """Development-only deterministic Timeline/What-If Specialist."""

    def execute(
        self, task: DelegationTask, state_view: SpecialistStateView
    ) -> TimelineFinding | CounterfactualFinding:
        if state_view.query.mode.value == "WHAT_IF":
            return CounterfactualFinding(
                finding_id="finding.fake.counterfactual",
                task_id=task.task_id,
                event_id=state_view.query.selected_event_id or "event.fake.001",
                allowed_change_id=state_view.query.allowed_change_id
                or "change.fake.001",
                changed_assumption="A fictional allowed change is applied.",
                directly_affected_nodes=("node.fake.001",),
                downstream_possible_effects=(
                    "A fictional downstream effect could occur.",
                ),
                unchanged_facts=(_statement("unchanged"),),
                unknowns=("Real-world effects remain unknown.",),
                confidence=ConfidenceLabel.LOW,
                mandatory_hypothetical_disclaimer=(
                    "This is a bounded hypothetical, not a prediction or alternate verdict."
                ),
                citations=(_citation(),),
            )

        event = TimelineEvent(
            event_id="event.fake.001",
            event_date=date(2009, 1, 1),
            title="Fictional timeline fixture",
            summary=FAKE_WARNING,
            track=TimelineTrack.CRIMINAL,
            evidence_ids=("evidence.fake.001",),
            source_ids=("source.fake.001",),
            citation_ids=("cit.fake.001",),
        )
        return TimelineFinding(
            finding_id="finding.fake.timeline",
            task_id=task.task_id,
            summary=FAKE_WARNING,
            events=(event,),
            citations=(_citation(),),
            confidence=ConfidenceLabel.HIGH,
        )


class FakeReviewer:
    """Development-only reviewer that approves an already valid draft."""

    def review(
        self, draft: CaseResearchBrief, context: ReviewContext
    ) -> ReviewResult:
        del context
        return ReviewResult(
            review_id="review.fake.001",
            approved=True,
            final_brief=draft,
        )


@dataclass(frozen=True)
class DevelopmentFakeAdapters:
    evidence: EvidenceSpecialistProtocol
    legal: LegalSpecialistProtocol
    timeline_analysis: TimelineAnalysisSpecialistProtocol
    reviewer: ReviewerProtocol
    checkpoint_label: str = FAKE_WARNING


def create_development_fake_adapters() -> DevelopmentFakeAdapters:
    """Explicit factory; production/live configuration never calls this silently."""

    return DevelopmentFakeAdapters(
        evidence=FakeEvidenceSpecialist(),
        legal=FakeLegalSpecialist(),
        timeline_analysis=FakeTimelineAnalysisSpecialist(),
        reviewer=FakeReviewer(),
    )
