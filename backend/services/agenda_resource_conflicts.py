from datetime import timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend import models
from backend.models import AgendaResource

_CANCELLED_STATUSES = {"annule", "cancelled", "canceled"}


def _status_value(status) -> str:
    return str(getattr(status, "value", status) or "").strip().lower()


def validate_assignable_resource(db: Session, employer_id: int, resource_id: int | None) -> AgendaResource | None:
    """Fail closed for cross-tenant, missing or inactive newly assigned resources."""
    if resource_id is None:
        return None
    resource = db.query(AgendaResource).filter(
        AgendaResource.id == resource_id,
        AgendaResource.employer_id == employer_id,
    ).first()
    if resource is None:
        raise HTTPException(status_code=404, detail="Ressource agenda introuvable")
    if not resource.is_active:
        raise HTTPException(status_code=409, detail="Ressource agenda inactive")
    return resource


def find_resource_conflict(
    db: Session,
    *,
    employer_id: int,
    resource_id: int | None,
    datetime_start,
    duration_minutes: int,
    exclude_appointment_id: int | None = None,
):
    """Return the first overlapping exact-time appointment for one capacity-1 resource."""
    if resource_id is None:
        return None
    candidate_end = datetime_start + timedelta(minutes=duration_minutes)
    query = db.query(models.Appointment).filter(
        models.Appointment.employer_id == employer_id,
        models.Appointment.resource_id == resource_id,
        models.Appointment.datetime_start < candidate_end,
    )
    if exclude_appointment_id is not None:
        query = query.filter(models.Appointment.id != exclude_appointment_id)
    for appointment in query.all():
        if _status_value(appointment.status) in _CANCELLED_STATUSES:
            continue
        if _status_value(getattr(appointment, "scheduling_type", "exact_time")) not in {"exact_time", "exact-time", "exact"}:
            continue
        existing_end = appointment.datetime_start + timedelta(minutes=appointment.duration_minutes)
        if datetime_start < existing_end:
            return appointment
    return None


def assert_resource_available(
    db: Session,
    *,
    employer_id: int,
    resource_id: int | None,
    datetime_start,
    duration_minutes: int,
    exclude_appointment_id: int | None = None,
) -> None:
    validate_assignable_resource(db, employer_id, resource_id)
    conflict = find_resource_conflict(
        db,
        employer_id=employer_id,
        resource_id=resource_id,
        datetime_start=datetime_start,
        duration_minutes=duration_minutes,
        exclude_appointment_id=exclude_appointment_id,
    )
    if conflict is not None:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "AGENDA_RESOURCE_CONFLICT",
                "message": "La ressource est déjà occupée sur ce créneau",
                "appointment_id": conflict.id,
                "resource_id": resource_id,
            },
        )
