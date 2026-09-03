"""Superadmin reissues preserve unrelated signed entitlement claims."""
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
import uuid

import pytest

from backend import models


@pytest.fixture
def platform_actor(db, dentiste):
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


def _client_with_cabinet(db, *, plan="GOLD"):
    user = models.User(
        email=f"license-client-{uuid.uuid4().hex[:10]}@cabinet.ma",
        hashed_password="unused-test-hash",
        role=models.UserRole.DENTISTE,
        nom_complet="License Client",
        is_active=True,
        is_licensed=True,
        license_expires_at=datetime.utcnow() + timedelta(days=60),
        subscription_plan=plan,
    )
    db.add(user)
    db.flush()
    db.add(
        models.CabinetConfig(
            owner_id=user.id,
            public_id=f"lic{user.id:013d}"[-16:],
            clinic_id=f"clinic-license-{user.id}",
            nom_cabinet="License Test",
            nom_praticien="Dr License",
        )
    )
    db.commit()
    db.refresh(user)
    return user


def _effective(*, max_devices=4, release_channel="beta", feature_set="ELITE"):
    return {
        "active": True,
        "license_type": "PAID",
        "expiration_date": datetime.utcnow() + timedelta(days=60),
        "max_devices": max_devices,
        "release_channel": release_channel,
        "feature_set": feature_set,
    }


def test_paid_extension_preserves_capacity_channel_and_feature_set(
    client, db, platform_actor
):
    platform_actor.permissions = {"license.extend": True}
    target = _client_with_cabinet(db, plan="GOLD")
    db.commit()

    issue = AsyncMock(return_value="signed")
    with patch(
        "backend.routers.superadmin.LicenseService.get_effective_license",
        new=AsyncMock(return_value=_effective()),
    ), patch("backend.routers.superadmin._issue_and_store_signed_license", new=issue):
        response = client.post(
            f"/api/superadmin/clients/{target.id}/grant-license?action=1m",
            headers=_headers(client, platform_actor),
        )

    assert response.status_code == 200, response.text
    kwargs = issue.await_args.kwargs
    assert kwargs["max_devices"] == 4
    assert kwargs["release_channel"] == "beta"
    assert kwargs["feature_set"] == "ELITE"


def test_release_channel_changes_only_channel_and_preserves_signed_claims(
    client, db, platform_actor
):
    platform_actor.permissions = {"license.change_release_channel": True}
    target = _client_with_cabinet(db, plan="GOLD")
    db.commit()

    issue = AsyncMock(return_value="signed")
    with patch(
        "backend.routers.superadmin.LicenseService.get_effective_license",
        new=AsyncMock(return_value=_effective(max_devices=6, release_channel="stable", feature_set="PREMIUM")),
    ), patch("backend.routers.superadmin._issue_and_store_signed_license", new=issue):
        response = client.patch(
            f"/api/superadmin/clients/{target.id}/release-channel?channel=beta",
            headers=_headers(client, platform_actor),
        )

    assert response.status_code == 200, response.text
    assert response.json() == {"status": "success", "release_channel": "beta", "changed": True}
    kwargs = issue.await_args.kwargs
    assert kwargs["license_type"] == "PAID"
    assert kwargs["max_devices"] == 6
    assert kwargs["feature_set"] == "PREMIUM"
    assert kwargs["release_channel"] == "beta"
    audit = db.query(models.AuditLog).filter(
        models.AuditLog.action == "SUPERADMIN_RELEASE_CHANNEL_CHANGE",
        models.AuditLog.resource_id == str(target.id),
    ).one()
    assert audit.user_id == platform_actor.id
    assert audit.details == "from=stable;to=beta"


def test_release_channel_requires_dedicated_permission(client, db, platform_actor):
    platform_actor.permissions = {"license.read": True}
    target = _client_with_cabinet(db)
    db.commit()
    response = client.patch(
        f"/api/superadmin/clients/{target.id}/release-channel?channel=beta",
        headers=_headers(client, platform_actor),
    )
    assert response.status_code == 403


def test_plan_reissue_preserves_capacity_and_release_channel(client, db, dentiste):
    target = _client_with_cabinet(db, plan="GOLD")
    issue = AsyncMock(return_value="signed")
    with patch("backend.platform_access.settings.PLATFORM_CONTROL_PLANE_ENABLED", True), patch(
        "backend.platform_access.settings.SUPERADMIN_USER_ID", dentiste.id
    ), patch(
        "backend.routers.superadmin.LicenseService.get_effective_license",
        new=AsyncMock(return_value=_effective(max_devices=5, release_channel="beta", feature_set="GOLD")),
    ), patch("backend.routers.superadmin._issue_and_store_signed_license", new=issue):
        response = client.patch(
            f"/api/superadmin/clients/{target.id}/plan?plan=PREMIUM",
            headers=_headers(client, dentiste),
        )

    assert response.status_code == 200, response.text
    kwargs = issue.await_args.kwargs
    assert kwargs["max_devices"] == 5
    assert kwargs["release_channel"] == "beta"
    assert kwargs["feature_set"] == "PREMIUM"
