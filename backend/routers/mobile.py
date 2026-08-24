"""Canonical mobile auth wrapper: user identity + tenant scope + rotating device refresh."""
from datetime import datetime, timedelta, timezone
import uuid

from fastapi import Depends, HTTPException
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend import database, models
from backend.security import ALGORITHM, SECRET_KEY, token_blacklist
from . import mobile_legacy as _legacy
from .mobile_legacy import *  # noqa: F401,F403

MOBILE_REFRESH_TTL = timedelta(days=30)


def _mobile_jti(employer_id: int, now: datetime) -> str:
    issued_us = int(now.timestamp() * 1_000_000)
    return f"mobile:{int(employer_id)}:{issued_us}:{uuid.uuid4().hex}"


def _create_mobile_jwt(
    user_id: int,
    role: str,
    employer_id: int | None = None,
    device_id: str | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    tenant_id = int(employer_id if employer_id is not None else user_id)
    payload = {
        "sub": str(user_id),
        "tenant_id": tenant_id,
        "device_id": device_id,
        "type": "mobile",
        "role": role,
        "jti": _mobile_jti(tenant_id, now),
        "iat": now,
        "exp": now + timedelta(hours=24),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _create_mobile_refresh_jwt(
    user_id: int,
    role: str,
    employer_id: int,
    device_id: str,
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "tenant_id": int(employer_id),
        "device_id": device_id,
        "type": "mobile_refresh",
        "role": role,
        "jti": _mobile_jti(int(employer_id), now),
        "iat": now,
        "exp": now + MOBILE_REFRESH_TTL,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


_legacy._create_mobile_jwt = _create_mobile_jwt
_legacy._create_mobile_refresh_jwt = _create_mobile_refresh_jwt
router = _legacy.router


class MobileRefreshRequest(BaseModel):
    refresh_token: str


@router.post('/refresh-token', summary='Renouveler la session mobile appairée')
def refresh_mobile_credentials(
    body: MobileRefreshRequest,
    db: Session = Depends(database.get_db),
):
    err = HTTPException(status_code=401, detail='Session mobile expirée ou révoquée.')
    try:
        payload = jwt.decode(body.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get('type') != 'mobile_refresh':
            raise err
        jti = payload.get('jti')
        device_id = payload.get('device_id')
        if not jti or not device_id or token_blacklist.is_revoked(jti, db):
            raise err
        user_id = int(payload['sub'])
        tenant_id = int(payload['tenant_id'])
    except HTTPException:
        raise
    except (JWTError, ValueError, KeyError, TypeError):
        raise err

    device = db.query(models.MobilePairedDevice).filter(
        models.MobilePairedDevice.device_id == device_id,
        models.MobilePairedDevice.user_id == user_id,
        models.MobilePairedDevice.employer_id == tenant_id,
        models.MobilePairedDevice.revoked_at.is_(None),
    ).first()
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not device or not user or not user.is_active or user.get_employer_id() != tenant_id:
        raise err
    if device.refresh_jti != jti:
        # A previously rotated refresh token is a replay signal: revoke the whole device chain.
        device.revoked_at = datetime.utcnow()
        db.commit()
        raise err

    role = user.role.value if hasattr(user.role, 'value') else str(user.role)
    access_token = _create_mobile_jwt(user.id, role, tenant_id, device_id)
    refresh_token = _create_mobile_refresh_jwt(user.id, role, tenant_id, device_id)
    refresh_payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
    device.refresh_jti = refresh_payload['jti']
    device.last_seen_at = datetime.utcnow()
    db.commit()
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'device_id': device_id,
        'user_id': user.id,
        'tenant_id': tenant_id,
        'role': role,
    }
