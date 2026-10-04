from __future__ import annotations

import base64
import hashlib
import re
import secrets
import unicodedata
from datetime import datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend import models
from backend.models_patient_companion import PatientCompanionAccess
from backend.routers.auth import get_current_user, require_permission
from backend.routers.patient_companion_common import (
    get_db,
    patient_identity,
    principal_for_access,
)
from backend.routers.workstation_mode import _find_workstation, _require_pin
from backend.services.qr_service import qr_service
from backend.services.station_arrival_bridge import (
    list_station_patient_appointments_for_today,
    mark_station_appointment_arrived,
    serialize_station_appointment,
    station_appointment_for_today,
)

router = APIRouter()
SESSION_TTL_SECONDS = 120
FALLBACK_FAILURE_LIMIT = 5
FALLBACK_FAILURE_WINDOW_SECONDS = 15 * 60
FALLBACK_MODES = {"phone_dob", "name_dob", "disabled"}


class StationPatientClaim(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=32, max_length=256)
    accessId: str = Field(min_length=36, max_length=36)


class StationPatientFallback(BaseModel):
    model_config = ConfigDict(extra="forbid")
    birthDate: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    phone: str | None = Field(default=None, min_length=5, max_length=32)
    firstName: str | None = Field(default=None, min_length=1, max_length=100)
    lastName: str | None = Field(default=None, min_length=1, max_length=100)


class StationPatientFallbackConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    fallbackMode: Literal["phone_dob", "name_dob", "disabled"]
    ownerPin: str = Field(pattern=r"^\d{4,8}$")


def _hash(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _normalized_text(raw: str | None) -> str:
    value = unicodedata.normalize("NFKD", raw or "")
    return " ".join("".join(ch for ch in value if not unicodedata.combining(ch)).casefold().split())


def _normalized_phone(raw: str | None) -> str:
    return re.sub(r"\D", "", raw or "")


def _fallback_mode(db: Session, employer_id: int) -> str:
    config = db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == employer_id).first()
    value = str(getattr(config, "station_identification_fallback", "disabled") or "disabled") if config else "disabled"
    return value if value in FALLBACK_MODES else "disabled"


def _fallback_failures_in_window(db: Session, workstation_id: str, now: datetime) -> int:
    window_start = now - timedelta(seconds=FALLBACK_FAILURE_WINDOW_SECONDS)
    rows = db.query(models.WorkstationPatientSession).filter(
        models.WorkstationPatientSession.workstation_id == workstation_id,
        models.WorkstationPatientSession.created_at >= window_start,
    ).all()
    return sum(int(item.fallback_failed_attempts or 0) for item in rows)


def _reserve_fallback_attempt(
    db: Session,
    row: models.WorkstationPatientSession,
    workstation_id: str,
    now: datetime,
) -> int:
    if _fallback_failures_in_window(db, workstation_id, now) >= FALLBACK_FAILURE_LIMIT:
        raise HTTPException(status_code=429, detail="STATION_FALLBACK_LOCKED")
    updated = db.query(models.WorkstationPatientSession).filter(
        models.WorkstationPatientSession.id == row.id,
        models.WorkstationPatientSession.claimed_at.is_(None),
        models.WorkstationPatientSession.purged_at.is_(None),
        models.WorkstationPatientSession.expires_at > now,
    ).update(
        {
            models.WorkstationPatientSession.fallback_failed_attempts:
                models.WorkstationPatientSession.fallback_failed_attempts + 1,
        },
        synchronize_session=False,
    )
    if updated != 1:
        db.rollback()
        raise HTTPException(status_code=409, detail="STATION_SESSION_ALREADY_USED")
    db.commit()
    db.refresh(row)
    failures = _fallback_failures_in_window(db, workstation_id, now)
    if failures > FALLBACK_FAILURE_LIMIT:
        raise HTTPException(status_code=429, detail="STATION_FALLBACK_LOCKED")
    return failures


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


def _identified_station_session_or_error(session_id: str, request: Request, db: Session, current_user: models.User):
    workstation = _station_or_423(request, db, current_user)
    row = db.query(models.WorkstationPatientSession).filter(
        models.WorkstationPatientSession.id == session_id,
        models.WorkstationPatientSession.employer_id == workstation.employer_id,
        models.WorkstationPatientSession.workstation_id == workstation.id,
        models.WorkstationPatientSession.purged_at.is_(None),
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="STATION_SESSION_NOT_FOUND")
    now = datetime.utcnow()
    if _expire_and_purge(db, row, now):
        raise HTTPException(status_code=409, detail="STATION_SESSION_INVALID_OR_USED")
    if row.claimed_at is None or row.patient_id is None:
        raise HTTPException(status_code=409, detail="STATION_PATIENT_NOT_IDENTIFIED")
    patient = db.query(models.Patient).filter(
        models.Patient.id == row.patient_id,
        models.Patient.employer_id == workstation.employer_id,
        models.Patient.deleted_at.is_(None),
    ).first()
    if patient is None:
        raise HTTPException(status_code=409, detail="STATION_SESSION_PATIENT_UNAVAILABLE")
    return workstation, row


@router.get("/patient-session/config")
def get_station_patient_session_config(
    response: Response,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    employer_id = int(current_user.get_employer_id())
    response.headers["Cache-Control"] = "no-store"
    return {"fallbackMode": _fallback_mode(db, employer_id)}


@router.patch("/patient-session/config")
def update_station_patient_session_config(
    body: StationPatientFallbackConfig,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    employer_id = int(current_user.get_employer_id())
    _require_pin(db, current_user, body.ownerPin)
    config = db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == employer_id).first()
    if config is None:
        raise HTTPException(status_code=404, detail="CABINET_CONFIG_NOT_FOUND")
    config.station_identification_fallback = body.fallbackMode
    db.commit()
    response.headers["Cache-Control"] = "no-store"
    return {"fallbackMode": body.fallbackMode}


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
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="STATION_SESSION_CONCURRENT_REPLACEMENT") from exc
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
        "fallbackMode": _fallback_mode(db, workstation.employer_id),
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



@router.post("/patient-session/{session_id}/fallback")
def fallback_station_patient_session(
    session_id: str,
    body: StationPatientFallback,
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
        models.WorkstationPatientSession.purged_at.is_(None),
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="STATION_SESSION_NOT_FOUND")

    now = datetime.utcnow()
    if _expire_and_purge(db, row, now):
        raise HTTPException(status_code=409, detail="STATION_SESSION_INVALID_OR_USED")
    if row.claimed_at is not None:
        raise HTTPException(status_code=409, detail="STATION_SESSION_ALREADY_USED")

    mode = _fallback_mode(db, workstation.employer_id)
    if mode == "disabled":
        raise HTTPException(status_code=403, detail="STATION_FALLBACK_DISABLED")
    try:
        birth_start = datetime.strptime(body.birthDate, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=422, detail="IDENTIFICATION_NOT_CONFIRMED") from None
    birth_end = birth_start + timedelta(days=1)

    expected_phone = ""
    expected_first = ""
    expected_last = ""
    if mode == "phone_dob":
        expected_phone = _normalized_phone(body.phone)
        if len(expected_phone) < 5:
            raise HTTPException(status_code=422, detail="IDENTIFICATION_NOT_CONFIRMED")
    else:
        expected_first = _normalized_text(body.firstName)
        expected_last = _normalized_text(body.lastName)
        if not expected_first or not expected_last:
            raise HTTPException(status_code=422, detail="IDENTIFICATION_NOT_CONFIRMED")

    reserved_failures = _reserve_fallback_attempt(db, row, workstation.id, now)

    candidates = db.query(models.Patient).filter(
        models.Patient.employer_id == workstation.employer_id,
        models.Patient.deleted_at.is_(None),
        models.Patient.date_naissance >= birth_start,
        models.Patient.date_naissance < birth_end,
    ).all()

    if mode == "phone_dob":
        matches = [
            patient
            for patient in candidates
            if expected_phone
            in {
                _normalized_phone(patient.telephone),
                _normalized_phone(patient.telephone_2),
                _normalized_phone(patient.telephone_3),
            }
        ]
    else:
        matches = [
            patient
            for patient in candidates
            if _normalized_text(patient.prenom) == expected_first
            and _normalized_text(patient.nom) == expected_last
        ]

    if len(matches) != 1:
        if reserved_failures >= FALLBACK_FAILURE_LIMIT:
            raise HTTPException(status_code=429, detail="STATION_FALLBACK_LOCKED")
        raise HTTPException(status_code=403, detail="IDENTIFICATION_NOT_CONFIRMED")

    patient = matches[0]
    updated = db.query(models.WorkstationPatientSession).filter(
        models.WorkstationPatientSession.id == row.id,
        models.WorkstationPatientSession.claimed_at.is_(None),
        models.WorkstationPatientSession.purged_at.is_(None),
        models.WorkstationPatientSession.expires_at > now,
    ).update(
        {
            models.WorkstationPatientSession.claimed_at: now,
            models.WorkstationPatientSession.patient_id: patient.id,
            models.WorkstationPatientSession.fallback_failed_attempts:
                models.WorkstationPatientSession.fallback_failed_attempts - 1,
        },
        synchronize_session=False,
    )
    if updated != 1:
        db.rollback()
        raise HTTPException(status_code=409, detail="STATION_SESSION_ALREADY_USED")

    db.add(models.AuditLog(
        user_id=current_user.id,
        employer_id=workstation.employer_id,
        action="STATION_PATIENT_FALLBACK_IDENTIFIED",
        resource_type="WorkstationPatientSession",
        resource_id=row.id,
        details=f"Fallback station identity confirmed; mode={mode}; credentials not logged.",
        ip_address=request.client.host if request.client else None,
    ))
    db.commit()
    response.headers["Cache-Control"] = "no-store"
    return {
        "status": "identified",
        "sessionId": row.id,
        "displayName": f"{patient.prenom or ''} {patient.nom or ''}".strip(),
    }


@router.get("/patient-session/{session_id}/appointments/today")
def station_patient_today_appointments(
    session_id: str,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    workstation, row = _identified_station_session_or_error(session_id, request, db, current_user)
    appointments = list_station_patient_appointments_for_today(
        db,
        employer_id=workstation.employer_id,
        patient_id=row.patient_id,
    )
    response.headers["Cache-Control"] = "no-store"
    if not appointments:
        return {"status": "none", "appointments": [], "staffActionRequired": True}
    return {
        "status": "single" if len(appointments) == 1 else "multiple",
        "appointments": [serialize_station_appointment(item) for item in appointments],
        "staffActionRequired": False,
    }


@router.post("/patient-session/{session_id}/staff-assistance")
def request_station_staff_assistance(
    session_id: str,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    workstation, row = _identified_station_session_or_error(session_id, request, db, current_user)
    appointments = list_station_patient_appointments_for_today(
        db,
        employer_id=workstation.employer_id,
        patient_id=row.patient_id,
    )
    if appointments:
        raise HTTPException(status_code=409, detail="STATION_STAFF_ASSISTANCE_NOT_REQUIRED")

    existing = db.query(models.AuditLog).filter(
        models.AuditLog.employer_id == workstation.employer_id,
        models.AuditLog.action == "STATION_STAFF_ASSISTANCE_REQUESTED",
        models.AuditLog.resource_type == "WorkstationPatientSession",
        models.AuditLog.resource_id == row.id,
    ).first()
    if existing is None:
        existing = models.AuditLog(
            user_id=current_user.id,
            employer_id=workstation.employer_id,
            action="STATION_STAFF_ASSISTANCE_REQUESTED",
            resource_type="WorkstationPatientSession",
            resource_id=row.id,
            severity="WARNING",
            details="Identified station visitor has no appointment today; staff assistance requested.",
            ip_address=request.client.host if request.client else None,
        )
        db.add(existing)
        db.commit()
        db.refresh(existing)
    response.headers["Cache-Control"] = "no-store"
    return {"status": "STAFF_NOTIFIED", "alertId": existing.id}


@router.get("/staff-assistance")
def list_station_staff_assistance(
    response: Response,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_permission("agenda")),
):
    employer_id = int(current_user.get_employer_id())
    day_start = datetime.combine(datetime.now().date(), datetime.min.time())
    requests = db.query(models.AuditLog).filter(
        models.AuditLog.employer_id == employer_id,
        models.AuditLog.action == "STATION_STAFF_ASSISTANCE_REQUESTED",
        models.AuditLog.timestamp >= day_start,
    ).order_by(models.AuditLog.timestamp.asc(), models.AuditLog.id.asc()).all()
    if not requests:
        response.headers["Cache-Control"] = "no-store"
        return {"alerts": []}

    request_ids = {str(item.id) for item in requests}
    acknowledged = db.query(models.AuditLog.resource_id).filter(
        models.AuditLog.employer_id == employer_id,
        models.AuditLog.action == "STATION_STAFF_ASSISTANCE_ACKNOWLEDGED",
        models.AuditLog.resource_type == "AuditLog",
        models.AuditLog.resource_id.in_(request_ids),
    ).all()
    acknowledged_ids = {str(item[0]) for item in acknowledged}
    alerts = [{
        "alertId": item.id,
        "requestedAt": item.timestamp,
    } for item in requests if str(item.id) not in acknowledged_ids]
    response.headers["Cache-Control"] = "no-store"
    return {"alerts": alerts}


@router.post("/staff-assistance/{alert_id}/acknowledge")
def acknowledge_station_staff_assistance(
    alert_id: int,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_permission("agenda")),
):
    employer_id = int(current_user.get_employer_id())
    requested = db.query(models.AuditLog).filter(
        models.AuditLog.id == alert_id,
        models.AuditLog.employer_id == employer_id,
        models.AuditLog.action == "STATION_STAFF_ASSISTANCE_REQUESTED",
    ).first()
    if requested is None:
        raise HTTPException(status_code=404, detail="STATION_STAFF_ASSISTANCE_NOT_FOUND")

    existing = db.query(models.AuditLog).filter(
        models.AuditLog.employer_id == employer_id,
        models.AuditLog.action == "STATION_STAFF_ASSISTANCE_ACKNOWLEDGED",
        models.AuditLog.resource_type == "AuditLog",
        models.AuditLog.resource_id == str(alert_id),
    ).first()
    if existing is None:
        db.add(models.AuditLog(
            user_id=current_user.id,
            employer_id=employer_id,
            action="STATION_STAFF_ASSISTANCE_ACKNOWLEDGED",
            resource_type="AuditLog",
            resource_id=str(alert_id),
            details="Station staff assistance acknowledged.",
            ip_address=request.client.host if request.client else None,
        ))
        db.commit()
    response.headers["Cache-Control"] = "no-store"
    return {"status": "ACKNOWLEDGED", "alertId": alert_id}


@router.post("/patient-session/{session_id}/appointments/{appointment_id}/arrive")
def station_patient_arrive(
    session_id: str,
    appointment_id: int,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    workstation, row = _identified_station_session_or_error(session_id, request, db, current_user)
    appointment = station_appointment_for_today(
        db,
        appointment_id=appointment_id,
        employer_id=workstation.employer_id,
        patient_id=row.patient_id,
    )
    if appointment is None:
        raise HTTPException(status_code=404, detail="STATION_APPOINTMENT_NOT_FOUND")
    try:
        appointment, changed = mark_station_appointment_arrived(
            db,
            appointment=appointment,
            employer_id=workstation.employer_id,
            patient_id=row.patient_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    if changed:
        db.add(models.AuditLog(
            user_id=current_user.id,
            employer_id=workstation.employer_id,
            action="STATION_APPOINTMENT_ARRIVED",
            resource_type="Appointment",
            resource_id=str(appointment.id),
            details="Arrival confirmed from registered Station; queue state not assigned.",
            ip_address=request.client.host if request.client else None,
        ))
        db.commit()
    response.headers["Cache-Control"] = "no-store"
    return {"status": "ARRIVED", "appointmentId": appointment.id}


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
