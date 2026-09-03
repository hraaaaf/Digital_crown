from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from backend.routers import superadmin_passkey


def test_platform_actor_allows_immutable_owner(monkeypatch):
    actor = SimpleNamespace(id=1)
    monkeypatch.setattr(superadmin_passkey, "is_platform_superadmin", lambda user: user is actor)
    monkeypatch.setattr(superadmin_passkey, "has_platform_permission", lambda *_args: False)

    assert superadmin_passkey._platform_actor(actor) is actor


def test_platform_actor_allows_explicit_delegated_permission(monkeypatch):
    actor = SimpleNamespace(id=2)
    monkeypatch.setattr(superadmin_passkey, "is_platform_superadmin", lambda _user: False)
    monkeypatch.setattr(
        superadmin_passkey,
        "has_platform_permission",
        lambda user, permission: user is actor and permission == "audit.read",
    )

    assert superadmin_passkey._platform_actor(actor) is actor


def test_platform_actor_denies_user_without_platform_authority(monkeypatch):
    actor = SimpleNamespace(id=3)
    monkeypatch.setattr(superadmin_passkey, "is_platform_superadmin", lambda _user: False)
    monkeypatch.setattr(superadmin_passkey, "has_platform_permission", lambda *_args: False)

    with pytest.raises(HTTPException) as error:
        superadmin_passkey._platform_actor(actor)

    assert error.value.status_code == 403
