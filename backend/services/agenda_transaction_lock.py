"""Serialize check+insert for canonical appointment bookings on PostgreSQL.

Postgres transaction advisory lock is scoped to the tenant (employer_id);
the caller MUST hold it through validation, INSERT and COMMIT. No lock is
acquired on SQLite/SQLCipher, whose cross-process booking serialization is
a separate deployment gate and is not certified by this PostgreSQL proof.
"""
from sqlalchemy import text


def lock_cabinet_booking(db, employer_id: int) -> bool:
    """Acquire a PostgreSQL transaction-scoped advisory lock for one cabinet.

    Requires default READ COMMITTED semantics for a fresh conflict read.
    Returns True when the real PostgreSQL lock is held, False otherwise.
    """
    if db.get_bind().dialect.name != "postgresql":
        return False
    db.execute(
        text("SELECT pg_advisory_xact_lock(1420958, :employer_id)"),
        {"employer_id": int(employer_id)},
    )
    return True
