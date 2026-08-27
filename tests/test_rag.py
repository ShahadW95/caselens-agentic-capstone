from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from caselens.contracts import InteractionMode, SourceTier  # noqa: E402
from caselens.rag import RagError  # noqa: E402
from caselens.rag.chunking import Chunk, chunk_document, chunk_documents  # noqa: E402
from caselens.rag.index import (  # noqa: E402
    DeterministicFakeEmbeddingClient,
    IndexBundle,
    build_index,
    load_index,
    save_index,
)
from caselens.rag.loaders import KnowledgeDocument, load_knowledge_documents  # noqa: E402
from caselens.rag.retriever import (  # noqa: E402
    MODE_PERMITTED_SOURCE_TYPES,
    assess_sufficiency,
    build_retrieval_plan,
    reformulate_query,
    retrieve,
    run_agentic_retrieval,
)

FIXTURE_KB_ROOT = Path(__file__).resolve().parent / "fixtures" / "kb_case_001_minimal"
CASE_ID = "US_SDNY_09CR00213_DC"


# ---------------------------------------------------------------------------
# loaders.py
# ---------------------------------------------------------------------------


def test_loads_fixture_knowledge_documents_deterministically_ordered() -> None:
    docs = load_knowledge_documents(CASE_ID, knowledge_root=FIXTURE_KB_ROOT)
    assert [d.meta.document_id for d in docs] == ["FIX_DOC_A", "FIX_DOC_B"]
    assert docs[0].meta.source_type == "FIXTURE_TYPE_A"
    assert docs[0].cited_source_ids == ("SRC_FIX_A",)


def test_dangling_source_id_is_rejected() -> None:
    with pytest.raises(RagError) as excinfo:
        load_knowledge_documents(
            CASE_ID, known_source_ids=frozenset({"SRC_FIX_B"}), knowledge_root=FIXTURE_KB_ROOT
        )
    assert excinfo.value.code == "DANGLING_SOURCE_ID"


def test_missing_frontmatter_is_rejected(tmp_path: Path) -> None:
    case_dir = tmp_path / "case_001"
    case_dir.mkdir()
    (case_dir / "bad.md").write_text("# No frontmatter here\n", encoding="utf-8")
    with pytest.raises(RagError) as excinfo:
        load_knowledge_documents(CASE_ID, knowledge_root=tmp_path)
    assert excinfo.value.code == "MISSING_FRONTMATTER"


def test_document_with_no_citations_is_rejected(tmp_path: Path) -> None:
    case_dir = tmp_path / "case_001"
    case_dir.mkdir()
    (case_dir / "uncited.md").write_text(
        "\n".join(
            [
                "---",
                "document_id: FIX_DOC_UNCITED",
                "title: Uncited",
                "case_id: US_SDNY_09CR00213_DC",
                "source_type: FIXTURE_TYPE_A",
                "source_tier: A",
                "jurisdiction: Fixture",
                "case_status: CLOSED_FIXTURE",
                "version: 0.0.1",
                "effective_or_published_date: 2026-08-27",
                "last_reviewed: 2026-08-27",
                "original_source_urls:",
                "  - https://example.invalid/x",
                "classification: PUBLIC",
                "---",
                "",
                "## A section",
                "",
                "No citation in this section at all.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    with pytest.raises(RagError) as excinfo:
        load_knowledge_documents(CASE_ID, knowledge_root=tmp_path)
    assert excinfo.value.code == "NO_CITATIONS_FOUND"


def test_duplicate_document_id_is_rejected(tmp_path: Path) -> None:
    case_dir = tmp_path / "case_001"
    case_dir.mkdir()
    body = "\n".join(
        [
            "---",
            "document_id: FIX_DOC_DUP",
            "title: Dup",
            "case_id: US_SDNY_09CR00213_DC",
            "source_type: FIXTURE_TYPE_A",
            "source_tier: A",
            "jurisdiction: Fixture",
            "case_status: CLOSED_FIXTURE",
            "version: 0.0.1",
            "effective_or_published_date: 2026-08-27",
            "last_reviewed: 2026-08-27",
            "original_source_urls:",
            "  - https://example.invalid/x",
            "classification: PUBLIC",
            "---",
            "",
            "## A section",
            "",
            "Cites [SRC_FIX_A].",
            "",
        ]
    )
    (case_dir / "one.md").write_text(body, encoding="utf-8")
    (case_dir / "two.md").write_text(body, encoding="utf-8")
    with pytest.raises(RagError) as excinfo:
        load_knowledge_documents(CASE_ID, knowledge_root=tmp_path)
    assert excinfo.value.code == "DUPLICATE_ID"


# ---------------------------------------------------------------------------
# chunking.py
# ---------------------------------------------------------------------------


def test_chunking_produces_stable_ids_and_inherited_metadata() -> None:
    docs = load_knowledge_documents(CASE_ID, knowledge_root=FIXTURE_KB_ROOT)
    chunks = chunk_documents(docs)
    assert [c.chunk_id for c in chunks] == [
        "FIX_DOC_A::first-fixture-section",
        "FIX_DOC_A::second-fixture-section",
        "FIX_DOC_B::only-fixture-section",
    ]
    first = chunks[0]
    assert first.document_id == "FIX_DOC_A"
    assert first.source_type == "FIXTURE_TYPE_A"
    assert first.source_tier == SourceTier.A
    assert first.cited_source_ids == ("SRC_FIX_A",)

    # Re-chunking is deterministic.
    assert chunk_documents(docs) == chunks


def test_no_headings_found_is_rejected() -> None:
    docs = load_knowledge_documents(CASE_ID, knowledge_root=FIXTURE_KB_ROOT)
    no_heading_doc = docs[0].model_copy(update={"body": "Just a paragraph, no H2 heading."})
    with pytest.raises(RagError) as excinfo:
        chunk_document(no_heading_doc)
    assert excinfo.value.code == "NO_HEADINGS_FOUND"


# ---------------------------------------------------------------------------
# index.py
# ---------------------------------------------------------------------------


def _fixture_chunks() -> tuple[Chunk, ...]:
    docs = load_knowledge_documents(CASE_ID, knowledge_root=FIXTURE_KB_ROOT)
    return chunk_documents(docs)


def test_build_save_and_load_index_roundtrip(tmp_path: Path) -> None:
    chunks = _fixture_chunks()
    client = DeterministicFakeEmbeddingClient(dimensions=8)
    bundle = build_index(CASE_ID, chunks, client)
    assert bundle.vectors.shape == (len(chunks), 8)

    save_index(bundle, storage_root=tmp_path, case_folder="case_001")
    from caselens.rag.index import _document_hashes  # internal helper, test-only import

    loaded = load_index(
        storage_root=tmp_path,
        case_folder="case_001",
        expected_document_hashes=_document_hashes(chunks),
        expected_dimensions=8,
    )
    assert isinstance(loaded, IndexBundle)
    assert [c.chunk_id for c in loaded.chunks] == [c.chunk_id for c in chunks]
    assert loaded.vectors.shape == bundle.vectors.shape


def test_index_not_found_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(RagError) as excinfo:
        load_index(
            storage_root=tmp_path, case_folder="case_001", expected_document_hashes={}, expected_dimensions=8
        )
    assert excinfo.value.code == "INDEX_NOT_FOUND"


def test_stale_index_is_rejected(tmp_path: Path) -> None:
    chunks = _fixture_chunks()
    client = DeterministicFakeEmbeddingClient(dimensions=8)
    bundle = build_index(CASE_ID, chunks, client)
    save_index(bundle, storage_root=tmp_path, case_folder="case_001")

    with pytest.raises(RagError) as excinfo:
        load_index(
            storage_root=tmp_path,
            case_folder="case_001",
            expected_document_hashes={"FIX_DOC_A": "not-the-real-hash"},
            expected_dimensions=8,
        )
    assert excinfo.value.code == "STALE_INDEX"


def test_dimension_mismatch_on_load_is_rejected(tmp_path: Path) -> None:
    chunks = _fixture_chunks()
    client = DeterministicFakeEmbeddingClient(dimensions=8)
    bundle = build_index(CASE_ID, chunks, client)
    save_index(bundle, storage_root=tmp_path, case_folder="case_001")
    from caselens.rag.index import _document_hashes

    with pytest.raises(RagError) as excinfo:
        load_index(
            storage_root=tmp_path,
            case_folder="case_001",
            expected_document_hashes=_document_hashes(chunks),
            expected_dimensions=16,
        )
    assert excinfo.value.code == "DIMENSION_MISMATCH"


def test_malformed_manifest_is_rejected(tmp_path: Path) -> None:
    case_dir = tmp_path / "case_001"
    case_dir.mkdir()
    (case_dir / "manifest.json").write_text("{not valid json", encoding="utf-8")
    (case_dir / "vectors.npy").write_bytes(b"")
    (case_dir / "chunks.json").write_text("[]", encoding="utf-8")
    with pytest.raises(RagError) as excinfo:
        load_index(
            storage_root=tmp_path, case_folder="case_001", expected_document_hashes={}, expected_dimensions=8
        )
    assert excinfo.value.code == "MALFORMED_INDEX_MANIFEST"


def test_embedding_client_failure_during_build_is_wrapped() -> None:
    class _BrokenClient:
        model_id = "broken"
        dimensions = 8

        def embed_documents(self, texts):
            raise RuntimeError("simulated provider outage")

        def embed_query(self, text):
            raise RuntimeError("simulated provider outage")

    with pytest.raises(RagError) as excinfo:
        build_index(CASE_ID, _fixture_chunks(), _BrokenClient())
    assert excinfo.value.code == "EMBEDDING_CLIENT_ERROR"


def test_wrong_vector_count_from_embedding_client_is_rejected() -> None:
    class _ShortClient:
        model_id = "short"
        dimensions = 8

        def embed_documents(self, texts):
            return [[0.0] * 8]  # too few vectors for len(texts) chunks

        def embed_query(self, text):
            return [0.0] * 8

    with pytest.raises(RagError) as excinfo:
        build_index(CASE_ID, _fixture_chunks(), _ShortClient())
    assert excinfo.value.code == "EMBEDDING_CLIENT_MISMATCH"


# ---------------------------------------------------------------------------
# retriever.py
# ---------------------------------------------------------------------------


def _chunk(chunk_id: str, text: str, source_type: str, source_tier: SourceTier) -> Chunk:
    return Chunk(
        chunk_id=chunk_id,
        document_id="TEST_DOC",
        file_path="knowledge_base/case_001/test.md",
        heading="Test heading",
        text=text,
        source_type=source_type,
        source_tier=source_tier,
        jurisdiction="Fixture jurisdiction",
        original_source_urls=("https://example.invalid/x",),
        cited_source_ids=("SRC_FIX_A",),
    )


class _FixedEmbeddingClient:
    """Test-only embedding client with fully controlled, hand-picked vectors."""

    model_id = "test-fixed-embedding"
    dimensions = 4

    def __init__(self, vectors: dict[str, list[float]]) -> None:
        self._vectors = vectors

    def embed_documents(self, texts):
        return [self._vectors[text] for text in texts]

    def embed_query(self, text):
        return self._vectors[text]


def test_mode_dependent_permitted_source_types_are_distinct() -> None:
    assert MODE_PERMITTED_SOURCE_TYPES[InteractionMode.ASK_CASE] == ()
    assert MODE_PERMITTED_SOURCE_TYPES[InteractionMode.EXPLAIN_VERDICT] != MODE_PERMITTED_SOURCE_TYPES[
        InteractionMode.VIEW_TIMELINE
    ]
    plan_ask = build_retrieval_plan(
        retrieval_id="r.ask", task_id="t.ask", query="q", mode=InteractionMode.ASK_CASE
    )
    plan_verdict = build_retrieval_plan(
        retrieval_id="r.verdict", task_id="t.verdict", query="q", mode=InteractionMode.EXPLAIN_VERDICT
    )
    assert plan_ask.permitted_source_types == ()
    assert plan_verdict.permitted_source_types == ("TEAM_DIGEST_LEGAL_PLEA_SENTENCE", "TEAM_DIGEST_REGULATORY_LAW")


def test_invalid_retrieval_plan_is_rejected() -> None:
    with pytest.raises(RagError) as excinfo:
        build_retrieval_plan(retrieval_id="r", task_id="t", query="", mode=InteractionMode.ASK_CASE)
    assert excinfo.value.code == "INVALID_RETRIEVAL_PLAN"


def test_retrieve_respects_top_k_and_is_deterministic() -> None:
    chunks = (
        _chunk("c.a", "alpha", "TYPE_X", SourceTier.A),
        _chunk("c.b", "beta", "TYPE_X", SourceTier.A),
        _chunk("c.c", "gamma", "TYPE_X", SourceTier.A),
    )
    vectors = {
        "alpha": [1.0, 0.0, 0.0, 0.0],
        "beta": [0.0, 1.0, 0.0, 0.0],
        "gamma": [0.0, 0.0, 1.0, 0.0],
        "query": [0.9, 0.3, 0.1, 0.0],
    }
    client = _FixedEmbeddingClient(vectors)
    bundle = build_index(CASE_ID, chunks, client)
    plan = build_retrieval_plan(
        retrieval_id="r.1", task_id="t.1", query="query", mode=InteractionMode.ASK_CASE, top_k=2
    )
    first = retrieve(plan, bundle, client)
    second = retrieve(plan, bundle, client)
    assert len(first) == 2
    assert [c.chunk_id for c in first] == ["c.a", "c.b"]  # alpha most aligned, then beta
    assert first == second  # deterministic given the same plan and index


def test_retrieve_filters_by_permitted_source_type_and_tier() -> None:
    chunks = (
        _chunk("c.a", "alpha", "TYPE_A", SourceTier.A),
        _chunk("c.b", "beta", "TYPE_B", SourceTier.B),
    )
    vectors = {"alpha": [1.0, 0.0, 0.0, 0.0], "beta": [1.0, 0.0, 0.0, 0.0], "query": [1.0, 0.0, 0.0, 0.0]}
    client = _FixedEmbeddingClient(vectors)
    bundle = build_index(CASE_ID, chunks, client)

    plan = build_retrieval_plan(
        retrieval_id="r.1",
        task_id="t.1",
        query="query",
        mode=InteractionMode.ASK_CASE,
        top_k=5,
        permitted_source_tiers=(SourceTier.A,),
    )
    results = retrieve(plan.model_copy(update={"permitted_source_types": ("TYPE_A",)}), bundle, client)
    assert [c.chunk_id for c in results] == ["c.a"]


def test_retrieve_with_no_eligible_chunks_returns_empty() -> None:
    chunks = (_chunk("c.a", "alpha", "TYPE_A", SourceTier.A),)
    vectors = {"alpha": [1.0, 0.0, 0.0, 0.0], "query": [1.0, 0.0, 0.0, 0.0]}
    client = _FixedEmbeddingClient(vectors)
    bundle = build_index(CASE_ID, chunks, client)
    plan = build_retrieval_plan(
        retrieval_id="r.1",
        task_id="t.1",
        query="query",
        mode=InteractionMode.ASK_CASE,
        permitted_source_tiers=(SourceTier.B,),  # no chunk has tier B
    )
    results = retrieve(plan.model_copy(update={"permitted_source_types": ("TYPE_A",)}), bundle, client)
    assert results == ()


def test_embedding_query_failure_during_retrieve_is_wrapped() -> None:
    class _BrokenClient:
        model_id = "broken"
        dimensions = 4

        def embed_documents(self, texts):
            return [[1.0, 0.0, 0.0, 0.0] for _ in texts]

        def embed_query(self, text):
            raise RuntimeError("simulated provider outage")

    chunks = (_chunk("c.a", "alpha", "TYPE_A", SourceTier.A),)
    build_client = _BrokenClient()
    # Build succeeds (embed_documents does not raise); only the query path fails.
    bundle = build_index(CASE_ID, chunks, build_client)
    plan = build_retrieval_plan(retrieval_id="r.1", task_id="t.1", query="query", mode=InteractionMode.ASK_CASE)
    with pytest.raises(RagError) as excinfo:
        retrieve(plan, bundle, build_client)
    assert excinfo.value.code == "EMBEDDING_CLIENT_ERROR"


def test_sufficient_evidence_stops_after_one_round() -> None:
    chunks = (
        _chunk("c.high", "high", "TYPE_A", SourceTier.A),
        _chunk("c.low", "low", "TYPE_A", SourceTier.A),
    )
    vectors = {
        "high": [1.0, 0.0, 0.0, 0.0],
        "low": [0.0, 1.0, 0.0, 0.0],
        "match high evidence": [1.0, 0.0, 0.0, 0.0],
    }
    client = _FixedEmbeddingClient(vectors)
    bundle = build_index(CASE_ID, chunks, client)

    result = run_agentic_retrieval(
        task_id="t.1", query="match high evidence", mode=InteractionMode.ASK_CASE, index=bundle, embedding_client=client
    )
    assert len(result.plans) == 1
    assert result.assessment.sufficient is True
    assert result.assessment.may_reformulate is False
    assert "c.high" in result.assessment.relevant_chunk_ids


def test_insufficient_evidence_reformulates_exactly_once_then_stops() -> None:
    chunks = (
        _chunk("c.high", "high", "TYPE_A", SourceTier.A),
        _chunk("c.low", "low", "TYPE_A", SourceTier.A),
    )
    original_query = "orthogonal query"
    reformulated_query = reformulate_query(original_query, ())
    orthogonal_vector = [0.0, 0.0, 1.0, 0.0]
    vectors = {
        "high": [1.0, 0.0, 0.0, 0.0],
        "low": [0.0, 1.0, 0.0, 0.0],
        original_query: orthogonal_vector,
        reformulated_query: orthogonal_vector,
    }
    client = _FixedEmbeddingClient(vectors)
    bundle = build_index(CASE_ID, chunks, client)

    result = run_agentic_retrieval(
        task_id="t.1", query=original_query, mode=InteractionMode.ASK_CASE, index=bundle, embedding_client=client
    )
    assert len(result.plans) == 2
    assert [p.round_number for p in result.plans] == [1, 2]
    assert result.plans[1].query == reformulated_query
    assert result.assessment.sufficient is False
    assert result.assessment.may_reformulate is False  # bounded to exactly two rounds


def test_no_key_or_network_required_for_offline_tests() -> None:
    client = DeterministicFakeEmbeddingClient(dimensions=8)
    assert client.model_id != "gemini-embedding-2"
    # Exercising the fake client end to end never touches the network or env secrets.
    assert client.embed_query("anything") != []
