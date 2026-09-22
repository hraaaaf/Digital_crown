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
import pytest
import backend.services.patient_companion_agenda as agenda_service
from backend.services.patient_companion_agenda import (
    cancel_appointment,
    create_appointment,
    issue_slots,
    list_appointments,
    reschedule_appointment,
)


@pytest.fixture(autouse=True)
def _isolate_agenda_availability(monkeypatch):
    monkeypatch.setattr(agenda_service, "validate_appointment_availability", lambda *_a, **_kw: None)
    monkeypatch.setattr(agenda_service, "assert_resource_available", lambda *_a, **_kw: None)


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



def test_slot_is_single_use_after_successful_booking(db, dentiste):
    patient, access = _access(db, dentiste)
    slot = _slot(db, dentiste, datetime(2030, 1, 4, 10, 0))

    first = create_appointment(db, access, {"slot_ref": slot.public_id})
    assert first.status == "ACCEPTED"
    db.refresh(slot)
    assert slot.consumed_at is not None

    second = create_appointment(db, access, {"slot_ref": slot.public_id})
    assert second.status == "REJECTED"
    assert second.response["code"] == "SLOT_NOT_FOUND"
    assert db.query(models.Appointment).filter(
        models.Appointment.patient_id == patient.id,
        models.Appointment.datetime_start == datetime(2030, 1, 4, 10, 0),
    ).count() == 1


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


def test_issue_slots_filters_conflicts_and_returns_no_internal_ids(db, dentiste):
    patient, access = _access(db, dentiste)
    busy = models.Appointment(
        patient_id=patient.id, datetime_start=datetime(2030, 1, 2, 10, 0),
        duration_minutes=30, status=models.AppointmentStatus.CONFIRME,
        scheduling_type=models.SchedulingType.EXACT_TIME, employer_id=dentiste.id,
        praticien_id=dentiste.id,
    )
    db.add(busy); db.flush()

    slots = issue_slots(
        db,
        access=access,
        starts=[datetime(2030, 1, 2, 10, 0), datetime(2030, 1, 2, 11, 0)],
        duration_minutes=30,
        practitioner_id=dentiste.id,
    )
    assert len(slots) == 1
    assert slots[0]["datetime_start"] == "2030-01-02T11:00:00"
    assert set(slots[0]) == {"slot_ref", "datetime_start", "duration_minutes", "expires_at"}
    uuid.UUID(slots[0]["slot_ref"])


def test_practitioner_alias_is_opaque_and_tenant_scoped(db, dentiste):
    from backend.models_patient_companion import PatientCompanionPractitionerRef
    alias = PatientCompanionPractitionerRef(
        public_id=str(uuid.uuid4()), employer_id=dentiste.id, practitioner_id=dentiste.id,
    )
    db.add(alias); db.flush()
    assert alias.public_id != str(dentiste.id)
    uuid.UUID(alias.public_id)
    assert alias.employer_id == dentiste.id


def test_list_appointments_returns_only_patient_safe_opaque_fields(db, dentiste):
    patient, access = _access(db, dentiste)
    appointment = models.Appointment(
        patient_id=patient.id,
        patient_name="Aya Agenda",
        datetime_start=datetime(2030, 1, 5, 9, 30),
        duration_minutes=30,
        status=models.AppointmentStatus.CONFIRME,
        scheduling_type=models.SchedulingType.EXACT_TIME,
        employer_id=dentiste.id,
        praticien_id=dentiste.id,
        motif="Contrôle",
    )
    db.add(appointment)
    db.flush()

    result = list_appointments(db, access, {})
    assert result.status == "ACCEPTED"
    items = result.response["items"]
    assert len(items) == 1
    item = items[0]
    assert set(item) == {
        "appointment_ref",
        "datetime_start",
        "duration_minutes",
        "motif",
        "status",
        "scheduling_type",
    }
    uuid.UUID(item["appointment_ref"])
    assert "appointment_id" not in item
    assert "patient_id" not in item
    assert "employer_id" not in item
