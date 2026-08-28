from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any

from backend.license_security import (
    LICENSE_AUDIENCE,
    LICENSE_ISSUER,
    LICENSE_SCHEMA_VERSION,
    LicenseSecurityError,
    sign_license,
)


SIGNING_PRIVATE_KEY_ENV = "DIGITALCROWN_LICENSE_SIGNING_PRIVATE_KEY_B64URL"
SIGNING_KEY_ID_ENV = "DIGITALCROWN_LICENSE_SIGNING_KEY_ID"


class LicenseIssuerUnavailable(RuntimeError):
    """The control plane has no usable signing key configured."""


def _signing_material() -> tuple[str, str]:
    private_key = os.getenv(SIGNING_PRIVATE_KEY_ENV, "").strip()
    key_id = os.getenv(SIGNING_KEY_ID_ENV, "").strip()
    if not private_key or not key_id:
        raise LicenseIssuerUnavailable(
            "License signing is unavailable: control-plane signing material is not configured."
        )
    return private_key, key_id


def _iso_utc(value: datetime) -> str:
    if value.tzinfo is None:
        raise LicenseSecurityError("license timestamps must include timezone")
    return value.astimezone(timezone.utc).isoformat()


def issue_license(
    *,
    cabinet_id: str,
    license_type: str,
    created_by_user_id: int,
    expires_at: datetime | None,
    release_channel: str = "stable",
    feature_set: str | list[str] = "full",
    max_devices: int | None = 1,
    status: str = "ACTIVE",
    subject_user_id: int | None = None,
    license_id: str | None = None,
    policy_version: str = "1",
    not_before: datetime | None = None,
    issued_at: datetime | None = None,
) -> str:
    """Issue a signed license from the secured control plane.

    The private key is loaded only at call time from the control-plane
    environment. The desktop verifier does not need, receive, or persist it.
    """
    private_key, key_id = _signing_material()
    now = issued_at or datetime.now(timezone.utc)
    starts_at = not_before or now

    claims: dict[str, Any] = {
        "schema_version": LICENSE_SCHEMA_VERSION,
        "issuer": LICENSE_ISSUER,
        "audience": LICENSE_AUDIENCE,
        "license_id": license_id or str(uuid.uuid4()),
        "cabinet_id": str(cabinet_id),
        "license_type": license_type,
        "status": status,
        "issued_at": _iso_utc(now),
        "not_before": _iso_utc(starts_at),
        "expires_at": _iso_utc(expires_at) if expires_at is not None else None,
        "release_channel": release_channel,
        "feature_set": feature_set,
        "max_devices": max_devices,
        "policy_version": str(policy_version),
        "created_by_user_id": int(created_by_user_id),
    }
    if subject_user_id is not None:
        claims["subject_user_id"] = int(subject_user_id)

    return sign_license(claims, private_key, key_id)
