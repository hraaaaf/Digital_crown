from datetime import datetime

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend import models
from backend.models_agenda_a4 import AgendaResource, install_agenda_resource_model
from backend.models_base import Base
from backend.services.agenda_resource_conflicts import assert_resource_available, find_resource_conflict, validate_assignable_resource


@pytest.fixture()
def db():
    install_agenda_resource_model()
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def _resource(db, employer_id=1, *, active=True, name="Fauteuil 1"):
    resource = AgendaResource(employer_id=employer_id, name=name, resource_type="CHAIR", is_active=active)
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource


def _appointment(db, resource_id, *, employer_id=1, start=None, duration=30, status=None):
    appt = models.Appointment(
        employer_id=employer_id,
        patient_name="Patient test",
        praticien_id=None,
        resource_id=resource_id,
        datetime_start=start or datetime(2026, 9, 18, 9, 0),
        duration_minutes=duration,
        status=status or models.AppointmentStatus.PREVU,
        scheduling_type=models.SchedulingType.EXACT_TIME,
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)
    return appt


def test_null_resource_never_blocks(db):
    assert_resource_available(
        db,
        employer_id=1,
        resource_id=None,
        datetime_start=datetime(2026, 9, 18, 9, 0),
        duration_minutes=30,
    )


def test_cross_tenant_resource_fails_closed(db):
    resource = _resource(db, employer_id=2)
    with pytest.raises(HTTPException) as exc:
        validate_assignable_resource(db, 1, resource.id)
    assert exc.value.status_code == 404


def test_inactive_resource_cannot_be_newly_assigned(db):
    resource = _resource(db, active=False)
    with pytest.raises(HTTPException) as exc:
        validate_assignable_resource(db, 1, resource.id)
    assert exc.value.status_code == 409


def test_same_resource_overlap_is_blocked(db):
    resource = _resource(db)
    existing = _appointment(db, resource.id)
    conflict = find_resource_conflict(
        db,
        employer_id=1,
        resource_id=resource.id,
        datetime_start=datetime(2026, 9, 18, 9, 15),
        duration_minutes=30,
    )
    assert conflict.id == existing.id
    with pytest.raises(HTTPException) as exc:
        assert_resource_available(
            db,
            employer_id=1,
            resource_id=resource.id,
            datetime_start=datetime(2026, 9, 18, 9, 15),
            duration_minutes=30,
        )
    assert exc.value.status_code == 409
    assert exc.value.detail["code"] == "AGENDA_RESOURCE_CONFLICT"


def test_touching_slots_do_not_overlap(db):
    resource = _resource(db)
    _appointment(db, resource.id, start=datetime(2026, 9, 18, 9, 0), duration=30)
    assert find_resource_conflict(
        db,
        employer_id=1,
        resource_id=resource.id,
        datetime_start=datetime(2026, 9, 18, 9, 30),
        duration_minutes=30,
    ) is None


def test_excluding_current_appointment_allows_update(db):
    resource = _resource(db)
    existing = _appointment(db, resource.id)
    assert find_resource_conflict(
        db,
        employer_id=1,
        resource_id=resource.id,
        datetime_start=existing.datetime_start,
        duration_minutes=existing.duration_minutes,
        exclude_appointment_id=existing.id,
    ) is None
