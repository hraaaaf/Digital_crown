from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend import models
from backend.models_patient_companion import PatientCompanionAccess, PatientCompanionShareGrant
from backend.services.accounting_service import accounting_service
from backend.utils.accounting_utils import extract_amount_from_clinical_data


def _enum_value(value: Any) -> Any:
    return getattr(value, "value", value)


def _document_business_date(doc: models.DocumentArchive) -> datetime | None:
    data = doc.clinical_data if isinstance(doc.clinical_data, dict) else {}
    raw = data.get("doc_date") or data.get("date")
    if isinstance(raw, str) and raw.strip():
        try:
            return datetime.fromisoformat(raw.strip().replace("Z", "+00:00"))
        except ValueError:
            try:
                return datetime.strptime(raw.strip()[:10], "%Y-%m-%d")
            except ValueError:
                pass
    return doc.created_at


def _patient_exists_in_tenant(db: Session, access: PatientCompanionAccess) -> bool:
    return db.query(models.Patient.id).filter(
        models.Patient.id == access.patient_id,
        models.Patient.employer_id == access.employer_id,
        models.Patient.deleted_at.is_(None),
    ).first() is not None


def _active_actes(db: Session, access: PatientCompanionAccess) -> list[models.Acte]:
    return (
        db.query(models.Acte)
        .join(models.Patient, models.Acte.patient_id == models.Patient.id)
        .filter(
            models.Acte.patient_id == access.patient_id,
            models.Patient.employer_id == access.employer_id,
            models.Patient.deleted_at.is_(None),
            models.Acte.deleted_at.is_(None),
            models.Acte.is_accounted.is_(True),
        )
        .order_by(models.Acte.date_debut.desc())
        .all()
    )


def _visible_payments(db: Session, access: PatientCompanionAccess) -> list[models.Payment]:
    return (
        db.query(models.Payment)
        .join(models.Patient, models.Payment.patient_id == models.Patient.id)
        .outerjoin(models.Acte, models.Payment.acte_id == models.Acte.id)
        .filter(
            models.Payment.patient_id == access.patient_id,
            models.Patient.employer_id == access.employer_id,
            models.Patient.deleted_at.is_(None),
            accounting_service._visible_payment_filter(),
        )
        .order_by(models.Payment.payment_date.desc(), models.Payment.id.desc())
        .all()
    )


def _standalone_invoice_docs(
    db: Session,
    access: PatientCompanionAccess,
) -> list[models.DocumentArchive]:
    linked_doc_ids = {
        row[0]
        for row in db.query(models.Acte.document_archive_id)
        .filter(
            models.Acte.patient_id == access.patient_id,
            models.Acte.document_archive_id.isnot(None),
        )
        .distinct()
        .all()
    }
    docs = (
        db.query(models.DocumentArchive)
        .join(models.Patient, models.DocumentArchive.patient_id == models.Patient.id)
        .filter(
            models.DocumentArchive.patient_id == access.patient_id,
            models.Patient.employer_id == access.employer_id,
            models.Patient.deleted_at.is_(None),
            models.DocumentArchive.document_type == models.DocumentType.NOTE_HONORAIRES,
            or_(
                models.DocumentArchive.status == models.DocumentStatus.ACTIF,
                models.DocumentArchive.status.is_(None),
            ),
            or_(
                models.DocumentArchive.is_latest_version.is_(True),
                models.DocumentArchive.is_latest_version.is_(None),
            ),
            or_(
                models.DocumentArchive.is_accounted.is_(True),
                models.DocumentArchive.is_accounted.is_(None),
            ),
        )
        .all()
    )
    return [doc for doc in docs if doc.id not in linked_doc_ids]


def _visible_installment_plans(
    db: Session,
    access: PatientCompanionAccess,
) -> list[models.InstallmentPlan]:
    return (
        db.query(models.InstallmentPlan)
        .join(models.Patient, models.InstallmentPlan.patient_id == models.Patient.id)
        .outerjoin(models.Acte, models.InstallmentPlan.acte_id == models.Acte.id)
        .filter(
            models.InstallmentPlan.patient_id == access.patient_id,
            models.Patient.employer_id == access.employer_id,
            models.Patient.deleted_at.is_(None),
            or_(
                models.InstallmentPlan.acte_id.is_(None),
                models.Acte.deleted_at.is_(None),
            ),
        )
        .order_by(models.InstallmentPlan.created_at.desc(), models.InstallmentPlan.id.desc())
        .all()
    )


def _shared_invoice_rows(
    db: Session,
    access: PatientCompanionAccess,
) -> list[tuple[PatientCompanionShareGrant, models.DocumentArchive]]:
    return (
        db.query(PatientCompanionShareGrant, models.DocumentArchive)
        .join(
            models.DocumentArchive,
            models.DocumentArchive.id == PatientCompanionShareGrant.resource_id,
        )
        .join(models.Patient, models.Patient.id == models.DocumentArchive.patient_id)
        .filter(
            PatientCompanionShareGrant.employer_id == access.employer_id,
            PatientCompanionShareGrant.patient_id == access.patient_id,
            PatientCompanionShareGrant.resource_type == "document",
            PatientCompanionShareGrant.revoked_at.is_(None),
            models.DocumentArchive.patient_id == access.patient_id,
            models.DocumentArchive.document_type == models.DocumentType.NOTE_HONORAIRES,
            models.DocumentArchive.status == models.DocumentStatus.ACTIF,
            or_(
                models.DocumentArchive.is_latest_version.is_(True),
                models.DocumentArchive.is_latest_version.is_(None),
            ),
            models.Patient.employer_id == access.employer_id,
            models.Patient.deleted_at.is_(None),
        )
        .order_by(models.DocumentArchive.created_at.desc(), models.DocumentArchive.id.desc())
        .all()
    )


def resolve_shared_invoice(
    db: Session,
    access: PatientCompanionAccess,
    share_public_id: str,
) -> tuple[PatientCompanionShareGrant, models.DocumentArchive] | None:
    return (
        db.query(PatientCompanionShareGrant, models.DocumentArchive)
        .join(
            models.DocumentArchive,
            models.DocumentArchive.id == PatientCompanionShareGrant.resource_id,
        )
        .join(models.Patient, models.Patient.id == models.DocumentArchive.patient_id)
        .filter(
            PatientCompanionShareGrant.public_id == share_public_id,
            PatientCompanionShareGrant.employer_id == access.employer_id,
            PatientCompanionShareGrant.patient_id == access.patient_id,
            PatientCompanionShareGrant.resource_type == "document",
            PatientCompanionShareGrant.revoked_at.is_(None),
            models.DocumentArchive.patient_id == access.patient_id,
            models.DocumentArchive.document_type == models.DocumentType.NOTE_HONORAIRES,
            models.DocumentArchive.status == models.DocumentStatus.ACTIF,
            or_(
                models.DocumentArchive.is_latest_version.is_(True),
                models.DocumentArchive.is_latest_version.is_(None),
            ),
            models.Patient.employer_id == access.employer_id,
            models.Patient.deleted_at.is_(None),
        )
        .first()
    )


def project_finance(
    db: Session,
    access: PatientCompanionAccess,
) -> dict[str, Any]:
    if not _patient_exists_in_tenant(db, access):
        return {
            "summary": {"billed": 0.0, "collected": 0.0, "remaining_due": 0.0},
            "payments": [],
            "schedules": [],
            "invoices": [],
            "online_payment": {"available": False},
        }

    actes = _active_actes(db, access)
    payments = _visible_payments(db, access)
    standalone_docs = _standalone_invoice_docs(db, access)
    plans = _visible_installment_plans(db, access)
    shared_invoices = _shared_invoice_rows(db, access)

    billed_actes = sum(float(row.montant or 0.0) for row in actes)
    billed_docs = sum(extract_amount_from_clinical_data(doc.clinical_data) for doc in standalone_docs)
    total_billed = float(billed_actes + billed_docs)
    total_collected = float(sum(float(row.amount or 0.0) for row in payments))
    remaining_due = max(total_billed - total_collected, 0.0)

    payment_items = [
        {
            "id": row.id,
            "amount": round(float(row.amount or 0.0), 2),
            "method": _enum_value(row.payment_method),
            "paid_at": row.payment_date,
            "source": (
                "installment"
                if row.installment_id is not None
                else "acte"
                if row.acte_id is not None
                else "document_or_manual"
            ),
        }
        for row in payments
    ]

    schedule_items: list[dict[str, Any]] = []
    for plan in plans:
        installments = sorted(plan.installments, key=lambda item: (item.due_date or datetime.max, item.id))
        schedule_items.append(
            {
                "id": plan.id,
                "title": plan.title,
                "total_amount": round(float(plan.total_amount or 0.0), 2),
                "items": [
                    {
                        "id": item.id,
                        "label": item.label,
                        "amount": round(float(item.amount or 0.0), 2),
                        "due_date": item.due_date,
                        "paid_date": item.paid_date,
                        "status": item.status,
                    }
                    for item in installments
                ],
            }
        )

    invoice_items = [
        {
            "share_id": share.public_id,
            "document_id": doc.id,
            "title": doc.title or doc.original_filename or "Note d'honoraires",
            "amount": round(float(extract_amount_from_clinical_data(doc.clinical_data)), 2),
            "issued_at": _document_business_date(doc),
            "download_path": f"/api/patient-companion/contexts/{access.public_id}/finance/invoices/{share.public_id}/download",
        }
        for share, doc in shared_invoices
    ]

    return {
        "summary": {
            "billed": round(total_billed, 2),
            "collected": round(total_collected, 2),
            "remaining_due": round(remaining_due, 2),
        },
        "payments": payment_items,
        "schedules": schedule_items,
        "invoices": invoice_items,
        "online_payment": {"available": False},
    }
