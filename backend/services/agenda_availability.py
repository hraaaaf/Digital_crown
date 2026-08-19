from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from backend.routers.agenda_settings import _settings_row
from backend.schemas.base import SchedulingType

_WEEKDAYS = (
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
)


def _agenda_schema_ready(db: Session) -> bool:
    """Read-only check: schema upgrades belong to Settings, never booking writes."""
    inspector = inspect(db.get_bind())
    tables = set(inspector.get_table_names())
    if not {"cabinet_settings", "agenda_exceptions"}.issubset(tables):
        return False
    settings_columns = {column["name"] for column in inspector.get_columns("cabinet_settings")}
    exception_columns = {column["name"] for column in inspector.get_columns("agenda_exceptions")}
    return {"employer_id", "weekly_schedule_json"}.issubset(settings_columns) and "employer_id" in exception_columns


def _local_naive(value: datetime) -> datetime:
    """Use the cabinet host's local wall clock for configured opening hours."""
    if value.tzinfo is not None:
        return value.astimezone().replace(tzinfo=None)
    return value


def _coerce_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return _local_naive(value)
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return _local_naive(parsed)


def _time_to_minutes(value: str) -> int:
    hour, minute = value.split(":", 1)
    return int(hour) * 60 + int(minute)


def _exception_reason(
    db: Session,
    employer_id: int,
    start: datetime,
    end: datetime,
) -> str | None:
    rows = db.execute(
        text(
            "SELECT start_date, end_date, reason FROM agenda_exceptions "
            "WHERE employer_id = :employer_id"
        ),
        {"employer_id": employer_id},
    ).mappings().all()
    for row in rows:
        exception_start = _coerce_datetime(row["start_date"])
        exception_end = _coerce_datetime(row["end_date"])
        if start < exception_end and end > exception_start:
            return row.get("reason") or "Fermeture du cabinet"
    return None


def validate_appointment_availability(
    db: Session,
    employer_id: int,
    datetime_start: datetime,
    duration_minutes: int,
    scheduling_type: SchedulingType | str,
) -> str | None:
    """Return a user-facing reason when an appointment violates Agenda settings.

    Legacy compatibility: until the additive R7 schema has been initialized by
    Settings, preserve historical booking behavior and do not mutate the DB here.
    """
    if duration_minutes <= 0:
        return "La durée du rendez-vous doit être positive."

    if not _agenda_schema_ready(db):
        return None
    settings = _settings_row(db, employer_id)
    if settings is None:
        return None

    start = _local_naive(datetime_start)
    end = start + timedelta(minutes=duration_minutes)
    if end.date() != start.date():
        return "Le rendez-vous ne peut pas dépasser minuit."

    weekday = _WEEKDAYS[start.weekday()]
    schedule = settings["weekly_schedule"][weekday]
    if not schedule.get("is_open", True):
        return "Le cabinet est fermé ce jour."

    exception = _exception_reason(db, employer_id, start, end)
    if exception:
        return f"Le cabinet est fermé sur ce créneau : {exception}."

    kind = getattr(scheduling_type, "value", scheduling_type)
    if kind != SchedulingType.EXACT_TIME.value:
        return None

    start_minutes = start.hour * 60 + start.minute
    end_minutes = start_minutes + duration_minutes
    morning_start = _time_to_minutes(schedule["morning_start"])
    morning_end = _time_to_minutes(schedule["morning_end"])

    if schedule.get("is_continuous", False):
        if start_minutes >= morning_start and end_minutes <= morning_end:
            return None
        return "Ce rendez-vous est en dehors des horaires d'ouverture du cabinet."

    afternoon_start = _time_to_minutes(schedule["afternoon_start"])
    afternoon_end = _time_to_minutes(schedule["afternoon_end"])
    fits_morning = start_minutes >= morning_start and end_minutes <= morning_end
    fits_afternoon = start_minutes >= afternoon_start and end_minutes <= afternoon_end
    if fits_morning or fits_afternoon:
        return None

    return "Ce rendez-vous chevauche une fermeture ou se situe hors des horaires d'ouverture."
