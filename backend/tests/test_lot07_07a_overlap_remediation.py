"""LOT07 07-A: duration-aware, tenant-scoped overlap checks (synthetic SQLite)."""
from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker

from backend import models
from backend.models import AgendaResource
from backend.models_base import Base
from backend.routers.appointments import _find_conflicts
from backend.schemas.appointments import AppointmentCreate, AppointmentUpdate, AppointmentImportItem
from backend.services.agenda_overlap_sql import existing_end_after
from backend.services.agenda_resource_conflicts import find_resource_conflict


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        yield session
    engine.dispose()


def record(db, *, cabinet=1, practitioner=10, resource=None,
           start=datetime(2026, 10, 19, 9), duration=360,
           status=models.AppointmentStatus.PREVU, deleted=False):
    row = models.Appointment(
        employer_id=cabinet, patient_name="SYNTHETIC",
        praticien_id=practitioner, resource_id=resource,
        datetime_start=start, duration_minutes=duration,
        scheduling_type=models.SchedulingType.EXACT_TIME, status=status,
    )
    if deleted:
        row.deleted_at = datetime(2026, 10, 18)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def find(db, practitioner=10, cabinet=1):
    return _find_conflicts(db, cabinet, practitioner, datetime(2026, 10, 19, 14, 30), 30)


def test_long_appointment_blocks_later_slot_for_same_practitioner(db):
    old = record(db)  # 09:00-15:00: historically missed by four-hour lookback.
    assert [x.id for x in find(db)] == [old.id]
    assert find(db, practitioner=11) == []
    assert [x.id for x in _find_conflicts(db,1,None,datetime(2026,10,19,14,30),30)] == [old.id]


def test_legacy_unassigned_blocks_all_practitioners(db):
    old = record(db, practitioner=None)
    assert [x.id for x in find(db, 10)] == [old.id]
    assert [x.id for x in find(db, 11)] == [old.id]


def test_canceled_deleted_and_other_tenant_do_not_block(db):
    record(db, status=models.AppointmentStatus.ANNULE)
    record(db, deleted=True)
    record(db, cabinet=2)
    assert find(db) == []


def test_shared_capacity_one_resource_overrides_practitioner_isolation(db):
    chair = AgendaResource(employer_id=1,name="Synthetic chair",resource_type="CHAIR",is_active=True)
    db.add(chair)
    db.commit()
    old = record(db, practitioner=11, resource=chair.id)
    conflict = find_resource_conflict(db,employer_id=1,resource_id=chair.id,
        datetime_start=datetime(2026,10,19,14,30),duration_minutes=30)
    assert conflict is not None and conflict.id == old.id
    assert find_resource_conflict(db,employer_id=2,resource_id=chair.id,
        datetime_start=datetime(2026,10,19,14,30),duration_minutes=30) is None
    assert find_resource_conflict(db,employer_id=1,resource_id=chair.id,
        datetime_start=datetime(2026,10,19,14,30),duration_minutes=30,
        exclude_appointment_id=old.id) is None


@pytest.mark.parametrize("duration",[0,-1,-60])
def test_invalid_durations_rejected_by_create_bulk_and_update(duration):
    base={"datetime_start":datetime(2026,10,19,14,30),"duration_minutes":duration,"patient_name":"SYNTHETIC"}
    for schema in (AppointmentCreate,AppointmentImportItem):
        with pytest.raises(ValidationError):
            schema.model_validate(base)
    with pytest.raises(ValidationError):
        AppointmentUpdate.model_validate({"duration_minutes":duration})


def test_duration_aware_sql_predicate_under_representative_history(db):
    """Bound candidate rows in SQL, rather than loading all old appointments into Python."""
    start = datetime(2026,10,19,14,30)
    # Ten thousand historical rows, deliberately outside any bounded lookback window.
    db.add_all([
        models.Appointment(
            employer_id=1,patient_name="SYNTHETIC",praticien_id=10,
            datetime_start=start-timedelta(days=100+i%50, minutes=i//50),
            duration_minutes=30,status=models.AppointmentStatus.PREVU,
            scheduling_type=models.SchedulingType.EXACT_TIME,
        ) for i in range(3000)
    ])
    db.commit()
    long_row = record(db,start=datetime(2026,10,19,9),duration=360)
    candidate = existing_end_after(db,start)
    assert candidate is not None
    rows = db.query(models.Appointment).filter(
        models.Appointment.employer_id==1,
        models.Appointment.datetime_start < start+timedelta(minutes=30),
        candidate,
    ).all()
    assert [r.id for r in rows] == [long_row.id]
    assert [r.id for r in find(db)] == [long_row.id]


def test_end_to_end_overlap_boundary_is_strict(db):
    record(db,start=datetime(2026,10,19,9),duration=330)  # ends 14:30
    assert find(db) == []
