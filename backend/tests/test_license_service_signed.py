import base64
from datetime import datetime, timedelta, timezone

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)

from backend.config import settings
from backend.license_security import LicenseSecurityError, sign_license
from backend.services import license_service as license_service_module
from backend.services.license_service import LicenseService


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
        "license_id": "lic-service-001",
        "cabinet_id": "cab-001",
        "license_type": "PAID",
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


def _trust(monkeypatch, public_key: str) -> None:
    monkeypatch.setattr(
        license_service_module,
        "TRUSTED_LICENSE_PUBLIC_KEYS",
        {"k1": public_key},
    )


def _prepare_local_vault(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DIGITALCROWN_USER_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("CABINET_MASTER_KEY_HEX", "ab" * 32)


def test_owner_service_verification_requires_configured_subject(monkeypatch, keypair, now):
    private, public = keypair
    _trust(monkeypatch, public)
    monkeypatch.setattr(settings, "SUPERADMIN_USER_ID", 42)

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

    verified = LicenseService._verify_signed_license(
        token,
        "cab-001",
        now + timedelta(seconds=1),
    )

    assert verified.license_type == "OWNER"
    assert verified.subject_user_id == 42


def test_owner_service_rejects_wrong_or_unprovisioned_subject(monkeypatch, keypair, now):
    private, public = keypair
    _trust(monkeypatch, public)
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

    monkeypatch.setattr(settings, "SUPERADMIN_USER_ID", 43)
    with pytest.raises(LicenseSecurityError, match="OWNER subject mismatch"):
        LicenseService._verify_signed_license(
            token,
            "cab-001",
            now + timedelta(seconds=1),
        )

    monkeypatch.setattr(settings, "SUPERADMIN_USER_ID", 0)
    with pytest.raises(LicenseSecurityError, match="provisioned"):
        LicenseService._verify_signed_license(
            token,
            "cab-001",
            now + timedelta(seconds=1),
        )


def test_revoked_token_can_be_authenticated_for_storage_but_not_activation(monkeypatch, keypair, now):
    private, public = keypair
    _trust(monkeypatch, public)
    token = sign_license(
        _claims(now, status="REVOKED"),
        private,
        "k1",
    )

    with pytest.raises(LicenseSecurityError, match="not active"):
        LicenseService._verify_signed_license(
            token,
            "cab-001",
            now + timedelta(seconds=1),
        )

    verified = LicenseService._verify_signed_license(
        token,
        "cab-001",
        now + timedelta(seconds=1),
        allow_inactive=True,
    )

    assert verified.status == "REVOKED"


def test_install_signed_license_verifies_then_persists_and_reads_back(monkeypatch, tmp_path, keypair):
    private, public = keypair
    _trust(monkeypatch, public)
    _prepare_local_vault(monkeypatch, tmp_path)
    current = datetime.now(timezone.utc)
    token = sign_license(
        _claims(
            current - timedelta(seconds=1),
            cabinet_id="cab-install",
            license_type="TRIAL",
            feature_set="GOLD",
            expires_at=(current + timedelta(days=30)).isoformat(),
        ),
        private,
        "k1",
    )

    service = LicenseService()
    installed = service.install_signed_license("cab-install", token)

    assert installed["active"] is True
    assert installed["source"] == "activation"
    assert installed["license_type"] == "TRIAL"
    assert installed["feature_set"] == "GOLD"
    vault = service._read_local_vault()
    assert vault["clinic_id"] == "cab-install"
    assert vault["signed_license"] == token


def test_install_signed_license_rejects_wrong_cabinet_without_local_activation(monkeypatch, tmp_path, keypair):
    private, public = keypair
    _trust(monkeypatch, public)
    _prepare_local_vault(monkeypatch, tmp_path)
    current = datetime.now(timezone.utc)
    token = sign_license(
        _claims(
            current - timedelta(seconds=1),
            cabinet_id="other-cabinet",
            license_type="TRIAL",
            feature_set="GOLD",
            expires_at=(current + timedelta(days=30)).isoformat(),
        ),
        private,
        "k1",
    )

    service = LicenseService()
    with pytest.raises(LicenseSecurityError, match="cabinet"):
        service.install_signed_license("cab-install", token)

    assert service._read_local_vault() == {}


def test_install_signed_license_fails_closed_when_vault_write_fails(monkeypatch, keypair):
    private, public = keypair
    _trust(monkeypatch, public)
    current = datetime.now(timezone.utc)
    token = sign_license(
        _claims(
            current - timedelta(seconds=1),
            cabinet_id="cab-install",
            license_type="TRIAL",
            feature_set="GOLD",
            expires_at=(current + timedelta(days=30)).isoformat(),
        ),
        private,
        "k1",
    )

    service = LicenseService()
    monkeypatch.setattr(service, "_write_local_vault", lambda _data: False)
    with pytest.raises(RuntimeError, match="persisted"):
        service.install_signed_license("cab-install", token)
