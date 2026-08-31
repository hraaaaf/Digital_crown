"""M6-I WebAuthn policy and device-bound biometric-session helpers."""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException
from jose import jwt
from sqlalchemy.orm import Session

from backend import models
from backend.models_mobile_passkey import MobilePasskeyCredential, MobileWebAuthnChallenge
from backend.security import ALGORITHM, SECRET_KEY

WEBAUTHN_RP_ID = os.getenv("DIGITALCROWN_WEBAUTHN_RP_ID", "digitalcrown.local").strip().lower()
WEBAUTHN_ORIGIN = os.getenv(
    "DIGITALCROWN_WEBAUTHN_ORIGIN", f"https://{WEBAUTHN_RP_ID}:8005"
).strip().rstrip("/")
WEBAUTHN_RP_NAME = "Digital Crown"
CHALLENGE_TTL = timedelta(minutes=3)
BIOMETRIC_SESSION_TTL = timedelta(minutes=5)


def b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def opaque_user_handle(*, user_id: int, employer_id: int, device_id: str) -> bytes:
    message = f"m6i:{int(employer_id)}:{int(user_id)}:{device_id}".encode("utf-8")
    return hmac.new(SECRET_KEY.encode("utf-8"), message, hashlib.sha256).digest()


def assert_stable_webauthn_origin(origin: str | None) -> None:
    if (origin or "").rstrip("/").lower() != WEBAUTHN_ORIGIN.lower():
        raise HTTPException(
            status_code=409,
            detail={
                "code": "WEBAUTHN_STABLE_ORIGIN_REQUIRED",
                "expected_origin": WEBAUTHN_ORIGIN,
            },
        )


def credential_for_device(
    db: Session, *, user_id: int, employer_id: int, device_id: str
) -> MobilePasskeyCredential | None:
    return db.query(MobilePasskeyCredential).filter(
        MobilePasskeyCredential.user_id == int(user_id),
        MobilePasskeyCredential.employer_id == int(employer_id),
        MobilePasskeyCredential.device_id == str(device_id),
    ).first()


def issue_challenge(
    db: Session, *, purpose: str, user_id: int, employer_id: int, device_id: str, challenge: bytes
) -> str:
    now = datetime.utcnow()
    # Bound table growth: stale/consumed challenges are disposable proof material.
    db.query(MobileWebAuthnChallenge).filter(
        MobileWebAuthnChallenge.expires_at <= now,
    ).delete(synchronize_session=False)
    db.query(MobileWebAuthnChallenge).filter(
        MobileWebAuthnChallenge.used_at.is_not(None),
    ).delete(synchronize_session=False)
    # Keep only one live challenge per purpose/device. Old live rows are consumed so
    # a second ceremony cannot race the first one with two usable challenges.
    db.query(MobileWebAuthnChallenge).filter(
        MobileWebAuthnChallenge.device_id == str(device_id),
        MobileWebAuthnChallenge.purpose == purpose,
        MobileWebAuthnChallenge.used_at.is_(None),
    ).update({MobileWebAuthnChallenge.used_at: now}, synchronize_session=False)
    challenge_id = str(uuid.uuid4())
    db.add(
        MobileWebAuthnChallenge(
            id=challenge_id,
            challenge_b64url=b64url_encode(challenge),
            purpose=purpose,
            user_id=int(user_id),
            employer_id=int(employer_id),
            device_id=str(device_id),
            expires_at=now + CHALLENGE_TTL,
        )
    )
    db.commit()
    return challenge_id


def consume_challenge(
    db: Session, *, challenge_id: str, purpose: str, user_id: int, employer_id: int, device_id: str
) -> bytes:
    now = datetime.utcnow()
    row = db.query(MobileWebAuthnChallenge).filter(
        MobileWebAuthnChallenge.id == challenge_id,
        MobileWebAuthnChallenge.purpose == purpose,
        MobileWebAuthnChallenge.user_id == int(user_id),
        MobileWebAuthnChallenge.employer_id == int(employer_id),
        MobileWebAuthnChallenge.device_id == str(device_id),
        MobileWebAuthnChallenge.used_at.is_(None),
        MobileWebAuthnChallenge.expires_at > now,
    ).first()
    if row is None:
        raise HTTPException(status_code=410, detail="Challenge WebAuthn expiré ou déjà utilisé.")
    updated = db.query(MobileWebAuthnChallenge).filter(
        MobileWebAuthnChallenge.id == row.id,
        MobileWebAuthnChallenge.used_at.is_(None),
    ).update({MobileWebAuthnChallenge.used_at: now}, synchronize_session=False)
    if updated != 1:
        db.rollback()
        raise HTTPException(status_code=410, detail="Challenge WebAuthn déjà utilisé.")
    db.commit()
    return b64url_decode(row.challenge_b64url)


def issue_biometric_access_token(*, user: models.User, employer_id: int, device_id: str) -> tuple[str, int]:
    now = datetime.now(timezone.utc)
    role = user.role.value if hasattr(user.role, "value") else str(user.role)
    exp = now + BIOMETRIC_SESSION_TTL
    payload = {
        "sub": str(user.id),
        "tenant_id": int(employer_id),
        "device_id": str(device_id),
        "type": "mobile",
        "role": role,
        "jti": f"mobile-uv:{int(employer_id)}:{uuid.uuid4().hex}",
        "iat": now,
        "exp": exp,
        "biometric_uv": True,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM), int(BIOMETRIC_SESSION_TTL.total_seconds())


def payload_has_biometric_uv(payload: dict[str, Any]) -> bool:
    return payload.get("type") == "mobile" and payload.get("biometric_uv") is True


def install_mobile_biometric_identity_gate(legacy_module) -> None:
    """Patch the canonical mobile decoder: enabled passkeys require a short UV JWT."""
    if getattr(legacy_module, "_m6i_identity_gate_installed", False):
        return
    base_decoder = legacy_module._decode_mobile_identity
    legacy_module._m6i_base_decode_mobile_identity = base_decoder

    def gated_decoder(authorization: str, db: Session):
        user, tenant_id, payload = base_decoder(authorization, db)
        device_id = str(payload.get("device_id") or "")
        credential = credential_for_device(
            db,
            user_id=user.id,
            employer_id=int(tenant_id),
            device_id=device_id,
        )
        if credential is not None and credential.enabled_at is not None and not payload_has_biometric_uv(payload):
            raise HTTPException(
                status_code=423,
                detail={"code": "MOBILE_BIOMETRIC_LOCKED", "message": "Déverrouillage biométrique requis."},
            )
        return user, tenant_id, payload

    legacy_module._decode_mobile_identity = gated_decoder
    legacy_module._m6i_identity_gate_installed = True
