"""Three real specialists behind the frozen v1 protocols.

Shared helpers only: building ``SourceCitation`` objects (from either a
source-manifest entry or a retrieved RAG chunk — neither the tools nor the
RAG layer hand back a ready-made citation, since ``RetrievedChunk`` has no
``source_id`` field and a tool result only carries bare ``source_ids``), and
a bounded one-repair pattern for the shared model boundary. No specialist
constructs a model/provider client itself; ``model`` is always injected.
"""

from __future__ import annotations

import re
from typing import Callable

from ..contracts import ConfidenceLabel, ModelRequest, SourceCitation
from ..protocols import ModelBoundaryProtocol
from ..services.case_loader import SourceManifestEntry

__all__ = [
    "SpecialistError",
    "extract_source_ids_from_text",
    "citation_from_manifest_source",
    "citation_from_chunk",
    "ModelSummary",
    "generate_with_one_repair",
    "combine_confidence",
]

_CONFIDENCE_ORDER = {ConfidenceLabel.LOW: 0, ConfidenceLabel.MEDIUM: 1, ConfidenceLabel.HIGH: 2}


def combine_confidence(*labels: ConfidenceLabel) -> ConfidenceLabel:
    """Conservatively combine independent confidence signals: the weakest wins."""

    return min(labels, key=lambda label: _CONFIDENCE_ORDER[label])

_CITATION_PATTERN = re.compile(r"\[(SRC_[A-Za-z0-9_]+)\]")


class SpecialistError(Exception):
    """Structured, user-safe error raised anywhere in the specialist boundary."""

    def __init__(self, code: str, user_message: str, *, recoverable: bool = False) -> None:
        self.code = code
        self.user_message = user_message
        self.recoverable = recoverable
        super().__init__(f"[{code}] {user_message}")

    def to_safe_error_fields(self) -> dict[str, object]:
        return {
            "error_id": f"error.specialists.{self.code.lower()}",
            "code": self.code,
            "user_message": self.user_message,
            "recoverable": self.recoverable,
            "retry_allowed": False,
        }


def extract_source_ids_from_text(text: str) -> tuple[str, ...]:
    return tuple(sorted(set(_CITATION_PATTERN.findall(text))))


def citation_from_manifest_source(source_id: str, manifest_by_id: dict[str, SourceManifestEntry]) -> SourceCitation:
    entry = manifest_by_id.get(source_id)
    if entry is None:
        raise SpecialistError("UNKNOWN_SOURCE_ID", f"'{source_id}' is not a known source in this case pack.")
    return SourceCitation(
        citation_id=f"cit.manifest.{source_id}",
        source_id=source_id,
        document_id=f"doc.manifest.{source_id}",
        chunk_id=f"chunk.manifest.{source_id}",
        title=entry.title,
        heading="Source manifest entry",
        source_type=entry.source_type,
        source_tier=entry.source_tier,
        original_url=entry.url,
    )


def citation_from_chunk(chunk, source_id: str, manifest_by_id: dict[str, SourceManifestEntry]) -> SourceCitation:
    """Build one citation for one (chunk, source_id) pair.

    A chunk may cite more than one source, so a specialist builds one
    ``SourceCitation`` per source_id actually cited inside that chunk's text.
    """

    entry = manifest_by_id.get(source_id)
    if entry is None:
        raise SpecialistError("UNKNOWN_SOURCE_ID", f"'{source_id}' is not a known source in this case pack.")
    return SourceCitation(
        citation_id=f"cit.{chunk.chunk_id}.{source_id}",
        source_id=source_id,
        document_id=chunk.document_id,
        chunk_id=chunk.chunk_id,
        title=entry.title,
        heading=chunk.heading,
        source_type=chunk.source_type,
        source_tier=chunk.source_tier,
        original_url=entry.url,
    )


class ModelSummary:
    """Result of a bounded, at-most-one-repair call to the model boundary."""

    __slots__ = ("text", "confidence")

    def __init__(self, text: str, confidence: ConfidenceLabel) -> None:
        self.text = text
        self.confidence = confidence


def generate_with_one_repair(
    model: ModelBoundaryProtocol,
    base_request: ModelRequest,
    parse: Callable[[str], str],
    *,
    fallback: str,
) -> ModelSummary:
    """Call the model, validate its response, and retry exactly once on failure.

    On a second failure (malformed output or a raised exception, from either
    attempt) this never raises: it returns ``fallback`` at LOW confidence, so
    a specialist can always produce a contract-valid finding even when
    interpretation is unavailable. The deterministic facts a finding carries
    never depend on this succeeding.
    """

    try:
        response = model.generate(base_request)
        return ModelSummary(parse(response.text), ConfidenceLabel.HIGH)
    except Exception:  # noqa: BLE001 - any failure triggers exactly one repair
        pass

    repaired_request = base_request.model_copy(
        update={
            "request_id": f"{base_request.request_id}.repair",
            "operation": (
                f"{base_request.operation} Your previous response was invalid or unusable; "
                "respond again, exactly in the required format."
            ),
        }
    )
    try:
        response = model.generate(repaired_request)
        return ModelSummary(parse(response.text), ConfidenceLabel.MEDIUM)
    except Exception:  # noqa: BLE001 - repair also failed; degrade, never raise
        return ModelSummary(fallback, ConfidenceLabel.LOW)
