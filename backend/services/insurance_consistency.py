"""Canonical Honoraires source loading and insurance draft consistency checks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Sequence

from sqlalchemy.orm import Session

from backend import models
from backend.schemas.insurance_submission import InsuranceOrganization, InsuranceSubmissionDraft


_PATIENT_INSURANCE_ORGANIZATION = {
    "CNSS": InsuranceOrganization.CNSS,
    "CNOPS": InsuranceOrganization.CNOPS,
    "MUTUELLE_FAR": InsuranceOrganization.FAR,
    "FAR": InsuranceOrganization.FAR,
}


@dataclass(frozen=True)
class HonorairesInsuranceSource:
    document: models.DocumentArchive
    patient: models.Patient
    payments: list[dict[str, Any]]
    actes: list[models.Acte]
    acte_ids: list[int]
    practitioner_id: int


def _normalize_teeth(item: dict[str, Any]) -> list[str]:
    raw_dents = item.get("dents") or []
    if raw_dents:
        return [str(value).strip() for value in raw_dents if str(value).strip()]
    raw_dent = str(item.get("dent") or "").strip()
    if not raw_dent or raw_dent == "-":
        return []
    return [value.strip() for value in raw_dent.split(",") if value.strip()]


def _service_date(item: dict[str, Any], document: models.DocumentArchive) -> date:
    raw = item.get("date")
    if raw not in (None, ""):
        if isinstance(raw, datetime):
            return raw.date()
        if isinstance(raw, date):
            return raw
        try:
            return date.fromisoformat(str(raw).split("T")[0])
        except (TypeError, ValueError) as exc:
            raise ValueError("Honoraires source contains an invalid service date") from exc
    if document.created_at is None:
        raise ValueError("Honoraires source line has no deterministic service date")
    return document.created_at.date()


def _amount(value: Any) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("Honoraires source contains an invalid amount") from exc
    if not result.is_finite() or result <= 0:
        raise ValueError("Honoraires source contains an invalid amount")
    return result


def _linked_acte_ids(payments: Sequence[dict], actes: Sequence[models.Acte]) -> list[int]:
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
            linked = [by_uid[uid] for uid in payment_uids]
        except KeyError as exc:
            raise ValueError("Honoraires UID linkage mismatch") from exc
        return [int(acte.id) for acte in linked]

    if any(payment_uids):
        raise ValueError("Mixed historical Honoraires UID linkage is ambiguous")
    return [int(acte.id) for acte in actes]


def load_honoraires_insurance_source(
    db: Session,
    *,
    honoraires_document_id: int,
    organization: InsuranceOrganization,
) -> HonorairesInsuranceSource:
    document = db.query(models.DocumentArchive).filter(
        models.DocumentArchive.id == int(honoraires_document_id),
        models.DocumentArchive.document_type == models.DocumentType.NOTE_HONORAIRES,
    ).first()
    if document is None:
        raise ValueError("Honoraires source document not found")

    patient = db.query(models.Patient).filter(models.Patient.id == document.patient_id).first()
    if patient is None:
        raise ValueError("Honoraires patient not found")
    raw_insurer = str(getattr(patient, "assurance", None) or "").strip().upper()
    if _PATIENT_INSURANCE_ORGANIZATION.get(raw_insurer) != organization:
        raise ValueError("Requested insurer does not match the patient insurance record")

    clinical_data = document.clinical_data or {}
    payments = clinical_data.get("payments") if isinstance(clinical_data, dict) else None
    if not isinstance(payments, list) or not payments:
        raise ValueError("Honoraires source has no canonical payment lines")
    if not all(isinstance(item, dict) for item in payments):
        raise ValueError("Honoraires payment snapshot is invalid")

    actes = (
        db.query(models.Acte)
        .filter(
            models.Acte.document_archive_id == document.id,
            models.Acte.deleted_at.is_(None),
        )
        .order_by(models.Acte.id.asc())
        .all()
    )
    acte_ids = _linked_acte_ids(payments, actes)
    by_id = {int(acte.id): acte for acte in actes}

    practitioner_ids = {int(acte.praticien_id) for acte in actes if acte.praticien_id is not None}
    if len(practitioner_ids) != 1:
        raise ValueError("Insurance submission requires one unambiguous practitioner")
    practitioner_id = next(iter(practitioner_ids))

    for index, (payment, acte_id) in enumerate(zip(payments, acte_ids)):
        acte = by_id[acte_id]
        payment_uid = str(payment.get("source_line_uid") or "").strip() or None
        acte_uid = str(getattr(acte, "source_line_uid", None) or "").strip() or None
        if payment_uid and payment_uid != acte_uid:
            raise ValueError(f"Honoraires source line #{index} UID mismatch")
        raw_catalog = payment.get("catalog_act_id")
        payment_catalog = int(raw_catalog) if raw_catalog not in (None, "") else None
        acte_catalog = getattr(acte, "catalog_act_id", None)
        if payment_catalog is not None and payment_catalog != acte_catalog:
            raise ValueError(f"Honoraires source line #{index} catalog link mismatch")

    return HonorairesInsuranceSource(
        document=document,
        patient=patient,
        payments=list(payments),
        actes=list(actes),
        acte_ids=acte_ids,
        practitioner_id=practitioner_id,
    )


def assert_draft_matches_honoraires_source(
    db: Session,
    *,
    draft: InsuranceSubmissionDraft,
) -> HonorairesInsuranceSource:
    """Reconcile every immutable clinical/financial draft field with server source."""
    source = load_honoraires_insurance_source(
        db,
        honoraires_document_id=draft.honoraires_document_id,
        organization=draft.organization,
    )
    if int(draft.patient_id) != int(source.patient.id):
        raise ValueError("Insurance draft patient mismatch")
    if len(draft.lines) != len(source.payments):
        raise ValueError("Insurance draft line count mismatch")

    for index, (line, payment, acte_id) in enumerate(
        zip(draft.lines, source.payments, source.acte_ids)
    ):
        expected_uid = str(payment.get("source_line_uid") or "").strip() or None
        raw_catalog = payment.get("catalog_act_id")
        expected_catalog = int(raw_catalog) if raw_catalog not in (None, "") else None
        expected_label = str(payment.get("acte") or "").strip()
        if not expected_label:
            raise ValueError("Honoraires source contains an empty act label")

        checks = (
            (line.source.honoraires_document_id == source.document.id, "document"),
            (line.source.honoraires_line_index == index, "line index"),
            (line.source.acte_id == acte_id, "Acte"),
            (line.source.source_line_uid == expected_uid, "UID"),
            (line.source.catalog_act_id == expected_catalog, "catalog link"),
            (line.service_date == _service_date(payment, source.document), "service date"),
            (line.label.strip() == expected_label, "label"),
            (line.teeth == _normalize_teeth(payment), "teeth"),
            (Decimal(str(line.amount_mad)) == _amount(payment.get("montant")), "amount"),
        )
        for ok, field in checks:
            if not ok:
                raise ValueError(f"Insurance draft line #{index} {field} mismatch")
    return source
