from datetime import datetime
import os
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend import database, models
from backend.core.paths import AppPaths
from backend.routers.auth import require_permission
from backend.schemas import installments as schemas
from backend.utils.access_control import assert_patient_access

MEDIA_DIR = AppPaths.get_user_data_dir() / "media"
DOCS_DIR = str(MEDIA_DIR / "documents")

router = APIRouter(tags=["installments"])


@router.get("/patient/{patient_id}", response_model=List[schemas.InstallmentPlanResponse])
def get_installment_plans(
    patient_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("accounting")),
):
    assert_patient_access(patient_id, current_user, db)
    # Deterministic lifecycle: callers that need the latest plan can safely use
    # the last returned row instead of depending on database incidental order.
    return (
        db.query(models.InstallmentPlan)
        .filter(models.InstallmentPlan.patient_id == patient_id)
        .order_by(models.InstallmentPlan.created_at.asc(), models.InstallmentPlan.id.asc())
        .all()
    )


@router.get("/patient/{patient_id}/latest", response_model=schemas.InstallmentPlanResponse)
def get_latest_installment_plan(
    patient_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("accounting")),
):
    assert_patient_access(patient_id, current_user, db)
    plan = (
        db.query(models.InstallmentPlan)
        .filter(models.InstallmentPlan.patient_id == patient_id)
        .order_by(models.InstallmentPlan.created_at.desc(), models.InstallmentPlan.id.desc())
        .first()
    )
    if not plan:
        raise HTTPException(status_code=404, detail="Aucun plan de paiement")
    return plan


@router.post("/", response_model=schemas.InstallmentPlanResponse)
def create_installment_plan(
    plan_req: schemas.InstallmentPlanCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("accounting")),
):
    assert_patient_access(plan_req.patient_id, current_user, db)
    try:
        db_plan = models.InstallmentPlan(
            patient_id=plan_req.patient_id,
            title=plan_req.title,
            total_amount=plan_req.total_amount,
        )
        db.add(db_plan)
        db.flush()

        for inst in plan_req.installments:
            db.add(models.Installment(
                plan_id=db_plan.id,
                label=inst.label,
                amount=inst.amount,
                due_date=inst.due_date,
                paid_date=inst.paid_date,
                status=inst.status,
                notes=inst.notes,
            ))

        db.commit()
        db.refresh(db_plan)
        return db_plan
    except Exception:
        db.rollback()
        raise


@router.put("/{installment_id}", response_model=schemas.InstallmentResponse)
def update_installment(
    installment_id: int,
    req: schemas.InstallmentUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("accounting")),
):
    inst = db.query(models.Installment).filter(models.Installment.id == installment_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Echéance introuvable")

    plan = db.query(models.InstallmentPlan).filter(models.InstallmentPlan.id == inst.plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan introuvable")
    assert_patient_access(plan.patient_id, current_user, db)

    # Une échéance déjà encaissée ne peut pas être réouverte ou rechiffrée sans
    # workflow comptable de contrepassation. Sinon le Payment historique diverge.
    if inst.status == "PAYE":
        if req.status is not None and req.status != "PAYE":
            raise HTTPException(
                status_code=409,
                detail="Une échéance payée ne peut pas être réouverte sans contrepassation comptable.",
            )
        if req.amount is not None and abs(float(req.amount) - float(inst.amount)) >= 0.005:
            raise HTTPException(
                status_code=409,
                detail="Le montant d'une échéance déjà payée ne peut pas être modifié sans contrepassation comptable.",
            )

    transitioning_to_paid = req.status == "PAYE" and inst.status != "PAYE"
    if transitioning_to_paid and req.payment_method is None:
        raise HTTPException(
            status_code=422,
            detail="Le mode de règlement est requis pour marquer une échéance comme payée.",
        )

    if req.amount is not None:
        inst.amount = req.amount
    if req.due_date is not None:
        inst.due_date = req.due_date
    if req.label is not None:
        inst.label = req.label
    if req.notes is not None:
        inst.notes = req.notes

    if transitioning_to_paid:
        paid_at = req.paid_date or datetime.now()
        inst.paid_date = paid_at
        inst.status = "PAYE"
        payment_method = getattr(models.PaymentMethod, req.payment_method)
        db.add(models.Payment(
            patient_id=plan.patient_id,
            amount=inst.amount,
            payment_method=payment_method,
            payment_date=paid_at,
            installment_id=inst.id,
            notes=f"Paiement échéance: {inst.label} ({plan.title})",
            validated_by=f"{current_user.nom_complet or 'Utilisateur'} ({current_user.role})",
        ))
    else:
        if req.status is not None:
            inst.status = req.status
        if req.paid_date is not None:
            inst.paid_date = req.paid_date

    try:
        db.commit()
        db.refresh(inst)
        return inst
    except Exception:
        db.rollback()
        raise


@router.post("/generate-preview")
def generate_installment_preview(
    req: schemas.InstallmentPreviewRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("accounting")),
):
    assert_patient_access(req.patient_id, current_user, db)
    patient = db.query(models.Patient).filter(models.Patient.id == req.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient introuvable")

    config = db.query(models.CabinetConfig).filter(
        models.CabinetConfig.owner_id == current_user.id
    ).first()

    patient_name = f"{patient.nom.upper()} {patient.prenom.capitalize()}"

    from backend.services.generators.installment_receipt_gen import generate_installment_receipt
    filepath = generate_installment_receipt(
        patient_name=patient_name,
        title=req.title,
        total_amount=req.total_amount,
        items=[
            {"label": it.label, "amount": it.amount, "due_date": it.due_date, "paid": it.paid}
            for it in req.items
        ],
        output_dir=DOCS_DIR,
        config=config,
        user=current_user,
    )
    filename = os.path.basename(filepath)
    return {"pdf_url": f"static/documents/{filename}"}


@router.delete("/plan/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_installment_plan(
    plan_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("accounting")),
):
    plan = db.query(models.InstallmentPlan).filter(models.InstallmentPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan introuvable")
    assert_patient_access(plan.patient_id, current_user, db)

    paid_installment = (
        db.query(models.Installment)
        .filter(models.Installment.plan_id == plan_id, models.Installment.status == "PAYE")
        .first()
    )
    if paid_installment:
        raise HTTPException(
            status_code=409,
            detail="Un plan contenant une échéance encaissée ne peut pas être supprimé sans contrepassation comptable.",
        )

    db.delete(plan)
    db.commit()
    return None
