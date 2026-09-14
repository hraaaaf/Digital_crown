from __future__ import annotations

from typing import Any, Dict, List

from backend.schemas.insurance_submission import InsuranceSubmissionDraft


INSURANCE_ARCHIVE_KIND = "INSURANCE_SUBMISSION"
INSURANCE_ARCHIVE_SCHEMA_VERSION = "1"


def build_insurance_archive_clinical_data(draft: InsuranceSubmissionDraft) -> Dict[str, Any]:
    """Build the immutable clinical_data snapshot stored beside the final PDF.

    This helper deliberately has no DB side effects. The actual archive write stays
    inside ArchiveService so the insurance flow reuses the canonical document store.
    """
    return {
        "kind": INSURANCE_ARCHIVE_KIND,
        "schema_version": INSURANCE_ARCHIVE_SCHEMA_VERSION,
        "organization": draft.organization.value,
        "patient_id": draft.patient_id,
        "source_honoraires_document_id": draft.honoraires_document_id,
        "source_ordonnance_document_id": draft.source_ordonnance_document_id,
        "template_version": draft.template.template_version,
        "template_hash": draft.template.template_hash,
        "template_source_url": draft.template.source_url,
        "ngap_reference_version": draft.reference.ngap_reference_version,
        "ngap_reference_hash": draft.reference.ngap_reference_hash,
        "validated_by_practitioner_id": draft.validated_by_practitioner_id,
        "validated_at": draft.validated_at.isoformat() if draft.validated_at else None,
        "draft": draft.model_dump(mode="json"),
    }


def build_insurance_archive_tags(draft: InsuranceSubmissionDraft) -> List[str]:
    """Return stable tags for browsing insurance submissions in DocumentArchive."""
    return [
        "insurance_submission",
        draft.organization.value.lower(),
        f"template:{draft.template.template_version}",
    ]
