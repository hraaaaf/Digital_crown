from __future__ import annotations

from datetime import datetime, time, timedelta
from sqlalchemy.orm import Session
from backend import models

DISCOVERABLE_STATION_STATUSES = (
    models.AppointmentStatus.PREVU,
    models.AppointmentStatus.CONFIRME,
    models.AppointmentStatus.EN_SALLE_ATTENTE,
)
ARRIVAL_SOURCE_STATUSES = (
    models.AppointmentStatus.PREVU,
    models.AppointmentStatus.CONFIRME,
)

def cabinet_local_day_bounds(now: datetime | None = None) -> tuple[datetime, datetime]:
    current = now or datetime.now()
    start = datetime.combine(current.date(), time.min)
    return start, start + timedelta(days=1)

def list_station_patient_appointments_for_today(db: Session, *, employer_id: int, patient_id: int, now: datetime | None = None) -> list[models.Appointment]:
    start, end = cabinet_local_day_bounds(now)
    return (
        db.query(models.Appointment)
        .filter(
            models.Appointment.employer_id == employer_id,
            models.Appointment.patient_id == patient_id,
            models.Appointment.deleted_at.is_(None),
            models.Appointment.datetime_start >= start,
            models.Appointment.datetime_start < end,
            models.Appointment.status.in_(DISCOVERABLE_STATION_STATUSES),
        )
        .order_by(models.Appointment.datetime_start.asc(), models.Appointment.id.asc())
        .all()
    )

def station_appointment_for_today(db: Session, *, appointment_id: int, employer_id: int, patient_id: int, now: datetime | None = None) -> models.Appointment | None:
    start, end = cabinet_local_day_bounds(now)
    return (
        db.query(models.Appointment)
        .filter(
            models.Appointment.id == appointment_id,
            models.Appointment.employer_id == employer_id,
            models.Appointment.patient_id == patient_id,
            models.Appointment.deleted_at.is_(None),
            models.Appointment.datetime_start >= start,
            models.Appointment.datetime_start < end,
        )
        .first()
    )

def mark_station_appointment_arrived(db: Session, *, appointment: models.Appointment, employer_id: int, patient_id: int, now: datetime | None = None) -> tuple[models.Appointment, bool]:
    start, end = cabinet_local_day_bounds(now)
    if appointment.status == models.AppointmentStatus.EN_SALLE_ATTENTE:
        return appointment, False
    if appointment.status not in ARRIVAL_SOURCE_STATUSES:
        raise ValueError("STATION_APPOINTMENT_STATUS_NOT_ARRIVABLE")
    scope = (
        models.Appointment.id == appointment.id,
        models.Appointment.employer_id == employer_id,
        models.Appointment.patient_id == patient_id,
        models.Appointment.deleted_at.is_(None),
        models.Appointment.datetime_start >= start,
        models.Appointment.datetime_start < end,
    )
    updated = (
        db.query(models.Appointment)
        .filter(*scope, models.Appointment.status.in_(ARRIVAL_SOURCE_STATUSES))
        .update({models.Appointment.status: models.AppointmentStatus.EN_SALLE_ATTENTE}, synchronize_session=False)
    )
    if updated != 1:
        db.rollback()
        refreshed = db.query(models.Appointment).filter(*scope, models.Appointment.status == models.AppointmentStatus.EN_SALLE_ATTENTE).first()
        if refreshed is not None:
            return refreshed, False
        raise ValueError("STATION_APPOINTMENT_STATUS_NOT_ARRIVABLE")
    db.flush()
    db.refresh(appointment)
    return appointment, True

def serialize_station_appointment(appointment: models.Appointment) -> dict:
    status_value = appointment.status.value if hasattr(appointment.status, "value") else str(appointment.status)
    scheduling_value = appointment.scheduling_type.value if hasattr(appointment.scheduling_type, "value") else str(appointment.scheduling_type)
    return {
        "appointmentId": appointment.id,
        "datetimeStart": appointment.datetime_start,
        "durationMinutes": appointment.duration_minutes,
        "schedulingType": scheduling_value,
        "status": status_value,
    }
