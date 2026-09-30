"""V1.5-00.3 trusted workstation-mode contract."""
from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from jose import JWTError, jwt
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend import database, models
from backend.config import settings
from backend.routers.auth import get_current_user, get_current_user_optional, has_permission, is_superadmin_user
from backend.security import ALGORITHM, SECRET_KEY, get_password_hash, verify_password
from backend.utils.rate_limit import check_rate_limit

router = APIRouter(tags=["Workstation Mode"])
get_db = database.get_db
logger = logging.getLogger(__name__)

WORKSTATION_COOKIE = "dc_workstation"
ESCAPE_COOKIE = "dc_station_escape"
ESCAPE_TTL_MINUTES = 5


class OwnerPinSetup(BaseModel):
    accountPassword: str = Field(min_length=1, max_length=256)
    newPin: str = Field(pattern=r"^\d{4,8}$")
class ModeChange(BaseModel):
    mode: Literal["cabinet", "station", "control_center"]
    ownerPin: str = Field(pattern=r"^\d{4,8}$")


class StationEscape(BaseModel):
    ownerPin: str = Field(pattern=r"^\d{4,8}$")


def _employer_id(user: models.User) -> int:
    return int(user.get_employer_id())


def _cookie_secure() -> bool:
    env = getattr(settings, "ENVIRONMENT", "development").lower()
    https = __import__("os").getenv("DIGITALCROWN_ENABLE_HTTPS", "false").lower() in {"1", "true", "yes", "on"}
    return env == "production" or (env == "cabinet" and https)


def _token_hash(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _set_workstation_cookie(response: Response, raw: str) -> None:
    response.set_cookie(
        WORKSTATION_COOKIE,
        raw,
        max_age=60 * 60 * 24 * 365 * 5,
        httponly=True,
        secure=_cookie_secure(),
        samesite="strict",
        path="/",
    )
def _authorized_admin(user: models.User) -> bool:
    return is_superadmin_user(user) or has_permission(user, "admin")


def _can_configure_pin(user: models.User) -> bool:
    if is_superadmin_user(user):
        return True
    employer_id = _employer_id(user)
    return user.employer_id is None and int(user.id) == employer_id


def _commit_with_audit(
    db: Session,
    *,
    user: models.User,
    action: str,
    resource_type: str,
    resource_id: str,
    details: str,
    request: Request,
) -> None:
    try:
        db.add(models.AuditLog(
            user_id=user.id,
            employer_id=_employer_id(user),
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=request.client.host if request.client else None,
        ))
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.exception("Atomic workstation audit commit failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Workstation change could not be audited",
        ) from exc


def _find_workstation(request: Request, db: Session, employer_id: int | None = None) -> models.WorkstationMode | None:
    raw = request.cookies.get(WORKSTATION_COOKIE)
    if not raw:
        return None
    query = db.query(models.WorkstationMode).filter(models.WorkstationMode.token_hash == _token_hash(raw))
    if employer_id is not None:
        query = query.filter(models.WorkstationMode.employer_id == employer_id)
    return query.first()


def _get_or_create_workstation(
    request: Request,
    response: Response,
    db: Session,
    user: models.User,
) -> models.WorkstationMode:
    employer_id = _employer_id(user)
    row = _find_workstation(request, db, employer_id)
    if row is not None:
        return row

    raw = secrets.token_urlsafe(32)
    row = models.WorkstationMode(
        employer_id=employer_id,
        token_hash=_token_hash(raw),
        default_experience=None,
    )
    db.add(row)
    db.flush()
    _commit_with_audit(
        db,
        user=user,
        action="WORKSTATION_REGISTERED",
        resource_type="WorkstationMode",
        resource_id=row.id,
        details="Opaque server-side workstation identity registered.",
        request=request,
    )
    db.refresh(row)
    _set_workstation_cookie(response, raw)
    return row
def _security_policy(db: Session, employer_id: int) -> models.WorkstationSecurityPolicy | None:
    return (
        db.query(models.WorkstationSecurityPolicy)
        .filter(models.WorkstationSecurityPolicy.employer_id == employer_id)
        .first()
    )


def _require_pin(db: Session, user: models.User, pin: str) -> models.WorkstationSecurityPolicy:
    if not _authorized_admin(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin/owner required")
    policy = _security_policy(db, _employer_id(user))
    if policy is None or not policy.owner_pin_hash:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Owner PIN is not configured")
    if not verify_password(pin, policy.owner_pin_hash):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid owner PIN")
    return policy


def _escape_payload(request: Request, row: models.WorkstationMode) -> dict | None:
    raw = request.cookies.get(ESCAPE_COOKIE)
    if not raw:
        return None
    try:
        payload = jwt.decode(raw, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
    if (
        payload.get("type") != "workstation_escape"
        or payload.get("wsid") != row.id
        or int(payload.get("tenant", -1)) != int(row.employer_id)
    ):
        return None
    return payload


def _escape_authorized(request: Request, row: models.WorkstationMode, user: models.User) -> bool:
    payload = _escape_payload(request, row)
    return bool(payload and str(payload.get("sub", "")) == str(user.id))
def _state_payload(request: Request, row: models.WorkstationMode, user: models.User, db: Session) -> dict:
    policy = _security_policy(db, _employer_id(user))
    return {
        "workstationId": row.id,
        "defaultExperience": row.default_experience,
        "pinConfigured": bool(policy and policy.owner_pin_hash),
        "canManage": _authorized_admin(user),
        "canConfigurePin": _can_configure_pin(user),
        "stationLocked": row.default_experience == "station",
        "stationEscapeAuthorized": _escape_authorized(request, row, user),
    }


@router.get("/bootstrap")
async def bootstrap_state(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User | None = Depends(get_current_user_optional),
):
    employer_id = _employer_id(current_user) if current_user is not None else None
    policy = _security_policy(db, employer_id) if employer_id is not None else None
    auth_context = {
        "authenticated": current_user is not None,
        "pinConfigured": bool(policy and policy.owner_pin_hash),
        "canManage": _authorized_admin(current_user) if current_user is not None else False,
        "canConfigurePin": _can_configure_pin(current_user) if current_user is not None else False,
    }

    row = _find_workstation(request, db, employer_id)
    if row is None:
        return {
            "workstationId": None,
            "defaultExperience": None,
            "stationLocked": False,
            "stationEscapeAuthorized": False,
            **auth_context,
        }

    # Escape authority is user-bound. Anonymous bootstrap may reveal only the
    # workstation's non-sensitive routing mode, never a prior user's escape.
    escape_authorized = (
        _escape_authorized(request, row, current_user)
        if current_user is not None
        else False
    )
    return {
        "workstationId": row.id,
        "defaultExperience": row.default_experience,
        "stationLocked": row.default_experience == "station",
        "stationEscapeAuthorized": escape_authorized,
        **auth_context,
    }


@router.get("/state")
def get_state(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    row = _get_or_create_workstation(request, response, db, current_user)
    return _state_payload(request, row, current_user, db)


@router.post("/owner-pin")
def configure_owner_pin(
    payload: OwnerPinSetup,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    check_rate_limit(request, scope="workstation-owner-pin", max_attempts=5)
    employer_id = _employer_id(current_user)
    if not _can_configure_pin(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Primary owner required")
    if not is_superadmin_user(current_user) and not verify_password(payload.accountPassword, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Current password is invalid")

    policy = _security_policy(db, employer_id)
    if policy is None:
        policy = models.WorkstationSecurityPolicy(employer_id=employer_id)
        db.add(policy)
    policy.owner_pin_hash = get_password_hash(payload.newPin)
    policy.updated_by_user_id = current_user.id
    _commit_with_audit(
        db,
        user=current_user,
        action="WORKSTATION_OWNER_PIN_CONFIGURED",
        resource_type="WorkstationSecurityPolicy",
        resource_id=str(employer_id),
        details="Owner PIN configured or rotated; PIN value not logged.",
        request=request,
    )
    return {"ok": True}


@router.post("/mode")
def change_mode(
    payload: ModeChange,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    check_rate_limit(request, scope="workstation-mode-pin", max_attempts=5)
    _require_pin(db, current_user, payload.ownerPin)
    row = _get_or_create_workstation(request, response, db, current_user)
    previous = row.default_experience
    row.default_experience = payload.mode
    row.updated_by_user_id = current_user.id
    _commit_with_audit(
        db,
        user=current_user,
        action="WORKSTATION_MODE_CHANGED",
        resource_type="WorkstationMode",
        resource_id=row.id,
        details=f"{previous or 'hub'} -> {payload.mode}",
        request=request,
    )
    response.delete_cookie(ESCAPE_COOKIE, path="/")
    return _state_payload(request, row, current_user, db)


@router.post("/station/escape")
def authorize_station_escape(
    payload: StationEscape,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    check_rate_limit(request, scope="workstation-station-escape", max_attempts=5)
    _require_pin(db, current_user, payload.ownerPin)
    row = _get_or_create_workstation(request, response, db, current_user)
    if row.default_experience != "station":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Workstation is not locked in Station mode")

    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "type": "workstation_escape",
            "wsid": row.id,
            "tenant": _employer_id(current_user),
            "sub": str(current_user.id),
            "iat": now,
            "exp": now + timedelta(minutes=ESCAPE_TTL_MINUTES),
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    response.set_cookie(
        ESCAPE_COOKIE,
        token,
        max_age=ESCAPE_TTL_MINUTES * 60,
        httponly=True,
        secure=_cookie_secure(),
        samesite="strict",
        path="/",
    )
    _commit_with_audit(
        db,
        user=current_user,
        action="WORKSTATION_STATION_ESCAPE_AUTHORIZED",
        resource_type="WorkstationMode",
        resource_id=row.id,
        details=f"Temporary Hub escape authorized for {ESCAPE_TTL_MINUTES} minutes.",
        request=request,
    )
    return {"ok": True, "expiresInSeconds": ESCAPE_TTL_MINUTES * 60}
