from __future__ import annotations

import uuid
from datetime import datetime

from backend import models
from backend.models_patient_companion import (
    PatientCompanionAccess,
    PatientCompanionAppointmentRef,
    PatientCompanionIdentity,
)
from backend.services.patient_companion_agenda import (
    cancel_appointment,
    create_appointment,
    reschedule_appointment,
)


def _access(db, dentiste):
    patient = models.Patient(
        numero_dossier=f"PC02-{uuid.uuid4().hex[:8]}",
        nom="Agenda",
        prenom="Aya",
        date_naissance=datetime(2010, 1, 1),
        sexe="F",
        employer_id=dentiste.id,
    )
    identity = PatientCompanionIdentity(provider="local_bridge", subject=f"device:{uuid.uuid4()}")
    db.add_all([patient, identity])
    db.flush()
    access = PatientCompanionAccess(
        identity_id=identity.id,
        employer_id=dentiste.id,
        patient_id=patient.id,
        relationship_type="SELF",
    )
    db.add(access)
    db.flush()
    return patient, access


def test_create_and_reschedule_fail_closed_without_cabinet_slot_reference(db, dentiste):
    patient, access = _access(db, dentiste)
    assert create_appointment(db, access, {"slot_ref": "opaque-slot"}).response["code"] == "SLOT_REFERENCE_REQUIRED"
    assert create_appointment(db, access, {"slot_ref": "opaque", "patient_id": patient.id}).response["code"] == "INVALID_REQUEST"
    assert reschedule_appointment(db, access, {"appointment_ref": str(uuid.uuid4()), "slot_ref": "opaque"}).response["code"] == "APPOINTMENT_NOT_FOUND"


def test_cancel_accepts_only_opaque_ref_scoped_to_access(db, dentiste):
    patient, access = _access(db, dentiste)
    appointment = models.Appointment(
        patient_id=patient.id,
        patient_name="Aya Agenda",
        datetime_start=datetime(2030, 1, 2, 10, 0),
        duration_minutes=30,
        status=models.AppointmentStatus.CONFIRME,
        scheduling_type=models.SchedulingType.EXACT_TIME,
        employer_id=dentiste.id,
        praticien_id=dentiste.id,
    )
    db.add(appointment)
    db.flush()
    ref = PatientCompanionAppointmentRef(
        public_id=str(uuid.uuid4()),
        employer_id=dentiste.id,
        patient_id=patient.id,
        appointment_id=appointment.id,
    )
    db.add(ref)
    db.flush()

    invalid = cancel_appointment(db, access, {"appointment_ref": ref.public_id, "appointment_id": appointment.id})
    assert invalid.status == "REJECTED"
    assert appointment.status == models.AppointmentStatus.CONFIRME

    result = cancel_appointment(db, access, {"appointment_ref": ref.public_id})
    assert result.status == "ACCEPTED"
    assert result.response == {"appointment_ref": ref.public_id, "state": "cancelled"}
    assert appointment.status == models.AppointmentStatus.ANNULE
