from __future__ import annotations

import uuid
from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from backend import models
from backend.models_patient_companion import (
    PatientCompanionAppointmentRef,
    PatientCompanionIdentity,
    PatientCompanionPractitionerRef,
    PatientCompanionRemoteKeyset,
)
from backend.routers.patient_companion_common import get_db, patient_identity, principal_for_access
from backend.services.patient_companion_agenda import issue_slots
from backend.services.patient_companion_remote_worker import process_remote_envelope
from backend.utils.rate_limit import check_rate_limit

router = APIRouter()


class RemoteCommandEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")
    blob: str = Field(min_length=16, max_length=350_000)


@router.post("/contexts/{access_id}/agenda/remote-command")
def patient_agenda_remote_command(
    access_id: str,
    body: RemoteCommandEnvelope,
    request: Request,
    identity: PatientCompanionIdentity = Depends(patient_identity),
    db: Session = Depends(get_db),
):
    check_rate_limit(request, scope="patient-companion-agenda-remote-command")
    access, _patient = principal_for_access(db, identity, access_id)
    keyset = db.query(PatientCompanionRemoteKeyset).filter(
        PatientCompanionRemoteKeyset.access_id == access.id,
        PatientCompanionRemoteKeyset.status == "ACTIVE",
        PatientCompanionRemoteKeyset.revoked_at.is_(None),
    ).first()
    if keyset is None:
        raise HTTPException(status_code=409, detail="Transport sécurisé Patient Companion non initialisé.")
    try:
        ack = process_remote_envelope(
            db,
            access=access,
            keyset=keyset,
            compact_jwe=body.blob,
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Commande distante Patient Companion invalide.") from None
    return {"blob": ack}



def _practitioner_aliases(db: Session, employer_id: int) -> list[tuple[PatientCompanionPractitionerRef, models.User]]:
    practitioners = db.query(models.User).filter(
        models.User.is_active.is_(True),
        models.User.role.in_([models.UserRole.DENTISTE, models.UserRole.ADMIN]),
        ((models.User.id == employer_id) | (models.User.employer_id == employer_id)),
    ).order_by(models.User.nom_complet.asc(), models.User.id.asc()).all()
    rows = []
    for practitioner in practitioners:
        alias = db.query(PatientCompanionPractitionerRef).filter(
            PatientCompanionPractitionerRef.employer_id == employer_id,
            PatientCompanionPractitionerRef.practitioner_id == practitioner.id,
        ).first()
        if alias is None:
            alias = PatientCompanionPractitionerRef(
                public_id=str(uuid.uuid4()),
                employer_id=employer_id,
                practitioner_id=practitioner.id,
            )
            db.add(alias)
            db.flush()
        if alias.revoked_at is None:
            rows.append((alias, practitioner))
    return rows


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
            db.add(ref); db.flush()
        items.append({
            "appointment_ref": ref.public_id,
            "datetime_start": appointment.datetime_start,
            "duration_minutes": appointment.duration_minutes,
            "status": getattr(appointment.status, "value", appointment.status),
            "scheduling_type": getattr(appointment.scheduling_type, "value", appointment.scheduling_type),
        })
    db.commit()
    return {"items": items}


@router.get("/contexts/{access_id}/agenda/practitioners")
def patient_agenda_practitioners(
    access_id: str,
    identity: PatientCompanionIdentity = Depends(patient_identity),
    db: Session = Depends(get_db),
):
    access, _patient = principal_for_access(db, identity, access_id)
    aliases = _practitioner_aliases(db, access.employer_id)
    db.commit()
    return {"items": [
        {"practitioner_ref": alias.public_id, "display_name": practitioner.nom_complet or "Praticien"}
        for alias, practitioner in aliases
    ]}


@router.get("/contexts/{access_id}/agenda/slots")
def patient_agenda_slots(
    access_id: str,
    practitioner_ref: str = Query(min_length=36, max_length=36),
    day: date = Query(),
    duration_minutes: int = Query(default=30, ge=10, le=180),
    identity: PatientCompanionIdentity = Depends(patient_identity),
    db: Session = Depends(get_db),
):
    access, _patient = principal_for_access(db, identity, access_id)
    try:
        uuid.UUID(practitioner_ref)
    except ValueError:
        return {"items": []}
    alias = db.query(PatientCompanionPractitionerRef).filter(
        PatientCompanionPractitionerRef.public_id == practitioner_ref,
        PatientCompanionPractitionerRef.employer_id == access.employer_id,
        PatientCompanionPractitionerRef.revoked_at.is_(None),
    ).first()
    if alias is None:
        return {"items": []}

    # Candidate generation is deliberately bounded. The canonical availability
    # service remains authoritative and filters closed hours and conflicts.
    starts = []
    cursor = datetime.combine(day, time(hour=8))
    end = datetime.combine(day, time(hour=20))
    while cursor < end:
        starts.append(cursor)
        cursor += timedelta(minutes=30)
    items = issue_slots(
        db,
        access=access,
        starts=starts,
        duration_minutes=duration_minutes,
        practitioner_id=alias.practitioner_id,
    )
    db.commit()
    return {"items": items}
