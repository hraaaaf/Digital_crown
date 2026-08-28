import base64
from datetime import datetime, timedelta, timezone

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat, PublicFormat

from backend.device_security import (
    DeviceSecurityError,
    derive_device_id,
    sign_device_certificate,
    verify_device_certificate,
)


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _keypair():
    private = Ed25519PrivateKey.generate()
    private_raw = private.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
    public_raw = private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    return _b64url(private_raw), _b64url(public_raw)


def _claims(now, device_public_key, **overrides):
    claims = {
        "schema_version": 1,
        "issuer": "digital-crown",
        "audience": "digital-crown-device",
        "certificate_id": "devcert-001",
        "cabinet_id": "cab-001",
        "license_id": "lic-001",
        "device_id": derive_device_id(device_public_key),
        "device_public_key": device_public_key,
        "platform": "windows",
        "status": "ACTIVE",
        "issued_at": now.isoformat(),
        "not_before": now.isoformat(),
        "expires_at": (now + timedelta(days=30)).isoformat(),
        "created_by_user_id": 7,
    }
    claims.update(overrides)
    return claims


def test_device_certificate_accepts_matching_device_and_rejects_copy():
    issuer_private, issuer_public = _keypair()
    _device_private, device_public = _keypair()
    _other_private, other_public = _keypair()
    now = datetime(2026, 8, 28, 12, 0, tzinfo=timezone.utc)

    token = sign_device_certificate(_claims(now, device_public), issuer_private, "issuer-k1")
    verified = verify_device_certificate(
        token,
        {"issuer-k1": issuer_public},
        expected_cabinet_id="cab-001",
        expected_license_id="lic-001",
        expected_device_id=derive_device_id(device_public),
        expected_platform="windows",
        now=now + timedelta(seconds=1),
    )
    assert verified.device_id == derive_device_id(device_public)
    assert verified.device_public_key == device_public

    with pytest.raises(DeviceSecurityError, match="device id mismatch"):
        verify_device_certificate(
            token,
            {"issuer-k1": issuer_public},
            expected_device_id=derive_device_id(other_public),
            now=now + timedelta(seconds=1),
        )


def test_device_id_is_derived_only_from_public_key():
    _private_a, public_a = _keypair()
    _private_b, public_b = _keypair()
    assert derive_device_id(public_a) == derive_device_id(public_a)
    assert derive_device_id(public_a) != derive_device_id(public_b)
    assert len(derive_device_id(public_a)) == 64


def test_tampered_device_certificate_is_rejected():
    issuer_private, issuer_public = _keypair()
    _device_private, device_public = _keypair()
    now = datetime(2026, 8, 28, 12, 0, tzinfo=timezone.utc)
    token = sign_device_certificate(_claims(now, device_public), issuer_private, "issuer-k1")

    header, payload, signature = token.split(".")
    replacement = "A" if payload[-1] != "A" else "B"
    tampered = f"{header}.{payload[:-1]}{replacement}.{signature}"
    with pytest.raises(DeviceSecurityError):
        verify_device_certificate(tampered, {"issuer-k1": issuer_public}, now=now + timedelta(seconds=1))


def test_certificate_rejects_public_key_device_id_mismatch_even_when_signed():
    issuer_private, issuer_public = _keypair()
    _device_private, device_public = _keypair()
    _other_private, other_public = _keypair()
    now = datetime(2026, 8, 28, 12, 0, tzinfo=timezone.utc)
    token = sign_device_certificate(
        _claims(now, device_public, device_id=derive_device_id(other_public)),
        issuer_private,
        "issuer-k1",
    )

    with pytest.raises(DeviceSecurityError, match="public key mismatch"):
        verify_device_certificate(token, {"issuer-k1": issuer_public}, now=now + timedelta(seconds=1))


def test_revoked_and_expired_device_certificates_fail_closed():
    issuer_private, issuer_public = _keypair()
    _device_private, device_public = _keypair()
    now = datetime(2026, 8, 28, 12, 0, tzinfo=timezone.utc)

    revoked = sign_device_certificate(
        _claims(now, device_public, status="REVOKED"),
        issuer_private,
        "issuer-k1",
    )
    with pytest.raises(DeviceSecurityError, match="not active"):
        verify_device_certificate(revoked, {"issuer-k1": issuer_public}, now=now + timedelta(seconds=1))

    expired = sign_device_certificate(
        _claims(now, device_public, expires_at=(now + timedelta(seconds=1)).isoformat()),
        issuer_private,
        "issuer-k1",
    )
    with pytest.raises(DeviceSecurityError, match="expired"):
        verify_device_certificate(expired, {"issuer-k1": issuer_public}, now=now + timedelta(seconds=2))
