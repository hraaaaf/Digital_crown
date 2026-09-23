from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from backend.models_patient_companion import (
    PatientCompanionAccess,
    PatientCompanionTeleconsultSession,
    PatientCompanionTeleconsultSignal,
)
from backend.services.patient_companion_remote_worker import RemoteDomainResult

PC09_MAX_SIGNAL_BYTES = 24 * 1024
PC09_SIGNAL_SYNC_LIMIT = 5
PC09_TERMINAL_STATES = {"ENDED", "REJECTED", "EXPIRED", "FAILED"}
PC09_SIGNAL_TYPES = {"offer", "answer", "ice"}


def normalize_uuid(raw: Any, code: str) -> str:
    if not isinstance(raw, str):
        raise ValueError(code)
    try:
        return str(uuid.UUID(raw))
    except (TypeError, ValueError):
        raise ValueError(code) from None


def serialize_session(row: PatientCompanionTeleconsultSession) -> dict[str, Any]:
    return {
        "session_id": row.public_id,
        "state": row.state,
        "created_at": row.created_at.isoformat(),
        "expires_at": row.expires_at.isoformat(),
        "patient_joined_at": row.patient_joined_at.isoformat() if row.patient_joined_at else None,
        "staff_joined_at": row.staff_joined_at.isoformat() if row.staff_joined_at else None,
        "connected_at": row.connected_at.isoformat() if row.connected_at else None,
        "ended_at": row.ended_at.isoformat() if row.ended_at else None,
        "ended_by": row.ended_by,
        "failure_code": row.failure_code,
    }


def serialize_signal(row: PatientCompanionTeleconsultSignal) -> dict[str, Any]:
    return {
        "signal_id": row.public_id,
        "client_signal_id": row.client_signal_id,
        "sender_kind": row.sender_kind,
        "signal_type": row.signal_type,
        "payload": json.loads(row.payload_json),
        "created_at": row.created_at.isoformat(),
    }


def _reject(code: str) -> RemoteDomainResult:
    return RemoteDomainResult(status="REJECTED", response={"code": code})


def _scoped_session(
    db: Session,
    access: PatientCompanionAccess,
    session_id: str,
    *,
    lock: bool = False,
) -> PatientCompanionTeleconsultSession | None:
    q = db.query(PatientCompanionTeleconsultSession).filter(
        PatientCompanionTeleconsultSession.public_id == session_id,
        PatientCompanionTeleconsultSession.access_id == access.id,
        PatientCompanionTeleconsultSession.employer_id == access.employer_id,
        PatientCompanionTeleconsultSession.patient_id == access.patient_id,
    )
    if lock:
        q = q.with_for_update()
    return q.first()


def expire_if_needed(row: PatientCompanionTeleconsultSession) -> bool:
    if row.state in PC09_TERMINAL_STATES:
        return False
    if row.expires_at <= datetime.utcnow():
        row.state = "EXPIRED"
        row.ended_at = datetime.utcnow()
        row.ended_by = "SYSTEM"
        return True
    return False


def mark_joined(row: PatientCompanionTeleconsultSession, actor: str) -> None:
    now = datetime.utcnow()
    if row.state in PC09_TERMINAL_STATES:
        raise ValueError("SESSION_CLOSED")
    if actor == "PATIENT":
        row.patient_joined_at = row.patient_joined_at or now
    elif actor == "STAFF":
        row.staff_joined_at = row.staff_joined_at or now
    else:
        raise ValueError("INVALID_ACTOR")
    if row.patient_joined_at and row.staff_joined_at:
        row.state = "NEGOTIATING"
    elif row.patient_joined_at:
        row.state = "WAITING_STAFF"
    else:
        row.state = "WAITING_PATIENT"


def mark_connected(row: PatientCompanionTeleconsultSession, actor: str) -> None:
    now = datetime.utcnow()
    if row.state in PC09_TERMINAL_STATES:
        raise ValueError("SESSION_CLOSED")
    if not row.patient_joined_at or not row.staff_joined_at:
        raise ValueError("SESSION_NOT_NEGOTIATING")
    if actor == "PATIENT":
        row.patient_connected_at = row.patient_connected_at or now
    elif actor == "STAFF":
        row.staff_connected_at = row.staff_connected_at or now
    else:
        raise ValueError("INVALID_ACTOR")
    if row.patient_connected_at and row.staff_connected_at:
        row.state = "CONNECTED"
        row.connected_at = row.connected_at or max(row.patient_connected_at, row.staff_connected_at)
    else:
        row.state = "NEGOTIATING"


def purge_signals(db: Session, row: PatientCompanionTeleconsultSession) -> None:
    db.query(PatientCompanionTeleconsultSignal).filter(
        PatientCompanionTeleconsultSignal.session_id == row.id,
    ).delete(synchronize_session=False)


def end_session(row: PatientCompanionTeleconsultSession, actor: str) -> None:
    if row.state in PC09_TERMINAL_STATES:
        return
    row.state = "ENDED"
    row.ended_at = datetime.utcnow()
    row.ended_by = actor


def add_signal(
    db: Session,
    row: PatientCompanionTeleconsultSession,
    *,
    sender_kind: str,
    sender_user_id: int | None,
    client_signal_id: str,
    signal_type: str,
    payload: Any,
) -> PatientCompanionTeleconsultSignal:
    if row.state in PC09_TERMINAL_STATES:
        raise ValueError("SESSION_CLOSED")
    client_signal_id = normalize_uuid(client_signal_id, "INVALID_CLIENT_SIGNAL_ID")
    if signal_type not in PC09_SIGNAL_TYPES:
        raise ValueError("INVALID_SIGNAL_TYPE")
    if not isinstance(payload, dict):
        raise ValueError("INVALID_SIGNAL_PAYLOAD")
    encoded = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    if len(encoded.encode("utf-8")) > PC09_MAX_SIGNAL_BYTES:
        raise ValueError("SIGNAL_TOO_LARGE")
    existing = db.query(PatientCompanionTeleconsultSignal).filter(
        PatientCompanionTeleconsultSignal.session_id == row.id,
        PatientCompanionTeleconsultSignal.client_signal_id == client_signal_id,
    ).first()
    if existing is not None:
        if (
            existing.sender_kind != sender_kind
            or existing.signal_type != signal_type
            or existing.payload_json != encoded
        ):
            raise ValueError("CLIENT_SIGNAL_CONFLICT")
        return existing
    signal = PatientCompanionTeleconsultSignal(
        session_id=row.id,
        client_signal_id=client_signal_id,
        sender_kind=sender_kind,
        sender_user_id=sender_user_id,
        signal_type=signal_type,
        payload_json=encoded,
    )
    db.add(signal)
    db.flush()
    return signal


def sync_signals(
    db: Session,
    row: PatientCompanionTeleconsultSession,
    *,
    recipient_kind: str,
    after_signal_id: str | None,
) -> list[PatientCompanionTeleconsultSignal]:
    q = db.query(PatientCompanionTeleconsultSignal).filter(
        PatientCompanionTeleconsultSignal.session_id == row.id,
        PatientCompanionTeleconsultSignal.sender_kind != recipient_kind,
    )
    if after_signal_id:
        cursor_id = normalize_uuid(after_signal_id, "INVALID_SIGNAL_CURSOR")
        cursor = db.query(PatientCompanionTeleconsultSignal).filter(
            PatientCompanionTeleconsultSignal.session_id == row.id,
            PatientCompanionTeleconsultSignal.public_id == cursor_id,
        ).first()
        if cursor is None:
            raise ValueError("SIGNAL_CURSOR_NOT_FOUND")
        q = q.filter(PatientCompanionTeleconsultSignal.id > cursor.id)
    return q.order_by(PatientCompanionTeleconsultSignal.id.asc()).limit(PC09_SIGNAL_SYNC_LIMIT).all()


def handle_teleconsult_list(
    db: Session,
    access: PatientCompanionAccess,
    payload: dict[str, Any],
) -> RemoteDomainResult:
    if payload:
        return _reject("INVALID_REQUEST")
    rows = (
        db.query(PatientCompanionTeleconsultSession)
        .filter(
            PatientCompanionTeleconsultSession.access_id == access.id,
            PatientCompanionTeleconsultSession.employer_id == access.employer_id,
            PatientCompanionTeleconsultSession.patient_id == access.patient_id,
        )
        .order_by(PatientCompanionTeleconsultSession.id.desc())
        .limit(20)
        .all()
    )
    for row in rows:
        if expire_if_needed(row):
            purge_signals(db, row)
    return RemoteDomainResult(
        status="ACCEPTED",
        response={"code": "SESSION_LIST", "items": [serialize_session(row) for row in rows]},
    )


def handle_teleconsult_join(
    db: Session,
    access: PatientCompanionAccess,
    payload: dict[str, Any],
) -> RemoteDomainResult:
    if set(payload) != {"session_id"}:
        return _reject("INVALID_REQUEST")
    try:
        session_id = normalize_uuid(payload.get("session_id"), "INVALID_SESSION_ID")
    except ValueError as exc:
        return _reject(str(exc))
    row = _scoped_session(db, access, session_id, lock=True)
    if row is None:
        return _reject("SESSION_NOT_FOUND")
    if expire_if_needed(row):
        return _reject("SESSION_EXPIRED")
    try:
        mark_joined(row, "PATIENT")
    except ValueError as exc:
        return _reject(str(exc))
    db.flush()
    return RemoteDomainResult(status="ACCEPTED", response={"code": "SESSION_JOINED", "session": serialize_session(row)})


def handle_teleconsult_signal(
    db: Session,
    access: PatientCompanionAccess,
    payload: dict[str, Any],
) -> RemoteDomainResult:
    if set(payload) != {"session_id", "client_signal_id", "signal_type", "payload"}:
        return _reject("INVALID_REQUEST")
    try:
        session_id = normalize_uuid(payload.get("session_id"), "INVALID_SESSION_ID")
    except ValueError as exc:
        return _reject(str(exc))
    row = _scoped_session(db, access, session_id, lock=True)
    if row is None:
        return _reject("SESSION_NOT_FOUND")
    if expire_if_needed(row):
        return _reject("SESSION_EXPIRED")
    try:
        signal = add_signal(
            db, row,
            sender_kind="PATIENT",
            sender_user_id=None,
            client_signal_id=payload.get("client_signal_id"),
            signal_type=str(payload.get("signal_type") or ""),
            payload=payload.get("payload"),
        )
    except ValueError as exc:
        return _reject(str(exc))
    return RemoteDomainResult(status="ACCEPTED", response={"code": "SIGNAL_STORED", "signal": serialize_signal(signal)})


def handle_teleconsult_sync(
    db: Session,
    access: PatientCompanionAccess,
    payload: dict[str, Any],
) -> RemoteDomainResult:
    if not set(payload).issubset({"session_id", "after_signal_id"}) or "session_id" not in payload:
        return _reject("INVALID_REQUEST")
    try:
        session_id = normalize_uuid(payload.get("session_id"), "INVALID_SESSION_ID")
    except ValueError as exc:
        return _reject(str(exc))
    row = _scoped_session(db, access, session_id, lock=True)
    if row is None:
        return _reject("SESSION_NOT_FOUND")
    if expire_if_needed(row):
        purge_signals(db, row)
    try:
        signals = sync_signals(
            db, row,
            recipient_kind="PATIENT",
            after_signal_id=payload.get("after_signal_id"),
        )
    except ValueError as exc:
        return _reject(str(exc))
    return RemoteDomainResult(
        status="ACCEPTED",
        response={
            "code": "SESSION_SYNC",
            "session": serialize_session(row),
            "signals": [serialize_signal(item) for item in signals],
        },
    )


def handle_teleconsult_connected(
    db: Session,
    access: PatientCompanionAccess,
    payload: dict[str, Any],
) -> RemoteDomainResult:
    if set(payload) != {"session_id"}:
        return _reject("INVALID_REQUEST")
    try:
        session_id = normalize_uuid(payload.get("session_id"), "INVALID_SESSION_ID")
    except ValueError as exc:
        return _reject(str(exc))
    row = _scoped_session(db, access, session_id, lock=True)
    if row is None:
        return _reject("SESSION_NOT_FOUND")
    if expire_if_needed(row):
        return _reject("SESSION_EXPIRED")
    try:
        mark_connected(row, "PATIENT")
    except ValueError as exc:
        return _reject(str(exc))
    db.flush()
    return RemoteDomainResult(status="ACCEPTED", response={"code": "PEER_CONNECTED", "session": serialize_session(row)})


def handle_teleconsult_end(
    db: Session,
    access: PatientCompanionAccess,
    payload: dict[str, Any],
) -> RemoteDomainResult:
    if set(payload) != {"session_id"}:
        return _reject("INVALID_REQUEST")
    try:
        session_id = normalize_uuid(payload.get("session_id"), "INVALID_SESSION_ID")
    except ValueError as exc:
        return _reject(str(exc))
    row = _scoped_session(db, access, session_id, lock=True)
    if row is None:
        return _reject("SESSION_NOT_FOUND")
    end_session(row, "PATIENT")
    purge_signals(db, row)
    db.flush()
    return RemoteDomainResult(status="ACCEPTED", response={"code": "SESSION_ENDED", "session": serialize_session(row)})


PC09_REMOTE_HANDLERS = {
    "teleconsult.list": handle_teleconsult_list,
    "teleconsult.join": handle_teleconsult_join,
    "teleconsult.signal": handle_teleconsult_signal,
    "teleconsult.sync": handle_teleconsult_sync,
    "teleconsult.connected": handle_teleconsult_connected,
    "teleconsult.end": handle_teleconsult_end,
}
