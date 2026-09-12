"""Request-scoped document author provenance for P3 multi-practitioner flows."""

from __future__ import annotations

from contextvars import ContextVar, Token
from typing import Optional


_document_author_practitioner_id: ContextVar[Optional[int]] = ContextVar(
    "document_author_practitioner_id",
    default=None,
)


def set_document_author_practitioner_id(practitioner_id: int) -> Token:
    """Bind the validated clinical author to the current request context."""
    return _document_author_practitioner_id.set(int(practitioner_id))


def reset_document_author_practitioner_id(token: Token) -> None:
    """Restore the previous request context after document generation."""
    _document_author_practitioner_id.reset(token)


def get_document_author_practitioner_id() -> Optional[int]:
    """Return the validated clinical author for this request, when one is bound."""
    return _document_author_practitioner_id.get()


def effective_document_practitioner_id(default_practitioner_id: Optional[int]) -> Optional[int]:
    """Use the request-scoped clinical author without changing the technical actor."""
    author_id = get_document_author_practitioner_id()
    return author_id if author_id is not None else default_practitioner_id
