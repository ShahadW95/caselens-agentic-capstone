"""Legal Explanation Specialist — handles EXPLAIN_VERDICT ("Explain the Judgment")."""

from __future__ import annotations

from ..contracts import (
    ClaimStatus,
    ConfidenceLabel,
    DelegationTask,
    FindingStatement,
    InteractionMode,
    LegalFinding,
    ModelRequest,
    MVP_CASE_ID,
    SpecialistRole,
    SpecialistStateView,
)
from ..protocols import ModelBoundaryProtocol
from ..rag.index import EmbeddingClientProtocol, IndexBundle
from ..rag.retriever import run_agentic_retrieval
from ..services.case_loader import CaseLoaderError, load_case_pack
from . import (
    SpecialistError,
    citation_from_chunk,
    combine_confidence,
    extract_source_ids_from_text,
    generate_with_one_repair,
)

__all__ = ["LegalSpecialist"]

_EDUCATIONAL_DISCLAIMER = (
    "This is educational research about a closed case, not legal advice, and does not "
    "predict or represent any ongoing or alternate legal outcome."
)
_DEFAULT_QUERY = "Explain the charges, the guilty plea, and the court's sentencing judgment."


def _parse_explanation(text: str) -> str:
    lines = [line.split(":", 1)[1].strip() for line in text.splitlines() if line.strip().upper().startswith("EXPLANATION:")]
    if not lines or not lines[0]:
        raise ValueError("model response did not contain an 'EXPLANATION:' line")
    return lines[0]


class LegalSpecialist:
    """Real Legal Explanation Specialist behind ``LegalSpecialistProtocol``."""

    def __init__(self, model: ModelBoundaryProtocol, embedding_client: EmbeddingClientProtocol, index: IndexBundle) -> None:
        self._model = model
        self._embedding_client = embedding_client
        self._index = index

    def execute(self, task: DelegationTask, state_view: SpecialistStateView) -> LegalFinding:
        if task.role is not SpecialistRole.LEGAL:
            raise SpecialistError("WRONG_ROLE", "This specialist only accepts LEGAL_EXPLANATION tasks.")
        if state_view.query.case_id != MVP_CASE_ID:
            raise SpecialistError("UNSUPPORTED_CASE", "Only the curated MVP case is supported.")
        if task.mode is not InteractionMode.EXPLAIN_VERDICT:
            raise SpecialistError("UNSUPPORTED_MODE", f"LegalSpecialist does not handle mode '{task.mode.value}'.")

        query = state_view.query.user_query.strip() or _DEFAULT_QUERY

        result = run_agentic_retrieval(
            task_id=task.task_id,
            query=query,
            mode=InteractionMode.EXPLAIN_VERDICT,
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
                "INSUFFICIENT_EVIDENCE", "No citable legal material was found after agentic retrieval."
            )

        base_request = ModelRequest(
            request_id=f"model.{task.task_id}",
            operation=(
                "Write exactly one line starting with 'EXPLANATION:' giving a plain-language "
                "explanation of the charges, guilty plea, and sentencing judgment, grounded only "
                "in the provided case context. Never invent a jury verdict or trial evidence; "
                "there was no trial."
            ),
            public_case_context="\n\n".join(c.excerpt for c in result.chunks[:5]),
            user_question=query,
            language=state_view.query.language,
        )
        fallback = statements[0].text[:200]
        explanation_result = generate_with_one_repair(
            self._model, base_request, _parse_explanation, fallback=fallback
        )

        rag_confidence = ConfidenceLabel.HIGH if result.assessment.sufficient else ConfidenceLabel.MEDIUM
        return LegalFinding(
            finding_id=f"finding.{task.task_id}",
            task_id=task.task_id,
            explanation=explanation_result.text,
            established_facts=tuple(statements),
            proceeding_records=pack.case_metadata.proceedings,
            citations=tuple(citations),
            confidence=combine_confidence(explanation_result.confidence, rag_confidence),
            educational_disclaimer=_EDUCATIONAL_DISCLAIMER,
        )
