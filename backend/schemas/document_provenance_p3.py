"""P3 response contracts exposing additive document provenance."""

from __future__ import annotations

import datetime
from typing import List, Optional

from backend import schemas as schema_package
from backend.schemas.documents import (
    DocumentArchiveOut as LegacyDocumentArchiveOut,
    DocumentArchiveResponse as LegacyDocumentArchiveResponse,
    DocumentConflictCheck as LegacyDocumentConflictCheck,
    DocumentListResponse as LegacyDocumentListResponse,
)


class DocumentArchiveOutP3(LegacyDocumentArchiveOut):
    uploaded_by_id: Optional[int] = None
    author_practitioner_id: Optional[int] = None
    signed_by_practitioner_id: Optional[int] = None
    signed_at: Optional[datetime.datetime] = None


class DocumentConflictCheckP3(LegacyDocumentConflictCheck):
    existing_document: Optional[DocumentArchiveOutP3] = None


class DocumentArchiveResponseP3(LegacyDocumentArchiveResponse):
    document: Optional[DocumentArchiveOutP3] = None
    conflict_info: Optional[DocumentConflictCheckP3] = None


class DocumentListResponseP3(LegacyDocumentListResponse):
    documents: List[DocumentArchiveOutP3]


def install_document_provenance_schema_contracts() -> None:
    """Override package-level aliases before the documents router declares responses."""
    schema_package.DocumentArchiveOut = DocumentArchiveOutP3
    schema_package.DocumentConflictCheck = DocumentConflictCheckP3
    schema_package.DocumentArchiveResponse = DocumentArchiveResponseP3
    schema_package.DocumentListResponse = DocumentListResponseP3
