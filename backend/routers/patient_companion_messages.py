from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from backend import models
from backend.models_patient_companion import (
    PatientCompanionAccess,
    PatientCompanionIdentity,
    PatientCompanionMessage,
    PatientCompanionRemoteKeyset,
)
from backend.routers.auth import get_current_user
from backend.routers.patient_companion_common import (
    get_db,
    patient_identity,
    principal_for_access,
    staff_patient_or_404,
)
from backend.services.patient_companion_messages import (
    PC08_MAX_BODY_BYTES,
    normalize_message_body,
    normalize_uuid,
    recent_messages,
    serialize_message,
)
from backend.services.patient_companion_remote_worker import process_remote_envelope
from backend.utils.rate_limit import check_rate_limit

router = APIRouter()


class RemoteCommandEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")
    blob: str = Field(min_length=16, max_length=256 * 1024)


class StaffMessageCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    access_id: str = Field(min_length=36, max_length=36)
    client_message_id: str = Field(min_length=36, max_length=36)
    body: str = Field(min_length=1, max_length=4096)


class StaffMessageRead(BaseModel):
    model_config = ConfigDict(extra="forbid")
    access_id: str = Field(min_length=36, max_length=36)
    message_ids: list[str] = Field(min_length=1, max_length=50)


def _active_patient_access(
    db: Session,
    *,
    employer_id: int,
    patient_id: int,
    access_public_id: str,
) -> PatientCompanionAccess:
    access = db.query(PatientCompanionAccess).filter(
        PatientCompanionAccess.public_id == access_public_id,
        PatientCompanionAccess.employer_id == employer_id,
        PatientCompanionAccess.patient_id == patient_id,
        PatientCompanionAccess.revoked_at.is_(None),
    ).first()
    if access is None:
        raise HTTPException(status_code=404, detail="Accès Patient Companion introuvable.")
    return access


def _access_projection(rows: list[PatientCompanionAccess]) -> list[dict[str, Any]]:
    return [
        {
            "access_id": row.public_id,
            "relationship_type": row.relationship_type,
            "created_at": row.created_at,
        }
        for row in rows
    ]


@router.get("/admin/patients/{patient_id}/messages")
def staff_message_thread(
    patient_id: int,
    access_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=50),
    response: Response = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    patient = staff_patient_or_404(db, current_user, patient_id)
    employer_id = int(current_user.get_employer_id())
    accesses = db.query(PatientCompanionAccess).filter(
        PatientCompanionAccess.employer_id == employer_id,
        PatientCompanionAccess.patient_id == patient.id,
        PatientCompanionAccess.revoked_at.is_(None),
    ).order_by(PatientCompanionAccess.created_at.asc()).all()

    selected = None
    if access_id:
        selected = _active_patient_access(
            db,
            employer_id=employer_id,
            patient_id=patient.id,
            access_public_id=access_id,
        )
    elif len(accesses) == 1:
        selected = accesses[0]

    items = recent_messages(db, selected, limit=limit) if selected is not None else []
    if response is not None:
        response.headers["Cache-Control"] = "no-store"
    return {
        "accesses": _access_projection(accesses),
        "selected_access_id": selected.public_id if selected else None,
        "items": [serialize_message(row) for row in items],
        "max_body_bytes": PC08_MAX_BODY_BYTES,
    }


@router.post("/admin/patients/{patient_id}/messages", status_code=201)
def staff_send_message(
    patient_id: int,
    body: StaffMessageCreate,
    response: Response,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    patient = staff_patient_or_404(db, current_user, patient_id)
    employer_id = int(current_user.get_employer_id())
    access_public_id = normalize_uuid(body.access_id, code="INVALID_ACCESS_ID")
    client_message_id = normalize_uuid(body.client_message_id, code="INVALID_CLIENT_MESSAGE_ID")
    try:
        text = normalize_message_body(body.body)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None

    access = _active_patient_access(
        db,
        employer_id=employer_id,
        patient_id=patient.id,
        access_public_id=access_public_id,
    )
    existing = db.query(PatientCompanionMessage).filter(
        PatientCompanionMessage.access_id == access.id,
        PatientCompanionMessage.employer_id == employer_id,
        PatientCompanionMessage.patient_id == patient.id,
        PatientCompanionMessage.client_message_id == client_message_id,
    ).first()
    if existing is not None:
        if existing.sender_kind != "STAFF" or existing.body != text:
            raise HTTPException(status_code=409, detail="CLIENT_MESSAGE_CONFLICT")
        response.headers["Cache-Control"] = "no-store"
        return {"message": serialize_message(existing), "idempotent": True}

    row = PatientCompanionMessage(
        access_id=access.id,
        employer_id=employer_id,
        patient_id=patient.id,
        client_message_id=client_message_id,
        sender_kind="STAFF",
        sender_user_id=current_user.id,
        body=text,
    )
    db.add(row)
    db.flush()
    db.add(models.AuditLog(
        user_id=current_user.id,
        employer_id=employer_id,
        action="PATIENT_COMPANION_MESSAGE_SENT",
        resource_type="PatientCompanionMessage",
        resource_id=row.public_id,
        severity="INFO",
        details=f"access_id={access.public_id}; sender=STAFF",
    ))
    db.commit()
    db.refresh(row)
    response.headers["Cache-Control"] = "no-store"
    return {"message": serialize_message(row), "idempotent": False}


@router.post("/admin/patients/{patient_id}/messages/read")
def staff_mark_messages_read(
    patient_id: int,
    body: StaffMessageRead,
    response: Response,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    patient = staff_patient_or_404(db, current_user, patient_id)
    employer_id = int(current_user.get_employer_id())
    access_public_id = normalize_uuid(body.access_id, code="INVALID_ACCESS_ID")
    access = _active_patient_access(
        db,
        employer_id=employer_id,
        patient_id=patient.id,
        access_public_id=access_public_id,
    )
    try:
        message_ids = [normalize_uuid(value, code="INVALID_MESSAGE_ID") for value in body.message_ids]
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None

    rows = db.query(PatientCompanionMessage).filter(
        PatientCompanionMessage.access_id == access.id,
        PatientCompanionMessage.employer_id == employer_id,
        PatientCompanionMessage.patient_id == patient.id,
        PatientCompanionMessage.public_id.in_(message_ids),
        PatientCompanionMessage.sender_kind == "PATIENT",
    ).all()
    if len({row.public_id for row in rows}) != len(set(message_ids)):
        raise HTTPException(status_code=404, detail="Message Patient Companion introuvable.")

    now = datetime.utcnow()
    changed = 0
    for row in rows:
        if row.staff_read_at is None:
            row.staff_read_at = now
            row.staff_read_by_user_id = current_user.id
            changed += 1
    if changed:
        db.add(models.AuditLog(
            user_id=current_user.id,
            employer_id=employer_id,
            action="PATIENT_COMPANION_MESSAGES_READ",
            resource_type="PatientCompanionAccess",
            resource_id=access.public_id,
            severity="INFO",
            details=f"message_count={changed}",
        ))
    db.commit()
    response.headers["Cache-Control"] = "no-store"
    return {"status": "read", "message_ids": message_ids}


@router.post("/contexts/{access_id}/messages/remote-command")
def patient_message_remote_command(
    access_id: str,
    body: RemoteCommandEnvelope,
    request: Request,
    response: Response,
    identity: PatientCompanionIdentity = Depends(patient_identity),
    db: Session = Depends(get_db),
):
    check_rate_limit(request, scope="patient-companion-messages-remote-command")
    principal, _patient = principal_for_access(db, identity, access_id)
    access = db.query(PatientCompanionAccess).filter(
        PatientCompanionAccess.public_id == principal.access_id,
        PatientCompanionAccess.identity_id == principal.identity_id,
        PatientCompanionAccess.employer_id == principal.employer_id,
        PatientCompanionAccess.patient_id == principal.patient_id,
        PatientCompanionAccess.revoked_at.is_(None),
    ).first()
    if access is None:
        raise HTTPException(status_code=404, detail="Contexte patient introuvable.")
    keyset = db.query(PatientCompanionRemoteKeyset).filter(
        PatientCompanionRemoteKeyset.access_id == access.id,
        PatientCompanionRemoteKeyset.status == "ACTIVE",
        PatientCompanionRemoteKeyset.revoked_at.is_(None),
    ).first()
    if keyset is None:
        raise HTTPException(status_code=409, detail="Transport sécurisé Patient Companion non initialisé.")
    try:
        ack = process_remote_envelope(
            db,
            access=access,
            keyset=keyset,
            compact_jwe=body.blob,
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Commande distante Patient Companion invalide.") from None
    response.headers["Cache-Control"] = "no-store"
    return {"blob": ack}
