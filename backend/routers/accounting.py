from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from backend import models, schemas, database
from backend.routers.auth import get_current_user
from backend.utils.access_control import assert_patient_access

router = APIRouter(tags=["Accounting & Payments"])

@router.post("/plans", response_model=schemas.InstallmentPlanOut)
def create_installment_plan(plan: schemas.InstallmentPlanCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    """Crée un nouveau plan de paiement avec ses échéances."""
    assert_patient_access(plan.patient_id, current_user, db)
    new_plan = models.InstallmentPlan(
        patient_id=plan.patient_id,
        title=plan.title,
        total_amount=plan.total_amount
    )
    db.add(new_plan)
    db.flush() # Pour avoir l'ID du plan
    
    for inst in plan.installments:
        new_inst = models.Installment(
            plan_id=new_plan.id,
            label=inst.label,
            amount=inst.amount,
            due_date=inst.due_date,
            status=inst.status,
            notes=inst.notes
        )
        db.add(new_inst)
    
    db.commit()
    db.refresh(new_plan)
    return new_plan

@router.get("/plans/patient/{patient_id}", response_model=List[schemas.InstallmentPlanOut])
def get_patient_plans(patient_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    """Récupère tous les plans de paiement d'un patient."""
    assert_patient_access(patient_id, current_user, db)
    return db.query(models.InstallmentPlan).filter(models.InstallmentPlan.patient_id == patient_id).all()

@router.put("/installments/{installment_id}", response_model=schemas.InstallmentOut)
def update_installment(installment_id: int, updates: dict, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    """Met à jour une échéance (marquer comme payée, changer date, etc.)."""
    inst = db.query(models.Installment).filter(models.Installment.id == installment_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Échéance introuvable")
    
    assert_patient_access(inst.plan.patient_id, current_user, db)
    
    for key, value in updates.items():
        if hasattr(inst, key):
            if key in ['due_date', 'paid_date'] and value:
                value = datetime.strptime(value, '%Y-%m-%d').date()
            setattr(inst, key, value)
    
    db.commit()
    db.refresh(inst)
    return inst

@router.delete("/plans/{plan_id}")
def delete_installment_plan(plan_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    """Supprime un plan de paiement complet."""
    plan = db.query(models.InstallmentPlan).filter(models.InstallmentPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan introuvable")
    
    assert_patient_access(plan.patient_id, current_user, db)
    
    db.delete(plan)
    db.commit()
    return {"status": "success", "message": "Plan supprimé"}

@router.get("/frequent-acts", response_model=List[dict])
def get_frequent_acts(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    """Récupère les actes les plus fréquents du praticien."""
    from backend.services.accounting_service import accounting_service
    return accounting_service.get_frequent_acts(db, current_user.id)

@router.post("/record-act")
def record_act(data: dict, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    """Enregistre manuellement l'usage d'un acte pour l'apprentissage."""
    from backend.services.accounting_service import accounting_service
    accounting_service.record_act_usage(
        db, 
        current_user.id, 
        data.get("name"), 
        float(data.get("price", 0.0)), 
        data.get("category")
    )
    return {"status": "success"}
