from __future__ import annotations

import base64
import binascii
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


LICENSE_SCHEMA_VERSION = 1
LICENSE_ISSUER = "digital-crown"
LICENSE_AUDIENCE = "digital-crown-desktop"
LICENSE_TOKEN_TYPE = "DC-LICENSE"
LICENSE_ALGORITHM = "EdDSA"

ALLOWED_LICENSE_TYPES = frozenset({"TRIAL", "PAID", "OWNER"})
ALLOWED_RELEASE_CHANNELS = frozenset({"stable", "beta"})
ALLOWED_STATUSES = frozenset({"ACTIVE", "REVOKED"})


class LicenseSecurityError(ValueError):
    """Raised when a Digital Crown license cannot be trusted or accepted."""


@dataclass(frozen=True)
class VerifiedLicense:
    claims: Mapping[str, Any]
    key_id: str

    @property
    def license_id(self) -> str:
        return str(self.claims["license_id"])

    @property
    def cabinet_id(self) -> str:
        return str(self.claims["cabinet_id"])

    @property
    def license_type(self) -> str:
        return str(self.claims["license_type"])

    @property
    def status(self) -> str:
        return str(self.claims["status"])

    @property
    def expires_at(self) -> datetime | None:
        raw = self.claims.get("expires_at")
        return _parse_datetime(raw, "expires_at") if raw is not None else None

    @property
    def subject_user_id(self) -> int | None:
        raw = self.claims.get("subject_user_id")
        return int(raw) if raw is not None else None


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    if not isinstance(value, str) or not value:
        raise LicenseSecurityError("invalid base64url segment")
    try:
        padding = "=" * (-len(value) % 4)
        return base64.urlsafe_b64decode((value + padding).encode("ascii"))
    except (ValueError, UnicodeEncodeError, binascii.Error) as exc:
        raise LicenseSecurityError("invalid base64url segment") from exc


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise LicenseSecurityError("license data is not valid JSON") from exc


def _decode_json_segment(segment: str, label: str) -> dict[str, Any]:
    try:
        value = json.loads(_b64url_decode(segment).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LicenseSecurityError(f"invalid {label}") from exc
    if not isinstance(value, dict):
        raise LicenseSecurityError(f"invalid {label}")
    return value


def _parse_datetime(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise LicenseSecurityError(f"invalid {field}")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise LicenseSecurityError(f"invalid {field}") from exc
    if parsed.tzinfo is None:
        raise LicenseSecurityError(f"{field} must include timezone")
    return parsed.astimezone(timezone.utc)


def _require_string(claims: Mapping[str, Any], field: str) -> str:
    value = claims.get(field)
    if not isinstance(value, str) or not value.strip():
        raise LicenseSecurityError(f"invalid {field}")
    return value


def _require_int(claims: Mapping[str, Any], field: str) -> int:
    value = claims.get(field)
    if isinstance(value, bool) or not isinstance(value, int):
        raise LicenseSecurityError(f"invalid {field}")
    return value


def _private_key_from_raw_b64url(value: str) -> Ed25519PrivateKey:
    raw = _b64url_decode(value)
    if len(raw) != 32:
        raise LicenseSecurityError("invalid Ed25519 private key")
    try:
        return Ed25519PrivateKey.from_private_bytes(raw)
    except ValueError as exc:
        raise LicenseSecurityError("invalid Ed25519 private key") from exc


def _public_key_from_raw_b64url(value: str) -> Ed25519PublicKey:
    raw = _b64url_decode(value)
    if len(raw) != 32:
        raise LicenseSecurityError("invalid Ed25519 public key")
    try:
        return Ed25519PublicKey.from_public_bytes(raw)
    except ValueError as exc:
        raise LicenseSecurityError("invalid Ed25519 public key") from exc


def sign_license(claims: Mapping[str, Any], private_key_b64url: str, key_id: str) -> str:
    """Create a compact signed Digital Crown license.

    This function is issuer-side only. The private key must never be shipped
    with the desktop application.
    """
    if not isinstance(key_id, str) or not key_id.strip():
        raise LicenseSecurityError("invalid key_id")

    payload = dict(claims)
    payload["key_id"] = key_id
    header = {
        "alg": LICENSE_ALGORITHM,
        "kid": key_id,
        "typ": LICENSE_TOKEN_TYPE,
    }

    encoded_header = _b64url_encode(_json_bytes(header))
    encoded_payload = _b64url_encode(_json_bytes(payload))
    signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")
    signature = _private_key_from_raw_b64url(private_key_b64url).sign(signing_input)
    return f"{encoded_header}.{encoded_payload}.{_b64url_encode(signature)}"


def verify_license(
    token: str,
    trusted_public_keys: Mapping[str, str],
    *,
    expected_cabinet_id: str | None = None,
    expected_owner_user_id: int | None = None,
    now: datetime | None = None,
    allow_inactive: bool = False,
) -> VerifiedLicense:
    """Verify and validate a compact Digital Crown license, fail-closed."""
    if not isinstance(token, str):
        raise LicenseSecurityError("invalid license token")
    parts = token.split(".")
    if len(parts) != 3:
        raise LicenseSecurityError("invalid license token")

    encoded_header, encoded_payload, encoded_signature = parts
    header = _decode_json_segment(encoded_header, "license header")
    claims = _decode_json_segment(encoded_payload, "license payload")

    if header.get("alg") != LICENSE_ALGORITHM:
        raise LicenseSecurityError("unsupported license algorithm")
    if header.get("typ") != LICENSE_TOKEN_TYPE:
        raise LicenseSecurityError("invalid license token type")

    key_id = header.get("kid")
    if not isinstance(key_id, str) or not key_id:
        raise LicenseSecurityError("missing license key id")
    public_key_encoded = trusted_public_keys.get(key_id)
    if not public_key_encoded:
        raise LicenseSecurityError("untrusted license signing key")

    signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")
    try:
        signature = _b64url_decode(encoded_signature)
        _public_key_from_raw_b64url(public_key_encoded).verify(signature, signing_input)
    except InvalidSignature as exc:
        raise LicenseSecurityError("invalid license signature") from exc

    if claims.get("key_id") != key_id:
        raise LicenseSecurityError("license key id mismatch")
    if claims.get("schema_version") != LICENSE_SCHEMA_VERSION:
        raise LicenseSecurityError("unsupported license schema")
    if claims.get("issuer") != LICENSE_ISSUER:
        raise LicenseSecurityError("invalid license issuer")
    if claims.get("audience") != LICENSE_AUDIENCE:
        raise LicenseSecurityError("invalid license audience")

    _require_string(claims, "license_id")
    cabinet_id = _require_string(claims, "cabinet_id")
    _require_int(claims, "created_by_user_id")
    _require_string(claims, "policy_version")

    license_type = _require_string(claims, "license_type")
    if license_type not in ALLOWED_LICENSE_TYPES:
        raise LicenseSecurityError("invalid license type")

    release_channel = _require_string(claims, "release_channel")
    if release_channel not in ALLOWED_RELEASE_CHANNELS:
        raise LicenseSecurityError("invalid release channel")

    status = _require_string(claims, "status")
    if status not in ALLOWED_STATUSES:
        raise LicenseSecurityError("invalid license status")
    if status != "ACTIVE" and not allow_inactive:
        raise LicenseSecurityError("license is not active")

    issued_at = _parse_datetime(claims.get("issued_at"), "issued_at")
    not_before = _parse_datetime(claims.get("not_before"), "not_before")
    expires_at_raw = claims.get("expires_at")
    expires_at = (
        _parse_datetime(expires_at_raw, "expires_at")
        if expires_at_raw is not None
        else None
    )

    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise LicenseSecurityError("verification time must include timezone")
    current = current.astimezone(timezone.utc)

    if issued_at > current:
        raise LicenseSecurityError("license issued_at is in the future")
    if not_before > current:
        raise LicenseSecurityError("license is not yet valid")

    if license_type == "OWNER":
        subject_user_id = _require_int(claims, "subject_user_id")
        if expires_at is not None:
            raise LicenseSecurityError("OWNER license must not expire")
        if expected_owner_user_id is not None and subject_user_id != expected_owner_user_id:
            raise LicenseSecurityError("OWNER subject mismatch")
    else:
        if expires_at is None:
            raise LicenseSecurityError("expiring license requires expires_at")
        if status == "ACTIVE" and expires_at <= current:
            raise LicenseSecurityError("license expired")
        if claims.get("subject_user_id") is not None:
            _require_int(claims, "subject_user_id")

    if expected_cabinet_id is not None and cabinet_id != str(expected_cabinet_id):
        raise LicenseSecurityError("license cabinet mismatch")

    max_devices = claims.get("max_devices")
    if license_type == "OWNER":
        if max_devices is not None:
            raise LicenseSecurityError("OWNER license must not set max_devices")
    else:
        if isinstance(max_devices, bool) or not isinstance(max_devices, int) or max_devices < 1:
            raise LicenseSecurityError("invalid max_devices")

    feature_set = claims.get("feature_set")
    if not isinstance(feature_set, (str, list)):
        raise LicenseSecurityError("invalid feature_set")
    if isinstance(feature_set, str) and not feature_set:
        raise LicenseSecurityError("invalid feature_set")
    if isinstance(feature_set, list):
        if not feature_set or any(not isinstance(v, str) or not v for v in feature_set):
            raise LicenseSecurityError("invalid feature_set")

    return VerifiedLicense(claims=claims, key_id=key_id)
