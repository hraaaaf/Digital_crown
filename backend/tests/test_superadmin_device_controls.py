"""Superadmin device-management RBAC and revocation tests."""
from unittest.mock import AsyncMock, patch
import uuid

import pytest

from backend import models


@pytest.fixture
def delegated_operator(db, dentiste):
    dentiste.permissions = {"license.manage_devices": True}
    db.add(
        models.CabinetConfig(
            owner_id=dentiste.id,
            public_id=f"dev{dentiste.id:013d}"[-16:],
            clinic_id=f"clinic-dev-{dentiste.id}",
            nom_cabinet="Device Test",
            nom_praticien="Dr Device",
        )
    )
    db.commit()
    db.refresh(dentiste)
    with patch("backend.platform_access.settings.PLATFORM_CONTROL_PLANE_ENABLED", True), patch(
        "backend.platform_access.settings.SUPERADMIN_USER_ID", dentiste.id + 999999
    ):
        yield dentiste


def _headers(client, user):
    response = client.post(
        "/api/auth/login",
        data={"username": user.email, "password": "TestPass123!"},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _device(db, user, *, revoked=False):
    device = models.MobilePairedDevice(
        device_id=str(uuid.uuid4()),
        user_id=user.id,
        employer_id=user.id,
        client_public_key_hex="04" + "00" * 64,
        refresh_jti=f"mobile:{user.id}:1:{uuid.uuid4().hex}",
        revoked_at=models.datetime.utcnow() if revoked else None,
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


def test_manage_devices_lists_only_safe_metadata(client, db, delegated_operator):
    device = models.MobilePairedDevice(
        device_id=str(uuid.uuid4()),
        user_id=delegated_operator.id,
        employer_id=delegated_operator.id,
        client_public_key_hex="04" + "11" * 64,
        refresh_jti=f"mobile:{delegated_operator.id}:1:{uuid.uuid4().hex}",
    )
    db.add(device)
    db.commit()

    with patch(
        "backend.routers.superadmin_license_controls.LicenseService.get_effective_license",
        new=AsyncMock(
            return_value={
                "active": True,
                "license_type": "PAID",
                "max_devices": 2,
            }
        ),
    ):
        response = client.get(
            f"/api/superadmin/platform-admins/clients/{delegated_operator.id}/devices",
            headers=_headers(client, delegated_operator),
        )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["license"]["max_devices"] == 2
    assert body["license"]["active_devices"] == 1
    serialized = body["devices"][0]
    assert serialized["device_id"] == device.device_id
    assert "client_public_key_hex" not in serialized
    assert "refresh_jti" not in serialized


def test_manage_devices_revoke_is_effective_and_audited(client, db, delegated_operator):
    device = models.MobilePairedDevice(
        device_id=str(uuid.uuid4()),
        user_id=delegated_operator.id,
        employer_id=delegated_operator.id,
        client_public_key_hex="04" + "22" * 64,
        refresh_jti=f"mobile:{delegated_operator.id}:1:{uuid.uuid4().hex}",
    )
    db.add(device)
    db.commit()

    response = client.post(
        f"/api/superadmin/platform-admins/clients/{delegated_operator.id}/devices/{device.device_id}/revoke",
        headers=_headers(client, delegated_operator),
    )
    assert response.status_code == 200, response.text
    assert response.json()["device"]["active"] is False

    db.refresh(device)
    assert device.revoked_at is not None
    audit = db.query(models.AuditLog).filter(
        models.AuditLog.action == "SUPERADMIN_DEVICE_REVOKE",
        models.AuditLog.resource_id == str(delegated_operator.id),
    ).one()
    assert audit.user_id == delegated_operator.id
    assert audit.severity == "CRITICAL"
    assert device.device_id in (audit.details or "")


def test_manage_devices_permission_is_required(client, db, delegated_operator):
    delegated_operator.permissions = {"license.read": True}
    db.commit()
    response = client.get(
        f"/api/superadmin/platform-admins/clients/{delegated_operator.id}/devices",
        headers=_headers(client, delegated_operator),
    )
    assert response.status_code == 403
