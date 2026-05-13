from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

from backend import database, models
from backend.routers.auth import get_current_user
from backend.services.elite_manager import elite_manager
from backend.utils.access_control import assert_patient_access

router = APIRouter(tags=["Elite Intelligence"])

@router.get("/patient/{patient_id}")
async def get_patient_intelligence(
    patient_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Récupère l'intelligence globale pour un patient (Résumé + Insights + Score).
    """
    assert_patient_access(patient_id, current_user, db)
    return await elite_manager.get_comprehensive_intelligence(
        db, 
        patient_id, 
        doctor_id=current_user.id
    )

@router.post("/patient/{patient_id}/audit")
async def audit_document_context(
    patient_id: int,
    context_type: str,
    doc_data: Dict[str, Any] = Body(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Audit spécifique d'un contexte de document (ex: audit d'une ordonnance en cours).
    """
    assert_patient_access(patient_id, current_user, db)
    return await elite_manager.get_comprehensive_intelligence(
        db,
        patient_id,
        context_type=context_type,
        doc_data=doc_data,
        doctor_id=current_user.id
    )

@router.get("/patient/{patient_id}/treatment-plan")
async def get_treatment_plan(
    patient_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Génère et récupère le plan de traitement méthodique basé sur les dernières analyses.
    """
    assert_patient_access(patient_id, current_user, db)
    return await elite_manager.get_treatment_plan(db, patient_id)
