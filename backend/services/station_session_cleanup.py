"""V1.5-04.6: bounded, independently scheduled cleanup of expired Station identities.

This scrubs patient references even if the shared kiosk and personal Companion
never make another request. Access checks still fail closed at the exact TTL;
the sweep is privacy retention cleanup, not a substitute for authorization.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from backend import models

STATION_SESSION_SWEEP_BATCH_SIZE = 100
STATION_SESSION_SWEEP_INTERVAL_SECONDS = 30
TTL_PURGE_ACTION = "STATION_DOCUMENT_SESSION_PURGED_TTL"


def purge_expired_station_session_on_read(
    db: Session,
    *,
    session_id: str,
    employer_id: int,
    now: datetime,
    actor: str,
) -> bool:
    """Request-triggered TTL scrub, sharing the same conditional audit contract.

    A concurrent periodic sweeper may win; then no second audit is written.
    """
    if actor not in {"ttl_station_read", "ttl_phone_read"}:
        raise ValueError("STATION_SESSION_INVALID_TTL_ACTOR")
    updated = db.query(models.WorkstationPatientSession).filter(
        models.WorkstationPatientSession.id == session_id,
        models.WorkstationPatientSession.employer_id == employer_id,
        models.WorkstationPatientSession.expires_at <= now,
        models.WorkstationPatientSession.purged_at.is_(None),
    ).update({
        models.WorkstationPatientSession.patient_id: None,
        models.WorkstationPatientSession.patient_access_id: None,
        models.WorkstationPatientSession.purged_at: now,
    }, synchronize_session=False)
    if updated == 1:
        db.add(models.AuditLog(
            employer_id=employer_id,
            user_id=None,
            action=TTL_PURGE_ACTION,
            resource_type="WorkstationPatientSession",
            resource_id=session_id,
            details=f"patient_binding_cleared=true;actor={actor}",
        ))
        db.commit()
    return updated == 1


def purge_expired_station_sessions(
    db: Session,
    *,
    now: datetime | None = None,
    batch_size: int = STATION_SESSION_SWEEP_BATCH_SIZE,
) -> int:
    """Atomically clear expired patient links and write a non-identifying audit.

    Only non-purged rows with an expired server deadline can be modified.
    A conditional update protects a session against double sweeps or races
    with user-requested purge. Run this in its own short-lived DB session.
    """
    if not 1 <= batch_size <= 1000:
        raise ValueError("STATION_SESSION_SWEEP_INVALID_BATCH")
    deadline = now or datetime.utcnow()
    candidates = db.query(
        models.WorkstationPatientSession.id,
        models.WorkstationPatientSession.employer_id,
    ).filter(
        models.WorkstationPatientSession.expires_at <= deadline,
        models.WorkstationPatientSession.purged_at.is_(None),
    ).order_by(
        models.WorkstationPatientSession.expires_at.asc(),
        models.WorkstationPatientSession.id.asc(),
    ).limit(batch_size).all()
    changed_count = 0
    for session_id, employer_id in candidates:
        updated = db.query(models.WorkstationPatientSession).filter(
            models.WorkstationPatientSession.id == session_id,
            models.WorkstationPatientSession.expires_at <= deadline,
            models.WorkstationPatientSession.purged_at.is_(None),
        ).update({
            models.WorkstationPatientSession.patient_id: None,
            models.WorkstationPatientSession.patient_access_id: None,
            models.WorkstationPatientSession.purged_at: deadline,
        }, synchronize_session=False)
        if updated != 1:
            continue
        db.add(models.AuditLog(
            employer_id=employer_id,
            user_id=None,
            action=TTL_PURGE_ACTION,
            resource_type="WorkstationPatientSession",
            resource_id=session_id,
            details="patient_binding_cleared=true;actor=ttl_sweep",
        ))
        changed_count += 1
    if changed_count:
        db.commit()
    return changed_count
