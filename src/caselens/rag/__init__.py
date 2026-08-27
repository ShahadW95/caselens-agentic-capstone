"""Agentic RAG preparation and retrieval over the curated knowledge base."""

from __future__ import annotations


class RagError(Exception):
    """Structured, user-safe error raised anywhere in the RAG boundary."""

    def __init__(self, code: str, user_message: str, *, recoverable: bool = False) -> None:
        self.code = code
        self.user_message = user_message
        self.recoverable = recoverable
        super().__init__(f"[{code}] {user_message}")

    def to_safe_error_fields(self) -> dict[str, object]:
        return {
            "error_id": f"error.rag.{self.code.lower()}",
            "code": self.code,
            "user_message": self.user_message,
            "recoverable": self.recoverable,
            "retry_allowed": False,
        }


__all__ = ["RagError"]
