from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime
import os
import pathlib

from backend import models, database
from backend.schemas import installments as schemas
from backend.routers.auth import require_permission
from backend.utils.access_control import assert_patient_access
from backend.core.paths import AppPaths

MEDIA_DIR = AppPaths.get_user_data_dir() / "media"
DOCS_DIR  = str(MEDIA_DIR / "documents")

router = APIRouter(tags=["installments"])

@router.get("/patient/{patient_id}", response_model=List[schemas.InstallmentPlanResponse])
def get_installment_plans(patient_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("accounting"))):
    assert_patient_access(patient_id, current_user, db)
    plans = db.query(models.InstallmentPlan).filter(models.InstallmentPlan.patient_id == patient_id).all()
    return plans

@router.post("/", response_model=schemas.InstallmentPlanResponse)
def create_installment_plan(plan_req: schemas.InstallmentPlanCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("accounting"))):
    assert_patient_access(plan_req.patient_id, current_user, db)
    db_plan = models.InstallmentPlan(
        patient_id=plan_req.patient_id,
        title=plan_req.title,
        total_amount=plan_req.total_amount
    )
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    
    for inst in plan_req.installments:
        db_inst = models.Installment(
            plan_id=db_plan.id,
            label=inst.label,
            amount=inst.amount,
            due_date=inst.due_date,
            paid_date=inst.paid_date,
            status=inst.status,
            notes=inst.notes
        )
        db.add(db_inst)
        
    db.commit()
    db.refresh(db_plan)
    return db_plan

@router.put("/{installment_id}", response_model=schemas.InstallmentResponse)
def update_installment(installment_id: int, req: schemas.InstallmentUpdate, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("accounting"))):
    inst = db.query(models.Installment).filter(models.Installment.id == installment_id).first()
    if inst:
        plan = db.query(models.InstallmentPlan).filter(models.InstallmentPlan.id == inst.plan_id).first()
        if not plan:
            raise HTTPException(status_code=404, detail="Plan introuvable")
        assert_patient_access(plan.patient_id, current_user, db)
    if not inst:
        raise HTTPException(status_code=404, detail="Echéance introuvable")
        
    # Si on marque comme PAYE et que ce n'était pas payé
    if req.status == "PAYE" and inst.status != "PAYE":
        inst.paid_date = datetime.now()
        inst.status = "PAYE"
        # Créer le paiement dans la trésorerie
        new_payment = models.Payment(
            patient_id=plan.patient_id,
            amount=inst.amount,
            payment_method=models.PaymentMethod.ESPECES, # Par défaut
            payment_date=datetime.now(),
            installment_id=inst.id,
            notes=f"Paiement échéance: {inst.label} ({inst.plan.title})",
            validated_by=f"{current_user.nom_complet or 'Utilisateur'} ({current_user.role})"
        )
        db.add(new_payment)
    else:
        if req.status is not None:
            inst.status = req.status
        if req.paid_date is not None:
            inst.paid_date = req.paid_date
    
    if req.amount is not None:
        inst.amount = req.amount
    if req.due_date is not None:
        inst.due_date = req.due_date
    if req.label is not None:
        inst.label = req.label
    if req.notes is not None:
        inst.notes = req.notes
        
    db.commit()
    db.refresh(inst)
    return inst

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
        items=[{"label": it.label, "amount": it.amount, "due_date": it.due_date, "paid": it.paid}
               for it in req.items],
        output_dir=DOCS_DIR,
        config=config,
        user=current_user,
    )
    filename = os.path.basename(filepath)
    return {"pdf_url": f"static/documents/{filename}"}


@router.delete("/plan/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_installment_plan(plan_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("accounting"))):
    plan = db.query(models.InstallmentPlan).filter(models.InstallmentPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan introuvable")
    assert_patient_access(plan.patient_id, current_user, db)
    db.delete(plan)
    db.commit()
    return None
