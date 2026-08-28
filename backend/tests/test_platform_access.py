from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from backend.config import Settings, settings
from backend.platform_access import has_platform_permission, is_platform_superadmin


def _user(
    *,
    user_id: int,
    email: str = "someone@example.com",
    permissions=None,
    active: bool = True,
):
    return SimpleNamespace(
        id=user_id,
        email=email,
        is_active=active,
        is_archived=False,
        is_suspended=False,
        permissions=permissions or {},
    )


def _enable_control_plane(monkeypatch, *, owner_id: int = 42):
    monkeypatch.setattr(settings, "PLATFORM_CONTROL_PLANE_ENABLED", True)
    monkeypatch.setattr(settings, "SUPERADMIN_USER_ID", owner_id)


def test_cabinet_environment_rejects_platform_control_plane():
    with pytest.raises(ValidationError, match="interdit en environnement cabinet"):
        Settings(
            ENVIRONMENT="cabinet",
            PLATFORM_CONTROL_PLANE_ENABLED=True,
        )


def test_cabinet_install_fails_closed_even_when_local_user_id_matches(monkeypatch):
    monkeypatch.setattr(settings, "PLATFORM_CONTROL_PLANE_ENABLED", False)
    monkeypatch.setattr(settings, "SUPERADMIN_USER_ID", 42)
    forged_local_owner = _user(
        user_id=42,
        permissions={"license.create_trial": True},
    )

    assert is_platform_superadmin(forged_local_owner) is False
    assert has_platform_permission(forged_local_owner, "license.create_trial") is False


def test_superadmin_authority_uses_immutable_user_id_not_email(monkeypatch):
    _enable_control_plane(monkeypatch)

    owner = _user(user_id=42, email="renamed@example.com")
    imposter = _user(user_id=99, email=settings.SUPERADMIN_DISPLAY_EMAIL)

    assert is_platform_superadmin(owner) is True
    assert is_platform_superadmin(imposter) is False


def test_legacy_superadmin_email_setting_cannot_reenable_authority():
    cfg = Settings(SUPERADMIN_EMAIL="attacker@example.com")

    assert cfg.SUPERADMIN_EMAIL == ""


def test_unprovisioned_superadmin_fails_closed(monkeypatch):
    _enable_control_plane(monkeypatch, owner_id=0)

    candidate = _user(user_id=42, email=settings.SUPERADMIN_DISPLAY_EMAIL)

    assert is_platform_superadmin(candidate) is False


def test_disabled_owner_is_not_superadmin(monkeypatch):
    _enable_control_plane(monkeypatch)

    assert is_platform_superadmin(_user(user_id=42, active=False)) is False


def test_sales_admin_needs_explicit_trial_permission(monkeypatch):
    _enable_control_plane(monkeypatch)

    sales = _user(user_id=7, permissions={"license.create_trial": True})
    generic_admin = _user(user_id=8, permissions={})

    assert has_platform_permission(sales, "license.create_trial") is True
    assert has_platform_permission(sales, "license.create_paid") is False
    assert has_platform_permission(generic_admin, "license.create_trial") is False


def test_superadmin_inherits_all_known_platform_permissions(monkeypatch):
    _enable_control_plane(monkeypatch)
    owner = _user(user_id=42)

    assert has_platform_permission(owner, "license.create_trial") is True
    assert has_platform_permission(owner, "license.revoke") is True


def test_unknown_permission_fails_closed(monkeypatch):
    _enable_control_plane(monkeypatch)
    owner = _user(user_id=42)

    assert has_platform_permission(owner, "platform.root.everything") is False
