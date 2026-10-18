"""Shared per-access transaction barrier for Patient Companion authorizations.

Every remote command (HTTP or Relay) acquires this lock before reloading the
principal and keyset; staff revocation acquires the same lock before updating
them. Thus a committed revoke cannot be followed by a command mutation based
on objects that were loaded before the revoke.

Order for a remote booking: patient-access barrier -> cabinet appointment lock.
The staff revocation path only acquires the patient-access barrier.
"""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session


_ACCESS_LOCK_NAMESPACE = 0xDC08


def lock_patient_access_transaction(db: Session, access_id: int) -> None:
    identifier = int(access_id)
    if identifier <= 0 or identifier > 0xFFFFFFFF:
        raise HTTPException(status_code=503, detail="Accès patient indisponible.")
    try:
        if db.get_bind().dialect.name == "postgresql":
            key = (_ACCESS_LOCK_NAMESPACE << 32) | identifier
            db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": key})
        elif db.get_bind().dialect.name == "sqlite":
            # SQLite cannot use advisory locks; this obtains the exclusive
            # write reservation without committing pending receipt/outbox data.
            db.execute(text(
                "UPDATE patient_companion_accesses SET id=id WHERE id=:access_id"
            ), {"access_id": identifier})
        else:
            raise HTTPException(
                status_code=503, detail="Verrouillage sécurisé des accès patient indisponible.",
            )
    except OperationalError as exc:
        db.rollback()
        raise HTTPException(
            status_code=503, detail="Accès patient temporairement occupé.",
        ) from exc
