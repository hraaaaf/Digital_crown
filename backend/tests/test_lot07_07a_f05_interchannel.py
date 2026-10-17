"""F05 channel-invariant regression tests. Synthetic DB fixtures only."""
from datetime import datetime, timedelta
import uuid

from fastapi import HTTPException
import pytest

from backend import models
from backend.models_patient_companion import (
    PatientCompanionAccess, PatientCompanionAgendaSlot, PatientCompanionIdentity,
)
from backend.routers.appointments import _find_conflicts, create_appointment
from backend.schemas.appointments import AppointmentCreate
from backend.services.patient_companion_agenda import create_appointment as companion_create


def test_legacy_unassigned_blocks_companion_and_keeps_slot_unconsumed(db, dentiste):
    # A legacy NULL practitioner reservation is a cabinet-wide blocker.
    from backend.models_patient_companion import PatientCompanionAccess
    patient = models.Patient(numero_dossier="F05-LEGACY", nom="F05", prenom="Synthetic", date_naissance=datetime(2010, 1, 1), sexe="F", employer_id=dentiste.id)
    identity = PatientCompanionIdentity(provider="local_bridge", subject=f"f05:{uuid.uuid4()}")
    db.add_all([patient, identity])
    db.flush()
    access = PatientCompanionAccess(
        public_id=str(uuid.uuid4()), patient_id=patient.id,
        employer_id=dentiste.id, identity_id=identity.id, relationship_type="SELF",
    )
    db.add(access)
    db.flush()
    slot = PatientCompanionAgendaSlot(
        public_id=str(uuid.uuid4()), employer_id=dentiste.id,
        practitioner_id=dentiste.id, resource_id=None,
        datetime_start=datetime(2030, 1, 2, 10), duration_minutes=30,
        expires_at=datetime.utcnow() + timedelta(minutes=15),
    )
    db.add(slot)
    db.add(models.Appointment(
        patient_name="Legacy F05", employer_id=dentiste.id,
        datetime_start=slot.datetime_start, duration_minutes=60,
        status=models.AppointmentStatus.PREVU,
        scheduling_type=models.SchedulingType.EXACT_TIME, praticien_id=None,
    ))
    db.flush()
    # The legacy row and opaque slot must be durable before the writer starts.
    db.commit()
    # Distinguish an invalid/revoked opaque fixture from a real cross-channel
    # conflict regression; do not weaken the expected SLOT_CONFLICT contract.
    from backend.services.patient_companion_agenda import _slot_for_ref
    visible_before = _slot_for_ref(db, access, slot.public_id) is not None
    result = companion_create(db, access, {"slot_ref": slot.public_id})
    assert result.status == "REJECTED" and result.response["code"] == "SLOT_CONFLICT", (
        "Synthetic stale-slot fixture is valid before lock?", visible_before,
        "observed_response", result.response, "slot_revoked", slot.revoked_at is not None,
        "slot_consumed", slot.consumed_at is not None,
    )
    db.refresh(slot)
    assert slot.consumed_at is None


def test_pending_counts_under_existing_oracle_and_refused_expired_do_not(db, dentiste):
    start = datetime(2030, 1, 2, 10)
    appointment = models.Appointment(
        patient_name="Pending F05", employer_id=dentiste.id,
        praticien_id=None, datetime_start=start, duration_minutes=30,
        scheduling_type=models.SchedulingType.EXACT_TIME,
        status=models.AppointmentStatus.EN_ATTENTE_DEMANDE,
    )
    db.add(appointment)
    db.flush()
    assert appointment in _find_conflicts(db, dentiste.id, dentiste.id, start, 30)
    appointment.expires_at = datetime.utcnow() - timedelta(seconds=1)
    db.flush()
    assert not _find_conflicts(db, dentiste.id, dentiste.id, start, 30), (
        "Expired pending requests must not reserve capacity forever"
    )
    appointment.expires_at = datetime.utcnow() + timedelta(minutes=10)
    db.flush()
    assert appointment in _find_conflicts(db, dentiste.id, dentiste.id, start, 30)
    appointment.status = models.AppointmentStatus.REFUSE
    db.flush()
    assert not _find_conflicts(db, dentiste.id, dentiste.id, start, 30)
    appointment.status = models.AppointmentStatus.EXPIRE
    db.flush()
    assert not _find_conflicts(db, dentiste.id, dentiste.id, start, 30)


def test_direct_canonical_call_checks_permission_not_only_fastapi_dependency(db, dentiste):
    # A direct call must not trust a FastAPI dependency that was never executed.
    secretary = models.User(
        email="f05-denied@example.invalid", hashed_password="synthetic",
        employer_id=dentiste.id, role=models.UserRole.SECRETAIRE,
        permissions={"agenda": False}, is_active=True,
    )
    db.add(secretary)
    db.flush()
    with pytest.raises(HTTPException) as raised:
        create_appointment(
            AppointmentCreate(patient_name="Synthetic", datetime_start=datetime(2030, 1, 2, 10)),
            db,
            secretary,
        )
    assert raised.value.status_code == 403


def test_bot_status_reactivation_rechecks_capacity(db, dentiste):
    """Bot must not resurrect a cancelled appointment over a live reservation."""
    from backend.services.bot.action_dispatcher import ActionDispatcher

    start = datetime(2030, 1, 2, 10)
    current = models.Appointment(
        patient_name="F05 current", employer_id=dentiste.id,
        praticien_id=dentiste.id, datetime_start=start, duration_minutes=30,
        status=models.AppointmentStatus.PREVU,
        scheduling_type=models.SchedulingType.EXACT_TIME,
    )
    cancelled = models.Appointment(
        patient_name="F05 cancelled", employer_id=dentiste.id,
        praticien_id=dentiste.id, datetime_start=start, duration_minutes=30,
        status=models.AppointmentStatus.ANNULE,
        scheduling_type=models.SchedulingType.EXACT_TIME,
    )
    db.add_all([current, cancelled]); db.flush()
    # Model a prior committed booking; the shared in-memory SQLite fixture
    # cannot faithfully reproduce an already committed writer via flush alone.
    db.commit()
    db.refresh(cancelled)
    with pytest.raises(HTTPException) as raised:
        ActionDispatcher()._exec_change_status(
            {"appointment_id": cancelled.id, "status": "PREVU"}, db, dentiste,
        )
    assert raised.value.status_code == 409
    db.refresh(cancelled)
    assert cancelled.status == models.AppointmentStatus.ANNULE


def test_bot_status_direct_call_denies_user_without_agenda(db, dentiste):
    from backend.services.bot.action_dispatcher import ActionDispatcher
    denied = models.User(
        email="f05-bot-denied@example.invalid", hashed_password="synthetic",
        employer_id=dentiste.id, role=models.UserRole.SECRETAIRE,
        permissions={"agenda": False}, is_active=True,
    )
    db.add(denied); db.flush()
    with pytest.raises(HTTPException) as raised:
        ActionDispatcher()._exec_change_status(
            {"appointment_id": 1, "status": "PREVU"}, db, denied,
        )
    assert raised.value.status_code == 403


def test_expired_pending_releases_shared_resource_without_touching_slot(db, dentiste):
    from backend.services.agenda_resource_conflicts import find_resource_conflict
    chair = models.AgendaResource(
        employer_id=dentiste.id, name="F05 synthetic chair",
        resource_type="CHAIR", is_active=True,
    )
    db.add(chair); db.flush()
    start = datetime(2030, 1, 2, 10)
    pending = models.Appointment(
        patient_name="F05 expired request", employer_id=dentiste.id,
        praticien_id=None, resource_id=chair.id,
        datetime_start=start, duration_minutes=30,
        status=models.AppointmentStatus.EN_ATTENTE_DEMANDE,
        scheduling_type=models.SchedulingType.EXACT_TIME,
        expires_at=datetime.utcnow() - timedelta(seconds=1),
    )
    db.add(pending); db.flush()
    assert find_resource_conflict(
        db, employer_id=dentiste.id, resource_id=chair.id,
        datetime_start=start, duration_minutes=30,
    ) is None
    pending.expires_at = datetime.utcnow() + timedelta(minutes=15)
    db.flush()
    assert find_resource_conflict(
        db, employer_id=dentiste.id, resource_id=chair.id,
        datetime_start=start, duration_minutes=30,
    ) is pending
