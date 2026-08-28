from __future__ import annotations

import base64
import binascii
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


DEVICE_CERT_SCHEMA_VERSION = 1
DEVICE_CERT_ISSUER = "digital-crown"
DEVICE_CERT_AUDIENCE = "digital-crown-device"
DEVICE_CERT_TOKEN_TYPE = "DC-DEVICE"
DEVICE_CERT_ALGORITHM = "EdDSA"

ALLOWED_DEVICE_STATUSES = frozenset({"ACTIVE", "REVOKED"})
ALLOWED_DEVICE_PLATFORMS = frozenset({"windows", "macos"})


class DeviceSecurityError(ValueError):
    """Raised when a device identity/certificate cannot be trusted."""


@dataclass(frozen=True)
class VerifiedDeviceCertificate:
    claims: Mapping[str, Any]
    key_id: str

    @property
    def certificate_id(self) -> str:
        return str(self.claims["certificate_id"])

    @property
    def cabinet_id(self) -> str:
        return str(self.claims["cabinet_id"])

    @property
    def license_id(self) -> str:
        return str(self.claims["license_id"])

    @property
    def device_id(self) -> str:
        return str(self.claims["device_id"])

    @property
    def device_public_key(self) -> str:
        return str(self.claims["device_public_key"])

    @property
    def platform(self) -> str:
        return str(self.claims["platform"])

    @property
    def status(self) -> str:
        return str(self.claims["status"])

    @property
    def expires_at(self) -> datetime | None:
        raw = self.claims.get("expires_at")
        return _parse_datetime(raw, "expires_at") if raw is not None else None


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    if not isinstance(value, str) or not value:
        raise DeviceSecurityError("invalid base64url segment")
    try:
        padding = "=" * (-len(value) % 4)
        return base64.urlsafe_b64decode((value + padding).encode("ascii"))
    except (ValueError, UnicodeEncodeError, binascii.Error) as exc:
        raise DeviceSecurityError("invalid base64url segment") from exc


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
        raise DeviceSecurityError("device certificate data is not valid JSON") from exc


def _decode_json_segment(segment: str, label: str) -> dict[str, Any]:
    try:
        value = json.loads(_b64url_decode(segment).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DeviceSecurityError(f"invalid {label}") from exc
    if not isinstance(value, dict):
        raise DeviceSecurityError(f"invalid {label}")
    return value


def _parse_datetime(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise DeviceSecurityError(f"invalid {field}")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise DeviceSecurityError(f"invalid {field}") from exc
    if parsed.tzinfo is None:
        raise DeviceSecurityError(f"{field} must include timezone")
    return parsed.astimezone(timezone.utc)


def _require_string(claims: Mapping[str, Any], field: str) -> str:
    value = claims.get(field)
    if not isinstance(value, str) or not value.strip():
        raise DeviceSecurityError(f"invalid {field}")
    return value


def _private_key_from_raw_b64url(value: str) -> Ed25519PrivateKey:
    raw = _b64url_decode(value)
    if len(raw) != 32:
        raise DeviceSecurityError("invalid Ed25519 private key")
    try:
        return Ed25519PrivateKey.from_private_bytes(raw)
    except ValueError as exc:
        raise DeviceSecurityError("invalid Ed25519 private key") from exc


def _public_key_from_raw_b64url(value: str) -> Ed25519PublicKey:
    raw = _b64url_decode(value)
    if len(raw) != 32:
        raise DeviceSecurityError("invalid Ed25519 public key")
    try:
        return Ed25519PublicKey.from_public_bytes(raw)
    except ValueError as exc:
        raise DeviceSecurityError("invalid Ed25519 public key") from exc


def derive_device_id(device_public_key_b64url: str) -> str:
    raw = _b64url_decode(device_public_key_b64url)
    if len(raw) != 32:
        raise DeviceSecurityError("invalid device public key")
    return hashlib.sha256(raw).hexdigest()


def sign_device_certificate(
    claims: Mapping[str, Any],
    private_key_b64url: str,
    key_id: str,
) -> str:
    if not isinstance(key_id, str) or not key_id.strip():
        raise DeviceSecurityError("invalid key_id")

    payload = dict(claims)
    payload["key_id"] = key_id
    header = {
        "alg": DEVICE_CERT_ALGORITHM,
        "kid": key_id,
        "typ": DEVICE_CERT_TOKEN_TYPE,
    }
    encoded_header = _b64url_encode(_json_bytes(header))
    encoded_payload = _b64url_encode(_json_bytes(payload))
    signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")
    signature = _private_key_from_raw_b64url(private_key_b64url).sign(signing_input)
    return f"{encoded_header}.{encoded_payload}.{_b64url_encode(signature)}"


def verify_device_certificate(
    token: str,
    trusted_public_keys: Mapping[str, str],
    *,
    expected_cabinet_id: str | None = None,
    expected_license_id: str | None = None,
    expected_device_id: str | None = None,
    expected_platform: str | None = None,
    now: datetime | None = None,
    allow_inactive: bool = False,
) -> VerifiedDeviceCertificate:
    if not isinstance(token, str):
        raise DeviceSecurityError("invalid device certificate")
    parts = token.split(".")
    if len(parts) != 3:
        raise DeviceSecurityError("invalid device certificate")

    encoded_header, encoded_payload, encoded_signature = parts
    header = _decode_json_segment(encoded_header, "device certificate header")
    claims = _decode_json_segment(encoded_payload, "device certificate payload")

    if header.get("alg") != DEVICE_CERT_ALGORITHM:
        raise DeviceSecurityError("unsupported device certificate algorithm")
    if header.get("typ") != DEVICE_CERT_TOKEN_TYPE:
        raise DeviceSecurityError("invalid device certificate token type")

    key_id = header.get("kid")
    if not isinstance(key_id, str) or not key_id:
        raise DeviceSecurityError("missing device certificate key id")
    public_key_encoded = trusted_public_keys.get(key_id)
    if not public_key_encoded:
        raise DeviceSecurityError("untrusted device certificate signing key")

    signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")
    try:
        signature = _b64url_decode(encoded_signature)
        _public_key_from_raw_b64url(public_key_encoded).verify(signature, signing_input)
    except InvalidSignature as exc:
        raise DeviceSecurityError("invalid device certificate signature") from exc

    if claims.get("key_id") != key_id:
        raise DeviceSecurityError("device certificate key id mismatch")
    if claims.get("schema_version") != DEVICE_CERT_SCHEMA_VERSION:
        raise DeviceSecurityError("unsupported device certificate schema")
    if claims.get("issuer") != DEVICE_CERT_ISSUER:
        raise DeviceSecurityError("invalid device certificate issuer")
    if claims.get("audience") != DEVICE_CERT_AUDIENCE:
        raise DeviceSecurityError("invalid device certificate audience")

    _require_string(claims, "certificate_id")
    cabinet_id = _require_string(claims, "cabinet_id")
    license_id = _require_string(claims, "license_id")
    device_id = _require_string(claims, "device_id")
    device_public_key = _require_string(claims, "device_public_key")
    platform = _require_string(claims, "platform")
    status = _require_string(claims, "status")

    if platform not in ALLOWED_DEVICE_PLATFORMS:
        raise DeviceSecurityError("invalid device platform")
    if status not in ALLOWED_DEVICE_STATUSES:
        raise DeviceSecurityError("invalid device status")
    if status != "ACTIVE" and not allow_inactive:
        raise DeviceSecurityError("device certificate is not active")

    if derive_device_id(device_public_key) != device_id:
        raise DeviceSecurityError("device id/public key mismatch")

    issued_at = _parse_datetime(claims.get("issued_at"), "issued_at")
    not_before = _parse_datetime(claims.get("not_before"), "not_before")
    expires_raw = claims.get("expires_at")
    expires_at = _parse_datetime(expires_raw, "expires_at") if expires_raw is not None else None

    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise DeviceSecurityError("verification time must include timezone")
    current = current.astimezone(timezone.utc)
    if issued_at > current:
        raise DeviceSecurityError("device certificate issued_at is in the future")
    if not_before > current:
        raise DeviceSecurityError("device certificate is not yet valid")
    if status == "ACTIVE" and expires_at is not None and expires_at <= current:
        raise DeviceSecurityError("device certificate expired")

    if expected_cabinet_id is not None and cabinet_id != str(expected_cabinet_id):
        raise DeviceSecurityError("device cabinet mismatch")
    if expected_license_id is not None and license_id != str(expected_license_id):
        raise DeviceSecurityError("device license mismatch")
    if expected_device_id is not None and device_id != str(expected_device_id):
        raise DeviceSecurityError("device id mismatch")
    if expected_platform is not None and platform != str(expected_platform):
        raise DeviceSecurityError("device platform mismatch")

    return VerifiedDeviceCertificate(claims=claims, key_id=key_id)
