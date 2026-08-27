"""Heading-aware chunking of loaded knowledge documents.

Splits each document's body on H2 (``## ``) headings so no chunk mixes text
from two unrelated sections. Chunk IDs are derived deterministically from the
document ID and heading, so a regenerated index is comparable to a prior one.
"""

from __future__ import annotations

import hashlib
import re

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field

from ..contracts import NonEmptyText, SourceTier, StableId
from . import RagError
from .loaders import KnowledgeDocument

__all__ = ["Chunk", "chunk_document", "chunk_documents"]

_H2_PATTERN = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
_CITATION_PATTERN = re.compile(r"\[(SRC_[A-Za-z0-9_]+)\]")


class Chunk(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    chunk_id: StableId
    document_id: StableId
    file_path: NonEmptyText
    heading: NonEmptyText
    text: NonEmptyText
    source_type: NonEmptyText
    source_tier: SourceTier
    jurisdiction: NonEmptyText
    original_source_urls: tuple[AnyHttpUrl, ...] = Field(min_length=1)
    cited_source_ids: tuple[StableId, ...] = ()


def _slugify(heading: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", heading.lower()).strip("-")
    return slug or hashlib.sha1(heading.encode("utf-8")).hexdigest()[:8]


def chunk_document(document: KnowledgeDocument) -> tuple[Chunk, ...]:
    matches = list(_H2_PATTERN.finditer(document.body))
    if not matches:
        raise RagError(
            "NO_HEADINGS_FOUND",
            f"'{document.file_path}' has no H2 (## ) sections to chunk on.",
        )

    chunks: list[Chunk] = []
    for index, match in enumerate(matches):
        heading = match.group(1).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(document.body)
        section_text = document.body[start:end].strip()
        if not section_text:
            raise RagError(
                "EMPTY_SECTION",
                f"'{document.file_path}' section '{heading}' has no content.",
            )
        cited = tuple(sorted(set(_CITATION_PATTERN.findall(section_text))))
        chunk_id = f"{document.meta.document_id}::{_slugify(heading)}"
        chunks.append(
            Chunk(
                chunk_id=chunk_id,
                document_id=document.meta.document_id,
                file_path=document.file_path,
                heading=heading,
                text=section_text,
                source_type=document.meta.source_type,
                source_tier=document.meta.source_tier,
                jurisdiction=document.meta.jurisdiction,
                original_source_urls=document.meta.original_source_urls,
                cited_source_ids=cited,
            )
        )

    chunk_ids = [chunk.chunk_id for chunk in chunks]
    if len(chunk_ids) != len(set(chunk_ids)):
        raise RagError(
            "DUPLICATE_ID",
            f"'{document.file_path}' has two sections that slugify to the same chunk_id.",
        )
    return tuple(chunks)


def chunk_documents(documents: tuple[KnowledgeDocument, ...]) -> tuple[Chunk, ...]:
    """Chunk every document, in document order, and enforce global chunk-id uniqueness."""

    all_chunks: list[Chunk] = []
    for document in documents:
        all_chunks.extend(chunk_document(document))

    chunk_ids = [chunk.chunk_id for chunk in all_chunks]
    if len(chunk_ids) != len(set(chunk_ids)):
        raise RagError("DUPLICATE_ID", "Duplicate chunk_id across the knowledge base.")
    return tuple(all_chunks)
