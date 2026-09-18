from datetime import datetime, timedelta, timezone
from pathlib import Path

from backend.routers.appointments import _naive_datetime


def test_api_datetime_is_interpreted_as_cabinet_wall_clock_not_runner_timezone():
    aware = datetime(2026, 9, 18, 9, 30, tzinfo=timezone(timedelta(hours=1)))
    assert _naive_datetime(aware) == datetime(2026, 9, 18, 9, 30)


def test_a5_contract_soft_delete_and_active_filters():
    text = Path("backend/routers/appointments.py").read_text(encoding="utf-8")
    assert "db.delete(db_appt)" not in text
    assert "db_appt.deleted_at = datetime.now()" in text
    assert text.count("models.Appointment.deleted_at.is_(None)") >= 4


def test_a5_bulk_persists_a4_resource_assignment():
    text = Path("backend/routers/appointments.py").read_text(encoding="utf-8")
    assert "resource_id=item.resource_id" in text


def test_a5_migration_extends_a4_single_head():
    text = Path("alembic/versions/a5th0000005_agenda_temporal_history.py").read_text(encoding="utf-8")
    assert 'down_revision: Union[str, None] = "a4rs0000004"' in text
    assert '"deleted_at"' in text
    assert '"deleted_by"' in text
