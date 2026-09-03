import base64
import datetime
import os

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)

from backend.core.paths import AppPaths
from backend.license_security import sign_license
from backend.services import license_service as license_service_module
from backend.services.license_service import LicenseService


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


@pytest.fixture(autouse=True)
def cleanup_vault():
    vault_path = AppPaths.get_user_data_dir() / "license_vault.bin"
    if vault_path.exists():
        try:
            os.remove(vault_path)
        except Exception:
            pass
    yield
    if vault_path.exists():
        try:
            os.remove(vault_path)
        except Exception:
            pass


@pytest.mark.asyncio
async def test_offline_no_vault_fails():
    service = LicenseService()
    service._db = None
    
    result = await service.validate_license("test_clinic")
    assert result is False


@pytest.mark.asyncio
async def test_online_validation_saves_local_vault(monkeypatch, tmp_path):
    monkeypatch.setenv("DIGITALCROWN_USER_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("CABINET_MASTER_KEY_HEX", "ab" * 32)

    private_key = Ed25519PrivateKey.generate()
    private_raw = private_key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
    public_raw = private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    private_b64url = _b64url(private_raw)
    public_b64url = _b64url(public_raw)
    monkeypatch.setattr(
        license_service_module,
        "TRUSTED_LICENSE_PUBLIC_KEYS",
        {"k1": public_b64url},
    )

    now = datetime.datetime.now(datetime.timezone.utc)
    token = sign_license(
        {
            "schema_version": 1,
            "issuer": "digital-crown",
            "audience": "digital-crown-desktop",
            "license_id": "lic-online-cache-001",
            "cabinet_id": "test_clinic",
            "license_type": "PAID",
            "status": "ACTIVE",
            "issued_at": (now - datetime.timedelta(seconds=1)).isoformat(),
            "not_before": (now - datetime.timedelta(seconds=1)).isoformat(),
            "expires_at": (now + datetime.timedelta(days=30)).isoformat(),
            "release_channel": "stable",
            "feature_set": ["catalog"],
            "max_devices": 1,
            "policy_version": "1",
            "created_by_user_id": 7,
        },
        private_b64url,
        "k1",
    )

    class _Doc:
        exists = True

        @staticmethod
        def to_dict():
            return {"signed_license": token}

    class _DocRef:
        @staticmethod
        def get():
            return _Doc()

    class _Collection:
        @staticmethod
        def document(_id):
            return _DocRef()

    class _Db:
        @staticmethod
        def collection(_name):
            return _Collection()

    service = LicenseService()
    service._db = _Db()

    result = await service.validate_license("test_clinic")

    assert result is True
    vault = service._read_local_vault()
    assert vault["clinic_id"] == "test_clinic"
    assert vault["signed_license"] == token


@pytest.mark.asyncio
async def test_offline_clock_rollback_detected():
    service = LicenseService()
    service._db = None
    
    now = datetime.datetime.now(datetime.timezone.utc)
    future_time = now + datetime.timedelta(hours=2)
    
    local_data = {
        "clinic_id": "test_clinic",
        "last_validated": future_time.isoformat(),
        "expiration_date": (future_time + datetime.timedelta(days=30)).isoformat(),
        "max_seen_time": future_time.isoformat()
    }
    service._write_local_vault(local_data)
    
    result = await service.validate_license("test_clinic")
    assert result is False


@pytest.mark.asyncio
async def test_offline_grace_period_expired():
    service = LicenseService()
    service._db = None
    
    now = datetime.datetime.now(datetime.timezone.utc)
    past_time = now - datetime.timedelta(hours=74)
    
    local_data = {
        "clinic_id": "test_clinic",
        "last_validated": past_time.isoformat(),
        "expiration_date": (now + datetime.timedelta(days=30)).isoformat(),
        "max_seen_time": past_time.isoformat()
    }
    service._write_local_vault(local_data)
    
    result = await service.validate_license("test_clinic")
    assert result is False


# ── CABINET-ONPREM-DEPLOYMENT-1 : sync licence non-destructif hors-ligne ─────

@pytest.mark.asyncio
async def test_with_expiry_unreachable_returns_none_not_false():
    """Firebase non configuré/injoignable → active=None (pas False).

    Le sync au démarrage (main.py::_sync_all_licenses_from_firebase) doit
    pouvoir distinguer "pas de réponse" (conserver l'état local) de
    "licence révoquée" (fail-closed). Avant ce fix, chaque redémarrage
    hors-ligne écrasait is_licensed=False pour tous les cabinets.
    """
    service = LicenseService()
    service._db = None

    result = await service.validate_license_with_expiry("test_clinic")
    assert result["active"] is None


@pytest.mark.asyncio
async def test_with_expiry_firebase_exception_returns_none():
    """Une exception de lecture Firebase → active=None (pas de réponse obtenue)."""

    class _BrokenDb:
        def collection(self, *_a, **_k):
            raise ConnectionError("network down")

    service = LicenseService()
    service._db = _BrokenDb()

    result = await service.validate_license_with_expiry("test_clinic")
    assert result["active"] is None


@pytest.mark.asyncio
async def test_with_expiry_explicit_inactive_stays_false():
    """Firebase répond ET dit inactive → active=False (fail-closed conservé)."""

    class _Doc:
        exists = True

        @staticmethod
        def to_dict():
            return {"active": False, "expiration_date": None}

    class _DocRef:
        @staticmethod
        def get():
            return _Doc()

    class _Collection:
        @staticmethod
        def document(_id):
            return _DocRef()

    class _Db:
        @staticmethod
        def collection(_name):
            return _Collection()

    service = LicenseService()
    service._db = _Db()

    result = await service.validate_license_with_expiry("test_clinic")
    assert result["active"] is False
