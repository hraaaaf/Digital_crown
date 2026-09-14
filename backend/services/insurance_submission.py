from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, Iterable, List, Optional, Sequence

from sqlalchemy.orm import Session

from backend import models
from backend.schemas.insurance_submission import (
    InsuranceDraftStatus,
    InsuranceLineSource,
    InsuranceMappingStatus,
    InsuranceOrganization,
    InsuranceSubmissionDraft,
    InsuranceSubmissionLine,
    InsuranceTemplateSnapshot,
)
from backend.services.archive_service import ArchiveService


INSURANCE_ARCHIVE_KIND = "INSURANCE_SUBMISSION"
INSURANCE_ARCHIVE_SCHEMA_VERSION = "1"


def _normalize_teeth(item: Dict[str, Any]) -> List[str]:
    raw_dents = item.get("dents") or []
    if raw_dents:
        return [str(value).strip() for value in raw_dents if str(value).strip()]

    raw_dent = str(item.get("dent") or "").strip()
    if not raw_dent or raw_dent == "-":
        return []
    return [value.strip() for value in raw_dent.split(",") if value.strip()]


def _service_date(item: Dict[str, Any], fallback: date) -> date:
    raw = item.get("date")
    if raw in (None, ""):
        return fallback
    if isinstance(raw, datetime):
        return raw.date()
    if isinstance(raw, date):
        return raw
    return date.fromisoformat(str(raw).split("T")[0])


def build_draft_from_honoraires_snapshot(
    *,
    patient_id: int,
    organization: InsuranceOrganization,
    honoraires_document_id: int,
    payments: Iterable[Dict[str, Any]],
    template_version: str,
    template_hash: Optional[str] = None,
    template_source_url: Optional[str] = None,
    active_acte_ids: Optional[Sequence[int]] = None,
    fallback_date: Optional[date] = None,
    unresolved_fields: Optional[List[str]] = None,
) -> InsuranceSubmissionDraft:
    """Create an initial fail-closed draft from the archived Honoraires snapshot.

    Teeth always come from the snapshot. `active_acte_ids`, when supplied for an
    historical document, must align 1:1 with the active Honoraires lines; otherwise
    linkage is ambiguous and the adapter refuses to guess.
    """
    item_list = list(payments)
    if not item_list:
        raise ValueError("Honoraires snapshot has no payment lines")

    if active_acte_ids is not None and len(active_acte_ids) != len(item_list):
        raise ValueError("Historical Honoraires/Acte line count mismatch")

    fallback = fallback_date or date.today()
    lines: List[InsuranceSubmissionLine] = []

    for index, item in enumerate(item_list):
        label = str(item.get("acte") or "").strip()
        if not label:
            raise ValueError(f"Honoraires line #{index} has no label")
        try:
            amount = float(item.get("montant"))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Honoraires line #{index} has invalid amount") from exc

        lines.append(
            InsuranceSubmissionLine(
                source=InsuranceLineSource(
                    honoraires_document_id=honoraires_document_id,
                    honoraires_line_index=index,
                    acte_id=(active_acte_ids[index] if active_acte_ids is not None else None),
                    source_line_uid=(str(item.get("source_line_uid")).strip() if item.get("source_line_uid") else None),
                    catalog_act_id=item.get("catalog_act_id"),
                ),
                service_date=_service_date(item, fallback),
                label=label,
                teeth=_normalize_teeth(item),
                amount_mad=amount,
                mapping_status=InsuranceMappingStatus.NOT_EVALUATED,
            )
        )

    return InsuranceSubmissionDraft(
        patient_id=patient_id,
        organization=organization,
        honoraires_document_id=honoraires_document_id,
        lines=lines,
        unresolved_fields=list(unresolved_fields or []),
        status=InsuranceDraftStatus.INCOMPLETE,
        template=InsuranceTemplateSnapshot(
            template_version=template_version,
            template_hash=template_hash,
            source_url=template_source_url,
        ),
    )


def build_insurance_archive_clinical_data(draft: InsuranceSubmissionDraft) -> Dict[str, Any]:
    """Build the immutable clinical_data snapshot stored beside the final PDF."""
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


def archive_validated_insurance_pdf(
    db: Session,
    *,
    draft: InsuranceSubmissionDraft,
    pdf_content: bytes,
    filename: str,
    uploaded_by_id: Optional[int] = None,
):
    """Archive a practitioner-validated insurance PDF in canonical DocumentArchive.

    P0 intentionally uses DocumentType.AUTRE to avoid an enum/database migration.
    The semantic type remains explicit in tags and `clinical_data.kind`.
    """
    if draft.status != InsuranceDraftStatus.VALIDATED:
        raise ValueError("Only a VALIDATED insurance draft can be archived")
    if not pdf_content or not pdf_content.startswith(b"%PDF"):
        raise ValueError("Insurance archive requires PDF content")

    service = ArchiveService(db)
    return service.archive_document(
        patient_id=draft.patient_id,
        file_content=pdf_content,
        filename=filename,
        doc_type=models.DocumentType.AUTRE,
        uploaded_by_id=uploaded_by_id,
        title=f"Feuille de soins {draft.organization.value}",
        description=f"Feuille de soins {draft.organization.value} validee par le praticien",
        tags=build_insurance_archive_tags(draft),
        clinical_data=build_insurance_archive_clinical_data(draft),
        is_accounted=False,
        is_collected=False,
        payment_status=models.PaiementStatut.EN_ATTENTE,
    )
