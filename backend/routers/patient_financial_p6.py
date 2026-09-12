from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend import database, models
from backend.routers.auth import require_permission
from backend.services.accounting_service import accounting_service
from backend.utils.access_control import assert_patient_access
from backend.routers import patient_practitioner_p2


router = APIRouter()
router.include_router(patient_practitioner_p2.router)


@router.get("/{patient_id}/financial-snapshot")
def get_patient_financial_snapshot_p6(
    patient_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission(["accounting", "payments"])),
):
    """Patient finance snapshot with an explicit billing-basis contract.

    `has_billing_data` means at least one active Acte row exists for the patient.
    Payments remain factual even when no Acte row exists, but in that situation
    `total_billed` and `remaining_due` must not be interpreted as proof that nothing
    is owed. Document-generated voided/trashed payments are excluded everywhere.

    P2 adds an additive practitioner breakdown. Revenue is attributed only when a
    payment can be traced to an Acte (directly, or through an installment plan linked
    to an Acte). Payments without that evidence remain explicitly unattributed.
    """
    assert_patient_access(patient_id, current_user, db)

    from datetime import date as date_type

    today = date_type.today()
    visible_payment = accounting_service._visible_payment_filter()

    active_actes = (
        db.query(models.Acte)
        .filter(
            models.Acte.patient_id == patient_id,
            models.Acte.deleted_at.is_(None),
        )
        .all()
    )
    acte_count = len(active_actes)
    has_billing_data = acte_count > 0

    total_billed = sum(float(acte.montant or 0.0) for acte in active_actes)
    total_collected = float(
        db.query(func.sum(models.Payment.amount))
        .outerjoin(models.Acte, models.Payment.acte_id == models.Acte.id)
        .filter(
            models.Payment.patient_id == patient_id,
            visible_payment,
        )
        .scalar()
        or 0.0
    )
    remaining_due = max(total_billed - total_collected, 0.0) if has_billing_data else None

    # P2 — production/encaissement par praticien, sans répartition inventée.
    acte_by_id = {acte.id: acte for acte in active_actes}
    practitioner_ids = {acte.praticien_id for acte in active_actes if acte.praticien_id is not None}
    practitioners = (
        db.query(models.User).filter(models.User.id.in_(practitioner_ids)).all()
        if practitioner_ids else []
    )
    practitioner_names = {
        user.id: (user.nom_complet or user.email or f"Praticien {user.id}")
        for user in practitioners
    }
    breakdown = {}
    for acte in active_actes:
        if acte.praticien_id is None:
            continue
        row = breakdown.setdefault(
            acte.praticien_id,
            {
                "practitioner_id": acte.praticien_id,
                "practitioner_name": practitioner_names.get(acte.praticien_id, f"Praticien {acte.praticien_id}"),
                "act_count": 0,
                "total_billed": 0.0,
                "linked_collected": 0.0,
            },
        )
        row["act_count"] += 1
        row["total_billed"] += float(acte.montant or 0.0)

    installment_to_acte = {
        installment_id: acte_id
        for installment_id, acte_id in (
            db.query(models.Installment.id, models.InstallmentPlan.acte_id)
            .join(models.InstallmentPlan, models.Installment.plan_id == models.InstallmentPlan.id)
            .filter(
                models.InstallmentPlan.patient_id == patient_id,
                models.InstallmentPlan.acte_id.isnot(None),
            )
            .all()
        )
    }
    visible_payments = (
        db.query(models.Payment)
        .outerjoin(models.Acte, models.Payment.acte_id == models.Acte.id)
        .filter(
            models.Payment.patient_id == patient_id,
            visible_payment,
        )
        .all()
    )
    unattributed_collected = 0.0
    for payment in visible_payments:
        linked_acte_id = payment.acte_id
        if linked_acte_id is None and payment.installment_id is not None:
            linked_acte_id = installment_to_acte.get(payment.installment_id)
        linked_acte = acte_by_id.get(linked_acte_id) if linked_acte_id is not None else None
        practitioner_id = linked_acte.praticien_id if linked_acte is not None else None
        if practitioner_id is not None and practitioner_id in breakdown:
            breakdown[practitioner_id]["linked_collected"] += float(payment.amount or 0.0)
        else:
            unattributed_collected += float(payment.amount or 0.0)

    by_practitioner = []
    for row in sorted(breakdown.values(), key=lambda item: item["practitioner_name"].lower()):
        row["total_billed"] = round(row["total_billed"], 2)
        row["linked_collected"] = round(row["linked_collected"], 2)
        row["linked_remaining_due"] = round(max(row["total_billed"] - row["linked_collected"], 0.0), 2)
        by_practitioner.append(row)

    overdue_actes = (
        db.query(models.Acte)
        .filter(
            models.Acte.patient_id == patient_id,
            models.Acte.deleted_at.is_(None),
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
        .outerjoin(models.Acte, models.Payment.acte_id == models.Acte.id)
        .filter(
            models.Payment.patient_id == patient_id,
            visible_payment,
        )
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
        .outerjoin(models.Acte, models.Payment.acte_id == models.Acte.id)
        .filter(
            models.Payment.patient_id == patient_id,
            visible_payment,
        )
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
        "by_practitioner": by_practitioner,
        "unattributed_collected": round(unattributed_collected, 2),
    }
