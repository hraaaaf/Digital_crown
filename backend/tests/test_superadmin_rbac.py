"""Granular platform RBAC tests for delegated Superadmin surfaces."""
from unittest.mock import patch
import uuid

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


def _platform_only_user(db, *, employer_id=None, permissions=None):
    user = models.User(
        email=f"platform-{uuid.uuid4().hex[:10]}@digitalcrown.local",
        hashed_password="unused-test-hash",
        role=models.UserRole.ADMIN,
        nom_complet="Platform Operator Test",
        is_active=True,
        is_licensed=False,
        employer_id=employer_id,
        permissions=permissions or {},
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


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


def test_suspend_permission_allows_delegated_suspension(
    client, db, delegated_platform_user
):
    _set_permissions(db, delegated_platform_user, {"license.suspend": True})
    response = client.patch(
        f"/api/superadmin/clients/{delegated_platform_user.id}/suspend",
        headers=_web_headers(client, delegated_platform_user),
    )
    assert response.status_code == 200, response.text
    assert response.json()["is_suspended"] is True
    db.refresh(delegated_platform_user)
    assert delegated_platform_user.is_suspended is True


def test_suspend_denies_delegated_user_without_permission(
    client, db, delegated_platform_user
):
    _set_permissions(db, delegated_platform_user, {"license.read": True})
    response = client.patch(
        f"/api/superadmin/clients/{delegated_platform_user.id}/suspend",
        headers=_web_headers(client, delegated_platform_user),
    )
    assert response.status_code == 403
    db.refresh(delegated_platform_user)
    assert delegated_platform_user.is_suspended is False


def test_admin_create_promotes_only_existing_platform_only_account(
    client, db, delegated_platform_user
):
    _set_permissions(
        db,
        delegated_platform_user,
        {"admin.create": True, "admin.read": True, "license.read": True},
    )
    target = _platform_only_user(db)
    response = client.post(
        f"/api/superadmin/platform-admins/{target.id}",
        json={"permissions": {"admin.read": True, "license.read": True}},
        headers=_web_headers(client, delegated_platform_user),
    )
    assert response.status_code == 200, response.text
    assert response.json()["permissions"] == {"admin.read": True, "license.read": True}


def test_admin_create_rejects_cabinet_attached_account(
    client, db, delegated_platform_user
):
    _set_permissions(db, delegated_platform_user, {"admin.create": True, "admin.read": True})
    target = _platform_only_user(db, employer_id=delegated_platform_user.id)
    response = client.post(
        f"/api/superadmin/platform-admins/{target.id}",
        json={"permissions": {"admin.read": True}},
        headers=_web_headers(client, delegated_platform_user),
    )
    assert response.status_code == 409


def test_admin_update_permissions_blocks_privilege_escalation(
    client, db, delegated_platform_user
):
    _set_permissions(
        db,
        delegated_platform_user,
        {"admin.update_permissions": True, "license.read": True},
    )
    target = _platform_only_user(db, permissions={"license.read": True})
    response = client.patch(
        f"/api/superadmin/platform-admins/{target.id}/permissions",
        json={"permissions": {"license.read": True, "license.revoke": True}},
        headers=_web_headers(client, delegated_platform_user),
    )
    assert response.status_code == 403
    db.refresh(target)
    assert target.permissions == {"license.read": True}


def test_admin_update_cannot_modify_immutable_owner(
    client, db, delegated_platform_user
):
    _set_permissions(
        db,
        delegated_platform_user,
        {"admin.update_permissions": True, "license.read": True},
    )
    owner = _platform_only_user(db, permissions={"license.read": True})
    with patch("backend.routers.superadmin_admins.settings.SUPERADMIN_USER_ID", owner.id):
        response = client.patch(
            f"/api/superadmin/platform-admins/{owner.id}/permissions",
            json={"permissions": {"license.read": True}},
            headers=_web_headers(client, delegated_platform_user),
        )
    assert response.status_code == 403


def test_admin_read_lists_platform_operators_only(
    client, db, delegated_platform_user
):
    _set_permissions(db, delegated_platform_user, {"admin.read": True})
    operator = _platform_only_user(db, permissions={"license.read": True})
    ordinary = _platform_only_user(db)
    response = client.get(
        "/api/superadmin/platform-admins",
        headers=_web_headers(client, delegated_platform_user),
    )
    assert response.status_code == 200, response.text
    ids = {row["id"] for row in response.json()}
    assert operator.id in ids
    assert ordinary.id not in ids
