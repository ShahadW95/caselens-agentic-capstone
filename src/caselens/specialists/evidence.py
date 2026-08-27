"""Source & Evidence Specialist — handles ASK_CASE evidence tasks and CHECK_CLAIM."""

from __future__ import annotations

from ..contracts import (
    ClaimStatus,
    ConfidenceLabel,
    DelegationTask,
    EvidenceFinding,
    FinancialAmount,
    FindingStatement,
    InteractionMode,
    ModelRequest,
    MVP_CASE_ID,
    SpecialistRole,
    SpecialistStateView,
)
from ..protocols import ModelBoundaryProtocol
from ..rag.index import EmbeddingClientProtocol, IndexBundle
from ..rag.retriever import run_agentic_retrieval
from ..services.case_loader import CaseLoaderError, load_case_pack
from ..tools import ToolError
from ..tools.claim_support import CheckClaimSupportRequest, check_claim_support
from . import (
    SpecialistError,
    citation_from_chunk,
    citation_from_manifest_source,
    combine_confidence,
    extract_source_ids_from_text,
    generate_with_one_repair,
)

__all__ = ["EvidenceSpecialist"]

_CLAIM_STATUS_TO_CATEGORY = {
    "supported": ("established_facts", ClaimStatus.SUPPORTED, ConfidenceLabel.HIGH),
    "contradicted": ("disputed_items", ClaimStatus.CONTRADICTED, ConfidenceLabel.HIGH),
    "partially_supported": ("disputed_items", ClaimStatus.PARTIALLY_SUPPORTED, ConfidenceLabel.MEDIUM),
    "insufficient_evidence": ("unknowns", ClaimStatus.INSUFFICIENT_EVIDENCE, ConfidenceLabel.LOW),
}


def _parse_summary_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip().upper().startswith("SUMMARY:"):
            summary = line.split(":", 1)[1].strip()
            if summary:
                return summary
    raise ValueError("model response did not contain a 'SUMMARY:' line")


class EvidenceSpecialist:
    """Real Source & Evidence Specialist behind ``EvidenceSpecialistProtocol``."""

    def __init__(self, model: ModelBoundaryProtocol, embedding_client: EmbeddingClientProtocol, index: IndexBundle) -> None:
        self._model = model
        self._embedding_client = embedding_client
        self._index = index

    def execute(self, task: DelegationTask, state_view: SpecialistStateView) -> EvidenceFinding:
        if task.role is not SpecialistRole.EVIDENCE:
            raise SpecialistError("WRONG_ROLE", "This specialist only accepts SOURCE_AND_EVIDENCE tasks.")
        if state_view.query.case_id != MVP_CASE_ID:
            raise SpecialistError("UNSUPPORTED_CASE", "Only the curated MVP case is supported.")

        if task.mode is InteractionMode.CHECK_CLAIM:
            return self._execute_check_claim(task, state_view)
        if task.mode is InteractionMode.ASK_CASE:
            return self._execute_ask_case(task, state_view)
        raise SpecialistError("UNSUPPORTED_MODE", f"EvidenceSpecialist does not handle mode '{task.mode.value}'.")

    # -- CHECK_CLAIM: deterministic tool 2, enriched with relevant retrieval --
    # (no model call: tool 2's explanation is already a complete, grounded verdict)

    def _execute_check_claim(self, task: DelegationTask, state_view: SpecialistStateView) -> EvidenceFinding:
        claim_id = state_view.query.selected_claim_id
        if claim_id is None:
            raise SpecialistError("MISSING_CLAIM_SELECTION", "CHECK_CLAIM requires a selected_claim_id.")

        try:
            result = check_claim_support(CheckClaimSupportRequest(case_id=MVP_CASE_ID, claim_id=claim_id))
        except ToolError as exc:
            raise SpecialistError("TOOL_FAILURE", exc.user_message) from exc

        try:
            pack = load_case_pack(MVP_CASE_ID)
        except CaseLoaderError as exc:
            raise SpecialistError("CASE_DATA_UNAVAILABLE", exc.user_message) from exc
        manifest_by_id = {s.source_id: s for s in pack.source_manifest.sources}

        if not result.supporting_source_ids:
            raise SpecialistError(
                "NO_CITABLE_SOURCES", f"Claim '{claim_id}' has no citable sources to ground a finding on."
            )

        citations = list(
            citation_from_manifest_source(sid, manifest_by_id) for sid in result.supporting_source_ids
        )

        retrieval = run_agentic_retrieval(
            task_id=task.task_id,
            query=result.normalized_claim_text,
            mode=InteractionMode.CHECK_CLAIM,
            index=self._index,
            embedding_client=self._embedding_client,
        )
        known_citation_ids = {c.citation_id for c in citations}
        for chunk in retrieval.chunks:
            for sid in extract_source_ids_from_text(chunk.excerpt):
                chunk_citation = citation_from_chunk(chunk, sid, manifest_by_id)
                if chunk_citation.citation_id not in known_citation_ids:
                    citations.append(chunk_citation)
                    known_citation_ids.add(chunk_citation.citation_id)

        category, claim_status, confidence = _CLAIM_STATUS_TO_CATEGORY[result.status]
        statement = FindingStatement(
            statement_id=f"statement.{task.task_id}.claim",
            text=result.explanation,
            status=claim_status,
            citation_ids=tuple(sorted(known_citation_ids)),
        )
        categories = {"established_facts": (), "allegations": (), "disputed_items": (), "unknowns": ()}
        categories[category] = (statement,)
        citations = tuple(citations)

        financial_amounts = tuple(
            FinancialAmount(
                amount_id=a.amount_id,
                amount_kind=a.amount_kind,
                currency=a.currency,
                value_or_range=a.value_or_range,
                as_of_date=a.as_of_date,
                source_ids=a.source_ids,
                measurement_note=a.measurement_note,
            )
            for a in result.financial_amounts
        )

        return EvidenceFinding(
            finding_id=f"finding.{task.task_id}",
            task_id=task.task_id,
            summary=result.explanation,
            established_facts=categories["established_facts"],
            allegations=categories["allegations"],
            disputed_items=categories["disputed_items"],
            unknowns=categories["unknowns"],
            financial_amounts=financial_amounts,
            citations=citations,
            confidence=confidence,
        )

    # -- ASK_CASE: agentic RAG, plus one model call for the summary --------

    def _execute_ask_case(self, task: DelegationTask, state_view: SpecialistStateView) -> EvidenceFinding:
        query = state_view.query.user_query.strip()
        if not query:
            raise SpecialistError("MISSING_QUERY_TEXT", "ASK_CASE requires a non-empty user_query.")

        result = run_agentic_retrieval(
            task_id=task.task_id,
            query=query,
            mode=InteractionMode.ASK_CASE,
            index=self._index,
            embedding_client=self._embedding_client,
        )

        try:
            pack = load_case_pack(MVP_CASE_ID)
        except CaseLoaderError as exc:
            raise SpecialistError("CASE_DATA_UNAVAILABLE", exc.user_message) from exc
        manifest_by_id = {s.source_id: s for s in pack.source_manifest.sources}

        citations = []
        statements = []
        for index, chunk in enumerate(result.chunks):
            source_ids = extract_source_ids_from_text(chunk.excerpt)
            if not source_ids:
                continue
            chunk_citations = tuple(citation_from_chunk(chunk, sid, manifest_by_id) for sid in source_ids)
            citations.extend(chunk_citations)
            statements.append(
                FindingStatement(
                    statement_id=f"statement.{task.task_id}.{index}",
                    text=chunk.excerpt,
                    status=ClaimStatus.ESTABLISHED,
                    citation_ids=tuple(c.citation_id for c in chunk_citations),
                )
            )

        if not citations:
            raise SpecialistError(
                "INSUFFICIENT_EVIDENCE",
                "No citable evidence was found for this question after agentic retrieval.",
            )

        base_request = ModelRequest(
            request_id=f"model.{task.task_id}",
            operation=(
                "Write exactly one line starting with 'SUMMARY:' giving a concise, neutral 1-2 "
                "sentence answer to the user's question, grounded only in the provided case context."
            ),
            public_case_context="\n\n".join(c.excerpt for c in result.chunks[:5]),
            user_question=query,
            language=state_view.query.language,
        )
        fallback = statements[0].text[:200]
        summary_result = generate_with_one_repair(self._model, base_request, _parse_summary_line, fallback=fallback)

        rag_confidence = ConfidenceLabel.HIGH if result.assessment.sufficient else ConfidenceLabel.MEDIUM
        return EvidenceFinding(
            finding_id=f"finding.{task.task_id}",
            task_id=task.task_id,
            summary=summary_result.text,
            established_facts=tuple(statements),
            citations=tuple(citations),
            confidence=combine_confidence(summary_result.confidence, rag_confidence),
        )
