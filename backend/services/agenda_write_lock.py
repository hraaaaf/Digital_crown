"""Per-cabinet transaction serialization for appointment mutations.

The lock must be acquired BEFORE reading appointment conflicts. It survives
through the caller's commit/rollback. An advisory transaction lock is used on
PostgreSQL; SQLite acquires a write transaction up front (same strategy as
presence-confirmation elsewhere in this router).

Only supported engines are accepted; failing to acquire the lock never means
"no conflicts". This does not change wall-clock or DST semantics.
"""
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session


# Namespaced 64-bit key prevents collisions with other advisory lock families.
_PG_LOCK_NAMESPACE = 0xDC07


def lock_cabinet_appointment_writes(db: Session, employer_id: int) -> None:
    dialect = db.get_bind().dialect.name
    try:
        if dialect == "postgresql":
            key = (_PG_LOCK_NAMESPACE << 32) | (int(employer_id) & 0xFFFFFFFF)
            db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": key})
        elif dialect == "sqlite":
            # Acquire SQLite's writer lock without an implicit COMMIT: Patient
            # Companion already owns an uncommitted replay receipt and its
            # booking must commit/rollback atomically with that receipt.
            # A no-op UPDATE still acquires the SQLite writer reservation.
            db.execute(text("UPDATE appointments SET id=id WHERE 1=0"))
        else:
            raise HTTPException(
                status_code=503,
                detail="Moteur de réservation non compatible avec le verrouillage sécurisé.",
            )
    except OperationalError as exc:
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail="Agenda temporairement occupé. Réessayez dans quelques secondes.",
        ) from exc
