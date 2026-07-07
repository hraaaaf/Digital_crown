import os
import pytest
import datetime
from backend.services.license_service import LicenseService
from backend.core.paths import AppPaths


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
async def test_online_validation_saves_local_vault():
    service = LicenseService()
    service._db = None
    
    now = datetime.datetime.now(datetime.timezone.utc)
    expiration = now + datetime.timedelta(days=30)
    
    local_data = {
        "clinic_id": "test_clinic",
        "last_validated": now.isoformat(),
        "expiration_date": expiration.isoformat(),
        "max_seen_time": now.isoformat()
    }
    service._write_local_vault(local_data)
    
    result = await service.validate_license("test_clinic")
    assert result is True


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
