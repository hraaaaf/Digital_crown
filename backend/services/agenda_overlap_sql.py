"""Conservative SQL prefilter for existing appointments whose end is after start.

No fixed lookback: rows of any positive duration remain eligible. SQLite's
Julian-day float comparison includes a one-second tolerance; Python performs
the final exact datetime overlap check. PostgreSQL uses native intervals.
Other SQL dialects fall back to exact Python filtering without a lower bound.
"""
from sqlalchemy import func, literal_column
from backend import models


def existing_end_after(db, candidate_start):
    start = models.Appointment.datetime_start
    minutes = models.Appointment.duration_minutes
    dialect = db.get_bind().dialect.name
    if dialect == "postgresql":
        return start + minutes * literal_column("INTERVAL '1 minute'") > candidate_start
    if dialect == "sqlite":
        return func.julianday(start) + minutes / 1440.0 > func.julianday(candidate_start) - (1.0 / 86400.0)
    return None
