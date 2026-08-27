"""Three deterministic local tools beyond RAG: timeline, claim support, counterfactual.

Every tool here is pure, offline, allowlisted-case-only, and has no network,
shell, arbitrary filesystem, or model access. Deterministic core logic is
kept separate from any LLM adapter — a specialist (B4) calls these functions
directly and only asks the model boundary to interpret/explain the result.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable

__all__ = [
    "ToolError",
    "ToolAuditRecord",
    "ToolSpec",
    "TOOL_REGISTRY",
    "register_tool",
    "timed_call",
]


class ToolError(Exception):
    """Structured, user-safe error raised anywhere in the tools boundary."""

    def __init__(self, code: str, user_message: str, *, recoverable: bool = False) -> None:
        self.code = code
        self.user_message = user_message
        self.recoverable = recoverable
        super().__init__(f"[{code}] {user_message}")

    def to_safe_error_fields(self) -> dict[str, object]:
        return {
            "error_id": f"error.tools.{self.code.lower()}",
            "code": self.code,
            "user_message": self.user_message,
            "recoverable": self.recoverable,
            "retry_allowed": False,
        }


@dataclass(frozen=True)
class ToolAuditRecord:
    """Safe, non-sensitive audit metadata about one tool call."""

    tool_name: str
    validated_parameter_summary: str
    status: str
    duration_ms: float
    result_count: int


@dataclass(frozen=True)
class ToolSpec:
    """Machine-readable registry entry Track A can inspect without importing internals."""

    name: str
    description: str
    permission_category: str
    input_schema: dict[str, object]
    result_schema: dict[str, object]


TOOL_REGISTRY: dict[str, ToolSpec] = {}


def register_tool(spec: ToolSpec) -> None:
    TOOL_REGISTRY[spec.name] = spec


def timed_call(tool_name: str, fn: Callable[[], object], *, parameter_summary: str) -> tuple[object, ToolAuditRecord]:
    """Run ``fn``, returning its result alongside a safe audit record.

    On failure the audit record's status is ``"error"`` and the original
    ``ToolError`` propagates after being recorded's duration is captured.
    """

    start = time.monotonic()
    try:
        result = fn()
    except ToolError as exc:
        duration_ms = (time.monotonic() - start) * 1000
        exc.audit_record = ToolAuditRecord(  # type: ignore[attr-defined]
            tool_name=tool_name,
            validated_parameter_summary=parameter_summary,
            status="error",
            duration_ms=duration_ms,
            result_count=0,
        )
        raise
    duration_ms = (time.monotonic() - start) * 1000
    result_count = len(result) if isinstance(result, (list, tuple)) else 1
    record = ToolAuditRecord(
        tool_name=tool_name,
        validated_parameter_summary=parameter_summary,
        status="ok",
        duration_ms=duration_ms,
        result_count=result_count,
    )
    return result, record
