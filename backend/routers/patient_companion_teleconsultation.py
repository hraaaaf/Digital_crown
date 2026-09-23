from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from backend import models
from backend.models_patient_companion import (
    PatientCompanionAccess,
    PatientCompanionAppointmentRef,
    PatientCompanionIdentity,
    PatientCompanionRemoteKeyset,
    PatientCompanionTeleconsultSession,
)
from backend.routers.auth import get_current_user
from backend.routers.patient_companion_common import (
    get_db,
    patient_identity,
    principal_for_access,
    staff_patient_or_404,
)
from backend.services.patient_companion_remote_worker import process_remote_envelope
from backend.services.patient_companion_teleconsultation import (
    add_signal,
    end_session,
    expire_if_needed,
    mark_connected,
    mark_joined,
    normalize_uuid,
    serialize_session,
    serialize_signal,
    sync_signals,
)
from backend.utils.rate_limit import check_rate_limit

router = APIRouter()


class RemoteCommandEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")
    blob: str = Field(min_length=16, max_length=256 * 1024)


class StaffSessionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    access_id: str = Field(min_length=36, max_length=36)
    appointment_ref: str | None = Field(default=None, min_length=36, max_length=36)
    ttl_minutes: int = Field(default=60, ge=5, le=240)


class StaffSessionAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    access_id: str = Field(min_length=36, max_length=36)


class StaffSignalCreate(StaffSessionAction):
    client_signal_id: str = Field(min_length=36, max_length=36)
    signal_type: str = Field(min_length=3, max_length=16)
    payload: dict[str, Any]


def _active_access(
    db: Session,
    *,
    employer_id: int,
    patient_id: int,
    access_id: str,
) -> PatientCompanionAccess:
    try:
        access_id = normalize_uuid(access_id, "INVALID_ACCESS_ID")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    row = db.query(PatientCompanionAccess).filter(
        PatientCompanionAccess.public_id == access_id,
        PatientCompanionAccess.employer_id == employer_id,
        PatientCompanionAccess.patient_id == patient_id,
        PatientCompanionAccess.revoked_at.is_(None),
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Accès Patient Companion introuvable.")
    return row


def _staff_session(
    db: Session,
    *,
    employer_id: int,
    patient_id: int,
    access: PatientCompanionAccess,
    session_id: str,
    lock: bool = False,
) -> PatientCompanionTeleconsultSession:
    try:
        session_id = normalize_uuid(session_id, "INVALID_SESSION_ID")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    q = db.query(PatientCompanionTeleconsultSession).filter(
        PatientCompanionTeleconsultSession.public_id == session_id,
        PatientCompanionTeleconsultSession.access_id == access.id,
        PatientCompanionTeleconsultSession.employer_id == employer_id,
        PatientCompanionTeleconsultSession.patient_id == patient_id,
    )
    if lock:
        q = q.with_for_update()
    row = q.first()
    if row is None:
        raise HTTPException(status_code=404, detail="Téléconsultation introuvable.")
    expire_if_needed(row)
    return row


@router.get("/admin/patients/{patient_id}/teleconsultations")
def staff_list_teleconsultations(
    patient_id: int,
    response: Response,
    access_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    patient = staff_patient_or_404(db, current_user, patient_id)
    employer_id = int(current_user.get_employer_id())
    q = db.query(PatientCompanionTeleconsultSession).filter(
        PatientCompanionTeleconsultSession.employer_id == employer_id,
        PatientCompanionTeleconsultSession.patient_id == patient.id,
    )
    if access_id:
        access = _active_access(db, employer_id=employer_id, patient_id=patient.id, access_id=access_id)
        q = q.filter(PatientCompanionTeleconsultSession.access_id == access.id)
    rows = q.order_by(PatientCompanionTeleconsultSession.id.desc()).limit(20).all()
    accesses = db.query(PatientCompanionAccess).filter(
        PatientCompanionAccess.employer_id == employer_id,
        PatientCompanionAccess.patient_id == patient.id,
        PatientCompanionAccess.revoked_at.is_(None),
    ).order_by(PatientCompanionAccess.created_at.asc()).all()
    changed = False
    for row in rows:
        changed = expire_if_needed(row) or changed
    if changed:
        db.commit()
    if response is not None:
        response.headers["Cache-Control"] = "no-store"
    access_by_id = {item.id: item.public_id for item in accesses}
    return {
        "accesses": [
            {
                "access_id": item.public_id,
                "relationship_type": item.relationship_type,
                "created_at": item.created_at,
            }
            for item in accesses
        ],
        "items": [
            {**serialize_session(row), "access_id": access_by_id.get(row.access_id)}
            for row in rows
        ],
    }


@router.post("/admin/patients/{patient_id}/teleconsultations", status_code=201)
def staff_create_teleconsultation(
    patient_id: int,
    body: StaffSessionCreate,
    response: Response,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    patient = staff_patient_or_404(db, current_user, patient_id)
    employer_id = int(current_user.get_employer_id())
    access = _active_access(db, employer_id=employer_id, patient_id=patient.id, access_id=body.access_id)

    appointment_ref_id = None
    if body.appointment_ref:
        try:
            ref_id = normalize_uuid(body.appointment_ref, "INVALID_APPOINTMENT_REF")
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from None
        ref = db.query(PatientCompanionAppointmentRef).filter(
            PatientCompanionAppointmentRef.public_id == ref_id,
            PatientCompanionAppointmentRef.employer_id == employer_id,
            PatientCompanionAppointmentRef.patient_id == patient.id,
        ).first()
        if ref is None:
            raise HTTPException(status_code=404, detail="Rendez-vous Patient Companion introuvable.")
        appointment_ref_id = ref.id

    now = datetime.utcnow()
    row = PatientCompanionTeleconsultSession(
        access_id=access.id,
        employer_id=employer_id,
        patient_id=patient.id,
        appointment_ref_id=appointment_ref_id,
        created_by_user_id=current_user.id,
        state="WAITING_PATIENT",
        created_at=now,
        expires_at=now + timedelta(minutes=body.ttl_minutes),
        staff_joined_at=now,
    )
    db.add(row)
    db.flush()
    db.add(models.AuditLog(
        user_id=current_user.id,
        employer_id=employer_id,
        action="PATIENT_COMPANION_TELECONSULT_CREATED",
        resource_type="PatientCompanionTeleconsultSession",
        resource_id=row.public_id,
        severity="INFO",
        details=f"access_id={access.public_id}",
    ))
    db.commit()
    db.refresh(row)
    response.headers["Cache-Control"] = "no-store"
    return {"session": {**serialize_session(row), "access_id": access.public_id}}


@router.post("/admin/patients/{patient_id}/teleconsultations/{session_id}/join")
def staff_join_teleconsultation(
    patient_id: int,
    session_id: str,
    body: StaffSessionAction,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    patient = staff_patient_or_404(db, current_user, patient_id)
    employer_id = int(current_user.get_employer_id())
    access = _active_access(db, employer_id=employer_id, patient_id=patient.id, access_id=body.access_id)
    row = _staff_session(db, employer_id=employer_id, patient_id=patient.id, access=access, session_id=session_id, lock=True)
    if row.state == "EXPIRED":
        raise HTTPException(status_code=409, detail="SESSION_EXPIRED")
    try:
        mark_joined(row, "STAFF")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    db.commit()
    return {"session": serialize_session(row)}


@router.post("/admin/patients/{patient_id}/teleconsultations/{session_id}/signals", status_code=201)
def staff_send_signal(
    patient_id: int,
    session_id: str,
    body: StaffSignalCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    patient = staff_patient_or_404(db, current_user, patient_id)
    employer_id = int(current_user.get_employer_id())
    access = _active_access(db, employer_id=employer_id, patient_id=patient.id, access_id=body.access_id)
    row = _staff_session(db, employer_id=employer_id, patient_id=patient.id, access=access, session_id=session_id, lock=True)
    if row.state == "EXPIRED":
        raise HTTPException(status_code=409, detail="SESSION_EXPIRED")
    try:
        signal = add_signal(
            db, row,
            sender_kind="STAFF",
            sender_user_id=current_user.id,
            client_signal_id=body.client_signal_id,
            signal_type=body.signal_type,
            payload=body.payload,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    db.commit()
    return {"signal": serialize_signal(signal)}


@router.get("/admin/patients/{patient_id}/teleconsultations/{session_id}/signals")
def staff_sync_signals(
    patient_id: int,
    session_id: str,
    access_id: str = Query(min_length=36, max_length=36),
    after_signal_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    patient = staff_patient_or_404(db, current_user, patient_id)
    employer_id = int(current_user.get_employer_id())
    access = _active_access(db, employer_id=employer_id, patient_id=patient.id, access_id=access_id)
    row = _staff_session(db, employer_id=employer_id, patient_id=patient.id, access=access, session_id=session_id, lock=True)
    try:
        signals = sync_signals(db, row, recipient_kind="STAFF", after_signal_id=after_signal_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    db.commit()
    return {"session": serialize_session(row), "signals": [serialize_signal(item) for item in signals]}


@router.post("/admin/patients/{patient_id}/teleconsultations/{session_id}/connected")
def staff_report_connected(
    patient_id: int,
    session_id: str,
    body: StaffSessionAction,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    patient = staff_patient_or_404(db, current_user, patient_id)
    employer_id = int(current_user.get_employer_id())
    access = _active_access(db, employer_id=employer_id, patient_id=patient.id, access_id=body.access_id)
    row = _staff_session(db, employer_id=employer_id, patient_id=patient.id, access=access, session_id=session_id, lock=True)
    if row.state == "EXPIRED":
        raise HTTPException(status_code=409, detail="SESSION_EXPIRED")
    try:
        mark_connected(row, "STAFF")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    db.commit()
    return {"session": serialize_session(row)}


@router.post("/admin/patients/{patient_id}/teleconsultations/{session_id}/end")
def staff_end_teleconsultation(
    patient_id: int,
    session_id: str,
    body: StaffSessionAction,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    patient = staff_patient_or_404(db, current_user, patient_id)
    employer_id = int(current_user.get_employer_id())
    access = _active_access(db, employer_id=employer_id, patient_id=patient.id, access_id=body.access_id)
    row = _staff_session(db, employer_id=employer_id, patient_id=patient.id, access=access, session_id=session_id, lock=True)
    end_session(row, "STAFF")
    db.add(models.AuditLog(
        user_id=current_user.id,
        employer_id=employer_id,
        action="PATIENT_COMPANION_TELECONSULT_ENDED",
        resource_type="PatientCompanionTeleconsultSession",
        resource_id=row.public_id,
        severity="INFO",
        details="actor=STAFF",
    ))
    db.commit()
    return {"session": serialize_session(row)}


@router.post("/contexts/{access_id}/teleconsultation/remote-command")
def patient_teleconsultation_remote_command(
    access_id: str,
    body: RemoteCommandEnvelope,
    request: Request,
    response: Response,
    identity: PatientCompanionIdentity = Depends(patient_identity),
    db: Session = Depends(get_db),
):
    principal, _patient = principal_for_access(db, identity, access_id)
    check_rate_limit(
        request,
        scope=f"patient-companion-teleconsult-remote-command:{principal.access_id}",
        max_attempts=600,
    )
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
        ack = process_remote_envelope(db, access=access, keyset=keyset, compact_jwe=body.blob)
    except ValueError:
        raise HTTPException(status_code=400, detail="Commande distante Patient Companion invalide.") from None
    response.headers["Cache-Control"] = "no-store"
    return {"blob": ack}
