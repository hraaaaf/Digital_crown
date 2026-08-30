"""Short-lived second-factor gate for privileged platform mutations.

The primary control-plane session remains a normal web access token. WebAuthn
issues a dedicated ``platform_step_up`` JWT kept in a scoped HttpOnly cookie.
A header fallback remains for isolated security tests and non-browser clients.
The proof can never become the primary SuperAdmin session.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from backend import models
from backend.security import ALGORITHM, SECRET_KEY

PLATFORM_STEP_UP_HEADER = "x-platform-step-up"
PLATFORM_STEP_UP_COOKIE = "platform_step_up"
PLATFORM_STEP_UP_TTL = timedelta(minutes=5)
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
    """Require a fresh platform WebAuthn proof bound to the current web user."""
    del db  # Signature kept stable for dependency callers; proof is self-contained.
    token = (
        request.cookies.get(PLATFORM_STEP_UP_COOKIE)
        or request.headers.get(PLATFORM_STEP_UP_HEADER)
        or ""
    ).strip()
    if not token:
        raise _deny(
            "PLATFORM_STEP_UP_REQUIRED",
            "Vérification WebAuthn récente requise pour cette action plateforme.",
        )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise _deny(
            "PLATFORM_STEP_UP_INVALID",
            "Preuve de vérification plateforme invalide ou expirée.",
        ) from exc

    if payload.get("type") != "platform_step_up":
        raise _deny(
            "PLATFORM_STEP_UP_INVALID_TYPE",
            "Le jeton fourni n'est pas une preuve de vérification plateforme.",
        )

    try:
        proof_user_id = int(payload.get("sub"))
    except (TypeError, ValueError) as exc:
        raise _deny(
            "PLATFORM_STEP_UP_INVALID_SUBJECT",
            "Identité de vérification plateforme invalide.",
        ) from exc
    if proof_user_id != int(current_user.id):
        raise _deny(
            "PLATFORM_STEP_UP_IDENTITY_MISMATCH",
            "La preuve WebAuthn ne correspond pas à la session plateforme.",
        )

    jti = str(payload.get("jti") or "")
    if not jti.startswith("platform-step-up:"):
        raise _deny(
            "PLATFORM_STEP_UP_INVALID_JTI",
            "Identifiant de preuve plateforme invalide.",
        )

    try:
        issued_at = datetime.fromtimestamp(float(payload["iat"]), tz=timezone.utc)
    except (KeyError, TypeError, ValueError, OSError) as exc:
        raise _deny(
            "PLATFORM_STEP_UP_INVALID_IAT",
            "Horodatage de vérification plateforme invalide.",
        ) from exc

    now = datetime.now(timezone.utc)
    if issued_at > now + _CLOCK_SKEW or now - issued_at > PLATFORM_STEP_UP_TTL + _CLOCK_SKEW:
        raise _deny(
            "PLATFORM_STEP_UP_EXPIRED",
            "La vérification WebAuthn plateforme doit dater de moins de cinq minutes.",
        )

    return payload


def enforce_platform_step_up_for_mutation(
    request: Request,
    *,
    current_user: models.User,
    db: Session,
) -> None:
    """Apply step-up only to state-changing SuperAdmin requests."""
    if not request.url.path.startswith("/api/superadmin"):
        return
    if request.method.upper() not in {"POST", "PUT", "PATCH", "DELETE"}:
        return
    verify_platform_step_up(request, current_user=current_user, db=db)
