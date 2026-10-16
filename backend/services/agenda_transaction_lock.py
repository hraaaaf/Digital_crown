"""Serialize the canonical availability-check-and-insert in one DB transaction.

PostgreSQL: tenant-scoped transaction advisory lock.
SQLite/SQLCipher: acquire a real database writer lock with an UPDATE that
matches no appointments (and therefore changes no clinical row). SQLite has
one writer per database; competing bookings wait or fail closed on busy/locked.
The caller MUST not commit between this fence, conflict check, and INSERT.
"""
from sqlalchemy import text


def lock_cabinet_booking(db, employer_id: int) -> bool:
    """Hold a DB-level transactional booking write lock through final COMMIT.

    In SQLite/SQLCipher a no-op UPDATE acquires a RESERVED write lock even
    if the predicate matches no rows. Avoid BEGIN IMMEDIATE here: /bot/execute
    already holds a write transaction for the pending->executing claim.
    """
    dialect = db.get_bind().dialect.name
    if dialect == "postgresql":
        db.execute(
            text("SELECT pg_advisory_xact_lock(1420958, :employer_id)"),
            {"employer_id": int(employer_id)},
        )
        return True
    if dialect == "sqlite":
        db.execute(text("UPDATE appointments SET id = id WHERE 1 = 0"))
        return True
    # Unknown dialect cannot silently skip concurrency protection.
    raise RuntimeError("Booking transaction lock unavailable for database dialect")
