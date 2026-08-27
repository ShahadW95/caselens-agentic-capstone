"""Embedding boundary and transparent local NumPy vector index.

The embedding client is injected through ``EmbeddingClientProtocol`` so the
production Gemini adapter and this checkpoint's deterministic fake share one
call site. No network call happens anywhere in this module or at import
time; a live embedding client is wired in only by the caller (never from
inside ``pytest`` and never silently).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol, Sequence, runtime_checkable

import numpy as np

from . import RagError
from .chunking import Chunk

__all__ = [
    "EmbeddingClientProtocol",
    "DeterministicFakeEmbeddingClient",
    "IndexManifest",
    "IndexBundle",
    "DEFAULT_STORAGE_ROOT",
    "build_index",
    "save_index",
    "load_index",
]

INDEX_SCHEMA_VERSION = "1"
DEFAULT_STORAGE_ROOT = Path(__file__).resolve().parents[3] / "storage"


@runtime_checkable
class EmbeddingClientProtocol(Protocol):
    model_id: str
    dimensions: int

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class DeterministicFakeEmbeddingClient:
    """Offline, seedless, hash-based embedding client for tests and CI.

    Never selected in production: callers must explicitly construct this
    class (e.g. via ``--fake-embeddings``); nothing here reaches the network.
    """

    model_id = "development-fake-embedding"

    def __init__(self, dimensions: int = 768) -> None:
        self.dimensions = dimensions

    def _embed_one(self, text: str, *, task: str) -> list[float]:
        digest_seed = f"{task}:{text}".encode("utf-8")
        vector = np.empty(self.dimensions, dtype=np.float64)
        block = b""
        offset = 0
        while offset < self.dimensions:
            block = hashlib.sha256(digest_seed + block + str(offset).encode("utf-8")).digest()
            take = min(len(block), self.dimensions - offset)
            vector[offset : offset + take] = np.frombuffer(block[:take], dtype=np.uint8)
            offset += take
        vector = vector / 255.0 - 0.5
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector.tolist()

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._embed_one(text, task="retrieval_document") for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed_one(text, task="retrieval_query")


@dataclass(frozen=True)
class IndexManifest:
    schema_version: str
    case_id: str
    embedding_model_id: str
    embedding_dimensions: int
    document_hashes: dict[str, str]
    chunk_count: int
    created_at: str

    def to_json(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "case_id": self.case_id,
            "embedding_model_id": self.embedding_model_id,
            "embedding_dimensions": self.embedding_dimensions,
            "document_hashes": self.document_hashes,
            "chunk_count": self.chunk_count,
            "created_at": self.created_at,
        }

    @classmethod
    def from_json(cls, data: dict[str, object]) -> "IndexManifest":
        try:
            return cls(
                schema_version=str(data["schema_version"]),
                case_id=str(data["case_id"]),
                embedding_model_id=str(data["embedding_model_id"]),
                embedding_dimensions=int(data["embedding_dimensions"]),
                document_hashes=dict(data["document_hashes"]),
                chunk_count=int(data["chunk_count"]),
                created_at=str(data["created_at"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise RagError("MALFORMED_INDEX_MANIFEST", "The index manifest is malformed.") from exc


@dataclass(frozen=True)
class IndexBundle:
    manifest: IndexManifest
    chunks: tuple[Chunk, ...]
    vectors: np.ndarray  # shape (len(chunks), embedding_dimensions), L2-normalized rows


def _document_hashes(chunks: tuple[Chunk, ...]) -> dict[str, str]:
    per_document: dict[str, list[str]] = {}
    for chunk in chunks:
        per_document.setdefault(chunk.document_id, []).append(chunk.text)
    return {
        document_id: hashlib.sha256("␟".join(sorted(texts)).encode("utf-8")).hexdigest()
        for document_id, texts in per_document.items()
    }


def build_index(
    case_id: str,
    chunks: tuple[Chunk, ...],
    embedding_client: EmbeddingClientProtocol,
) -> IndexBundle:
    if not chunks:
        raise RagError("NO_CHUNKS_TO_INDEX", "There are no chunks to build an index from.")
    try:
        raw_vectors = embedding_client.embed_documents([chunk.text for chunk in chunks])
    except Exception as exc:  # noqa: BLE001 - normalized into a safe error below
        raise RagError("EMBEDDING_CLIENT_ERROR", "The embedding client failed to embed documents.") from exc
    if len(raw_vectors) != len(chunks):
        raise RagError("EMBEDDING_CLIENT_MISMATCH", "Embedding client returned the wrong vector count.")
    vectors = np.asarray(raw_vectors, dtype=np.float64)
    if vectors.ndim != 2 or vectors.shape[1] != embedding_client.dimensions:
        raise RagError(
            "DIMENSION_MISMATCH",
            f"Expected {embedding_client.dimensions}-dimensional vectors from the embedding client.",
        )
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    vectors = vectors / norms

    manifest = IndexManifest(
        schema_version=INDEX_SCHEMA_VERSION,
        case_id=case_id,
        embedding_model_id=embedding_client.model_id,
        embedding_dimensions=embedding_client.dimensions,
        document_hashes=_document_hashes(chunks),
        chunk_count=len(chunks),
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    return IndexBundle(manifest=manifest, chunks=chunks, vectors=vectors)


def save_index(bundle: IndexBundle, *, storage_root: Path | None = None, case_folder: str) -> Path:
    root = (storage_root if storage_root is not None else DEFAULT_STORAGE_ROOT) / case_folder
    root.mkdir(parents=True, exist_ok=True)
    np.save(root / "vectors.npy", bundle.vectors)
    (root / "chunks.json").write_text(
        json.dumps([chunk.model_dump(mode="json") for chunk in bundle.chunks]), encoding="utf-8"
    )
    (root / "manifest.json").write_text(json.dumps(bundle.manifest.to_json()), encoding="utf-8")
    return root


def load_index(
    *,
    storage_root: Path | None = None,
    case_folder: str,
    expected_document_hashes: dict[str, str],
    expected_dimensions: int,
) -> IndexBundle:
    root = (storage_root if storage_root is not None else DEFAULT_STORAGE_ROOT) / case_folder
    manifest_path = root / "manifest.json"
    vectors_path = root / "vectors.npy"
    chunks_path = root / "chunks.json"
    if not (manifest_path.exists() and vectors_path.exists() and chunks_path.exists()):
        raise RagError("INDEX_NOT_FOUND", "No generated index was found for this case.")

    try:
        manifest = IndexManifest.from_json(json.loads(manifest_path.read_text(encoding="utf-8")))
    except json.JSONDecodeError as exc:
        raise RagError("MALFORMED_INDEX_MANIFEST", "The index manifest is not valid JSON.") from exc

    if manifest.schema_version != INDEX_SCHEMA_VERSION:
        raise RagError("STALE_INDEX", "The generated index uses an outdated schema version.")
    if manifest.embedding_dimensions != expected_dimensions:
        raise RagError(
            "DIMENSION_MISMATCH",
            "The generated index's embedding dimensionality does not match the configured model.",
        )
    if manifest.document_hashes != expected_document_hashes:
        raise RagError("STALE_INDEX", "The generated index is stale relative to the knowledge base.")

    try:
        raw_chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RagError("MALFORMED_INDEX_MANIFEST", "The index chunk store is not valid JSON.") from exc
    chunks = tuple(Chunk.model_validate(item) for item in raw_chunks)

    vectors = np.load(vectors_path)
    if vectors.shape != (len(chunks), expected_dimensions):
        raise RagError("DIMENSION_MISMATCH", "The stored vector matrix shape does not match the chunk store.")

    return IndexBundle(manifest=manifest, chunks=chunks, vectors=vectors)
