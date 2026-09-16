from __future__ import annotations

import json
from datetime import date, datetime, timedelta
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
    """Read-only check: schema upgrades belong to Settings/startup, never booking writes."""
    inspector = inspect(db.get_bind())
    tables = set(inspector.get_table_names())
    if not {"cabinet_settings", "agenda_exceptions"}.issubset(tables):
        return False
    settings_columns = {column["name"] for column in inspector.get_columns("cabinet_settings")}
    exception_columns = {column["name"] for column in inspector.get_columns("agenda_exceptions")}
    return {"employer_id", "weekly_schedule_json"}.issubset(settings_columns) and "employer_id" in exception_columns


def _practitioner_schema_ready(db: Session) -> bool:
    inspector = inspect(db.get_bind())
    tables = set(inspector.get_table_names())
    return {"practitioner_agenda_settings", "practitioner_agenda_exceptions"}.issubset(tables)


def _local_naive(value: datetime) -> datetime:
    """Preserve the cabinet wall-clock value; never convert through the runner/server timezone."""
    return value.replace(tzinfo=None) if value.tzinfo is not None else value


def _coerce_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return _local_naive(value)
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return _local_naive(parsed)


def _time_to_minutes(value: str) -> int:
    hour, minute = value.split(":", 1)
    return int(hour) * 60 + int(minute)


def _exception_reason(db: Session, employer_id: int, start: datetime, end: datetime) -> str | None:
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


def _load_practitioner_schedule(
    db: Session,
    employer_id: int,
    practitioner_id: int | None,
) -> dict | None:
    """None means inheritance; an empty dict means an invalid explicit configuration."""
    if practitioner_id is None or not _practitioner_schema_ready(db):
        return None
    raw = db.execute(
        text(
            "SELECT weekly_schedule_json FROM practitioner_agenda_settings "
            "WHERE employer_id = :employer_id AND practitioner_id = :practitioner_id "
            "ORDER BY id LIMIT 1"
        ),
        {"employer_id": employer_id, "practitioner_id": practitioner_id},
    ).scalar_one_or_none()
    if raw is None:
        return None
    try:
        value = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _practitioner_exception_reason(
    db: Session,
    employer_id: int,
    practitioner_id: int | None,
    start: datetime,
    end: datetime,
) -> str | None:
    if practitioner_id is None or not _practitioner_schema_ready(db):
        return None
    rows = db.execute(
        text(
            "SELECT start_date, end_date, reason FROM practitioner_agenda_exceptions "
            "WHERE employer_id = :employer_id AND practitioner_id = :practitioner_id"
        ),
        {"employer_id": employer_id, "practitioner_id": practitioner_id},
    ).mappings().all()
    for row in rows:
        exception_start = _coerce_datetime(row["start_date"])
        exception_end = _coerce_datetime(row["end_date"])
        if start < exception_end and end > exception_start:
            return row.get("reason") or "Indisponibilité praticien"
    return None


def _cabinet_exact_error(start: datetime, end: datetime, schedule: dict) -> str | None:
    start_minutes = start.hour * 60 + start.minute
    end_minutes = start_minutes + int((end - start).total_seconds() // 60)
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


def _normalized_practitioner_intervals(schedule: dict, weekday: str) -> list[tuple[int, int]] | None:
    day = schedule.get(weekday)
    if not isinstance(day, dict):
        return None
    intervals = day.get("intervals", [])
    if not isinstance(intervals, list):
        return None
    normalized: list[tuple[int, int]] = []
    try:
        for interval in intervals:
            interval_start = _time_to_minutes(interval["start"])
            interval_end = _time_to_minutes(interval["end"])
            if interval_start >= interval_end:
                raise ValueError
            normalized.append((interval_start, interval_end))
    except (KeyError, TypeError, ValueError):
        return None
    normalized.sort()
    if any(previous[1] > current[0] for previous, current in zip(normalized, normalized[1:])):
        return None
    return normalized


def _practitioner_exact_error(start: datetime, end: datetime, schedule: dict, weekday: str) -> str | None:
    normalized = _normalized_practitioner_intervals(schedule, weekday)
    if normalized is None:
        return "Les horaires individuels du praticien sont invalides. Corrigez-les dans Réglages."
    if not normalized:
        return "Ce praticien ne travaille pas ce jour."

    start_minutes = start.hour * 60 + start.minute
    end_minutes = start_minutes + int((end - start).total_seconds() // 60)
    if any(start_minutes >= interval_start and end_minutes <= interval_end for interval_start, interval_end in normalized):
        return None

    if start_minutes >= normalized[0][0] and end_minutes <= normalized[-1][1]:
        return "Ce créneau correspond à une pause du praticien."
    return "Ce rendez-vous est en dehors des horaires de ce praticien."


def get_practitioner_day_availability(
    db: Session,
    employer_id: int,
    practitioner_id: int,
    target_date: date,
) -> dict:
    """Read the practitioner layer used by the synchronized A3 grid."""
    schedule = _load_practitioner_schedule(db, employer_id, practitioner_id)
    day_start = datetime.combine(target_date, datetime.min.time())
    day_end = day_start + timedelta(days=1)
    exceptions: list[dict] = []
    if _practitioner_schema_ready(db):
        rows = db.execute(
            text(
                "SELECT id, start_date, end_date, reason FROM practitioner_agenda_exceptions "
                "WHERE employer_id = :employer_id AND practitioner_id = :practitioner_id "
                "AND start_date < :day_end AND end_date > :day_start "
                "ORDER BY start_date, id"
            ),
            {
                "employer_id": employer_id,
                "practitioner_id": practitioner_id,
                "day_start": day_start,
                "day_end": day_end,
            },
        ).mappings().all()
        exceptions = [
            {
                "id": row["id"],
                "start_date": _coerce_datetime(row["start_date"]).isoformat(),
                "end_date": _coerce_datetime(row["end_date"]).isoformat(),
                "reason": row.get("reason") or "Indisponibilité praticien",
            }
            for row in rows
        ]

    weekday = _WEEKDAYS[target_date.weekday()]
    intervals: list[dict] = []
    config_error = False
    if schedule is not None:
        normalized = _normalized_practitioner_intervals(schedule, weekday)
        if normalized is None:
            config_error = True
        else:
            day = schedule.get(weekday) or {}
            intervals = list(day.get("intervals", []))

    return {
        "date": target_date.isoformat(),
        "inherits_cabinet": schedule is None,
        "config_error": config_error,
        "intervals": intervals,
        "exceptions": exceptions,
    }


def validate_appointment_availability(
    db: Session,
    employer_id: int,
    datetime_start: datetime,
    duration_minutes: int,
    scheduling_type: SchedulingType | str,
    practitioner_id: int | None = None,
) -> str | None:
    """Validate effective availability = cabinet ∩ practitioner, fail-closed for invalid overrides."""
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
    if kind == SchedulingType.EXACT_TIME.value:
        cabinet_error = _cabinet_exact_error(start, end, schedule)
        if cabinet_error:
            return cabinet_error

    practitioner_exception = _practitioner_exception_reason(
        db, employer_id, practitioner_id, start, end
    )
    if practitioner_exception:
        return f"Ce praticien est indisponible sur ce créneau : {practitioner_exception}."

    practitioner_schedule = _load_practitioner_schedule(db, employer_id, practitioner_id)
    if practitioner_schedule is None:
        return None
    if not practitioner_schedule:
        return "Les horaires individuels du praticien sont invalides. Corrigez-les dans Réglages."

    normalized = _normalized_practitioner_intervals(practitioner_schedule, weekday)
    if normalized is None:
        return "Les horaires individuels du praticien sont invalides. Corrigez-les dans Réglages."
    if not normalized:
        return "Ce praticien ne travaille pas ce jour."

    if kind != SchedulingType.EXACT_TIME.value:
        return None
    return _practitioner_exact_error(start, end, practitioner_schedule, weekday)
