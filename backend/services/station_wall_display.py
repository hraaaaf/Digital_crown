from __future__ import annotations

from datetime import datetime, timedelta, timezone
import re

from sqlalchemy.orm import Session

from backend import models
from backend.services.station_arrival_bridge import cabinet_local_day_bounds

WALL_CALL_TTL_SECONDS = 20
WALL_DISPLAY_MAX_ENTRIES = 8
WALL_IDENTITY_MODES = {"initials", "full_name", "number_only"}


def _initials_from_text(value: str | None) -> str:
    tokens = [token for token in re.split(r"\s+", (value or "").strip()) if token]
    if not tokens:
        return "P."
    selected = tokens[:1] if len(tokens) == 1 else [tokens[0], tokens[-1]]
    return " ".join(f"{token[0].upper()}." for token in selected if token)


def public_full_name(appointment: models.Appointment) -> str:
    patient = appointment.patient
    if patient is not None:
        return " ".join(part for part in [patient.prenom or "", patient.nom or ""] if part).strip()
    return (appointment.patient_name or "").strip()


def public_initials(appointment: models.Appointment) -> str:
    return _initials_from_text(public_full_name(appointment))


def wall_identity_mode(db: Session, employer_id: int) -> str:
    config = db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == employer_id).first()
    value = str(getattr(config, "wall_display_identity_mode", "initials") or "initials") if config else "initials"
    return value if value in WALL_IDENTITY_MODES else "initials"


def public_identity_label(appointment: models.Appointment, mode: str) -> str | None:
    if mode == "number_only":
        return None
    if mode == "full_name":
        value = public_full_name(appointment)
        return value or public_initials(appointment)
    return public_initials(appointment)


def waiting_appointments(
    db: Session,
    *,
    employer_id: int,
    now: datetime | None = None,
) -> list[models.Appointment]:
    start, end = cabinet_local_day_bounds(now)
    return (
        db.query(models.Appointment)
        .filter(
            models.Appointment.employer_id == employer_id,
            models.Appointment.deleted_at.is_(None),
            models.Appointment.datetime_start >= start,
            models.Appointment.datetime_start < end,
            models.Appointment.status == models.AppointmentStatus.EN_SALLE_ATTENTE,
        )
        .order_by(models.Appointment.datetime_start.asc(), models.Appointment.id.asc())
        .all()
    )


def serialize_public_waiting(appointment: models.Appointment, mode: str) -> dict:
    return {
        "ticketNumber": int(appointment.ticket_number),
        "identityLabel": public_identity_label(appointment, mode),
    }



def bounded_public_waiting_entries(waiting: list[models.Appointment], *, mode: str = "initials") -> list[dict]:
    result: list[dict] = []
    for appointment in waiting:
        try:
            ticket_number = int(appointment.ticket_number)
        except (TypeError, ValueError):
            continue
        if ticket_number < 1 or ticket_number > 999:
            continue
        duplicate = any(
            other.id != appointment.id and other.ticket_number == appointment.ticket_number
            for other in waiting
        )
        if duplicate:
            continue
        result.append(serialize_public_waiting(appointment, mode))
        if len(result) >= WALL_DISPLAY_MAX_ENTRIES:
            break
    return result



def latest_active_wall_call(
    db: Session,
    *,
    employer_id: int,
    mode: str = "initials",
    now: datetime | None = None,
) -> dict | None:
    current = now or datetime.utcnow()
    local_start, local_end = cabinet_local_day_bounds(datetime.now())
    event = (
        db.query(models.AuditLog)
        .filter(
            models.AuditLog.employer_id == employer_id,
            models.AuditLog.action == "STATION_WALL_PATIENT_CALLED",
            models.AuditLog.resource_type == "Appointment",
            models.AuditLog.timestamp > current - timedelta(seconds=WALL_CALL_TTL_SECONDS),
        )
        .order_by(models.AuditLog.timestamp.desc(), models.AuditLog.id.desc())
        .first()
    )
    if event is None:
        return None

    try:
        appointment_id = int(event.resource_id or "")
    except (TypeError, ValueError):
        return None

    appointment = (
        db.query(models.Appointment)
        .filter(
            models.Appointment.id == appointment_id,
            models.Appointment.employer_id == employer_id,
            models.Appointment.deleted_at.is_(None),
            models.Appointment.datetime_start >= local_start,
            models.Appointment.datetime_start < local_end,
            models.Appointment.status == models.AppointmentStatus.EN_SALLE_ATTENTE,
            models.Appointment.ticket_number.is_not(None),
        )
        .first()
    )
    if appointment is None:
        return None

    ticket_number = int(appointment.ticket_number)
    if ticket_number < 1 or ticket_number > 999:
        return None
    collision = db.query(models.Appointment.id).filter(
        models.Appointment.employer_id == employer_id,
        models.Appointment.id != appointment.id,
        models.Appointment.deleted_at.is_(None),
        models.Appointment.datetime_start >= local_start,
        models.Appointment.datetime_start < local_end,
        models.Appointment.status == models.AppointmentStatus.EN_SALLE_ATTENTE,
        models.Appointment.ticket_number == ticket_number,
    ).first()
    if collision is not None:
        return None

    expires_at = event.timestamp + timedelta(seconds=WALL_CALL_TTL_SECONDS)
    if expires_at <= current:
        return None
    return {
        "ticketNumber": ticket_number,
        "identityLabel": public_identity_label(appointment, mode),
        "expiresAt": expires_at.replace(tzinfo=timezone.utc),
    }
