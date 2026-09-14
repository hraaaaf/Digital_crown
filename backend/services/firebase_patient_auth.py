from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from firebase_admin import auth as firebase_auth
from firebase_admin import credentials, get_app, initialize_app

from backend.core.paths import AppPaths

logger = logging.getLogger("patient_companion.firebase_auth")


class FirebasePatientAuthError(Exception):
    """Base class for patient Firebase authentication errors."""


class FirebasePatientAuthUnavailable(FirebasePatientAuthError):
    """Firebase verifier cannot be initialized safely."""


class FirebasePatientAuthInvalid(FirebasePatientAuthError):
    """Credential is invalid, expired, revoked or disabled."""


@dataclass(frozen=True)
class FirebasePatientCredential:
    subject: str
    issued_at: datetime | None
    expires_at: datetime | None
    auth_time: datetime | None


def _as_datetime(value) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromtimestamp(int(value), tz=timezone.utc)
    except (TypeError, ValueError, OSError):
        return None


def _ensure_firebase_app():
    try:
        return get_app()
    except ValueError:
        cred_path = AppPaths.get_base_dir() / "backend" / "core" / "firebase_creds.json"
        if not cred_path.exists():
            raise FirebasePatientAuthUnavailable(
                "Firebase patient authentication is unavailable."
            )
        try:
            return initialize_app(credentials.Certificate(str(cred_path)))
        except Exception as exc:
            logger.error(
                "Unable to initialize Firebase patient verifier: %s",
                exc.__class__.__name__,
            )
            raise FirebasePatientAuthUnavailable(
                "Firebase patient authentication is unavailable."
            ) from None


def verify_patient_id_token(id_token: str) -> FirebasePatientCredential:
    """Verify a Firebase ID token and return only the claims needed by Patient Companion.

    Token contents are never logged. Revocation checks are enabled because this principal
    gates patient health data; any verifier failure is fail-closed.
    """
    if not id_token or len(id_token) > 8192:
        raise FirebasePatientAuthInvalid("Invalid patient credential.")

    app = _ensure_firebase_app()
    try:
        decoded = firebase_auth.verify_id_token(
            id_token,
            app=app,
            check_revoked=True,
        )
    except Exception as exc:
        logger.warning(
            "Firebase patient credential rejected: %s",
            exc.__class__.__name__,
        )
        raise FirebasePatientAuthInvalid("Invalid patient credential.") from None

    subject = str(decoded.get("uid") or decoded.get("sub") or "").strip()
    if not subject or len(subject) > 128:
        raise FirebasePatientAuthInvalid("Invalid patient credential.")

    return FirebasePatientCredential(
        subject=subject,
        issued_at=_as_datetime(decoded.get("iat")),
        expires_at=_as_datetime(decoded.get("exp")),
        auth_time=_as_datetime(decoded.get("auth_time")),
    )
