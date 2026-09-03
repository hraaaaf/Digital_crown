from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from backend.routers import superadmin_license_controls as controls


class _DeviceQuery:
    def __init__(self, devices):
        self._devices = devices

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def all(self):
        return self._devices


class _Db:
    def __init__(self, devices):
        self._devices = devices

    def query(self, model):
        return _DeviceQuery(self._devices)


@pytest.mark.asyncio
async def test_devices_projection_exposes_signed_release_channel(monkeypatch):
    devices = [
        SimpleNamespace(
            device_id="device-1",
            user_id=42,
            created_at=None,
            last_seen_at=None,
            revoked_at=None,
        )
    ]
    db = _Db(devices)
    cabinet = SimpleNamespace(clinic_id="clinic-42", public_id="cabinet-42")

    monkeypatch.setattr(controls, "_client", lambda _db, _user_id: SimpleNamespace(id=42))
    monkeypatch.setattr(controls, "_cabinet", lambda _db, _user_id: cabinet)

    effective = AsyncMock(return_value={
        "active": True,
        "license_type": "PAID",
        "max_devices": 3,
        "release_channel": "beta",
    })
    monkeypatch.setattr(
        controls,
        "LicenseService",
        lambda: SimpleNamespace(get_effective_license=effective),
    )

    payload = await controls.list_client_devices(
        42,
        db=db,
        actor=SimpleNamespace(id=1),
    )

    assert payload["license"] == {
        "active": True,
        "license_type": "PAID",
        "max_devices": 3,
        "active_devices": 1,
        "release_channel": "beta",
    }
    assert payload["devices"][0]["device_id"] == "device-1"
    effective.assert_awaited_once_with("clinic-42")
