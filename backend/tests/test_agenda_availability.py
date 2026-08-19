from datetime import datetime

import backend.services.agenda_availability as availability
from backend.schemas.base import SchedulingType


class _Rows:
    def __init__(self, rows):
        self._rows = rows

    def mappings(self):
        return self

    def all(self):
        return self._rows


class _Db:
    def __init__(self, exceptions=None):
        self.exceptions = exceptions or []

    def execute(self, *_args, **_kwargs):
        return _Rows(self.exceptions)


def _week():
    day = {
        "is_open": True,
        "is_continuous": False,
        "morning_start": "09:00",
        "morning_end": "13:00",
        "afternoon_start": "14:00",
        "afternoon_end": "18:00",
    }
    return {
        key: dict(day)
        for key in (
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        )
    }


def _settings():
    return {"weekly_schedule": _week()}


def _wire(monkeypatch, settings):
    monkeypatch.setattr(availability, "_ensure_tenant_columns", lambda _db: None)
    monkeypatch.setattr(availability, "_settings_row", lambda _db, _employer_id: settings)


def test_legacy_install_without_settings_keeps_historical_behavior(monkeypatch):
    _wire(monkeypatch, None)
    assert availability.validate_appointment_availability(
        _Db(), 1, datetime(2026, 8, 17, 3, 0), 30, SchedulingType.EXACT_TIME
    ) is None


def test_exact_time_must_fit_entire_opening_window(monkeypatch):
    _wire(monkeypatch, _settings())
    assert availability.validate_appointment_availability(
        _Db(), 1, datetime(2026, 8, 17, 12, 30), 30, SchedulingType.EXACT_TIME
    ) is None
    assert "chevauche" in availability.validate_appointment_availability(
        _Db(), 1, datetime(2026, 8, 17, 12, 45), 30, SchedulingType.EXACT_TIME
    )
    assert availability.validate_appointment_availability(
        _Db(), 1, datetime(2026, 8, 17, 14, 0), 30, SchedulingType.EXACT_TIME
    ) is None
    assert "hors" in availability.validate_appointment_availability(
        _Db(), 1, datetime(2026, 8, 17, 17, 45), 30, SchedulingType.EXACT_TIME
    ) or "chevauche" in availability.validate_appointment_availability(
        _Db(), 1, datetime(2026, 8, 17, 17, 45), 30, SchedulingType.EXACT_TIME
    )


def test_closed_day_and_exception_are_rejected(monkeypatch):
    settings = _settings()
    settings["weekly_schedule"]["monday"]["is_open"] = False
    _wire(monkeypatch, settings)
    assert "fermé ce jour" in availability.validate_appointment_availability(
        _Db(), 1, datetime(2026, 8, 17, 10, 0), 30, SchedulingType.EXACT_TIME
    )

    settings["weekly_schedule"]["monday"]["is_open"] = True
    exceptions = [{
        "start_date": datetime(2026, 8, 17, 0, 0),
        "end_date": datetime(2026, 8, 17, 23, 59, 59),
        "reason": "Congés",
    }]
    error = availability.validate_appointment_availability(
        _Db(exceptions), 1, datetime(2026, 8, 17, 10, 0), 30, SchedulingType.EXACT_TIME
    )
    assert "Congés" in error


def test_flexible_booking_still_respects_closed_days_but_not_exact_clock(monkeypatch):
    _wire(monkeypatch, _settings())
    assert availability.validate_appointment_availability(
        _Db(), 1, datetime(2026, 8, 17, 13, 30), 30, SchedulingType.MORNING
    ) is None


def test_continuous_day_uses_single_interval(monkeypatch):
    settings = _settings()
    monday = settings["weekly_schedule"]["monday"]
    monday["is_continuous"] = True
    monday["morning_end"] = "17:00"
    _wire(monkeypatch, settings)
    assert availability.validate_appointment_availability(
        _Db(), 1, datetime(2026, 8, 17, 13, 30), 30, SchedulingType.EXACT_TIME
    ) is None
    assert "dehors" in availability.validate_appointment_availability(
        _Db(), 1, datetime(2026, 8, 17, 16, 45), 30, SchedulingType.EXACT_TIME
    )
