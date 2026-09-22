from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from backend.models_patient_companion import (
    PatientCompanionAccess,
    PatientCompanionMessage,
)
from backend.services.patient_companion_remote_worker import RemoteDomainResult

PC08_MAX_BODY_BYTES = 4096
PC08_SYNC_LIMIT = 20
PC08_PATIENT_SENDS_PER_HOUR = 60


def normalize_message_body(raw: Any) -> str:
    if not isinstance(raw, str):
        raise ValueError("MESSAGE_BODY_INVALID")
    body = raw.strip()
    if not body:
        raise ValueError("MESSAGE_BODY_EMPTY")
    if len(body.encode("utf-8")) > PC08_MAX_BODY_BYTES:
        raise ValueError("MESSAGE_BODY_TOO_LARGE")
    return body


def normalize_uuid(raw: Any, *, code: str = "INVALID_ID") -> str:
    if not isinstance(raw, str):
        raise ValueError(code)
    try:
        value = str(uuid.UUID(raw))
    except (TypeError, ValueError):
        raise ValueError(code) from None
    return value


def serialize_message(row: PatientCompanionMessage) -> dict[str, Any]:
    return {
        "message_id": row.public_id,
        "client_message_id": row.client_message_id,
        "sender_kind": row.sender_kind,
        "body": row.body,
        "created_at": row.created_at.isoformat(),
        "staff_read_at": row.staff_read_at.isoformat() if row.staff_read_at else None,
        "patient_received_at": row.patient_received_at.isoformat() if row.patient_received_at else None,
        "patient_read_at": row.patient_read_at.isoformat() if row.patient_read_at else None,
    }


def _scoped_query(db: Session, access: PatientCompanionAccess):
    return db.query(PatientCompanionMessage).filter(
        PatientCompanionMessage.access_id == access.id,
        PatientCompanionMessage.employer_id == access.employer_id,
        PatientCompanionMessage.patient_id == access.patient_id,
    )


def recent_messages(
    db: Session,
    access: PatientCompanionAccess,
    *,
    limit: int = PC08_SYNC_LIMIT,
) -> list[PatientCompanionMessage]:
    rows = (
        _scoped_query(db, access)
        .order_by(PatientCompanionMessage.id.desc())
        .limit(limit)
        .all()
    )
    rows.reverse()
    return rows


def messages_before(
    db: Session,
    access: PatientCompanionAccess,
    *,
    before_message_id: str,
    limit: int = PC08_SYNC_LIMIT,
) -> list[PatientCompanionMessage]:
    cursor = _scoped_query(db, access).filter(
        PatientCompanionMessage.public_id == before_message_id,
    ).first()
    if cursor is None:
        raise ValueError("MESSAGE_CURSOR_NOT_FOUND")
    rows = (
        _scoped_query(db, access)
        .filter(PatientCompanionMessage.id < cursor.id)
        .order_by(PatientCompanionMessage.id.desc())
        .limit(limit)
        .all()
    )
    rows.reverse()
    return rows


def _reject(code: str) -> RemoteDomainResult:
    return RemoteDomainResult(status="REJECTED", response={"code": code})


def handle_message_send(
    db: Session,
    access: PatientCompanionAccess,
    payload: dict[str, Any],
) -> RemoteDomainResult:
    if set(payload) != {"client_message_id", "body"}:
        return _reject("INVALID_REQUEST")
    try:
        client_message_id = normalize_uuid(payload.get("client_message_id"), code="INVALID_CLIENT_MESSAGE_ID")
        body = normalize_message_body(payload.get("body"))
    except ValueError as exc:
        return _reject(str(exc))

    existing = _scoped_query(db, access).filter(
        PatientCompanionMessage.client_message_id == client_message_id,
    ).first()
    if existing is not None:
        if existing.sender_kind != "PATIENT" or existing.body != body:
            return _reject("CLIENT_MESSAGE_CONFLICT")
        return RemoteDomainResult(
            status="ACCEPTED",
            response={"code": "MESSAGE_STORED", "message": serialize_message(existing)},
        )

    cutoff = datetime.utcnow() - timedelta(hours=1)
    recent_count = _scoped_query(db, access).filter(
        PatientCompanionMessage.sender_kind == "PATIENT",
        PatientCompanionMessage.created_at >= cutoff,
    ).count()
    if recent_count >= PC08_PATIENT_SENDS_PER_HOUR:
        return _reject("MESSAGE_RATE_LIMITED")

    row = PatientCompanionMessage(
        access_id=access.id,
        employer_id=access.employer_id,
        patient_id=access.patient_id,
        client_message_id=client_message_id,
        sender_kind="PATIENT",
        sender_user_id=None,
        body=body,
    )
    db.add(row)
    db.flush()
    return RemoteDomainResult(
        status="ACCEPTED",
        response={"code": "MESSAGE_STORED", "message": serialize_message(row)},
    )


def handle_message_sync(
    db: Session,
    access: PatientCompanionAccess,
    payload: dict[str, Any],
) -> RemoteDomainResult:
    if not set(payload).issubset({"before_message_id"}):
        return _reject("INVALID_REQUEST")
    before = payload.get("before_message_id")
    try:
        if before is None:
            rows = recent_messages(db, access)
        else:
            cursor = normalize_uuid(before, code="INVALID_MESSAGE_CURSOR")
            rows = messages_before(db, access, before_message_id=cursor)
    except ValueError as exc:
        return _reject(str(exc))

    items = [serialize_message(row) for row in rows]
    has_more = False
    if rows:
        has_more = _scoped_query(db, access).filter(
            PatientCompanionMessage.id < rows[0].id,
        ).count() > 0
    return RemoteDomainResult(
        status="ACCEPTED",
        response={
            "code": "MESSAGE_SYNC",
            "items": items,
            "before_cursor": items[0]["message_id"] if items else before,
            "has_more": has_more,
            "limit": PC08_SYNC_LIMIT,
        },
    )


def _receipt_message_ids(payload: dict[str, Any]) -> list[str] | None:
    if set(payload) != {"message_ids"}:
        return None
    raw_ids = payload.get("message_ids")
    if not isinstance(raw_ids, list) or not (1 <= len(raw_ids) <= PC08_SYNC_LIMIT):
        return None
    try:
        return [normalize_uuid(value, code="INVALID_MESSAGE_ID") for value in raw_ids]
    except ValueError:
        return None


def _staff_messages_for_receipt(
    db: Session,
    access: PatientCompanionAccess,
    message_ids: list[str],
) -> list[PatientCompanionMessage]:
    rows = _scoped_query(db, access).filter(
        PatientCompanionMessage.public_id.in_(message_ids),
        PatientCompanionMessage.sender_kind == "STAFF",
    ).all()
    by_id = {row.public_id: row for row in rows}
    if any(message_id not in by_id for message_id in message_ids):
        return []
    return [by_id[message_id] for message_id in message_ids]


def handle_message_received(
    db: Session,
    access: PatientCompanionAccess,
    payload: dict[str, Any],
) -> RemoteDomainResult:
    message_ids = _receipt_message_ids(payload)
    if message_ids is None:
        return _reject("INVALID_REQUEST")
    rows = _staff_messages_for_receipt(db, access, message_ids)
    if len(rows) != len(message_ids):
        return _reject("MESSAGE_NOT_FOUND")
    now = datetime.utcnow()
    for row in rows:
        if row.patient_received_at is None:
            row.patient_received_at = now
    db.flush()
    return RemoteDomainResult(
        status="ACCEPTED",
        response={
            "code": "MESSAGE_RECEIVED",
            "message_ids": message_ids,
            "items": [serialize_message(row) for row in rows],
        },
    )


def handle_message_read(
    db: Session,
    access: PatientCompanionAccess,
    payload: dict[str, Any],
) -> RemoteDomainResult:
    message_ids = _receipt_message_ids(payload)
    if message_ids is None:
        return _reject("INVALID_REQUEST")
    rows = _staff_messages_for_receipt(db, access, message_ids)
    if len(rows) != len(message_ids):
        return _reject("MESSAGE_NOT_FOUND")
    now = datetime.utcnow()
    for row in rows:
        if row.patient_received_at is None:
            row.patient_received_at = now
        if row.patient_read_at is None:
            row.patient_read_at = now
    db.flush()
    return RemoteDomainResult(
        status="ACCEPTED",
        response={
            "code": "MESSAGE_READ",
            "message_ids": message_ids,
            "items": [serialize_message(row) for row in rows],
        },
    )


PC08_REMOTE_HANDLERS = {
    "message.send": handle_message_send,
    "message.sync": handle_message_sync,
    "message.received": handle_message_received,
    "message.read": handle_message_read,
}
