"""Load and validate the curated markdown knowledge base for a case.

Parses the YAML-style frontmatter each ``knowledge_base/<case>/*.md`` file
starts with (a flat set of ``key: value`` pairs plus one list-valued key,
``original_source_urls``) without adding a new third-party dependency, since
the frontmatter format is small and entirely self-authored.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field

from ..contracts import MVP_CASE_ID, NonEmptyText, SourceTier, StableId
from . import RagError

__all__ = [
    "KnowledgeDocumentMeta",
    "KnowledgeDocument",
    "DEFAULT_KNOWLEDGE_ROOT",
    "CASE_ID_TO_FOLDER",
    "load_knowledge_documents",
]

CASE_ID_TO_FOLDER: dict[str, str] = {MVP_CASE_ID: "case_001"}
DEFAULT_KNOWLEDGE_ROOT = Path(__file__).resolve().parents[3] / "knowledge_base"

_CITATION_PATTERN = re.compile(r"\[(SRC_[A-Za-z0-9_]+)\]")
_FRONTMATTER_DELIM = "---"


class KnowledgeDocumentMeta(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    document_id: StableId
    title: NonEmptyText
    case_id: Literal[MVP_CASE_ID] = MVP_CASE_ID
    source_type: NonEmptyText
    source_tier: SourceTier
    jurisdiction: NonEmptyText
    case_status: NonEmptyText
    version: NonEmptyText
    effective_or_published_date: date
    last_reviewed: date
    original_source_urls: tuple[AnyHttpUrl, ...] = Field(min_length=1)
    classification: NonEmptyText


class KnowledgeDocument(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    meta: KnowledgeDocumentMeta
    file_path: NonEmptyText
    body: str
    cited_source_ids: tuple[StableId, ...]


def _parse_frontmatter(text: str, filename: str) -> tuple[dict[str, object], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != _FRONTMATTER_DELIM:
        raise RagError("MISSING_FRONTMATTER", f"'{filename}' does not start with a frontmatter block.")
    try:
        end_index = next(
            index for index in range(1, len(lines)) if lines[index].strip() == _FRONTMATTER_DELIM
        )
    except StopIteration as exc:
        raise RagError(
            "MALFORMED_FRONTMATTER", f"'{filename}' has an unterminated frontmatter block."
        ) from exc

    meta: dict[str, object] = {}
    current_list_key: str | None = None
    for raw_line in lines[1:end_index]:
        if not raw_line.strip():
            continue
        if raw_line.startswith("  - "):
            if current_list_key is None:
                raise RagError(
                    "MALFORMED_FRONTMATTER",
                    f"'{filename}' has a list item outside of any list key.",
                )
            meta.setdefault(current_list_key, [])
            meta[current_list_key].append(raw_line[4:].strip())
            continue
        if ":" not in raw_line:
            raise RagError(
                "MALFORMED_FRONTMATTER", f"'{filename}' has an unparseable frontmatter line."
            )
        key, _, value = raw_line.partition(":")
        key = key.strip()
        value = value.strip()
        if value == "":
            current_list_key = key
            meta[key] = []
        else:
            current_list_key = None
            meta[key] = value

    body = "\n".join(lines[end_index + 1 :]).strip("\n")
    return meta, body


def _load_one(path: Path, *, root_parent: Path) -> KnowledgeDocument:
    text = path.read_text(encoding="utf-8")
    raw_meta, body = _parse_frontmatter(text, path.name)
    try:
        meta = KnowledgeDocumentMeta.model_validate(raw_meta)
    except Exception as exc:  # noqa: BLE001 - normalized below
        raise RagError(
            "SCHEMA_VALIDATION_FAILED", f"'{path.name}' frontmatter failed validation: {exc}"
        ) from exc
    if not body.strip():
        raise RagError("EMPTY_DOCUMENT_BODY", f"'{path.name}' has no content after its frontmatter.")
    cited = tuple(sorted(set(_CITATION_PATTERN.findall(body))))
    if not cited:
        raise RagError(
            "NO_CITATIONS_FOUND", f"'{path.name}' cites no [SRC_...] source IDs in its body."
        )
    return KnowledgeDocument(
        meta=meta,
        file_path=str(path.relative_to(root_parent)),
        body=body,
        cited_source_ids=cited,
    )


def load_knowledge_documents(
    case_id: str,
    *,
    known_source_ids: frozenset[str] | None = None,
    knowledge_root: Path | None = None,
) -> tuple[KnowledgeDocument, ...]:
    """Load every markdown document for an allowlisted case, deterministically ordered.

    ``known_source_ids``, when given, cross-checks every cited ``[SRC_...]`` id
    against the case's source manifest so an undocumented citation fails loudly
    instead of silently entering the retrieval corpus.
    """

    if case_id not in CASE_ID_TO_FOLDER:
        raise RagError("UNSUPPORTED_CASE", f"Case '{case_id}' is not part of the curated case library.")
    root = knowledge_root if knowledge_root is not None else DEFAULT_KNOWLEDGE_ROOT
    case_dir = root / CASE_ID_TO_FOLDER[case_id]
    if not case_dir.is_dir():
        raise RagError("MISSING_KNOWLEDGE_DIRECTORY", "The knowledge base directory was not found.")

    paths = sorted(case_dir.glob("*.md"))
    if not paths:
        raise RagError("NO_DOCUMENTS_FOUND", "No knowledge base documents were found for this case.")

    documents = tuple(_load_one(path, root_parent=root.parent) for path in paths)

    document_ids = [doc.meta.document_id for doc in documents]
    if len(document_ids) != len(set(document_ids)):
        raise RagError("DUPLICATE_ID", "Duplicate document_id found in the knowledge base.")

    if known_source_ids is not None:
        for doc in documents:
            missing = set(doc.cited_source_ids) - known_source_ids
            if missing:
                raise RagError(
                    "DANGLING_SOURCE_ID",
                    f"'{doc.file_path}' cites unknown source id '{sorted(missing)[0]}'.",
                )

    return tuple(sorted(documents, key=lambda doc: doc.meta.document_id))
