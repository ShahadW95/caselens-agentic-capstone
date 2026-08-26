"""Runtime-checkable v1 boundaries implemented independently by both tracks."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .contracts import (
    CaseResearchBrief,
    CounterfactualFinding,
    DelegationTask,
    EvidenceFinding,
    LegalFinding,
    ModelRequest,
    ModelResponse,
    ReviewContext,
    ReviewResult,
    SpecialistStateView,
    TimelineFinding,
)


@runtime_checkable
class EvidenceSpecialistProtocol(Protocol):
    def execute(
        self, task: DelegationTask, state_view: SpecialistStateView
    ) -> EvidenceFinding: ...


@runtime_checkable
class LegalSpecialistProtocol(Protocol):
    def execute(
        self, task: DelegationTask, state_view: SpecialistStateView
    ) -> LegalFinding: ...


@runtime_checkable
class TimelineAnalysisSpecialistProtocol(Protocol):
    def execute(
        self, task: DelegationTask, state_view: SpecialistStateView
    ) -> TimelineFinding | CounterfactualFinding: ...


@runtime_checkable
class ReviewerProtocol(Protocol):
    def review(
        self, draft: CaseResearchBrief, context: ReviewContext
    ) -> ReviewResult: ...


@runtime_checkable
class ModelBoundaryProtocol(Protocol):
    def generate(self, request: ModelRequest) -> ModelResponse: ...
