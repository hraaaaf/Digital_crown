"""C05B-03I PRODUCT-DOMAIN PRECHECK — real backend services + isolated fixture DB.

These tests intentionally interleave actions inside ONE SQLAlchemy session.
They are not the simultaneous multi-connection/5-VM/FUE certification.
"""
from __future__ import annotations

import uuid
from datetime import datetime

import pytest

from backend import models
from backend.models_patient_companion import PatientCompanionAccess, PatientCompanionIdentity, PatientCompanionMessage
from backend.services.patient_companion_agenda import create_appointment, issue_slots
from backend.services.patient_companion_messages import handle_message_send, handle_message_sync
import backend.services.patient_companion_agenda as agenda_module


@pytest.fixture(autouse=True)
def _isolated_schedule(monkeypatch):
    # Safety fixture only: test intended to probe conflict control, not real clinic hours.
    monkeypatch.setattr(agenda_module, "validate_appointment_availability", lambda *_a, **_kw: None)
    monkeypatch.setattr(agenda_module, "assert_resource_available", lambda *_a, **_kw: None)


def _patient_access(db, dentiste, label):
    patient = models.Patient(
        numero_dossier=f"DC06I-{label}-{uuid.uuid4().hex[:6]}",
        nom="Synthetic", prenom=label,
        date_naissance=datetime(2010, 1, 1), sexe="F", employer_id=dentiste.id,
    )
    identity = PatientCompanionIdentity(provider="local_bridge", subject=f"dc06i:{label}:{uuid.uuid4()}")
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


def test_c05b03i_two_patient_messages_dentist_read_and_no_cross_patient(db, dentiste):
    a, access_a = _patient_access(db, dentiste, "A")
    b, access_b = _patient_access(db, dentiste, "B")
    id_a, id_b = str(uuid.uuid4()), str(uuid.uuid4())
    first = handle_message_send(db, access_a, {"client_message_id": id_a, "body": "A: demande RV"})
    second = handle_message_send(db, access_b, {"client_message_id": id_b, "body": "B: message"})
    assert (first.status, second.status) == ("ACCEPTED", "ACCEPTED")
    assert handle_message_send(db, access_a, {"client_message_id": id_a, "body": "A: demande RV"}).status == "ACCEPTED"
    conflict = handle_message_send(db, access_a, {"client_message_id": id_a, "body": "altered"})
    assert conflict.status == "REJECTED" and conflict.response["code"] == "CLIENT_MESSAGE_CONFLICT"
    db.commit()
    # Dentist reads persisted messages, never mixing patient A and patient B.
    staff_rows_a = db.query(PatientCompanionMessage).filter_by(employer_id=dentiste.id, patient_id=a.id).all()
    staff_rows_b = db.query(PatientCompanionMessage).filter_by(employer_id=dentiste.id, patient_id=b.id).all()
    assert len(staff_rows_a) == len(staff_rows_b) == 1
    assert staff_rows_a[0].body == "A: demande RV" and staff_rows_b[0].body == "B: message"
    sync_a = handle_message_sync(db, access_a, {})
    sync_b = handle_message_sync(db, access_b, {})
    assert [x["body"] for x in sync_a.response["items"]] == ["A: demande RV"]
    assert [x["body"] for x in sync_b.response["items"]] == ["B: message"]
    assert db.query(PatientCompanionMessage).filter_by(employer_id=dentiste.id).count() == 2


def test_c05b03i_two_issued_slots_cannot_double_book_one_interval(db, dentiste):
    a, access_a = _patient_access(db, dentiste, "A")
    b, access_b = _patient_access(db, dentiste, "B")
    start = datetime(2030, 1, 2, 10, 0)
    # Both patients discover same free interval before either confirms.
    slots_a = issue_slots(db, access=access_a, starts=[start], duration_minutes=30, practitioner_id=dentiste.id)
    slots_b = issue_slots(db, access=access_b, starts=[start], duration_minutes=30, practitioner_id=dentiste.id)
    assert len(slots_a) == len(slots_b) == 1
    db.commit()
    accepted = create_appointment(db, access_a, {"slot_ref": slots_a[0]["slot_ref"]})
    assert accepted.status == "ACCEPTED" and accepted.response["state"] == "confirmed"
    db.commit()  # Host remote worker's commit boundary, not actual concurrent sessions.
    denied = create_appointment(db, access_b, {"slot_ref": slots_b[0]["slot_ref"]})
    assert denied.status == "REJECTED" and denied.response["code"] in ("SLOT_CONFLICT", "SLOT_UNAVAILABLE")
    assert db.query(models.Appointment).filter(
        models.Appointment.employer_id == dentiste.id,
        models.Appointment.datetime_start == start,
        models.Appointment.praticien_id == dentiste.id,
    ).count() == 1
    assert db.query(models.Appointment).filter_by(patient_id=b.id).count() == 0
    assert db.query(models.Appointment).filter_by(patient_id=a.id).count() == 1
