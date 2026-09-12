from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from datetime import datetime, timedelta

from backend import models, schemas, database
from backend.routers.auth import get_current_user, require_permission
from backend.utils.access_control import assert_patient_access
from backend.services.elite_manager import elite_manager
from backend.services.notification_service import notification_service
from backend.services.audit_service import audit_service
from backend.services.agenda_availability import validate_appointment_availability

router = APIRouter(tags=["Appointments"])


def _naive_datetime(value: datetime) -> datetime:
    """Normalize API datetimes to the naive local representation used by the agenda DB."""
    return value.replace(tzinfo=None) if value.tzinfo is not None else value


def _is_exact_time(value) -> bool:
    return getattr(value, "value", value) == "EXACT_TIME"


def _is_assignable_practitioner(user: models.User, employer_id: int) -> bool:
    if not user.is_active or user.approval_status != models.ApprovalStatus.APPROVED.value:
        return False
    if user.id == employer_id:
        return user.role in (models.UserRole.DENTISTE, models.UserRole.ADMIN)
    return user.employer_id == employer_id and user.role == models.UserRole.DENTISTE


def _validate_practitioner(db: Session, employer_id: int, practitioner_id: int) -> models.User:
    practitioner = db.query(models.User).filter(models.User.id == practitioner_id).first()
    if not practitioner or not _is_assignable_practitioner(practitioner, employer_id):
        raise HTTPException(status_code=403, detail="Praticien non assignable dans ce cabinet")
    return practitioner


def _resolve_practitioner_id(
    db: Session,
    employer_id: int,
    current_user: models.User,
    requested_id: Optional[int],
) -> int:
    if requested_id is not None:
        _validate_practitioner(db, employer_id, requested_id)
        return requested_id
    if _is_assignable_practitioner(current_user, employer_id):
        return current_user.id
    raise HTTPException(status_code=422, detail="praticien_id est requis pour ce rendez-vous")


def _conflict_detail(conflicts: list) -> dict:
    return {
        "message": "Créneau en conflit avec un autre rendez-vous",
        "conflicts": [
            {
                "id": conflict.id,
                "patient_id": conflict.patient_id,
                "patient_name": conflict.patient_name,
                "praticien_id": conflict.praticien_id,
                "datetime_start": conflict.datetime_start.isoformat(),
                "duration_minutes": conflict.duration_minutes,
            }
            for conflict in conflicts
        ],
    }


def _find_conflicts(
    db: Session,
    employer_id: int,
    practitioner_id: Optional[int],
    datetime_start: datetime,
    duration_minutes: int,
    exclude_id: int | None = None,
) -> list:
    """Return overlapping exact-time appointments for one practitioner.

    Legacy appointments with ``praticien_id = NULL`` are global blockers. A legacy
    candidate (``practitioner_id is None``) also conflicts with every overlapping
    appointment in the cabinet.
    """
    datetime_start = _naive_datetime(datetime_start)
    end = datetime_start + timedelta(minutes=duration_minutes)
    window_start = datetime_start - timedelta(hours=4)
    q = db.query(models.Appointment).filter(
        models.Appointment.employer_id == employer_id,
        models.Appointment.status != models.AppointmentStatus.ANNULE,
        models.Appointment.scheduling_type == models.SchedulingType.EXACT_TIME,
        models.Appointment.datetime_start < end,
        models.Appointment.datetime_start >= window_start,
    )
    if practitioner_id is not None:
        q = q.filter(
            or_(
                models.Appointment.praticien_id == practitioner_id,
                models.Appointment.praticien_id.is_(None),
            )
        )
    if exclude_id:
        q = q.filter(models.Appointment.id != exclude_id)
    rows = q.all()
    return [
        appointment
        for appointment in rows
        if _naive_datetime(appointment.datetime_start) + timedelta(minutes=appointment.duration_minutes) > datetime_start
        and _naive_datetime(appointment.datetime_start) < end
    ]


def _appointments_overlap(start_a: datetime, duration_a: int, start_b: datetime, duration_b: int) -> bool:
    start_a = _naive_datetime(start_a)
    start_b = _naive_datetime(start_b)
    return start_a < start_b + timedelta(minutes=duration_b) and start_b < start_a + timedelta(minutes=duration_a)


@router.get("/", response_model=List[schemas.AppointmentOut])
def get_appointments(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("agenda")),
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
    current_user: models.User = Depends(require_permission("agenda")),
):
    if appt.patient_id:
        assert_patient_access(appt.patient_id, current_user, db)

    employer_id = current_user.get_employer_id()
    practitioner_id = _resolve_practitioner_id(db, employer_id, current_user, appt.praticien_id)
    normalized_start = _naive_datetime(appt.datetime_start)
    availability_error = validate_appointment_availability(
        db, employer_id, normalized_start, appt.duration_minutes, appt.scheduling_type
    )
    if availability_error:
        raise HTTPException(status_code=422, detail=availability_error)

    if _is_exact_time(appt.scheduling_type):
        conflicts = _find_conflicts(
            db,
            employer_id,
            practitioner_id,
            normalized_start,
            appt.duration_minutes,
        )
        if conflicts:
            raise HTTPException(status_code=409, detail=_conflict_detail(conflicts))

    appt_data = appt.model_dump()
    appt_data["datetime_start"] = normalized_start
    appt_data["employer_id"] = employer_id
    appt_data["praticien_id"] = practitioner_id
    db_appt = models.Appointment(**appt_data)
    db.add(db_appt)
    db.commit()
    db.refresh(db_appt)
    audit_service.log(
        db=db,
        user_id=current_user.id,
        employer_id=employer_id,
        action="CREATE",
        resource_type="Appointment",
        resource_id=str(db_appt.id),
        details=f"RDV patient {appt.patient_id}",
    )
    return db_appt


@router.put("/{id}", response_model=schemas.AppointmentOut)
def update_appointment(
    id: int,
    appt_update: schemas.AppointmentUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("agenda")),
):
    employer_id = current_user.get_employer_id()
    db_appt = db.query(models.Appointment).filter(
        models.Appointment.id == id,
        models.Appointment.employer_id == employer_id,
    ).first()
    if not db_appt:
        raise HTTPException(status_code=404, detail="Rendez-vous introuvable")

    update_data = appt_update.model_dump(exclude_unset=True)
    if "patient_id" in update_data and update_data["patient_id"] is not None:
        assert_patient_access(update_data["patient_id"], current_user, db)

    if "praticien_id" in update_data:
        if update_data["praticien_id"] is None:
            raise HTTPException(status_code=422, detail="praticien_id ne peut pas être supprimé d'un rendez-vous existant")
        _validate_practitioner(db, employer_id, update_data["praticien_id"])

    if any(key in update_data for key in ("datetime_start", "duration_minutes", "scheduling_type", "praticien_id")):
        effective_start = _naive_datetime(update_data.get("datetime_start", db_appt.datetime_start))
        effective_duration = update_data.get("duration_minutes", db_appt.duration_minutes)
        effective_type = update_data.get("scheduling_type", db_appt.scheduling_type)
        effective_practitioner = update_data.get("praticien_id", db_appt.praticien_id)
        availability_error = validate_appointment_availability(
            db, employer_id, effective_start, effective_duration, effective_type
        )
        if availability_error:
            raise HTTPException(status_code=422, detail=availability_error)

        if _is_exact_time(effective_type):
            conflicts = _find_conflicts(
                db,
                employer_id,
                effective_practitioner,
                effective_start,
                effective_duration,
                exclude_id=id,
            )
            if conflicts:
                raise HTTPException(status_code=409, detail=_conflict_detail(conflicts))

        if "datetime_start" in update_data and update_data["datetime_start"] is not None:
            update_data["datetime_start"] = effective_start

    for key, value in update_data.items():
        setattr(db_appt, key, value)

    db.commit()
    db.refresh(db_appt)
    audit_service.log(
        db=db,
        user_id=current_user.id,
        employer_id=employer_id,
        action="UPDATE",
        resource_type="Appointment",
        resource_id=str(id),
        details=f"Champs: {', '.join(update_data.keys())}",
    )
    return db_appt


@router.delete("/{id}")
def delete_appointment(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("agenda")),
):
    employer_id = current_user.get_employer_id()
    db_appt = db.query(models.Appointment).filter(
        models.Appointment.id == id,
        models.Appointment.employer_id == employer_id,
    ).first()
    if not db_appt:
        raise HTTPException(status_code=404, detail="Rendez-vous introuvable")
    db.delete(db_appt)
    db.commit()
    audit_service.log(
        db=db,
        user_id=current_user.id,
        employer_id=employer_id,
        action="DELETE",
        resource_type="Appointment",
        resource_id=str(id),
    )
    return {"status": "success"}


@router.post("/bulk", response_model=List[schemas.AppointmentOut])
def create_bulk_appointments(
    payload: schemas.AppointmentBulkCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("agenda")),
):
    employer_id = current_user.get_employer_id()
    prepared = []

    for index, item in enumerate(payload.appointments):
        if item.patient_id:
            assert_patient_access(item.patient_id, current_user, db)
        practitioner_id = _resolve_practitioner_id(db, employer_id, current_user, item.praticien_id)
        normalized_start = _naive_datetime(item.datetime_start)
        availability_error = validate_appointment_availability(
            db, employer_id, normalized_start, item.duration_minutes, item.scheduling_type
        )
        if availability_error:
            raise HTTPException(status_code=422, detail=availability_error)
        if _is_exact_time(item.scheduling_type):
            conflicts = _find_conflicts(
                db,
                employer_id,
                practitioner_id,
                normalized_start,
                item.duration_minutes,
            )
            if conflicts:
                raise HTTPException(status_code=409, detail=_conflict_detail(conflicts))
            for previous_index, previous in enumerate(prepared):
                if (
                    _is_exact_time(previous["item"].scheduling_type)
                    and previous["praticien_id"] == practitioner_id
                    and _appointments_overlap(
                        previous["datetime_start"],
                        previous["item"].duration_minutes,
                        normalized_start,
                        item.duration_minutes,
                    )
                ):
                    raise HTTPException(
                        status_code=409,
                        detail={
                            "message": "Conflit interne au lot de rendez-vous",
                            "indexes": [previous_index, index],
                            "praticien_id": practitioner_id,
                        },
                    )
        prepared.append({"item": item, "praticien_id": practitioner_id, "datetime_start": normalized_start})

    created_appts = []
    for prepared_item in prepared:
        item = prepared_item["item"]
        db_appt = models.Appointment(
            patient_name=item.patient_name,
            patient_id=item.patient_id,
            praticien_id=prepared_item["praticien_id"],
            datetime_start=prepared_item["datetime_start"],
            duration_minutes=item.duration_minutes,
            notes=item.notes,
            status=item.status,
            scheduling_type=item.scheduling_type,
            employer_id=employer_id,
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
    current_user: models.User = Depends(require_permission("agenda")),
):
    sent_count = notification_service.cron_send_reminders(db)
    return {"status": "success", "reminders_sent": sent_count}


@router.get("/suggest/{patient_id}", response_model=schemas.AppointmentSuggestionOut)
async def suggest_appointment(
    patient_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("agenda")),
):
    assert_patient_access(patient_id, current_user, db)
    plan = await elite_manager.get_treatment_plan(db, patient_id)
    phases = plan.get("phases", {}) if isinstance(plan, dict) else {}
    phase_order = ["URGENCE", "INITIALE", "CONSERVATRICE", "REHABILITATION", "MAINTENANCE"]
    for phase in phase_order:
        acts = phases.get(phase, [])
        if acts:
            act = acts[0]
            suggested = act.get("suggested_act", "Consultation")
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
                notes=f"Suggestion auto depuis le plan (phase {phase})",
            )
    return schemas.AppointmentSuggestionOut(
        patient_id=patient_id,
        motif="Consultation & Bilan de routine",
        duration_minutes=15,
        notes="Aucun acte pending – suggestion générique",
    )


@router.get("/patient/{patient_id}", response_model=List[schemas.AppointmentOut])
def get_patient_appointments(
    patient_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    assert_patient_access(patient_id, current_user, db)
    return db.query(models.Appointment).filter(
        models.Appointment.patient_id == patient_id,
        models.Appointment.employer_id == current_user.get_employer_id(),
    ).order_by(models.Appointment.datetime_start.desc()).all()


@router.get("/check-conflicts")
def check_conflicts(
    datetime_start: str = Query(...),
    duration_minutes: int = Query(30),
    praticien_id: Optional[int] = Query(None),
    exclude_id: Optional[int] = Query(None),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("agenda")),
):
    try:
        dt = _naive_datetime(datetime.fromisoformat(datetime_start.replace("Z", "+00:00")))
    except ValueError:
        raise HTTPException(status_code=422, detail="Format datetime invalide")
    employer_id = current_user.get_employer_id()
    practitioner_id = _resolve_practitioner_id(db, employer_id, current_user, praticien_id)
    conflicts = _find_conflicts(db, employer_id, practitioner_id, dt, duration_minutes, exclude_id)
    return {
        "has_conflict": bool(conflicts),
        "praticien_id": practitioner_id,
        "conflicts": [
            {
                "id": c.id,
                "patient_name": c.patient_name,
                "praticien_id": c.praticien_id,
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
    current_user: models.User = Depends(require_permission("agenda")),
):
    appt = db.query(models.Appointment).filter(
        models.Appointment.id == appointment_id,
        models.Appointment.employer_id == current_user.get_employer_id(),
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
    current_user: models.User = Depends(require_permission("agenda")),
):
    from backend.routers.team import _get_plan

    employer_id = current_user.get_employer_id()
    owner = db.query(models.User).filter(models.User.id == employer_id).first()
    plan = _get_plan(owner) if owner else "GOLD"
    if plan == "GOLD":
        raise HTTPException(status_code=403, detail="Vue multi-praticien disponible à partir de PREMIUM")

    dentists = db.query(models.User).filter(
        models.User.employer_id == employer_id,
        models.User.role == models.UserRole.DENTISTE,
        models.User.is_active.is_(True),
        models.User.approval_status == models.ApprovalStatus.APPROVED.value,
    ).all()
    all_dentists = list(dentists)
    if owner and _is_assignable_practitioner(owner, employer_id):
        all_dentists.insert(0, owner)

    q_base = db.query(models.Appointment).filter(models.Appointment.employer_id == employer_id)
    if start_date:
        q_base = q_base.filter(models.Appointment.datetime_start >= datetime.fromisoformat(start_date.replace("Z", "+00:00")))
    if end_date:
        q_base = q_base.filter(models.Appointment.datetime_start <= datetime.fromisoformat(end_date.replace("Z", "+00:00")))
    all_appts = q_base.order_by(models.Appointment.datetime_start.asc()).all()

    def serialize(a: models.Appointment) -> dict:
        return {
            "id": a.id,
            "patient_name": a.patient_name,
            "patient_id": a.patient_id,
            "praticien_id": a.praticien_id,
            "datetime_start": a.datetime_start.isoformat(),
            "duration_minutes": a.duration_minutes,
            "motif": a.motif,
            "status": a.status,
            "scheduling_type": a.scheduling_type,
            "reminder_sent": a.reminder_sent,
        }

    result = [
        {
            "dentist_id": dentist.id,
            "dentist_name": dentist.nom_complet or dentist.email,
            "appointments": [serialize(a) for a in all_appts if a.praticien_id == dentist.id],
        }
        for dentist in all_dentists
    ]
    legacy = [serialize(a) for a in all_appts if a.praticien_id is None]
    return {
        "plan": plan,
        "dentists": result,
        "legacy_unassigned": legacy,
        "total_appointments": len(all_appts),
    }
