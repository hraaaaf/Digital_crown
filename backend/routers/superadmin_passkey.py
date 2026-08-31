"""WebAuthn ceremonies dedicated to the SuperAdmin platform control plane."""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from jose import jwt
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from backend import database, models
from backend.models_platform_passkey import PlatformPasskeyCredential, PlatformWebAuthnChallenge
from backend.platform_access import PLATFORM_LICENSE_PERMISSIONS, has_platform_permission, is_platform_superadmin
from backend.platform_step_up import verify_platform_step_up
from backend.routers.auth import get_current_user
from backend.security import ALGORITHM, SECRET_KEY
from backend.services.mobile_biometric import (
    WEBAUTHN_ORIGIN,
    WEBAUTHN_RP_ID,
    WEBAUTHN_RP_NAME,
    assert_stable_webauthn_origin,
    b64url_decode,
    b64url_encode,
)

router = APIRouter(prefix="/passkey", tags=["SuperAdmin Passkey"])
CHALLENGE_TTL = timedelta(minutes=3)
STEP_UP_TTL = timedelta(minutes=5)
STEP_UP_COOKIE = "platform_step_up"


class CeremonyResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    challenge_id: str = Field(min_length=36, max_length=36)
    credential: dict[str, Any]


def _platform_actor(current_user: models.User = Depends(get_current_user)) -> models.User:
    if is_platform_superadmin(current_user) or any(
        has_platform_permission(current_user, permission)
        for permission in PLATFORM_LICENSE_PERMISSIONS
    ):
        return current_user
    raise HTTPException(
        status_code=403,
        detail="Accès refusé. Autorité plateforme requise.",
    )


def _origin(request: Request) -> str | None:
    return request.headers.get("origin")


def _enum_value(value: Any) -> str:
    return str(getattr(value, "value", value))


def _options_payload(options: Any, *, challenge_id: str) -> dict[str, Any]:
    from webauthn import options_to_json

    payload = json.loads(options_to_json(options))
    payload["challenge_id"] = challenge_id
    return payload


def _credential(db: Session, user_id: int) -> PlatformPasskeyCredential | None:
    return db.query(PlatformPasskeyCredential).filter(
        PlatformPasskeyCredential.user_id == int(user_id)
    ).first()


def _issue_challenge(db: Session, *, purpose: str, user_id: int, challenge: bytes) -> str:
    challenge_id = str(uuid.uuid4())
    db.add(
        PlatformWebAuthnChallenge(
            id=challenge_id,
            challenge_b64url=b64url_encode(challenge),
            purpose=purpose,
            user_id=int(user_id),
            expires_at=datetime.utcnow() + CHALLENGE_TTL,
        )
    )
    db.commit()
    return challenge_id


def _consume_challenge(db: Session, *, challenge_id: str, purpose: str, user_id: int) -> bytes:
    row = db.query(PlatformWebAuthnChallenge).filter(
        PlatformWebAuthnChallenge.id == challenge_id,
        PlatformWebAuthnChallenge.purpose == purpose,
        PlatformWebAuthnChallenge.user_id == int(user_id),
    ).first()
    if row is None or row.used_at is not None or row.expires_at <= datetime.utcnow():
        raise HTTPException(status_code=400, detail="Challenge WebAuthn plateforme invalide ou expiré.")
    row.used_at = datetime.utcnow()
    challenge = b64url_decode(row.challenge_b64url)
    db.commit()
    return challenge


def _issue_step_up_token(user_id: int) -> tuple[str, int]:
    now = datetime.now(timezone.utc)
    expires = now + STEP_UP_TTL
    token = jwt.encode(
        {
            "sub": str(int(user_id)),
            "type": "platform_step_up",
            "iat": int(now.timestamp()),
            "exp": expires,
            "jti": f"platform-step-up:{uuid.uuid4().hex}",
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    return token, int(STEP_UP_TTL.total_seconds())


def _set_step_up_cookie(response: Response, request: Request, user_id: int) -> int:
    # The platform control plane is HTTPS-only by configuration. Never infer the
    # browser transport from request.url.scheme: TLS may terminate at a reverse proxy.
    del request
    token, expires_in = _issue_step_up_token(user_id)
    response.set_cookie(
        key=STEP_UP_COOKIE,
        value=token,
        max_age=expires_in,
        httponly=True,
        secure=True,
        samesite="strict",
        path="/api/superadmin",
    )
    return expires_in


def _step_up_valid(request: Request, admin: models.User, db: Session) -> bool:
    try:
        verify_platform_step_up(request, current_user=admin, db=db)
        return True
    except HTTPException:
        return False


def _audit_registration(db: Session, user_id: int, credential_id: str) -> None:
    db.add(
        models.AuditLog(
            user_id=int(user_id),
            employer_id=None,
            action="SUPERADMIN_PASSKEY_REGISTER",
            resource_type="PlatformPasskeyCredential",
            resource_id=credential_id[:100],
            severity="CRITICAL",
            details="user_verification=required",
        )
    )


@router.get("/status")
def passkey_status(
    request: Request,
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(_platform_actor),
):
    credential = _credential(db, admin.id)
    origin = (_origin(request) or "").rstrip("/").lower()
    return {
        "enrolled": credential is not None,
        "credential_id": credential.credential_id if credential else None,
        "rp_id": WEBAUTHN_RP_ID,
        "expected_origin": WEBAUTHN_ORIGIN,
        "origin_ready": origin == WEBAUTHN_ORIGIN.lower(),
        "user_verification": "required",
        "step_up_valid": _step_up_valid(request, admin, db),
    }


@router.post("/registration/options")
def registration_options(
    request: Request,
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(_platform_actor),
):
    assert_stable_webauthn_origin(_origin(request))
    if _credential(db, admin.id) is not None:
        raise HTTPException(status_code=409, detail="Une passkey plateforme est déjà enregistrée.")

    from webauthn import generate_registration_options
    from webauthn.helpers.structs import AuthenticatorSelectionCriteria, ResidentKeyRequirement, UserVerificationRequirement

    user_handle = hashlib.sha256(f"digital-crown-platform:{admin.id}".encode("utf-8")).digest()
    options = generate_registration_options(
        rp_id=WEBAUTHN_RP_ID,
        rp_name=WEBAUTHN_RP_NAME,
        user_id=user_handle,
        user_name=f"platform-user-{admin.id}",
        user_display_name=admin.nom_complet or "Digital Crown SuperAdmin",
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.REQUIRED,
        ),
        timeout=60000,
    )
    challenge_id = _issue_challenge(
        db,
        purpose="register",
        user_id=admin.id,
        challenge=options.challenge,
    )
    return _options_payload(options, challenge_id=challenge_id)


@router.post("/registration/verify")
def registration_verify(
    request: Request,
    response: Response,
    body: CeremonyResponse,
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(_platform_actor),
):
    assert_stable_webauthn_origin(_origin(request))
    if _credential(db, admin.id) is not None:
        raise HTTPException(status_code=409, detail="Une passkey plateforme est déjà enregistrée.")

    expected_challenge = _consume_challenge(
        db,
        challenge_id=body.challenge_id,
        purpose="register",
        user_id=admin.id,
    )
    try:
        from webauthn import verify_registration_response
        from webauthn.helpers.exceptions import InvalidRegistrationResponse

        verification = verify_registration_response(
            credential=body.credential,
            expected_challenge=expected_challenge,
            expected_rp_id=WEBAUTHN_RP_ID,
            expected_origin=WEBAUTHN_ORIGIN,
            require_user_verification=True,
        )
    except InvalidRegistrationResponse as exc:
        raise HTTPException(status_code=400, detail="Réponse WebAuthn plateforme invalide.") from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Enrôlement WebAuthn plateforme impossible.") from exc

    credential_id = b64url_encode(verification.credential_id)
    response_data = body.credential.get("response") if isinstance(body.credential, dict) else None
    transports = response_data.get("transports", []) if isinstance(response_data, dict) else []
    transports = [str(value)[:32] for value in transports[:8] if isinstance(value, str)]
    db.add(
        PlatformPasskeyCredential(
            credential_id=credential_id,
            user_id=admin.id,
            credential_public_key=b64url_encode(verification.credential_public_key),
            sign_count=int(verification.sign_count),
            transports=transports,
            credential_device_type=_enum_value(verification.credential_device_type),
            credential_backed_up=bool(verification.credential_backed_up),
        )
    )
    _audit_registration(db, admin.id, credential_id)
    db.commit()
    expires_in = _set_step_up_cookie(response, request, admin.id)
    return {
        "enrolled": True,
        "credential_id": credential_id,
        "user_verified": True,
        "expires_in": expires_in,
    }


@router.post("/authentication/options")
def authentication_options(
    request: Request,
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(_platform_actor),
):
    assert_stable_webauthn_origin(_origin(request))
    credential = _credential(db, admin.id)
    if credential is None:
        raise HTTPException(status_code=404, detail="Aucune passkey plateforme enregistrée.")

    from webauthn import generate_authentication_options
    from webauthn.helpers.structs import PublicKeyCredentialDescriptor, UserVerificationRequirement

    options = generate_authentication_options(
        rp_id=WEBAUTHN_RP_ID,
        allow_credentials=[PublicKeyCredentialDescriptor(id=b64url_decode(credential.credential_id))],
        user_verification=UserVerificationRequirement.REQUIRED,
        timeout=60000,
    )
    challenge_id = _issue_challenge(
        db,
        purpose="authenticate",
        user_id=admin.id,
        challenge=options.challenge,
    )
    return _options_payload(options, challenge_id=challenge_id)


@router.post("/authentication/verify")
def authentication_verify(
    request: Request,
    response: Response,
    body: CeremonyResponse,
    db: Session = Depends(database.get_db),
    admin: models.User = Depends(_platform_actor),
):
    assert_stable_webauthn_origin(_origin(request))
    credential = _credential(db, admin.id)
    if credential is None:
        raise HTTPException(status_code=404, detail="Aucune passkey plateforme enregistrée.")

    expected_challenge = _consume_challenge(
        db,
        challenge_id=body.challenge_id,
        purpose="authenticate",
        user_id=admin.id,
    )
    try:
        from webauthn import verify_authentication_response
        from webauthn.helpers.exceptions import InvalidAuthenticationResponse

        verification = verify_authentication_response(
            credential=body.credential,
            expected_challenge=expected_challenge,
            expected_rp_id=WEBAUTHN_RP_ID,
            expected_origin=WEBAUTHN_ORIGIN,
            credential_public_key=b64url_decode(credential.credential_public_key),
            credential_current_sign_count=int(credential.sign_count),
            require_user_verification=True,
        )
    except InvalidAuthenticationResponse as exc:
        raise HTTPException(status_code=401, detail="Vérification WebAuthn plateforme refusée.") from exc
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Vérification WebAuthn plateforme impossible.") from exc

    if b64url_encode(verification.credential_id) != credential.credential_id:
        raise HTTPException(status_code=401, detail="Passkey plateforme incompatible.")
    credential.sign_count = int(verification.new_sign_count)
    credential.last_used_at = datetime.utcnow()
    credential.credential_device_type = _enum_value(verification.credential_device_type)
    credential.credential_backed_up = bool(verification.credential_backed_up)
    db.commit()

    expires_in = _set_step_up_cookie(response, request, admin.id)
    return {
        "expires_in": expires_in,
        "credential_id": credential.credential_id,
        "user_verified": bool(verification.user_verified),
    }
