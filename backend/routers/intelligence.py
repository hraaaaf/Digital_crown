from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from backend import database, models
from backend.routers.auth import get_current_user, require_permission
from backend.services.elite_manager import elite_manager
from backend.utils.access_control import assert_patient_access

router = APIRouter(tags=["Elite Intelligence"])

@router.get("/patient/{patient_id}")
async def get_patient_intelligence(
    patient_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients"))
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
    current_user: models.User = Depends(require_permission("patients"))
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
    current_user: models.User = Depends(require_permission("patients"))
):
    """
    Génère et récupère le plan de traitement méthodique basé sur les dernières analyses.
    """
    assert_patient_access(patient_id, current_user, db)
    return await elite_manager.get_treatment_plan(db, patient_id)


@router.get("/briefing-j1")
def get_briefing_j1(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients"))
):
    """C2 — Briefing financier J-1 : patients de demain avec leurs soldes impayés."""
    employer_id = current_user.get_employer_id()
    tomorrow = datetime.now().date() + timedelta(days=1)
    tomorrow_start = datetime.combine(tomorrow, datetime.min.time())
    tomorrow_end = datetime.combine(tomorrow, datetime.max.time())

    appts = db.query(models.Appointment).join(models.Patient).filter(
        models.Patient.employer_id == employer_id,
        models.Appointment.datetime_start >= tomorrow_start,
        models.Appointment.datetime_start <= tomorrow_end,
        models.Appointment.status != "ANNULÉ"
    ).order_by(models.Appointment.datetime_start).all()

    result = []
    total_outstanding = 0.0
    seen_patient_ids = set()

    for appt in appts:
        if appt.patient_id in seen_patient_ids:
            continue
        seen_patient_ids.add(appt.patient_id)

        patient = db.query(models.Patient).filter(models.Patient.id == appt.patient_id).first()
        if not patient:
            continue

        solde = db.query(func.sum(models.Acte.montant)).filter(
            models.Acte.patient_id == appt.patient_id,
            models.Acte.statut_paiement == "EN_ATTENTE"
        ).scalar() or 0.0

        total_outstanding += solde
        result.append({
            "patient_id": appt.patient_id,
            "nom": patient.nom,
            "prenom": patient.prenom,
            "appointment_time": appt.datetime_start.strftime("%H:%M"),
            "motif": appt.motif or "",
            "solde_attente": round(float(solde), 2),
        })

    return {
        "date": tomorrow.isoformat(),
        "total_patients": len(result),
        "total_outstanding": round(total_outstanding, 2),
        "patients": result,
    }
