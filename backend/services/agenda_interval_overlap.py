"""Indexed, conservative SQL interval predicate with exact half-open final checks.

SQLite/SQLCipher julianday() uses floating point. For adjacent slots,
(start + duration/1440.0) may exceed the exact next start by one ULP.
The SQL predicate intentionally includes a tiny extra guard band;
Python datetime arithmetic then removes false positives, never dropping a
genuine overlap at the millisecond/microsecond boundary.
"""
from datetime import datetime, timedelta

from sqlalchemy import DateTime, Float, func, literal_column
from sqlalchemy.orm import Session


# 0.0864 seconds. This deliberately exceeds SQLite julianday 1-ms
# representational granularity + roundoff but does NOT decide occupation:
# all candidates are rechecked using integer timedelta arithmetic in Python.
_SQLITE_CONSERVATIVE_DAYS = 0.000001


def indexed_end_after(db: Session, candidate_start: datetime):
    dialect = db.get_bind().dialect.name
    if dialect == "postgresql":
        end_expr = literal_column(
            "(appointments.datetime_start + appointments.duration_minutes * INTERVAL '1 minute')",
            type_=DateTime(),
        )
        return end_expr > candidate_start
    if dialect == "sqlite":
        end_julian = literal_column(
            "(julianday(appointments.datetime_start) + appointments.duration_minutes / 1440.0)",
            type_=Float(),
        )
        return end_julian > (
            func.julianday(candidate_start) - _SQLITE_CONSERVATIVE_DAYS
        )
    raise RuntimeError("Unsupported clinical booking conflict dialect")


def exact_half_open_overlap(
    existing_start: datetime, existing_duration_minutes: int,
    candidate_start: datetime, candidate_end: datetime,
) -> bool:
    if existing_start.tzinfo is not None:
        existing_start = existing_start.replace(tzinfo=None)
    if candidate_start.tzinfo is not None:
        candidate_start = candidate_start.replace(tzinfo=None)
    if candidate_end.tzinfo is not None:
        candidate_end = candidate_end.replace(tzinfo=None)
    return (
        existing_start < candidate_end
        and existing_start + timedelta(minutes=existing_duration_minutes) > candidate_start
    )
