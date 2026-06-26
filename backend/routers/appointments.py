from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from typing import List, Optional
from datetime import datetime, timedelta

from backend import models, schemas, database
from backend.routers.auth import get_current_user, require_permission
from backend.utils.access_control import assert_patient_access
from backend.services.elite_manager import elite_manager
from backend.services.notification_service import notification_service
from backend.services.audit_service import audit_service

router = APIRouter(tags=["Appointments"])


def _find_conflicts(db: Session, employer_id: int, datetime_start: datetime, duration_minutes: int, exclude_id: int | None = None) -> list:
    """Retourne les RDV qui se chevauchent avec le créneau donné."""
    end = datetime_start + timedelta(minutes=duration_minutes)
    # SQL pre-filter : fenêtre large (±4h) pour laisser le filtrage précis à Python
    window_start = datetime_start - timedelta(hours=4)
    q = db.query(models.Appointment).filter(
        models.Appointment.employer_id == employer_id,
        models.Appointment.status != models.AppointmentStatus.ANNULE,
        models.Appointment.scheduling_type == models.SchedulingType.EXACT_TIME,
        models.Appointment.datetime_start < end,
        models.Appointment.datetime_start >= window_start,
    )
    if exclude_id:
        q = q.filter(models.Appointment.id != exclude_id)
    # Filtrage précis en Python (SQLAlchemy ne supporte pas datetime + timedelta en filtre SQL)
    rows = q.all()
    return [
        a for a in rows
        if a.datetime_start + timedelta(minutes=a.duration_minutes) > datetime_start
        and a.datetime_start < end
    ]

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
    audit_service.log(db=db, user_id=current_user.id, employer_id=current_user.get_employer_id(), action="CREATE", resource_type="Appointment", resource_id=str(db_appt.id), details=f"RDV patient {appt.patient_id}")
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
    audit_service.log(db=db, user_id=current_user.id, employer_id=current_user.get_employer_id(), action="UPDATE", resource_type="Appointment", resource_id=str(id), details=f"Champs: {', '.join(update_data.keys())}")
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
    audit_service.log(db=db, user_id=current_user.id, employer_id=current_user.get_employer_id(), action="DELETE", resource_type="Appointment", resource_id=str(id))
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

@router.get("/patient/{patient_id}", response_model=List[schemas.AppointmentOut])
def get_patient_appointments(
    patient_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    assert_patient_access(patient_id, current_user, db)
    return db.query(models.Appointment).filter(models.Appointment.patient_id == patient_id).order_by(models.Appointment.datetime_start.desc()).all()


@router.get("/check-conflicts")
def check_conflicts(
    datetime_start: str = Query(...),
    duration_minutes: int = Query(30),
    exclude_id: Optional[int] = Query(None),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("agenda"))
):
    """Vérifie les chevauchements de créneaux avant création/modification."""
    try:
        dt = datetime.fromisoformat(datetime_start.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        raise HTTPException(status_code=422, detail="Format datetime invalide")
    conflicts = _find_conflicts(db, current_user.get_employer_id(), dt, duration_minutes, exclude_id)
    return {
        "has_conflict": len(conflicts) > 0,
        "conflicts": [
            {
                "id": c.id,
                "patient_name": c.patient_name,
                "datetime_start": c.datetime_start.isoformat(),
                "duration_minutes": c.duration_minutes,
            }
            for c in conflicts
        ],
    }


@router.post("/{appointment_id}/remind")
def send_individual_reminder(
    appointment_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("agenda"))
):
    """Envoie un rappel SMS/WhatsApp pour un rendez-vous spécifique."""
    appt = db.query(models.Appointment).filter(
        models.Appointment.id == appointment_id,
        models.Appointment.employer_id == current_user.get_employer_id()
    ).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Rendez-vous introuvable")
    if not appt.patient_id:
        raise HTTPException(status_code=422, detail="Aucun patient lié à ce rendez-vous")

    success = notification_service.send_appointment_reminder(db, appointment_id)
    if not success:
        raise HTTPException(status_code=422, detail="Rappel impossible : numéro de téléphone manquant ou erreur d'envoi")
    return {"status": "success", "message": "Rappel envoyé", "appointment_id": appointment_id}


@router.get("/multi-practitioner")
def get_multi_practitioner_appointments(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("agenda"))
):
    """Vue multi-praticien (PREMIUM/ELITE). Retourne les RDV groupés par dentiste."""
    from backend.routers.team import _get_plan
    owner = db.query(models.User).filter(models.User.id == current_user.get_employer_id()).first()
    plan = _get_plan(owner) if owner else "GOLD"
    if plan == "GOLD":
        raise HTTPException(status_code=403, detail="Vue multi-praticien disponible à partir de PREMIUM")

    emp_id = current_user.get_employer_id()

    # Récupère tous les dentistes du cabinet
    dentists = db.query(models.User).filter(
        models.User.employer_id == emp_id,
        models.User.role == models.UserRole.DENTISTE,
        models.User.approval_status == models.ApprovalStatus.APPROVED,
    ).all()
    # Inclut le propriétaire principal (dentiste principal)
    owner_user = db.query(models.User).filter(models.User.id == emp_id).first()
    all_dentists = ([owner_user] if owner_user else []) + list(dentists)

    # Filtres de date
    q_base = db.query(models.Appointment).filter(models.Appointment.employer_id == emp_id)
    if start_date:
        q_base = q_base.filter(models.Appointment.datetime_start >= datetime.fromisoformat(start_date.replace("Z", "+00:00")))
    if end_date:
        q_base = q_base.filter(models.Appointment.datetime_start <= datetime.fromisoformat(end_date.replace("Z", "+00:00")))
    all_appts = q_base.order_by(models.Appointment.datetime_start.asc()).all()

    # Pour l'instant tous les RDV appartiennent au cabinet; on les groupe par employer_id
    # (structure prête pour when individual-dentist tracking is added)
    result = []
    for dentist in all_dentists:
        result.append({
            "dentist_id": dentist.id,
            "dentist_name": dentist.nom_complet or dentist.email,
            "appointments": [
                {
                    "id": a.id,
                    "patient_name": a.patient_name,
                    "patient_id": a.patient_id,
                    "datetime_start": a.datetime_start.isoformat(),
                    "duration_minutes": a.duration_minutes,
                    "motif": a.motif,
                    "status": a.status,
                    "scheduling_type": a.scheduling_type,
                    "reminder_sent": a.reminder_sent,
                }
                for a in all_appts
            ] if dentist.id == emp_id else [],  # RDV du praticien principal seulement pour l'instant
        })

    return {"plan": plan, "dentists": result, "total_appointments": len(all_appts)}
