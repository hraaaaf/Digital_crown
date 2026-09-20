from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend import models
from backend.models_patient_companion import PatientCompanionAccess, PatientCompanionAppointmentRef
from backend.services.agenda_availability import validate_appointment_availability
from backend.services.agenda_resource_conflicts import assert_resource_available
from backend.services.patient_companion_remote_worker import RemoteDomainResult

ACTIVE_CANCEL_BLOCKERS = {
    models.AppointmentStatus.TERMINE,
    models.AppointmentStatus.ANNULE,
}


def _reject(code: str) -> RemoteDomainResult:
    return RemoteDomainResult(status="REJECTED", response={"code": code})


def _parse_start(value) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.replace(tzinfo=None) if parsed.tzinfo is not None else parsed
    except (TypeError, ValueError):
        return None


def _opaque_ref(db: Session, access: PatientCompanionAccess, appointment: models.Appointment) -> PatientCompanionAppointmentRef:
    row = db.query(PatientCompanionAppointmentRef).filter(
        PatientCompanionAppointmentRef.employer_id == access.employer_id,
        PatientCompanionAppointmentRef.appointment_id == appointment.id,
    ).first()
    if row is None:
        row = PatientCompanionAppointmentRef(
            public_id=str(uuid.uuid4()),
            employer_id=access.employer_id,
            patient_id=access.patient_id,
            appointment_id=appointment.id,
        )
        db.add(row)
        db.flush()
    return row


def _appointment_for_ref(db: Session, access: PatientCompanionAccess, public_id: str) -> models.Appointment | None:
    try:
        uuid.UUID(str(public_id))
    except (TypeError, ValueError):
        return None
    row = db.query(PatientCompanionAppointmentRef).filter(
        PatientCompanionAppointmentRef.public_id == str(public_id),
        PatientCompanionAppointmentRef.employer_id == access.employer_id,
        PatientCompanionAppointmentRef.patient_id == access.patient_id,
    ).first()
    if row is None:
        return None
    return db.query(models.Appointment).filter(
        models.Appointment.id == row.appointment_id,
        models.Appointment.employer_id == access.employer_id,
        models.Appointment.patient_id == access.patient_id,
        models.Appointment.deleted_at.is_(None),
    ).first()


def _validate_exact_slot(db: Session, access: PatientCompanionAccess, *, start: datetime, duration: int, practitioner_id: int, resource_id: int | None, exclude_id: int | None = None) -> str | None:
    error = validate_appointment_availability(
        db, access.employer_id, start, duration, models.SchedulingType.EXACT_TIME,
        practitioner_id=practitioner_id,
    )
    if error:
        return "SLOT_UNAVAILABLE"
    end = start + __import__("datetime").timedelta(minutes=duration)
    q = db.query(models.Appointment).filter(
        models.Appointment.employer_id == access.employer_id,
        models.Appointment.deleted_at.is_(None),
        models.Appointment.status != models.AppointmentStatus.ANNULE,
        models.Appointment.scheduling_type == models.SchedulingType.EXACT_TIME,
        models.Appointment.datetime_start < end,
        models.Appointment.praticien_id == practitioner_id,
    )
    if exclude_id is not None:
        q = q.filter(models.Appointment.id != exclude_id)
    for existing in q.all():
        if existing.datetime_start + __import__("datetime").timedelta(minutes=existing.duration_minutes) > start:
            return "SLOT_CONFLICT"
    try:
        assert_resource_available(
            db,
            employer_id=access.employer_id,
            resource_id=resource_id,
            datetime_start=start,
            duration_minutes=duration,
            exclude_appointment_id=exclude_id,
        )
    except HTTPException:
        return "SLOT_CONFLICT"
    return None


def create_appointment(db: Session, access: PatientCompanionAccess, payload: dict) -> RemoteDomainResult:
    # v1 accepts only a cabinet-issued opaque slot description; numeric internal IDs are never accepted from patient payload.
    allowed = {"slot_ref", "datetime_start", "duration_minutes"}
    if set(payload) - allowed or not isinstance(payload.get("slot_ref"), str):
        return _reject("INVALID_REQUEST")
    # Slot catalogue/mapping is the next slice; fail closed until a cabinet-issued slot resolver exists.
    return _reject("SLOT_REFERENCE_REQUIRED")


def reschedule_appointment(db: Session, access: PatientCompanionAccess, payload: dict) -> RemoteDomainResult:
    if set(payload) != {"appointment_ref", "slot_ref"}:
        return _reject("INVALID_REQUEST")
    appointment = _appointment_for_ref(db, access, payload.get("appointment_ref"))
    if appointment is None:
        return _reject("APPOINTMENT_NOT_FOUND")
    return _reject("SLOT_REFERENCE_REQUIRED")


def cancel_appointment(db: Session, access: PatientCompanionAccess, payload: dict) -> RemoteDomainResult:
    if set(payload) != {"appointment_ref"}:
        return _reject("INVALID_REQUEST")
    appointment = _appointment_for_ref(db, access, payload.get("appointment_ref"))
    if appointment is None:
        return _reject("APPOINTMENT_NOT_FOUND")
    if appointment.status in ACTIVE_CANCEL_BLOCKERS:
        return _reject("APPOINTMENT_NOT_CANCELLABLE")
    appointment.status = models.AppointmentStatus.ANNULE
    ref = _opaque_ref(db, access, appointment)
    return RemoteDomainResult(
        status="ACCEPTED",
        response={"appointment_ref": ref.public_id, "state": "cancelled"},
    )


PC02_REMOTE_HANDLERS = {
    "agenda.create": create_appointment,
    "agenda.reschedule": reschedule_appointment,
    "agenda.cancel": cancel_appointment,
}
