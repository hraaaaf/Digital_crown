"""Short-lived second-factor gate for privileged platform mutations.

The primary control-plane session must remain a normal web access token. This
module accepts the existing server-verified WebAuthn UV token only as a second
factor through ``X-Platform-Step-Up``. A mobile token therefore never becomes a
Superadmin session by itself.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from backend import models
from backend.routers.mobile_legacy import _decode_mobile_identity
from backend.services.mobile_biometric import BIOMETRIC_SESSION_TTL, payload_has_biometric_uv

PLATFORM_STEP_UP_HEADER = "x-platform-step-up"
_CLOCK_SKEW = timedelta(seconds=30)


def _deny(code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=403,
        detail={"code": code, "message": message},
    )


def verify_platform_step_up(
    request: Request,
    *,
    current_user: models.User,
    db: Session,
) -> dict:
    """Require a fresh WebAuthn user-verification proof for a platform mutation.

    The proof is intentionally separate from the primary web access token. The
    mobile identity decoder validates signature, expiry, JTI revocation, tenant,
    user and paired-device state; this function additionally requires the
    biometric-UV claim and binds that proof to the exact current web user.
    """
    token = (request.headers.get(PLATFORM_STEP_UP_HEADER) or "").strip()
    if not token:
        raise _deny(
            "PLATFORM_STEP_UP_REQUIRED",
            "Vérification biométrique récente requise pour cette action plateforme.",
        )

    try:
        uv_user, tenant_id, payload = _decode_mobile_identity(f"Bearer {token}", db)
    except HTTPException as exc:
        raise _deny(
            "PLATFORM_STEP_UP_INVALID",
            "Preuve de vérification plateforme invalide ou expirée.",
        ) from exc

    if uv_user.id != current_user.id:
        raise _deny(
            "PLATFORM_STEP_UP_IDENTITY_MISMATCH",
            "La preuve biométrique ne correspond pas à la session plateforme.",
        )

    if int(tenant_id) != int(current_user.get_employer_id()):
        raise _deny(
            "PLATFORM_STEP_UP_TENANT_MISMATCH",
            "La preuve biométrique appartient à un autre cabinet.",
        )

    if not payload_has_biometric_uv(payload):
        raise _deny(
            "PLATFORM_STEP_UP_UV_REQUIRED",
            "Une vérification WebAuthn utilisateur est requise.",
        )

    try:
        issued_at = datetime.fromtimestamp(float(payload["iat"]), tz=timezone.utc)
    except (KeyError, TypeError, ValueError, OSError) as exc:
        raise _deny(
            "PLATFORM_STEP_UP_INVALID_IAT",
            "Horodatage de vérification plateforme invalide.",
        ) from exc

    now = datetime.now(timezone.utc)
    if issued_at > now + _CLOCK_SKEW or now - issued_at > BIOMETRIC_SESSION_TTL + _CLOCK_SKEW:
        raise _deny(
            "PLATFORM_STEP_UP_EXPIRED",
            "La vérification biométrique plateforme doit dater de moins de cinq minutes.",
        )

    return payload


def enforce_platform_step_up_for_mutation(
    request: Request,
    *,
    current_user: models.User,
    db: Session,
) -> None:
    """Apply step-up only to state-changing Superadmin requests."""
    if not request.url.path.startswith("/api/superadmin"):
        return
    if request.method.upper() not in {"POST", "PUT", "PATCH", "DELETE"}:
        return
    verify_platform_step_up(request, current_user=current_user, db=db)
