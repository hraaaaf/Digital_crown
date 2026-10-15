"""Frontdesk appointment request management — FRONTDESK-AGENDA-MVP-1."""
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List

from backend.database import get_db
from backend import models, schemas
from backend.routers.auth import get_current_user, has_permission
from backend.services.audit_service import audit_service
from backend.services.agenda_transaction_lock import lock_cabinet_booking

router = APIRouter(tags=["frontdesk"])

_PENDING = (
    models.AppointmentStatus.EN_ATTENTE_DEMANDE,
    models.AppointmentStatus.EN_ATTENTE_CONFIRM,
)


def _pending_request(db: Session, employer_id: int, appointment_id: int):
    """Caller MUST obtain lock_cabinet_booking before this tenant-scoped read."""
    return db.query(models.Appointment).filter(
        models.Appointment.id == appointment_id,
        models.Appointment.employer_id == employer_id,
        models.Appointment.deleted_at.is_(None),
    ).first()


def _cas_request_state(
    db: Session, employer_id: int, appointment_id: int,
    statuses: tuple, new_status, **fields,
) -> None:
    """Never accept stale ORM state; one winning conditional transition."""
    changed = db.query(models.Appointment).filter(
        models.Appointment.id == appointment_id,
        models.Appointment.employer_id == employer_id,
        models.Appointment.deleted_at.is_(None),
        models.Appointment.status.in_(statuses),
    ).update({"status": new_status, **fields}, synchronize_session=False)
    if changed != 1:
        db.rollback()
        raise HTTPException(status_code=409, detail="Demande déjà traitée ou modifiée.")


def _frontdesk_audit(db: Session, user, appointment, action: str) -> None:
    # Same COMMIT as the corresponding clinical state change.
    db.add(models.AuditLog(
        user_id=user.id,
        employer_id=user.get_employer_id(),
        action=action,
        resource_type="APPOINTMENT",
        resource_id=str(appointment.id),
        severity="INFO",
        details=f"Demande de rendez-vous : {appointment.patient_name}",
    ))



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

    appointment = models.Appointment(
        patient_name=f"{req.last_name} {req.first_name}",
        datetime_start=req.requested_start,
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
    db.flush()
    _frontdesk_audit(db, current_user, appointment, "FRONTDESK_REQUEST_CREATED")
    db.commit()
    db.refresh(appointment)

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
    lock_cabinet_booking(db, employer_id)
    appt = _pending_request(db, employer_id, appointment_id)
    if appt is None:
        raise HTTPException(status_code=404, detail="Rendez-vous introuvable.")
    if appt.status != schemas.AppointmentStatus.EN_ATTENTE_DEMANDE:
        raise HTTPException(status_code=409, detail="Transition de demande déjà traitée.")
    _cas_request_state(
        db, employer_id, appt.id,
        (schemas.AppointmentStatus.EN_ATTENTE_DEMANDE,),
        schemas.AppointmentStatus.EN_ATTENTE_CONFIRM,
    )
    _frontdesk_audit(db, current_user, appt, "FRONTDESK_CONFIRMATION_REQUESTED")
    db.commit()
    db.refresh(appt)

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
    """Confirm only a STILL-pending, non-expired request under cabinet lock."""
    if not has_permission(current_user, "agenda"):
        raise HTTPException(status_code=403, detail="Permission refusée.")
    employer_id = current_user.get_employer_id()
    # Lock FIRST. A stale SELECT prior to this lock could resurrect a
    # rejected/expired request when another worker commits concurrently.
    lock_cabinet_booking(db, employer_id)
    appt = _pending_request(db, employer_id, appointment_id)
    if appt is None:
        raise HTTPException(status_code=404, detail="Rendez-vous introuvable.")
    if appt.status not in _PENDING:
        raise HTTPException(status_code=409, detail="Demande déjà traitée.")
    if appt.expires_at and appt.expires_at <= datetime.utcnow():
        _cas_request_state(
            db, employer_id, appt.id, _PENDING,
            schemas.AppointmentStatus.EXPIRE,
            expires_at=datetime.utcnow(),
        )
        _frontdesk_audit(db, current_user, appt, "FRONTDESK_APPOINTMENT_EXPIRED")
        db.commit()
        raise HTTPException(status_code=410, detail="Demande expirée.")

    from backend.routers.appointments import (
        _find_conflicts, _resolve_practitioner_id,
    )
    from backend.services.agenda_availability import validate_appointment_availability
    # Never confirm an unassigned legacy request as a GLOBAL blocking slot.
    # Dentists default to themselves; secretaries must supply a practitioner
    # through the canonical Agenda before final confirmation.
    practitioner_id = _resolve_practitioner_id(
        db, employer_id, current_user, appt.praticien_id,
    )
    availability_error = validate_appointment_availability(
        db, employer_id, appt.datetime_start, appt.duration_minutes,
        appt.scheduling_type, practitioner_id=practitioner_id,
    )
    if availability_error:
        raise HTTPException(status_code=422, detail=availability_error)
    if _find_conflicts(
        db, employer_id, practitioner_id, appt.datetime_start,
        appt.duration_minutes, exclude_id=appt.id,
    ):
        raise HTTPException(status_code=409, detail="Créneau déjà occupé.")
    now = datetime.utcnow()
    _cas_request_state(
        db, employer_id, appt.id, _PENDING,
        schemas.AppointmentStatus.CONFIRME,
        praticien_id=practitioner_id,
        confirmed_by_id=current_user.id,
        confirmed_at=now,
    )
    _frontdesk_audit(db, current_user, appt, "FRONTDESK_APPOINTMENT_CONFIRMED")
    db.commit()
    db.refresh(appt)
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
    if not has_permission(current_user, "agenda"):
        raise HTTPException(status_code=403, detail="Permission refusée.")
    employer_id = current_user.get_employer_id()
    lock_cabinet_booking(db, employer_id)
    appt = _pending_request(db, employer_id, appointment_id)
    if appt is None:
        raise HTTPException(status_code=404, detail="Rendez-vous introuvable.")
    _cas_request_state(
        db, employer_id, appointment_id, _PENDING,
        schemas.AppointmentStatus.REFUSE, expires_at=datetime.utcnow(),
    )
    _frontdesk_audit(db, current_user, appt, "FRONTDESK_APPOINTMENT_REJECTED")
    db.commit()
    return {"id": appt.id, "status": schemas.AppointmentStatus.REFUSE.value}


@router.post("/appointments/{appointment_id}/expire")
async def expire_appointment(
    appointment_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not has_permission(current_user, "agenda"):
        raise HTTPException(status_code=403, detail="Permission refusée.")
    employer_id = current_user.get_employer_id()
    lock_cabinet_booking(db, employer_id)
    appt = _pending_request(db, employer_id, appointment_id)
    if appt is None:
        raise HTTPException(status_code=404, detail="Rendez-vous introuvable.")
    _cas_request_state(
        db, employer_id, appointment_id, _PENDING,
        schemas.AppointmentStatus.EXPIRE, expires_at=datetime.utcnow(),
    )
    _frontdesk_audit(db, current_user, appt, "FRONTDESK_APPOINTMENT_EXPIRED")
    db.commit()
    return {"id": appt.id, "status": schemas.AppointmentStatus.EXPIRE.value}
