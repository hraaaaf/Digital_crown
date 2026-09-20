from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend import models
from backend.models_patient_companion import PatientCompanionAppointmentRef, PatientCompanionIdentity
from backend.routers.patient_companion_common import get_db, patient_identity, principal_for_access
from backend.services.patient_companion_agenda import issue_slots

router = APIRouter()


@router.get("/contexts/{access_id}/agenda")
def patient_agenda(
    access_id: str,
    identity: PatientCompanionIdentity = Depends(patient_identity),
    db: Session = Depends(get_db),
):
    access, _patient = principal_for_access(db, identity, access_id)
    appointments = db.query(models.Appointment).filter(
        models.Appointment.employer_id == access.employer_id,
        models.Appointment.patient_id == access.patient_id,
        models.Appointment.deleted_at.is_(None),
        models.Appointment.status != models.AppointmentStatus.ANNULE,
    ).order_by(models.Appointment.datetime_start.asc()).all()

    items = []
    for appointment in appointments:
        ref = db.query(PatientCompanionAppointmentRef).filter(
            PatientCompanionAppointmentRef.employer_id == access.employer_id,
            PatientCompanionAppointmentRef.appointment_id == appointment.id,
        ).first()
        if ref is None:
            ref = PatientCompanionAppointmentRef(
                employer_id=access.employer_id,
                patient_id=access.patient_id,
                appointment_id=appointment.id,
            )
            db.add(ref)
            db.flush()
        items.append({
            "appointment_ref": ref.public_id,
            "datetime_start": appointment.datetime_start,
            "duration_minutes": appointment.duration_minutes,
            "status": getattr(appointment.status, "value", appointment.status),
            "scheduling_type": getattr(appointment.scheduling_type, "value", appointment.scheduling_type),
        })
    db.commit()
    return {"items": items}


@router.get("/contexts/{access_id}/agenda/slots")
def patient_agenda_slots(
    access_id: str,
    practitioner_ref: str = Query(min_length=36, max_length=36),
    day: datetime = Query(),
    duration_minutes: int = Query(default=30, ge=10, le=180),
    identity: PatientCompanionIdentity = Depends(patient_identity),
    db: Session = Depends(get_db),
):
    # practitioner_ref is intentionally opaque in the patient API. v1 derives it
    # from a cabinet-issued UUID alias; until aliases exist, no numeric fallback.
    access, _patient = principal_for_access(db, identity, access_id)
    try:
        import uuid
        uuid.UUID(practitioner_ref)
    except ValueError:
        return {"items": []}

    # Fail closed until the cabinet practitioner alias catalogue is issued.
    # This endpoint establishes the patient contract without accepting an internal ID.
    return {"items": []}
