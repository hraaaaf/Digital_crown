"""Frontdesk appointment request management — FRONTDESK-AGENDA-MVP-1."""
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List

from backend.database import get_db
from backend import models, schemas
from backend.routers.auth import get_current_user, has_permission
from backend.services.audit_service import audit_service
from backend.services.agenda_write_lock import lock_cabinet_appointment_writes
from backend.services.agenda_availability import validate_appointment_availability
from backend.services.agenda_resource_conflicts import assert_resource_available
from backend.routers.appointments import _find_conflicts, _naive_datetime

router = APIRouter(tags=["frontdesk"])


@router.post("/frontdesk/appointment-request")
async def create_appointment_request(
    req: schemas.FrontdeskCreateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Create a new frontdesk appointment request (status=EN_ATTENTE_DEMANDE)."""
    if not has_permission(current_user, "agenda"):
        raise HTTPException(status_code=403, detail="Permission refusée.")

    employer_id = current_user.get_employer_id()
    # The existing Agenda oracle treats EN_ATTENTE_* as capacity blockers;
    # preserve that contract rather than inventing a new pending policy.
    lock_cabinet_appointment_writes(db, employer_id)
    start = _naive_datetime(req.requested_start)
    unavailable = validate_appointment_availability(
        db, employer_id, start, req.duration_minutes, models.SchedulingType.EXACT_TIME,
        practitioner_id=None,
    )
    if unavailable:
        raise HTTPException(status_code=422, detail=unavailable)
    if _find_conflicts(db, employer_id, None, start, req.duration_minutes):
        raise HTTPException(status_code=409, detail="Créneau déjà occupé")

    appointment = models.Appointment(
        patient_name=f"{req.last_name} {req.first_name}",
        datetime_start=start,
        duration_minutes=req.duration_minutes,
        motif=req.appointment_reason,
        status=schemas.AppointmentStatus.EN_ATTENTE_DEMANDE,
        scheduling_type=schemas.SchedulingType.EXACT_TIME,
        source=req.source,
        phone=req.phone,
        notes=req.notes,
        employer_id=employer_id,
        expires_at=datetime.utcnow() + timedelta(minutes=30),
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    audit_service.log(
        db=db,
        user_id=current_user.id,
        employer_id=employer_id,
        action="FRONTDESK_REQUEST_CREATED",
        resource_type="APPOINTMENT",
        resource_id=str(appointment.id),
        severity="INFO",
        details=f"Demande RDV créée : {req.last_name} {req.first_name}",
    )

    return {
        "id": appointment.id,
        "patient_name": appointment.patient_name,
        "phone": appointment.phone,
        "datetime_start": appointment.datetime_start,
        "motif": appointment.motif,
        "status": appointment.status.value,
        "source": appointment.source,
        "created_at": appointment.created_at.isoformat(),
    }


@router.get("/appointments/pending")
async def list_pending_appointments(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """List all pending appointment requests for the current employer."""
    if not has_permission(current_user, "agenda"):
        raise HTTPException(status_code=403, detail="Permission refusée.")

    employer_id = current_user.get_employer_id()

    appointments = (
        db.query(models.Appointment)
        .filter(
            models.Appointment.employer_id == employer_id,
            models.Appointment.status.in_(
                [
                    schemas.AppointmentStatus.EN_ATTENTE_DEMANDE,
                    schemas.AppointmentStatus.EN_ATTENTE_CONFIRM,
                ]
            ),
        )
        .order_by(models.Appointment.datetime_start)
        .all()
    )

    return [
        {
            "id": appt.id,
            "patient_name": appt.patient_name,
            "phone": appt.phone,
            "datetime_start": appt.datetime_start,
            "duration_minutes": appt.duration_minutes,
            "motif": appt.motif,
            "status": appt.status.value,
            "source": appt.source,
            "expires_at": appt.expires_at.isoformat() if appt.expires_at else None,
            "created_at": appt.created_at.isoformat(),
        }
        for appt in appointments
    ]


@router.post("/appointments/{appointment_id}/request-confirmation")
async def request_patient_confirmation(
    appointment_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Transition appointment from EN_ATTENTE_DEMANDE to EN_ATTENTE_CONFIRM."""
    if not has_permission(current_user, "agenda"):
        raise HTTPException(status_code=403, detail="Permission refusée.")

    employer_id = current_user.get_employer_id()
    # Serialize status transitions with CONFIRM and all appointment producers.
    lock_cabinet_appointment_writes(db, employer_id)
    appt = db.query(models.Appointment).filter(
        models.Appointment.id == appointment_id,
        models.Appointment.employer_id == employer_id,
    ).first()

    if not appt:
        raise HTTPException(status_code=404, detail="Rendez-vous introuvable.")

    if appt.status != schemas.AppointmentStatus.EN_ATTENTE_DEMANDE:
        raise HTTPException(
            status_code=409,
            detail=f"Transition invalide : {appt.status.value} → EN_ATTENTE_CONFIRM",
        )

    appt.status = schemas.AppointmentStatus.EN_ATTENTE_CONFIRM
    db.commit()

    audit_service.log(
        db=db,
        user_id=current_user.id,
        employer_id=employer_id,
        action="FRONTDESK_CONFIRMATION_REQUESTED",
        resource_type="APPOINTMENT",
        resource_id=str(appt.id),
        severity="INFO",
        details=f"Confirmation demandée au patient : {appt.patient_name}",
    )

    message_template = f"""Bonjour {appt.patient_name.split()[0]}, votre demande de rendez-vous
pour le {appt.datetime_start.strftime('%d/%m/%Y')} à {appt.datetime_start.strftime('%H:%M')} est disponible.
Merci de confirmer votre présence."""

    return {
        "status": appt.status.value,
        "message_template": message_template,
        "note": "Message template copiable — WhatsApp intégration à venir",
    }


@router.post("/appointments/{appointment_id}/confirm")
async def confirm_appointment(
    appointment_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Confirm appointment: EN_ATTENTE_DEMANDE or EN_ATTENTE_CONFIRM → CONFIRME."""
    if not has_permission(current_user, "agenda"):
        raise HTTPException(status_code=403, detail="Permission refusée.")

    employer_id = current_user.get_employer_id()
    # Locks are per cabinet across Frontdesk, Agenda, Bot and Patient Companion.
    # Re-read status and effective capacity only after acquiring the lock.
    lock_cabinet_appointment_writes(db, employer_id)
    appt = db.query(models.Appointment).filter(
        models.Appointment.id == appointment_id,
        models.Appointment.employer_id == employer_id,
        models.Appointment.deleted_at.is_(None),
    ).first()

    if not appt:
        raise HTTPException(status_code=404, detail="Rendez-vous introuvable.")

    if appt.status not in [
        schemas.AppointmentStatus.EN_ATTENTE_DEMANDE,
        schemas.AppointmentStatus.EN_ATTENTE_CONFIRM,
    ]:
        raise HTTPException(status_code=409, detail=f"Statut invalide pour confirmation: {appt.status.value}")

    if appt.expires_at and appt.expires_at < datetime.utcnow():
        appt.status = schemas.AppointmentStatus.EXPIRE
        db.commit()
        raise HTTPException(status_code=410, detail="Demande expirée.")

    if appt.scheduling_type == models.SchedulingType.EXACT_TIME:
        unavailable = validate_appointment_availability(
            db, employer_id, appt.datetime_start, appt.duration_minutes,
            models.SchedulingType.EXACT_TIME, practitioner_id=appt.praticien_id,
        )
        if unavailable:
            raise HTTPException(status_code=422, detail=unavailable)
        if _find_conflicts(
            db, employer_id, appt.praticien_id, appt.datetime_start,
            appt.duration_minutes, exclude_id=appt.id,
        ):
            raise HTTPException(status_code=409, detail="Créneau déjà occupé")
        assert_resource_available(
            db, employer_id=employer_id, resource_id=appt.resource_id,
            datetime_start=appt.datetime_start, duration_minutes=appt.duration_minutes,
            exclude_appointment_id=appt.id,
        )

    appt.status = schemas.AppointmentStatus.CONFIRME
    appt.confirmed_by_id = current_user.id
    appt.confirmed_at = datetime.utcnow()
    db.commit()

    audit_service.log(
        db=db,
        user_id=current_user.id,
        employer_id=employer_id,
        action="FRONTDESK_APPOINTMENT_CONFIRMED",
        resource_type="APPOINTMENT",
        resource_id=str(appt.id),
        severity="INFO",
        details=f"Rendez-vous confirmé : {appt.patient_name}",
    )

    return {
        "id": appt.id,
        "status": appt.status.value,
        "confirmed_by_id": appt.confirmed_by_id,
        "confirmed_at": appt.confirmed_at.isoformat() if appt.confirmed_at else None,
    }


@router.post("/appointments/{appointment_id}/reject")
async def reject_appointment(
    appointment_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Reject appointment: EN_ATTENTE_* → REFUSE."""
    if not has_permission(current_user, "agenda"):
        raise HTTPException(status_code=403, detail="Permission refusée.")

    employer_id = current_user.get_employer_id()
    # Serialize status transitions with CONFIRM and all appointment producers.
    lock_cabinet_appointment_writes(db, employer_id)
    appt = db.query(models.Appointment).filter(
        models.Appointment.id == appointment_id,
        models.Appointment.employer_id == employer_id,
    ).first()

    if not appt:
        raise HTTPException(status_code=404, detail="Rendez-vous introuvable.")

    if appt.status not in [
        schemas.AppointmentStatus.EN_ATTENTE_DEMANDE,
        schemas.AppointmentStatus.EN_ATTENTE_CONFIRM,
    ]:
        raise HTTPException(status_code=409, detail=f"Cannot reject status: {appt.status.value}")

    appt.status = schemas.AppointmentStatus.REFUSE
    appt.expires_at = datetime.utcnow()
    db.commit()

    audit_service.log(
        db=db,
        user_id=current_user.id,
        employer_id=employer_id,
        action="FRONTDESK_APPOINTMENT_REJECTED",
        resource_type="APPOINTMENT",
        resource_id=str(appt.id),
        severity="INFO",
        details=f"Rendez-vous refusé : {appt.patient_name}",
    )

    return {"id": appt.id, "status": appt.status.value}


@router.post("/appointments/{appointment_id}/expire")
async def expire_appointment(
    appointment_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Manually expire an appointment."""
    if not has_permission(current_user, "agenda"):
        raise HTTPException(status_code=403, detail="Permission refusée.")

    employer_id = current_user.get_employer_id()
    # Serialize status transitions with CONFIRM and all appointment producers.
    lock_cabinet_appointment_writes(db, employer_id)
    appt = db.query(models.Appointment).filter(
        models.Appointment.id == appointment_id,
        models.Appointment.employer_id == employer_id,
    ).first()

    if not appt:
        raise HTTPException(status_code=404, detail="Rendez-vous introuvable.")

    if appt.status not in [
        schemas.AppointmentStatus.EN_ATTENTE_DEMANDE,
        schemas.AppointmentStatus.EN_ATTENTE_CONFIRM,
    ]:
        raise HTTPException(status_code=409, detail=f"Cannot expire status: {appt.status.value}")

    appt.status = schemas.AppointmentStatus.EXPIRE
    appt.expires_at = datetime.utcnow()
    db.commit()

    audit_service.log(
        db=db,
        user_id=current_user.id,
        employer_id=employer_id,
        action="FRONTDESK_APPOINTMENT_EXPIRED",
        resource_type="APPOINTMENT",
        resource_id=str(appt.id),
        severity="INFO",
        details=f"Rendez-vous expiré : {appt.patient_name}",
    )

    return {"id": appt.id, "status": appt.status.value}


# D0 Patient Companion is mounted here only because main.py exposes this router at /api.
# Business logic stays isolated in its own module; this keeps the public contract
# /api/patient-companion/* without creating another app-level router registry.
from backend.routers import patient_companion as patient_companion
router.include_router(patient_companion.router, prefix="/patient-companion")
