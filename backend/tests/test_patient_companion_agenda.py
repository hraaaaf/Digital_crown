from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from backend import models
from backend.models_patient_companion import (
    PatientCompanionAccess,
    PatientCompanionAgendaSlot,
    PatientCompanionAppointmentRef,
    PatientCompanionIdentity,
)
from backend.services.patient_companion_agenda import cancel_appointment, create_appointment, reschedule_appointment


def _access(db, dentiste):
    patient = models.Patient(numero_dossier=f"PC02-{uuid.uuid4().hex[:8]}", nom="Agenda", prenom="Aya", date_naissance=datetime(2010, 1, 1), sexe="F", employer_id=dentiste.id)
    identity = PatientCompanionIdentity(provider="local_bridge", subject=f"device:{uuid.uuid4()}")
    db.add_all([patient, identity]); db.flush()
    access = PatientCompanionAccess(identity_id=identity.id, employer_id=dentiste.id, patient_id=patient.id, relationship_type="SELF")
    db.add(access); db.flush()
    return patient, access


def _slot(db, dentiste, start):
    row = PatientCompanionAgendaSlot(
        public_id=str(uuid.uuid4()), employer_id=dentiste.id, practitioner_id=dentiste.id,
        datetime_start=start, duration_minutes=30,
        expires_at=datetime.utcnow() + timedelta(minutes=15),
    )
    db.add(row); db.flush()
    return row


def test_create_rejects_internal_ids_and_accepts_only_cabinet_slot(db, dentiste):
    patient, access = _access(db, dentiste)
    slot = _slot(db, dentiste, datetime(2030, 1, 2, 10, 0))
    invalid = create_appointment(db, access, {"slot_ref": slot.public_id, "patient_id": patient.id})
    assert invalid.status == "REJECTED" and invalid.response["code"] == "INVALID_REQUEST"

    result = create_appointment(db, access, {"slot_ref": slot.public_id})
    assert result.status == "ACCEPTED"
    assert result.response["state"] == "confirmed"
    assert "appointment_id" not in result.response
    created = db.query(models.Appointment).filter(models.Appointment.patient_id == patient.id).one()
    assert created.praticien_id == dentiste.id
    assert created.source == "patient_companion"


def test_reschedule_and_cancel_are_scoped_by_opaque_ref(db, dentiste):
    patient, access = _access(db, dentiste)
    appointment = models.Appointment(
        patient_id=patient.id, patient_name="Aya Agenda", datetime_start=datetime(2030, 1, 2, 10, 0),
        duration_minutes=30, status=models.AppointmentStatus.CONFIRME,
        scheduling_type=models.SchedulingType.EXACT_TIME, employer_id=dentiste.id, praticien_id=dentiste.id,
    )
    db.add(appointment); db.flush()
    ref = PatientCompanionAppointmentRef(public_id=str(uuid.uuid4()), employer_id=dentiste.id, patient_id=patient.id, appointment_id=appointment.id)
    db.add(ref); db.flush()
    slot = _slot(db, dentiste, datetime(2030, 1, 3, 11, 0))

    moved = reschedule_appointment(db, access, {"appointment_ref": ref.public_id, "slot_ref": slot.public_id})
    assert moved.status == "ACCEPTED"
    assert appointment.datetime_start == datetime(2030, 1, 3, 11, 0)
    assert "appointment_id" not in moved.response

    invalid = cancel_appointment(db, access, {"appointment_ref": ref.public_id, "appointment_id": appointment.id})
    assert invalid.status == "REJECTED"
    assert appointment.status == models.AppointmentStatus.CONFIRME

    cancelled = cancel_appointment(db, access, {"appointment_ref": ref.public_id})
    assert cancelled.status == "ACCEPTED"
    assert appointment.status == models.AppointmentStatus.ANNULE


def test_expired_slot_fails_closed(db, dentiste):
    _, access = _access(db, dentiste)
    slot = PatientCompanionAgendaSlot(
        public_id=str(uuid.uuid4()), employer_id=dentiste.id, practitioner_id=dentiste.id,
        datetime_start=datetime(2030, 1, 2, 10, 0), duration_minutes=30,
        expires_at=datetime.utcnow() - timedelta(seconds=1),
    )
    db.add(slot); db.flush()
    result = create_appointment(db, access, {"slot_ref": slot.public_id})
    assert result.status == "REJECTED"
    assert result.response["code"] == "SLOT_NOT_FOUND"
