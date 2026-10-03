from __future__ import annotations

import base64
import hashlib
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from backend import models
from backend.models_patient_companion import PatientCompanionAccess
from backend.routers.auth import get_current_user
from backend.routers.patient_companion_common import (
    PatientPrincipal,
    get_db,
    patient_identity,
    principal_for_access,
)
from backend.routers.workstation_mode import _find_workstation
from backend.services.qr_service import qr_service

router = APIRouter()
SESSION_TTL_SECONDS = 120


class StationPatientClaim(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=32, max_length=256)
    accessId: str = Field(min_length=36, max_length=36)


def _hash(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _station_or_423(request: Request, db: Session, current_user: models.User) -> models.WorkstationMode:
    row = _find_workstation(request, db, int(current_user.get_employer_id()))
    if row is None or row.default_experience != "station":
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="STATION_IDENTITY_REQUIRED")
    return row


def _expire_and_purge(db: Session, row: models.WorkstationPatientSession, now: datetime) -> bool:
    if row.purged_at is not None:
        return True
    if row.expires_at > now:
        return False
    row.patient_access_id = None
    row.patient_id = None
    row.purged_at = now
    db.commit()
    return True


@router.post("/patient-session", status_code=201)
def create_station_patient_session(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    workstation = _station_or_423(request, db, current_user)
    now = datetime.utcnow()

    db.query(models.WorkstationPatientSession).filter(
        models.WorkstationPatientSession.workstation_id == workstation.id,
        models.WorkstationPatientSession.purged_at.is_(None),
    ).update(
        {
            models.WorkstationPatientSession.patient_access_id: None,
            models.WorkstationPatientSession.patient_id: None,
            models.WorkstationPatientSession.purged_at: now,
        },
        synchronize_session=False,
    )

    raw = secrets.token_urlsafe(32)
    row = models.WorkstationPatientSession(
        employer_id=workstation.employer_id,
        workstation_id=workstation.id,
        claim_token_hash=_hash(raw),
        created_at=now,
        expires_at=now + timedelta(seconds=SESSION_TTL_SECONDS),
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    handoff_url = str(request.base_url).rstrip("/") + "/companion?stationSession=" + raw
    qr_data_url = "data:image/png;base64," + base64.b64encode(
        qr_service.generate_qr_bytes(handoff_url, qr_style="classic").getvalue()
    ).decode("ascii")
    response.headers["Cache-Control"] = "no-store"
    return {
        "sessionId": row.id,
        "handoffUrl": handoff_url,
        "qrDataUrl": qr_data_url,
        "expiresAt": row.expires_at,
        "nfcPayload": handoff_url,
    }


@router.post("/patient-session/claim")
def claim_station_patient_session(
    body: StationPatientClaim,
    response: Response,
    db: Session = Depends(get_db),
    identity=Depends(patient_identity),
):
    now = datetime.utcnow()
    row = db.query(models.WorkstationPatientSession).filter(
        models.WorkstationPatientSession.claim_token_hash == _hash(body.token),
        models.WorkstationPatientSession.purged_at.is_(None),
        models.WorkstationPatientSession.claimed_at.is_(None),
        models.WorkstationPatientSession.expires_at > now,
    ).first()
    if row is None:
        raise HTTPException(status_code=409, detail="STATION_SESSION_INVALID_OR_USED")

    principal, _patient = principal_for_access(db, identity, body.accessId)
    if int(principal.employer_id) != int(row.employer_id):
        raise HTTPException(status_code=404, detail="STATION_SESSION_NOT_FOUND")

    access = db.query(PatientCompanionAccess).filter(
        PatientCompanionAccess.public_id == principal.access_id,
        PatientCompanionAccess.identity_id == identity.id,
        PatientCompanionAccess.revoked_at.is_(None),
    ).first()
    if access is None:
        raise HTTPException(status_code=404, detail="PATIENT_CONTEXT_NOT_FOUND")

    updated = db.query(models.WorkstationPatientSession).filter(
        models.WorkstationPatientSession.id == row.id,
        models.WorkstationPatientSession.claimed_at.is_(None),
        models.WorkstationPatientSession.purged_at.is_(None),
        models.WorkstationPatientSession.expires_at > now,
    ).update(
        {
            models.WorkstationPatientSession.claimed_at: now,
            models.WorkstationPatientSession.patient_access_id: access.id,
            models.WorkstationPatientSession.patient_id: principal.patient_id,
        },
        synchronize_session=False,
    )
    if updated != 1:
        db.rollback()
        raise HTTPException(status_code=409, detail="STATION_SESSION_ALREADY_USED")
    db.commit()
    response.headers["Cache-Control"] = "no-store"
    return {"status": "identified", "sessionId": row.id}


@router.get("/patient-session/{session_id}")
def station_patient_session_status(
    session_id: str,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    workstation = _station_or_423(request, db, current_user)
    row = db.query(models.WorkstationPatientSession).filter(
        models.WorkstationPatientSession.id == session_id,
        models.WorkstationPatientSession.employer_id == workstation.employer_id,
        models.WorkstationPatientSession.workstation_id == workstation.id,
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="STATION_SESSION_NOT_FOUND")
    now = datetime.utcnow()
    if _expire_and_purge(db, row, now):
        return {"status": "expired", "sessionId": row.id}

    payload = {"status": "pending", "sessionId": row.id, "expiresAt": row.expires_at}
    if row.claimed_at is not None and row.patient_id is not None:
        patient = db.query(models.Patient).filter(
            models.Patient.id == row.patient_id,
            models.Patient.employer_id == row.employer_id,
            models.Patient.deleted_at.is_(None),
        ).first()
        if patient is None:
            raise HTTPException(status_code=409, detail="STATION_SESSION_PATIENT_UNAVAILABLE")
        payload = {
            "status": "identified",
            "sessionId": row.id,
            "displayName": f"{patient.prenom or ''} {patient.nom or ''}".strip(),
            "claimedAt": row.claimed_at,
        }
    response.headers["Cache-Control"] = "no-store"
    return payload


@router.post("/patient-session/{session_id}/purge", status_code=204)
def purge_station_patient_session(
    session_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    workstation = _station_or_423(request, db, current_user)
    now = datetime.utcnow()
    updated = db.query(models.WorkstationPatientSession).filter(
        models.WorkstationPatientSession.id == session_id,
        models.WorkstationPatientSession.employer_id == workstation.employer_id,
        models.WorkstationPatientSession.workstation_id == workstation.id,
        models.WorkstationPatientSession.purged_at.is_(None),
    ).update(
        {
            models.WorkstationPatientSession.patient_access_id: None,
            models.WorkstationPatientSession.patient_id: None,
            models.WorkstationPatientSession.purged_at: now,
        },
        synchronize_session=False,
    )
    if updated:
        db.commit()
    return Response(status_code=204)

