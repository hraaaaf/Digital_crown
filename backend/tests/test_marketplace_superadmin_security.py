"""P10 — preuves web-only et CSRF du control-plane Marketplace."""

import uuid

from backend import models
from backend.config import settings
from backend.routers.mobile import _create_mobile_jwt
from backend.security import get_password_hash


def _superadmin(db, monkeypatch):
    email = "p10-control-plane@test.ma"
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        user = models.User(
            email=email,
            hashed_password=get_password_hash("TestPass123!"),
            role=models.UserRole.DENTISTE,
            nom_complet="P10 Control Plane",
            is_active=True,
            is_licensed=True,
        )
        db.add(user)
    else:
        user.hashed_password = get_password_hash("TestPass123!")
        user.is_active = True
        user.is_licensed = True
        user.employer_id = None
    db.commit()
    db.refresh(user)
    monkeypatch.setattr(settings, "PLATFORM_CONTROL_PLANE_ENABLED", True)
    monkeypatch.setattr(settings, "SUPERADMIN_USER_ID", user.id)
    return user


def test_mobile_superadmin_session_is_rejected_from_marketplace_control_plane(client, db, monkeypatch):
    admin = _superadmin(db, monkeypatch)
    device_id = str(uuid.uuid4())
    device = models.MobilePairedDevice(
        device_id=device_id,
        user_id=admin.id,
        employer_id=admin.id,
        client_public_key_hex="04" + ("00" * 64),
        refresh_jti="p10-mobile-security",
    )
    db.add(device)
    db.commit()
    token = _create_mobile_jwt(admin.id, "DENTISTE", admin.id, device_id)

    response = client.get(
        "/api/superadmin/marketplace/overview",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403, response.text
    assert response.json()["detail"] == "Accès plateforme réservé à une session web privilégiée."


def test_cookie_marketplace_mutation_requires_origin(client, db, monkeypatch):
    admin = _superadmin(db, monkeypatch)
    monkeypatch.setattr(settings, "ALLOWED_ORIGINS", "https://admin.marketplace.test")
    login = client.post(
        "/api/auth/login",
        data={"username": admin.email, "password": "TestPass123!"},
    )
    assert login.status_code == 200, login.text
    assert client.cookies.get("access_token")

    response = client.patch(
        "/api/superadmin/marketplace/suppliers/999999/governance",
        json={"confirm": True, "isActive": False},
    )

    assert response.status_code == 403, response.text
    assert response.json()["detail"]["code"] == "MARKETPLACE_ORIGIN_REQUIRED"


def test_cookie_marketplace_mutation_rejects_non_https_origin(client, db, monkeypatch):
    admin = _superadmin(db, monkeypatch)
    monkeypatch.setattr(settings, "ALLOWED_ORIGINS", "https://admin.marketplace.test")
    login = client.post(
        "/api/auth/login",
        data={"username": admin.email, "password": "TestPass123!"},
    )
    assert login.status_code == 200, login.text

    response = client.patch(
        "/api/superadmin/marketplace/suppliers/999999/governance",
        json={"confirm": True, "isActive": False},
        headers={"Origin": "http://admin.marketplace.test"},
    )

    assert response.status_code == 403, response.text
    assert response.json()["detail"]["code"] == "MARKETPLACE_ORIGIN_FORBIDDEN"


def test_cookie_marketplace_mutation_accepts_exact_https_origin(client, db, monkeypatch):
    admin = _superadmin(db, monkeypatch)
    monkeypatch.setattr(settings, "ALLOWED_ORIGINS", "https://admin.marketplace.test")
    login = client.post(
        "/api/auth/login",
        data={"username": admin.email, "password": "TestPass123!"},
    )
    assert login.status_code == 200, login.text

    response = client.patch(
        "/api/superadmin/marketplace/suppliers/999999/governance",
        json={"confirm": True, "isActive": False},
        headers={"Origin": "https://admin.marketplace.test"},
    )

    assert response.status_code == 404, response.text
