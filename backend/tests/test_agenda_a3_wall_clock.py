from datetime import datetime, timedelta, timezone

from backend.services.agenda_availability import _local_naive


def test_agenda_a3_preserves_explicit_wall_clock_when_dropping_timezone():
    aware = datetime(2026, 9, 16, 9, 30, tzinfo=timezone(timedelta(hours=1)))
    assert _local_naive(aware) == datetime(2026, 9, 16, 9, 30)
