import base64
import json
from datetime import datetime, timedelta, timezone

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)

from backend.license_issuer import (
    LicenseIssuerUnavailable,
    issue_license,
)
from backend.license_security import LicenseSecurityError, sign_license, verify_license


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


@pytest.fixture
def keypair():
    private = Ed25519PrivateKey.generate()
    private_raw = private.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
    public_raw = private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    return _b64url(private_raw), _b64url(public_raw)


@pytest.fixture
def now():
    return datetime(2026, 8, 28, 12, 0, tzinfo=timezone.utc)


def _claims(now: datetime, **overrides):
    claims = {
        "schema_version": 1,
        "issuer": "digital-crown",
        "audience": "digital-crown-desktop",
        "license_id": "lic-001",
        "cabinet_id": "cab-001",
        "license_type": "TRIAL",
        "status": "ACTIVE",
        "issued_at": now.isoformat(),
        "not_before": now.isoformat(),
        "expires_at": (now + timedelta(days=30)).isoformat(),
        "release_channel": "stable",
        "feature_set": "full",
        "max_devices": 1,
        "policy_version": "1",
        "created_by_user_id": 7,
    }
    claims.update(overrides)
    return claims


def _tamper_payload(token: str, **changes) -> str:
    header, payload, signature = token.split(".")
    padding = "=" * (-len(payload) % 4)
    value = json.loads(base64.urlsafe_b64decode((payload + padding).encode()).decode())
    value.update(changes)
    changed = _b64url(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    )
    return f"{header}.{changed}.{signature}"


def test_valid_trial_is_accepted(keypair, now):
    private, public = keypair
    token = sign_license(_claims(now), private, "k1")

    verified = verify_license(
        token,
        {"k1": public},
        expected_cabinet_id="cab-001",
        now=now + timedelta(seconds=1),
    )

    assert verified.license_type == "TRIAL"
    assert verified.license_id == "lic-001"


def test_payload_tampering_is_rejected(keypair, now):
    private, public = keypair
    token = sign_license(_claims(now), private, "k1")
    tampered = _tamper_payload(
        token,
        expires_at=(now + timedelta(days=3650)).isoformat(),
    )

    with pytest.raises(LicenseSecurityError, match="signature"):
        verify_license(tampered, {"k1": public}, now=now + timedelta(seconds=1))


def test_wrong_cabinet_is_rejected(keypair, now):
    private, public = keypair
    token = sign_license(_claims(now), private, "k1")

    with pytest.raises(LicenseSecurityError, match="cabinet"):
        verify_license(
            token,
            {"k1": public},
            expected_cabinet_id="other-cabinet",
            now=now + timedelta(seconds=1),
        )


def test_expired_license_is_rejected(keypair, now):
    private, public = keypair
    token = sign_license(
        _claims(now, expires_at=(now + timedelta(minutes=1)).isoformat()),
        private,
        "k1",
    )

    with pytest.raises(LicenseSecurityError, match="expired"):
        verify_license(token, {"k1": public}, now=now + timedelta(minutes=2))


def test_revoked_license_is_rejected(keypair, now):
    private, public = keypair
    token = sign_license(_claims(now, status="REVOKED"), private, "k1")

    with pytest.raises(LicenseSecurityError, match="not active"):
        verify_license(token, {"k1": public}, now=now + timedelta(seconds=1))


def test_untrusted_key_id_is_rejected(keypair, now):
    private, _public = keypair
    token = sign_license(_claims(now), private, "unknown")

    with pytest.raises(LicenseSecurityError, match="untrusted"):
        verify_license(token, {}, now=now + timedelta(seconds=1))


def test_owner_requires_matching_immutable_subject(keypair, now):
    private, public = keypair
    token = sign_license(
        _claims(
            now,
            license_type="OWNER",
            expires_at=None,
            max_devices=None,
            subject_user_id=42,
        ),
        private,
        "k1",
    )

    verified = verify_license(
        token,
        {"k1": public},
        expected_owner_user_id=42,
        now=now + timedelta(seconds=1),
    )
    assert verified.subject_user_id == 42

    with pytest.raises(LicenseSecurityError, match="subject"):
        verify_license(
            token,
            {"k1": public},
            expected_owner_user_id=43,
            now=now + timedelta(seconds=1),
        )


def test_issuer_fails_closed_without_private_key(monkeypatch):
    monkeypatch.delenv("DIGITALCROWN_LICENSE_SIGNING_PRIVATE_KEY_B64URL", raising=False)
    monkeypatch.delenv("DIGITALCROWN_LICENSE_SIGNING_KEY_ID", raising=False)

    with pytest.raises(LicenseIssuerUnavailable):
        issue_license(
            cabinet_id="cab-001",
            license_type="TRIAL",
            created_by_user_id=7,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )


def test_issuer_uses_control_plane_key_only(monkeypatch, keypair, now):
    private, public = keypair
    monkeypatch.setenv("DIGITALCROWN_LICENSE_SIGNING_PRIVATE_KEY_B64URL", private)
    monkeypatch.setenv("DIGITALCROWN_LICENSE_SIGNING_KEY_ID", "k1")

    token = issue_license(
        cabinet_id="cab-001",
        license_type="TRIAL",
        created_by_user_id=7,
        expires_at=now + timedelta(days=30),
        issued_at=now,
        not_before=now,
    )

    verified = verify_license(
        token,
        {"k1": public},
        expected_cabinet_id="cab-001",
        now=now + timedelta(seconds=1),
    )
    assert verified.license_type == "TRIAL"
