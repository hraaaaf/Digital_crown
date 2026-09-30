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
from backend.utils.rate_limit import (
    enforce_failure_rate_limit,
    record_rate_limit_failure,
    reset_rate_limit_failures,
)

router = APIRouter(tags=["Workstation Mode"])
get_db = database.get_db
logger = logging.getLogger(__name__)

WORKSTATION_COOKIE = "dc_workstation"
ESCAPE_COOKIE = "dc_station_escape"
ESCAPE_TTL_MINUTES = 5


class OwnerPinSetup(BaseModel):
    accountPassword: str = Field(min_length=1, max_length=256)
    newPin: str = Field(pattern=r"^\d{4,8}$")


class WorkstationEnrollment(BaseModel):
    accountPassword: str = Field(min_length=1, max_length=256)


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


def _access_session_jti(request: Request) -> str | None:
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
    if payload.get("type") != "access":
        return None
    jti = payload.get("jti")
    return str(jti) if jti else None


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


def _enforce_failure_limit_with_audit(
    request: Request,
    db: Session,
    user: models.User,
    *,
    scope: str,
    action: str,
    resource_id: str,
) -> None:
    try:
        enforce_failure_rate_limit(request, scope=scope, max_attempts=5)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            _commit_with_audit(
                db,
                user=user,
                action=action,
                resource_type="WorkstationSecurity",
                resource_id=resource_id,
                details="Privileged workstation action blocked by failure-only rate limit.",
                request=request,
            )
        raise


def _find_workstation(request: Request, db: Session, employer_id: int | None = None) -> models.WorkstationMode | None:
    raw = request.cookies.get(WORKSTATION_COOKIE)
    if not raw:
        return None
    query = db.query(models.WorkstationMode).filter(models.WorkstationMode.token_hash == _token_hash(raw))
    if employer_id is not None:
        query = query.filter(models.WorkstationMode.employer_id == employer_id)
    return query.first()


def _tenant_has_workstations(db: Session, employer_id: int) -> bool:
    return (
        db.query(models.WorkstationMode.id)
        .filter(models.WorkstationMode.employer_id == employer_id)
        .first()
        is not None
    )


def _register_workstation(
    request: Request,
    response: Response,
    db: Session,
    user: models.User,
) -> models.WorkstationMode:
    raw = secrets.token_urlsafe(32)
    row = models.WorkstationMode(
        employer_id=_employer_id(user),
        token_hash=_token_hash(raw),
        default_experience=None,
        mode_revision=0,
        updated_by_user_id=user.id,
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
    response.delete_cookie(ESCAPE_COOKIE, path="/")
    return row


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

    if _tenant_has_workstations(db, employer_id):
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="WORKSTATION_ENROLLMENT_REQUIRED",
        )

    return _register_workstation(request, response, db, user)
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
        or int(payload.get("rev", -1)) != int(row.mode_revision or 0)
    ):
        return None
    return payload


def _escape_authorized(
    request: Request,
    row: models.WorkstationMode,
    user: models.User,
    session_jti: str | None = None,
) -> bool:
    payload = _escape_payload(request, row)
    current_jti = session_jti or _access_session_jti(request)
    return bool(
        payload
        and current_jti
        and str(payload.get("sub", "")) == str(user.id)
        and str(payload.get("sid", "")) == current_jti
    )


def _escape_expires_at(
    request: Request,
    row: models.WorkstationMode,
    user: models.User,
    session_jti: str | None = None,
) -> int | None:
    payload = _escape_payload(request, row)
    if not _escape_authorized(request, row, user, session_jti=session_jti):
        return None
    try:
        return int(payload.get("exp"))
    except (TypeError, ValueError):
        return None


def enforce_workstation_access_from_values(
    *,
    db: Session,
    user: models.User,
    workstation_cookie: str | None,
    escape_cookie: str | None,
    session_jti: str | None,
) -> None:
    """Transport-neutral Station authority used by HTTP and long-lived channels."""
    employer_id = _employer_id(user)
    row = None
    if workstation_cookie:
        row = (
            db.query(models.WorkstationMode)
            .filter(
                models.WorkstationMode.token_hash == _token_hash(workstation_cookie),
                models.WorkstationMode.employer_id == employer_id,
            )
            .first()
        )

    if row is None:
        if workstation_cookie or _tenant_has_workstations(db, employer_id):
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="WORKSTATION_IDENTITY_REQUIRED",
            )
        return

    escape_authorized = False
    if row.default_experience == "station" and escape_cookie and session_jti:
        try:
            payload = jwt.decode(escape_cookie, SECRET_KEY, algorithms=[ALGORITHM])
            escape_authorized = bool(
                payload.get("type") == "workstation_escape"
                and payload.get("wsid") == row.id
                and int(payload.get("tenant", -1)) == int(row.employer_id)
                and int(payload.get("rev", -1)) == int(row.mode_revision or 0)
                and str(payload.get("sub", "")) == str(user.id)
                and str(payload.get("sid", "")) == session_jti
            )
        except (JWTError, TypeError, ValueError):
            escape_authorized = False

    if row.default_experience == "station" and not escape_authorized:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="WORKSTATION_STATION_LOCKED",
        )


def enforce_authenticated_workstation_access(
    request: Request,
    db: Session,
    user: models.User,
    *,
    session_jti: str | None,
) -> None:
    enforce_workstation_access_from_values(
        db=db,
        user=user,
        workstation_cookie=request.cookies.get(WORKSTATION_COOKIE),
        escape_cookie=request.cookies.get(ESCAPE_COOKIE),
        session_jti=session_jti,
    )


def _state_payload(request: Request, row: models.WorkstationMode, user: models.User, db: Session) -> dict:
    policy = _security_policy(db, _employer_id(user))
    session_jti = _access_session_jti(request)
    escape_authorized = _escape_authorized(request, row, user, session_jti=session_jti)
    return {
        "workstationId": row.id,
        "defaultExperience": row.default_experience,
        "pinConfigured": bool(policy and policy.owner_pin_hash),
        "canManage": _authorized_admin(user),
        "canConfigurePin": _can_configure_pin(user),
        "stationLocked": row.default_experience == "station",
        "stationEscapeAuthorized": escape_authorized,
        "stationEscapeExpiresAt": _escape_expires_at(request, row, user, session_jti=session_jti),
        "enrollmentRequired": False,
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
        enrollment_required = bool(
            current_user is not None
            and employer_id is not None
            and _tenant_has_workstations(db, employer_id)
        )
        return {
            "workstationId": None,
            "defaultExperience": None,
            "stationLocked": False,
            "stationEscapeAuthorized": False,
            "stationEscapeExpiresAt": None,
            "enrollmentRequired": enrollment_required,
            **auth_context,
        }

    # Escape authority is user- and access-session-bound. Anonymous bootstrap
    # may reveal only the workstation's non-sensitive routing mode.
    if current_user is not None:
        session_jti = _access_session_jti(request)
        escape_authorized = _escape_authorized(request, row, current_user, session_jti=session_jti)
        escape_expires_at = _escape_expires_at(request, row, current_user, session_jti=session_jti)
    else:
        escape_authorized = False
        escape_expires_at = None
    return {
        "workstationId": row.id,
        "defaultExperience": row.default_experience,
        "stationLocked": row.default_experience == "station",
        "stationEscapeAuthorized": escape_authorized,
        "stationEscapeExpiresAt": escape_expires_at,
        "enrollmentRequired": False,
        **auth_context,
    }


@router.post("/enroll")
def enroll_workstation(
    payload: WorkstationEnrollment,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    employer_id = _employer_id(current_user)
    scope = f"workstation-enroll:{employer_id}"
    _enforce_failure_limit_with_audit(
        request,
        db,
        current_user,
        scope=scope,
        action="WORKSTATION_ENROLLMENT_RATE_LIMITED",
        resource_id=str(employer_id),
    )
    if not _can_configure_pin(current_user):
        _commit_with_audit(
            db,
            user=current_user,
            action="WORKSTATION_ENROLLMENT_REJECTED",
            resource_type="WorkstationMode",
            resource_id=str(employer_id),
            details="Workstation enrollment rejected: primary owner required.",
            request=request,
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Primary owner required")
    if not is_superadmin_user(current_user) and not verify_password(payload.accountPassword, current_user.hashed_password):
        record_rate_limit_failure(request, scope)
        _commit_with_audit(
            db,
            user=current_user,
            action="WORKSTATION_ENROLLMENT_REJECTED",
            resource_type="WorkstationMode",
            resource_id=str(employer_id),
            details="Workstation enrollment rejected: current account password invalid.",
            request=request,
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Current password is invalid")

    reset_rate_limit_failures(request, scope)
    existing = _find_workstation(request, db, employer_id)
    if existing is not None:
        return _state_payload(request, existing, current_user, db)

    row = _register_workstation(request, response, db, current_user)
    return _state_payload(request, row, current_user, db)


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
    response: Response,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    employer_id = _employer_id(current_user)
    scope = f"workstation-owner-pin:{employer_id}"
    _enforce_failure_limit_with_audit(
        request,
        db,
        current_user,
        scope=scope,
        action="WORKSTATION_OWNER_PIN_RATE_LIMITED",
        resource_id=str(employer_id),
    )
    if not _can_configure_pin(current_user):
        _commit_with_audit(
            db,
            user=current_user,
            action="WORKSTATION_OWNER_PIN_REJECTED",
            resource_type="WorkstationSecurityPolicy",
            resource_id=str(employer_id),
            details="Owner PIN setup rejected: primary owner required.",
            request=request,
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Primary owner required")
    if not is_superadmin_user(current_user) and not verify_password(payload.accountPassword, current_user.hashed_password):
        record_rate_limit_failure(request, scope)
        _commit_with_audit(
            db,
            user=current_user,
            action="WORKSTATION_OWNER_PIN_REJECTED",
            resource_type="WorkstationSecurityPolicy",
            resource_id=str(employer_id),
            details="Owner PIN setup rejected: current account password invalid.",
            request=request,
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Current password is invalid")

    policy = _security_policy(db, employer_id)
    if policy is None:
        policy = models.WorkstationSecurityPolicy(employer_id=employer_id)
        db.add(policy)
    policy.owner_pin_hash = get_password_hash(payload.newPin)
    policy.updated_by_user_id = current_user.id
    # PIN rotation revokes every outstanding Station escape for the tenant,
    # including copied/replayed cookies that the browser can no longer delete.
    for workstation in db.query(models.WorkstationMode).filter(
        models.WorkstationMode.employer_id == employer_id
    ).all():
        workstation.mode_revision = int(workstation.mode_revision or 0) + 1
        workstation.updated_by_user_id = current_user.id
    _commit_with_audit(
        db,
        user=current_user,
        action="WORKSTATION_OWNER_PIN_CONFIGURED",
        resource_type="WorkstationSecurityPolicy",
        resource_id=str(employer_id),
        details="Owner PIN configured or rotated; PIN value not logged.",
        request=request,
    )
    reset_rate_limit_failures(request, scope)
    response.delete_cookie(ESCAPE_COOKIE, path="/")
    return {"ok": True}


@router.post("/mode")
def change_mode(
    payload: ModeChange,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    row = _get_or_create_workstation(request, response, db, current_user)
    scope = f"workstation-mode-pin:{_employer_id(current_user)}:{row.id}"
    _enforce_failure_limit_with_audit(
        request,
        db,
        current_user,
        scope=scope,
        action="WORKSTATION_MODE_RATE_LIMITED",
        resource_id=row.id,
    )
    try:
        _require_pin(db, current_user, payload.ownerPin)
    except HTTPException as exc:
        if exc.detail == "Invalid owner PIN":
            record_rate_limit_failure(request, scope)
        _commit_with_audit(
            db,
            user=current_user,
            action="WORKSTATION_MODE_REJECTED",
            resource_type="WorkstationMode",
            resource_id=row.id,
            details=f"Mode change rejected; target={payload.mode}; reason={exc.detail}.",
            request=request,
        )
        raise

    previous = row.default_experience
    row.default_experience = payload.mode
    row.mode_revision = int(row.mode_revision or 0) + 1
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
    reset_rate_limit_failures(request, scope)
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
    row = _get_or_create_workstation(request, response, db, current_user)
    scope = f"workstation-station-escape:{_employer_id(current_user)}:{row.id}"
    _enforce_failure_limit_with_audit(
        request,
        db,
        current_user,
        scope=scope,
        action="WORKSTATION_STATION_ESCAPE_RATE_LIMITED",
        resource_id=row.id,
    )
    try:
        _require_pin(db, current_user, payload.ownerPin)
    except HTTPException as exc:
        if exc.detail == "Invalid owner PIN":
            record_rate_limit_failure(request, scope)
        _commit_with_audit(
            db,
            user=current_user,
            action="WORKSTATION_STATION_ESCAPE_REJECTED",
            resource_type="WorkstationMode",
            resource_id=row.id,
            details=f"Station escape rejected; reason={exc.detail}.",
            request=request,
        )
        raise

    if row.default_experience != "station":
        _commit_with_audit(
            db,
            user=current_user,
            action="WORKSTATION_STATION_ESCAPE_REJECTED",
            resource_type="WorkstationMode",
            resource_id=row.id,
            details="Station escape rejected: workstation is not in Station mode.",
            request=request,
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Workstation is not locked in Station mode")

    reset_rate_limit_failures(request, scope)
    session_jti = _access_session_jti(request)
    if not session_jti:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access session required")

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=ESCAPE_TTL_MINUTES)
    token = jwt.encode(
        {
            "type": "workstation_escape",
            "wsid": row.id,
            "tenant": _employer_id(current_user),
            "sub": str(current_user.id),
            "sid": session_jti,
            "rev": int(row.mode_revision or 0),
            "iat": now,
            "exp": expires_at,
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
    return {
        "ok": True,
        "expiresInSeconds": ESCAPE_TTL_MINUTES * 60,
        "expiresAt": int(expires_at.timestamp()),
    }
