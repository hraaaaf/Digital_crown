"""Granular platform RBAC tests for delegated Superadmin surfaces."""
from unittest.mock import patch

import pytest

from backend import models
from backend.routers.superadmin import _paid_license_permission


@pytest.fixture
def delegated_platform_user(db, dentiste):
    dentiste.permissions = {}
    db.commit()
    db.refresh(dentiste)
    with patch("backend.platform_access.settings.PLATFORM_CONTROL_PLANE_ENABLED", True), patch(
        "backend.platform_access.settings.SUPERADMIN_USER_ID", dentiste.id + 999999
    ):
        yield dentiste


def _web_headers(client, user) -> dict[str, str]:
    login = client.post(
        "/api/auth/login",
        data={"username": user.email, "password": "TestPass123!"},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _set_permissions(db, user, permissions: dict[str, bool]) -> None:
    user.permissions = permissions
    db.add(user)
    db.commit()
    db.refresh(user)


def test_license_read_permission_allows_delegated_client_listing(
    client, db, delegated_platform_user
):
    _set_permissions(db, delegated_platform_user, {"license.read": True})
    response = client.get(
        "/api/superadmin/clients",
        headers=_web_headers(client, delegated_platform_user),
    )
    assert response.status_code == 200, response.text


def test_client_listing_denies_delegated_user_without_license_read(
    client, db, delegated_platform_user
):
    _set_permissions(db, delegated_platform_user, {"audit.read": True})
    response = client.get(
        "/api/superadmin/clients",
        headers=_web_headers(client, delegated_platform_user),
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Accès refusé. Permission plateforme insuffisante."


def test_license_history_uses_license_read_permission(
    client, db, delegated_platform_user
):
    _set_permissions(db, delegated_platform_user, {"license.read": True})
    db.add(
        models.LicenseHistory(
            user_id=delegated_platform_user.id,
            admin_id=delegated_platform_user.id,
            action="TEST_HISTORY",
            duration=30,
        )
    )
    db.commit()

    response = client.get(
        f"/api/superadmin/clients/{delegated_platform_user.id}/license-history",
        headers=_web_headers(client, delegated_platform_user),
    )
    assert response.status_code == 200, response.text
    assert response.json()[0]["action"] == "TEST_HISTORY"


def test_audit_read_returns_only_platform_audit_events(
    client, db, delegated_platform_user
):
    _set_permissions(db, delegated_platform_user, {"audit.read": True})
    db.add_all(
        [
            models.AuditLog(
                user_id=delegated_platform_user.id,
                employer_id=None,
                action="SUPERADMIN_TEST_EVENT",
                resource_type="User",
                resource_id=str(delegated_platform_user.id),
                severity="WARNING",
                details="safe=true",
            ),
            models.AuditLog(
                user_id=delegated_platform_user.id,
                employer_id=delegated_platform_user.id,
                action="PATIENT_UPDATE",
                resource_type="Patient",
                resource_id="123",
                severity="INFO",
                details="clinical=true",
            ),
        ]
    )
    db.commit()

    response = client.get(
        "/api/superadmin/audit?limit=10",
        headers=_web_headers(client, delegated_platform_user),
    )
    assert response.status_code == 200, response.text
    actions = [row["action"] for row in response.json()]
    assert "SUPERADMIN_TEST_EVENT" in actions
    assert "PATIENT_UPDATE" not in actions


def test_audit_read_denies_user_without_permission(
    client, db, delegated_platform_user
):
    _set_permissions(db, delegated_platform_user, {"license.read": True})
    response = client.get(
        "/api/superadmin/audit",
        headers=_web_headers(client, delegated_platform_user),
    )
    assert response.status_code == 403


def test_paid_permission_uses_signed_entitlement_state():
    assert _paid_license_permission({"active": False}) == "license.create_paid"
    assert _paid_license_permission({"active": True, "license_type": "TRIAL"}) == "license.create_paid"
    assert _paid_license_permission({"active": True, "license_type": "PAID"}) == "license.extend"


def test_revoke_requires_revoke_permission_before_target_lookup(
    client, db, delegated_platform_user
):
    _set_permissions(db, delegated_platform_user, {"license.extend": True})
    response = client.post(
        "/api/superadmin/clients/999999/grant-license?action=revoke",
        headers=_web_headers(client, delegated_platform_user),
    )
    assert response.status_code == 403


def test_paid_grant_requires_create_or_extend_permission_before_target_lookup(
    client, db, delegated_platform_user
):
    _set_permissions(db, delegated_platform_user, {"audit.read": True})
    response = client.post(
        "/api/superadmin/clients/999999/grant-license?action=1m",
        headers=_web_headers(client, delegated_platform_user),
    )
    assert response.status_code == 403
