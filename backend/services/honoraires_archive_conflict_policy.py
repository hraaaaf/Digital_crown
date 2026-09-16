"""Honoraires archive conflict policy for insurance linkage metadata.

Insurance linkage enriches archived Honoraires payment lines with technical metadata
(`source_line_uid` and nullable `catalog_act_id`). Those fields must not make an otherwise
identical user submission look like a new business document.

The installer augments ArchiveService.check_conflicts only for NOTE_HONORAIRES. The
existing conflict algorithm runs first unchanged; if it finds nothing, a second
business-content comparison ignores `source_line_uid` and treats missing/None
`catalog_act_id` as equivalent. A real non-null catalog id remains significant.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from backend import models
from backend.models import DocumentStatus, DocumentType
from backend.schemas import ConflictResolution


_INSTALLED = False


def _normalize_honoraires_duplicate_payload(value: Any) -> Any:
    if not isinstance(value, dict):
        return value

    normalized = deepcopy(value)
    payments = normalized.get("payments")
    if isinstance(payments, list):
        cleaned_payments = []
        for item in payments:
            if not isinstance(item, dict):
                cleaned_payments.append(item)
                continue
            cleaned = dict(item)
            cleaned.pop("source_line_uid", None)
            if cleaned.get("catalog_act_id") in (None, ""):
                cleaned.pop("catalog_act_id", None)
            cleaned_payments.append(cleaned)
        normalized["payments"] = cleaned_payments
    return normalized


def install_honoraires_archive_conflict_policy() -> None:
    global _INSTALLED
    if _INSTALLED:
        return

    from backend.services.archive_service import ArchiveService

    original_check_conflicts = ArchiveService.check_conflicts
    if getattr(original_check_conflicts, "_honoraires_linkage_policy", False):
        _INSTALLED = True
        return

    def check_conflicts_with_honoraires_policy(
        self,
        patient_id: int,
        file_hash: str,
        filename: str,
        doc_type: DocumentType,
        clinical_data: dict | None = None,
    ) -> dict:
        result = original_check_conflicts(
            self,
            patient_id,
            file_hash,
            filename,
            doc_type,
            clinical_data=clinical_data,
        )
        if result.get("has_conflict"):
            return result
        if doc_type != DocumentType.NOTE_HONORAIRES or not isinstance(clinical_data, dict):
            return result

        incoming_business = _normalize_honoraires_duplicate_payload(clinical_data)
        candidates = self.db.query(models.DocumentArchive).filter(
            models.DocumentArchive.patient_id == patient_id,
            models.DocumentArchive.document_type == doc_type,
            models.DocumentArchive.status == DocumentStatus.ACTIF,
        ).all()
        for document in candidates:
            if _normalize_honoraires_duplicate_payload(document.clinical_data) == incoming_business:
                return {
                    "has_conflict": True,
                    "existing_document": document,
                    "conflict_reason": "duplicate_content",
                    "suggested_action": ConflictResolution.CANCEL,
                    "message": "Une note identique existe déjà pour ce patient (mêmes actes).",
                }
        return result

    check_conflicts_with_honoraires_policy._honoraires_linkage_policy = True
    ArchiveService.check_conflicts = check_conflicts_with_honoraires_policy
    _INSTALLED = True
