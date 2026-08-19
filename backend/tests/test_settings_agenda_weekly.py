import json

import pytest
from pydantic import ValidationError

from backend.routers.agenda_settings import _hydrate_settings_row, _legacy_weekly_schedule
from backend.schemas.agenda import AgendaDaySchedule, AgendaExceptionCreate, WeeklyAgendaSchedule


LEGACY_ROW = {
    "id": 1,
    "opening_time_morning": "09:00",
    "closing_time_morning": "13:00",
    "opening_time_afternoon": "14:00",
    "closing_time_afternoon": "18:00",
    "is_continuous": False,
    "agenda_mode": "EXACT",
    "use_tickets": True,
}


def _week():
    return {
        key: {
            "is_open": True,
            "is_continuous": False,
            "morning_start": "09:00",
            "morning_end": "13:00",
            "afternoon_start": "14:00",
            "afternoon_end": "18:00",
        }
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


def test_legacy_week_preserves_existing_global_hours_for_all_days():
    week = _legacy_weekly_schedule(LEGACY_ROW)
    assert len(week) == 7
    assert all(day["morning_start"] == "09:00" for day in week.values())
    assert all(day["afternoon_end"] == "18:00" for day in week.values())
    assert all(day["is_open"] is True for day in week.values())


def test_hydrate_settings_derives_week_when_column_is_null():
    hydrated = _hydrate_settings_row({**LEGACY_ROW, "weekly_schedule_json": None})
    assert hydrated["weekly_schedule"]["sunday"]["morning_start"] == "09:00"
    assert "weekly_schedule_json" not in hydrated


def test_hydrate_settings_prefers_persisted_week():
    week = _week()
    week["sunday"]["is_open"] = False
    hydrated = _hydrate_settings_row({**LEGACY_ROW, "weekly_schedule_json": json.dumps(week)})
    assert hydrated["weekly_schedule"]["sunday"]["is_open"] is False


def test_weekly_schedule_requires_all_seven_days():
    week = _week()
    week.pop("sunday")
    with pytest.raises(ValidationError):
        WeeklyAgendaSchedule(**week)


def test_day_schedule_rejects_overlapping_split_ranges():
    with pytest.raises(ValidationError):
        AgendaDaySchedule(
            is_open=True,
            is_continuous=False,
            morning_start="09:00",
            morning_end="14:30",
            afternoon_start="14:00",
            afternoon_end="18:00",
        )


def test_closed_day_does_not_require_meaningful_time_ranges():
    day = AgendaDaySchedule(
        is_open=False,
        morning_start="18:00",
        morning_end="09:00",
        afternoon_start="18:00",
        afternoon_end="09:00",
    )
    assert day.is_open is False


def test_exception_rejects_reversed_dates():
    with pytest.raises(ValidationError):
        AgendaExceptionCreate(
            start_date="2026-08-20T00:00:00",
            end_date="2026-08-19T23:59:59",
            reason="Congé",
            is_holiday=False,
        )
