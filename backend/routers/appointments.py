from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime

from backend import models, schemas, database
from backend.routers.auth import get_current_user, require_permission
from backend.utils.access_control import assert_patient_access
from backend.services.elite_manager import elite_manager
from backend.services.notification_service import notification_service

router = APIRouter(tags=["Appointments"])

@router.get("/", response_model=List[schemas.AppointmentOut])
def get_appointments(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("agenda"))
):
    user_employer_id = current_user.get_employer_id()
    query = db.query(models.Appointment).filter(models.Appointment.employer_id == user_employer_id)
    if start_date:
        query = query.filter(models.Appointment.datetime_start >= datetime.fromisoformat(start_date.replace("Z", "+00:00")))
    if end_date:
        query = query.filter(models.Appointment.datetime_start <= datetime.fromisoformat(end_date.replace("Z", "+00:00")))
    return query.order_by(models.Appointment.datetime_start.asc()).all()

@router.post("/", response_model=schemas.AppointmentOut)
def create_appointment(
    appt: schemas.AppointmentCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("agenda"))
):
    if appt.patient_id:
        assert_patient_access(appt.patient_id, current_user, db)
        
    appt_data = appt.model_dump()
    appt_data['employer_id'] = current_user.get_employer_id()
    db_appt = models.Appointment(**appt_data)
    db.add(db_appt)
    db.commit()
    db.refresh(db_appt)
    return db_appt

@router.put("/{id}", response_model=schemas.AppointmentOut)
def update_appointment(
    id: int,
    appt_update: schemas.AppointmentUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("agenda"))
):
    user_employer_id = current_user.get_employer_id()
    db_appt = db.query(models.Appointment).filter(
        models.Appointment.id == id,
        models.Appointment.employer_id == user_employer_id
    ).first()
    if not db_appt: raise HTTPException(status_code=404, detail="Rendez-vous introuvable")
    
    update_data = appt_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_appt, key, value)
        
    db.commit()
    db.refresh(db_appt)
    return db_appt

@router.delete("/{id}")
def delete_appointment(id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("agenda"))):
    user_employer_id = current_user.get_employer_id()
    db_appt = db.query(models.Appointment).filter(
        models.Appointment.id == id,
        models.Appointment.employer_id == user_employer_id
    ).first()
    if not db_appt: raise HTTPException(status_code=404, detail="Rendez-vous introuvable")
    db.delete(db_appt)
    db.commit()
    return {"status": "success"}

@router.post("/bulk", response_model=List[schemas.AppointmentOut])
def create_bulk_appointments(
    payload: schemas.AppointmentBulkCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("agenda"))
):
    created_appts = []
    user_employer_id = current_user.get_employer_id()
    for item in payload.appointments:
        if item.patient_id:
            assert_patient_access(item.patient_id, current_user, db)
            
        db_appt = models.Appointment(
            patient_name=item.patient_name,
            patient_id=item.patient_id,
            datetime_start=item.datetime_start,
            duration_minutes=item.duration_minutes,
            notes=item.notes,
            status=item.status,
            scheduling_type=item.scheduling_type,
            employer_id=user_employer_id
        )
        db.add(db_appt)
        created_appts.append(db_appt)
    
    db.commit()
    for appt in created_appts:
        db.refresh(appt)
        
    return created_appts

@router.post("/reminders/send")
def trigger_reminders(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("agenda"))
):
    """
    Déclenche manuellement ou via un service planifié l'envoi de rappels automatisés de rendez-vous pour les prochaines 24h.
    """
    sent_count = notification_service.cron_send_reminders(db)
    return {"status": "success", "reminders_sent": sent_count}

@router.get("/suggest/{patient_id}", response_model=schemas.AppointmentSuggestionOut)
async def suggest_appointment(
    patient_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("agenda"))
):
    """Renvoie une proposition d'appel basée sur le plan de traitement actif.
    Algorithme déterministe :
    - récupère le plan via elite_manager
    - parcourt les phases dans l'ordre clinique
    - retourne le premier acte trouvé avec durée estimée
    Si aucun plan n'existe, propose une consultation de routine.
    """
    # Vérification d'accès patient
    assert_patient_access(patient_id, current_user, db)

    # 1️⃣ Récupérer le plan de traitement
    plan = await elite_manager.get_treatment_plan(db, patient_id)
    phases = plan.get("phases", {}) if isinstance(plan, dict) else {}
    phase_order = ["URGENCE", "INITIALE", "CONSERVATRICE", "REHABILITATION", "MAINTENANCE"]

    # 2️⃣ Recherche du premier acte suggéré
    for phase in phase_order:
        acts = phases.get(phase, [])
        if acts:
            act = acts[0]
            suggested = act.get("suggested_act", "Consultation")
            # Durée estimée (déterministe)
            if "implant" in suggested.lower() or "couronne" in suggested.lower() or "endodontique" in suggested.lower():
                duration = 45
            elif "détartrage" in suggested.lower() or "prophylaxie" in suggested.lower():
                duration = 20
            else:
                duration = 30
            return schemas.AppointmentSuggestionOut(
                patient_id=patient_id,
                motif=suggested,
                duration_minutes=duration,
                notes=f"Suggestion auto depuis le plan (phase {phase})"
            )

    # 3️⃣ Fallback générique
    return schemas.AppointmentSuggestionOut(
        patient_id=patient_id,
        motif="Consultation & Bilan de routine",
        duration_minutes=15,
        notes="Aucun acte pending – suggestion générique"
    )
