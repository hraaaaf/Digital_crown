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
