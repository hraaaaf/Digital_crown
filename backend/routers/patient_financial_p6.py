from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend import database, models
from backend.routers.auth import require_permission
from backend.utils.access_control import assert_patient_access


router = APIRouter()


@router.get("/{patient_id}/financial-snapshot")
def get_patient_financial_snapshot_p6(
    patient_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission(["accounting", "payments"])),
):
    """Patient finance snapshot with an explicit billing-basis contract.

    `has_billing_data` means at least one Acte row exists for the patient. Payments remain
    factual even when no Acte row exists, but in that situation `total_billed` and
    `remaining_due` must not be interpreted as proof that nothing is owed.
    """
    assert_patient_access(patient_id, current_user, db)

    from datetime import date as date_type

    today = date_type.today()
    acte_count = int(
        db.query(func.count(models.Acte.id))
        .filter(models.Acte.patient_id == patient_id)
        .scalar()
        or 0
    )
    has_billing_data = acte_count > 0

    total_billed = float(
        db.query(func.sum(models.Acte.montant))
        .filter(models.Acte.patient_id == patient_id)
        .scalar()
        or 0.0
    )
    total_collected = float(
        db.query(func.sum(models.Payment.amount))
        .filter(models.Payment.patient_id == patient_id)
        .scalar()
        or 0.0
    )
    remaining_due = max(total_billed - total_collected, 0.0) if has_billing_data else None

    overdue_actes = (
        db.query(models.Acte)
        .filter(
            models.Acte.patient_id == patient_id,
            models.Acte.statut_paiement.in_(["EN_ATTENTE", "A_ENCAISSER", "PARTIEL"]),
        )
        .order_by(models.Acte.date_debut.desc())
        .limit(10)
        .all()
    )
    overdue_total = sum(float(a.montant) for a in overdue_actes)
    overdue_items = [
        {
            "id": a.id,
            "libelle": a.libelle,
            "montant": float(a.montant),
            "statut_paiement": a.statut_paiement,
            "date_debut": a.date_debut.isoformat() if a.date_debut else None,
            "type_acte": a.type_acte,
        }
        for a in overdue_actes
    ]

    upcoming_installments = (
        db.query(models.Installment)
        .join(models.InstallmentPlan, models.Installment.plan_id == models.InstallmentPlan.id)
        .filter(
            models.InstallmentPlan.patient_id == patient_id,
            models.Installment.status == "EN_ATTENTE",
            models.Installment.due_date >= today,
        )
        .order_by(models.Installment.due_date.asc(), models.Installment.id.asc())
        .limit(5)
        .all()
    )
    upcoming_total = sum(float(i.amount) for i in upcoming_installments)
    upcoming_list = [
        {
            "id": i.id,
            "label": i.label,
            "amount": float(i.amount),
            "due_date": i.due_date.isoformat() if i.due_date else None,
        }
        for i in upcoming_installments
    ]
    next_installment = upcoming_list[0] if upcoming_list else None

    recent_payments = (
        db.query(models.Payment)
        .filter(models.Payment.patient_id == patient_id)
        .order_by(models.Payment.payment_date.desc(), models.Payment.id.desc())
        .limit(5)
        .all()
    )
    recent_list = [
        {
            "id": p.id,
            "amount": float(p.amount),
            "payment_method": p.payment_method,
            "payment_date": p.payment_date.isoformat() if p.payment_date else None,
            "notes": p.notes,
        }
        for p in recent_payments
    ]

    methods_rows = (
        db.query(
            models.Payment.payment_method,
            func.sum(models.Payment.amount).label("total"),
            func.count(models.Payment.id).label("count"),
        )
        .filter(models.Payment.patient_id == patient_id)
        .group_by(models.Payment.payment_method)
        .all()
    )
    payment_methods = {
        str(m.payment_method): {"total": float(m.total), "count": int(m.count)}
        for m in methods_rows
    }

    return {
        "has_billing_data": has_billing_data,
        "total_billed": round(total_billed, 2),
        "total_collected": round(total_collected, 2),
        "remaining_due": round(remaining_due, 2) if remaining_due is not None else None,
        "overdue_count": len(overdue_items),
        "overdue_total": round(overdue_total, 2),
        "overdue_items": overdue_items,
        "upcoming_installments_count": len(upcoming_list),
        "upcoming_installments_total": round(upcoming_total, 2),
        "upcoming_installments": upcoming_list,
        "next_installment": next_installment,
        "recent_payments": recent_list,
        "payment_methods": payment_methods,
    }
