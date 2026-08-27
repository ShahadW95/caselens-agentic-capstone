"""Agentic retrieval: plan, retrieve, assess sufficiency, reformulate once.

Builds and returns the frozen v1 contracts (``RetrievalPlan``,
``RetrievedChunk``, ``EvidenceAssessment``) directly, so a specialist built in
B4 can consume this module's output with no adapter layer in between.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..contracts import (
    EvidenceAssessment,
    InteractionMode,
    MVP_CASE_ID,
    RetrievalPlan,
    RetrievedChunk,
    SourceTier,
)
from . import RagError
from .index import EmbeddingClientProtocol, IndexBundle

__all__ = [
    "MODE_PERMITTED_SOURCE_TYPES",
    "build_retrieval_plan",
    "retrieve",
    "assess_sufficiency",
    "reformulate_query",
    "AgenticRetrievalResult",
    "run_agentic_retrieval",
]

# Mode-dependent filters: which topic-tagged knowledge documents a given
# interaction mode should prioritize. ASK_CASE is intentionally unrestricted.
MODE_PERMITTED_SOURCE_TYPES: dict[InteractionMode, tuple[str, ...]] = {
    InteractionMode.ASK_CASE: (),
    InteractionMode.VIEW_TIMELINE: ("TEAM_DIGEST_TIMELINE",),
    InteractionMode.CHECK_CLAIM: ("TEAM_DIGEST_CLAIMS_EVIDENCE", "TEAM_DIGEST_TIMELINE"),
    InteractionMode.EXPLAIN_VERDICT: ("TEAM_DIGEST_LEGAL_PLEA_SENTENCE", "TEAM_DIGEST_REGULATORY_LAW"),
    InteractionMode.WHAT_IF: ("TEAM_DIGEST_TIMELINE", "TEAM_DIGEST_CLAIMS_EVIDENCE"),
}


def build_retrieval_plan(
    *,
    retrieval_id: str,
    task_id: str,
    query: str,
    mode: InteractionMode,
    round_number: int = 1,
    top_k: int = 5,
    permitted_source_tiers: tuple[SourceTier, ...] = (SourceTier.A, SourceTier.B),
) -> RetrievalPlan:
    try:
        return RetrievalPlan(
            retrieval_id=retrieval_id,
            task_id=task_id,
            case_id=MVP_CASE_ID,
            query=query,
            permitted_source_types=MODE_PERMITTED_SOURCE_TYPES.get(mode, ()),
            permitted_source_tiers=permitted_source_tiers,
            top_k=top_k,
            round_number=round_number,
        )
    except Exception as exc:  # noqa: BLE001 - normalized into a safe error below
        raise RagError("INVALID_RETRIEVAL_PLAN", f"Could not build a retrieval plan: {exc}") from exc


def retrieve(plan: RetrievalPlan, index: IndexBundle, embedding_client: EmbeddingClientProtocol) -> tuple[RetrievedChunk, ...]:
    if index.vectors.shape[0] != len(index.chunks):
        raise RagError("INDEX_CORRUPT", "The index vector count does not match its chunk count.")

    try:
        raw_query_vector = embedding_client.embed_query(plan.query)
    except Exception as exc:  # noqa: BLE001 - normalized into a safe error below
        raise RagError("EMBEDDING_CLIENT_ERROR", "The embedding client failed to embed the query.") from exc
    query_vector = np.asarray(raw_query_vector, dtype=np.float64)
    if query_vector.shape != (embedding_client.dimensions,):
        raise RagError("DIMENSION_MISMATCH", "The query embedding has an unexpected shape.")
    norm = np.linalg.norm(query_vector)
    if norm > 0:
        query_vector = query_vector / norm

    eligible_indices = [
        i
        for i, chunk in enumerate(index.chunks)
        if (not plan.permitted_source_types or chunk.source_type in plan.permitted_source_types)
        and chunk.source_tier in plan.permitted_source_tiers
    ]
    if not eligible_indices:
        return ()

    scores = index.vectors[eligible_indices] @ query_vector
    ranked = sorted(
        zip(eligible_indices, scores),
        key=lambda pair: (-round(float(pair[1]), 10), index.chunks[pair[0]].chunk_id),
    )[: plan.top_k]

    results: list[RetrievedChunk] = []
    for chunk_index, score in ranked:
        chunk = index.chunks[chunk_index]
        results.append(
            RetrievedChunk(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                file_path=chunk.file_path,
                heading=chunk.heading,
                excerpt=chunk.text,
                similarity_score=max(0.0, min(1.0, (float(score) + 1.0) / 2.0)),
                source_type=chunk.source_type,
                source_tier=chunk.source_tier,
                jurisdiction=chunk.jurisdiction,
                original_source_urls=chunk.original_source_urls,
            )
        )
    return tuple(results)


def assess_sufficiency(
    *,
    assessment_id: str,
    retrieval_id: str,
    chunks: tuple[RetrievedChunk, ...],
    minimum_chunks: int = 1,
    minimum_score: float = 0.55,
) -> EvidenceAssessment:
    strong_chunks = [c for c in chunks if c.similarity_score >= minimum_score]
    sufficient = len(strong_chunks) >= minimum_chunks
    missing: tuple[str, ...] = ()
    if not sufficient:
        missing = ("No sufficiently similar chunk was found in the permitted source types/tiers.",)
    return EvidenceAssessment(
        assessment_id=assessment_id,
        retrieval_id=retrieval_id,
        sufficient=sufficient,
        rationale=(
            f"{len(strong_chunks)} of {len(chunks)} retrieved chunks met the "
            f"{minimum_score:.2f} similarity threshold."
            if chunks
            else "No chunks were retrieved under the current filters."
        ),
        relevant_chunk_ids=tuple(c.chunk_id for c in strong_chunks) or tuple(c.chunk_id for c in chunks),
        missing_information=missing,
        may_reformulate=not sufficient,
    )


def reformulate_query(original_query: str, missing_information: tuple[str, ...]) -> str:
    del missing_information  # heuristic keeps the audit trail simple and bounded
    return f"{original_query.strip()} (broaden: case overview, timeline, claims, and legal context)"


@dataclass(frozen=True)
class AgenticRetrievalResult:
    plans: tuple[RetrievalPlan, ...]
    chunks: tuple[RetrievedChunk, ...]
    assessment: EvidenceAssessment


def run_agentic_retrieval(
    *,
    task_id: str,
    query: str,
    mode: InteractionMode,
    index: IndexBundle,
    embedding_client: EmbeddingClientProtocol,
    top_k: int = 5,
    permitted_source_tiers: tuple[SourceTier, ...] = (SourceTier.A, SourceTier.B),
) -> AgenticRetrievalResult:
    """Plan, retrieve, and assess; reformulate and retrieve once more if insufficient."""

    round_one_plan = build_retrieval_plan(
        retrieval_id=f"retrieval.{task_id}.r1",
        task_id=task_id,
        query=query,
        mode=mode,
        round_number=1,
        top_k=top_k,
        permitted_source_tiers=permitted_source_tiers,
    )
    round_one_chunks = retrieve(round_one_plan, index, embedding_client)
    round_one_assessment = assess_sufficiency(
        assessment_id=f"assessment.{task_id}.r1",
        retrieval_id=round_one_plan.retrieval_id,
        chunks=round_one_chunks,
    )

    if round_one_assessment.sufficient or not round_one_assessment.may_reformulate:
        return AgenticRetrievalResult(
            plans=(round_one_plan,), chunks=round_one_chunks, assessment=round_one_assessment
        )

    round_two_plan = build_retrieval_plan(
        retrieval_id=f"retrieval.{task_id}.r2",
        task_id=task_id,
        query=reformulate_query(query, round_one_assessment.missing_information),
        mode=mode,
        round_number=2,
        top_k=top_k,
        permitted_source_tiers=permitted_source_tiers,
    )
    round_two_chunks = retrieve(round_two_plan, index, embedding_client)
    round_two_assessment = assess_sufficiency(
        assessment_id=f"assessment.{task_id}.r2",
        retrieval_id=round_two_plan.retrieval_id,
        chunks=round_two_chunks,
    )
    # Round two never reformulates again; the boundary is exactly two rounds.
    round_two_assessment = round_two_assessment.model_copy(update={"may_reformulate": False})

    return AgenticRetrievalResult(
        plans=(round_one_plan, round_two_plan),
        chunks=round_two_chunks,
        assessment=round_two_assessment,
    )
