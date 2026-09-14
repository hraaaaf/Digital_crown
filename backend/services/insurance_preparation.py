"""Prepare an insurance submission draft from one archived Honoraires document.

This service is intentionally renderer-agnostic. It links canonical Honoraires lines to
active Acte rows, preserves historical fallback rules, prefills only explicit admin data
and optionally evaluates the versioned NGAP mapping. Nothing is signed or generated.
"""

from __future__ import annotations

from datetime import date
from typing import Sequence

from sqlalchemy.orm import Session

from backend import models
from backend.schemas.insurance_submission import (
    InsuranceOrganization,
    InsuranceSubmissionDraft,
)
from backend.services.insurance_administrative import prefill_cnss_administrative
from backend.services.insurance_submission import (
    apply_ngap_reference_to_draft,
    build_draft_from_honoraires_snapshot,
)
from backend.services.insurance_template_registry import (
    CNOPS_DENTAL_PENDING,
    CNSS_610_1_04,
    FAR_2021_1,
    InsuranceTemplateDefinition,
    LockedInsuranceTemplate,
)


_TEMPLATE_BY_ORGANIZATION = {
    InsuranceOrganization.CNSS: CNSS_610_1_04,
    InsuranceOrganization.CNOPS: CNOPS_DENTAL_PENDING,
    InsuranceOrganization.FAR: FAR_2021_1,
}


def _active_actes(db: Session, document_archive_id: int) -> list[models.Acte]:
    return (
        db.query(models.Acte)
        .filter(
            models.Acte.document_archive_id == int(document_archive_id),
            models.Acte.deleted_at.is_(None),
        )
        .order_by(models.Acte.id.asc())
        .all()
    )


def _linked_acte_ids(
    payments: Sequence[dict],
    actes: Sequence[models.Acte],
) -> list[int]:
    """Link snapshot lines to Actes; explicit UID wins, index is legacy-only fallback."""
    if not payments or not actes or len(payments) != len(actes):
        raise ValueError("Historical Honoraires/Acte line count mismatch")
    if any(acte.id is None for acte in actes):
        raise ValueError("Honoraires contains an unpersisted Acte")

    payment_uids = [str(item.get("source_line_uid") or "").strip() or None for item in payments]
    acte_uids = [str(getattr(acte, "source_line_uid", None) or "").strip() or None for acte in actes]

    if all(payment_uids):
        if len(set(payment_uids)) != len(payment_uids):
            raise ValueError("Duplicate Honoraires source_line_uid")
        by_uid: dict[str, models.Acte] = {}
        for acte, uid in zip(actes, acte_uids):
            if not uid:
                raise ValueError("Honoraires UID linkage is incomplete")
            if uid in by_uid:
                raise ValueError("Duplicate Acte source_line_uid")
            by_uid[uid] = acte
        try:
            return [int(by_uid[uid].id) for uid in payment_uids]
        except KeyError as exc:
            raise ValueError("Honoraires UID linkage mismatch") from exc

    if any(payment_uids):
        raise ValueError("Mixed historical Honoraires UID linkage is ambiguous")

    # Historical compatibility: exact active line count + stable Acte.id order only.
    return [int(acte.id) for acte in actes]


def _single_practitioner_id(actes: Sequence[models.Acte]) -> int:
    practitioner_ids = {int(acte.praticien_id) for acte in actes if acte.praticien_id is not None}
    if len(practitioner_ids) != 1:
        raise ValueError("Insurance submission requires one unambiguous practitioner")
    return next(iter(practitioner_ids))


def _template_definition(organization: InsuranceOrganization) -> InsuranceTemplateDefinition:
    try:
        return _TEMPLATE_BY_ORGANIZATION[organization]
    except KeyError as exc:
        raise ValueError("Unsupported insurance organization") from exc


def prepare_insurance_draft_from_honoraires(
    db: Session,
    *,
    honoraires_document_id: int,
    organization: InsuranceOrganization,
    locked_template: LockedInsuranceTemplate | None = None,
    ngap_reference_version: str | None = None,
    on_date: date | None = None,
) -> InsuranceSubmissionDraft:
    """Build a traceable, non-final insurance draft from one archived Honoraires note."""
    document = db.query(models.DocumentArchive).filter(
        models.DocumentArchive.id == int(honoraires_document_id),
        models.DocumentArchive.document_type == models.DocumentType.NOTE_HONORAIRES,
    ).first()
    if document is None:
        raise ValueError("Honoraires source document not found")

    patient = db.query(models.Patient).filter(models.Patient.id == document.patient_id).first()
    if patient is None:
        raise ValueError("Honoraires patient not found")

    clinical_data = document.clinical_data or {}
    payments = clinical_data.get("payments") if isinstance(clinical_data, dict) else None
    if not isinstance(payments, list) or not payments:
        raise ValueError("Honoraires source has no canonical payment lines")
    if not all(isinstance(item, dict) for item in payments):
        raise ValueError("Honoraires payment snapshot is invalid")

    actes = _active_actes(db, document.id)
    acte_ids = _linked_acte_ids(payments, actes)
    practitioner_id = _single_practitioner_id(actes)
    practitioner = db.query(models.User).filter(
        models.User.id == practitioner_id,
        models.User.is_active.is_(True),
    ).first()
    if practitioner is None:
        raise ValueError("Honoraires practitioner is unavailable")

    definition = _template_definition(organization)
    if locked_template is not None:
        if locked_template.definition.organization != organization:
            raise ValueError("Locked template organization mismatch")
        if locked_template.definition.version != definition.version:
            raise ValueError("Locked template version mismatch")
        template_hash = locked_template.sha256
        template_source_url = locked_template.source_url
        template_trust = locked_template.definition.trust
    else:
        template_hash = None
        template_source_url = None
        template_trust = definition.trust

    draft = build_draft_from_honoraires_snapshot(
        patient_id=patient.id,
        organization=organization,
        honoraires_document_id=document.id,
        payments=payments,
        template_version=definition.version,
        template_hash=template_hash,
        template_source_url=template_source_url,
        template_trust=template_trust,
        active_acte_ids=acte_ids,
        fallback_date=(document.created_at.date() if document.created_at else on_date),
    )

    if organization == InsuranceOrganization.CNSS:
        draft = prefill_cnss_administrative(
            db,
            draft=draft,
            patient=patient,
            practitioner=practitioner,
        )

    if ngap_reference_version:
        draft = apply_ngap_reference_to_draft(
            db,
            draft=draft,
            reference_version=ngap_reference_version,
            on_date=on_date,
        )
    return draft
