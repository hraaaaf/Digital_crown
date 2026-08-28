from backend import models
from backend.config import settings
from backend.security import get_password_hash


def _create_user(db, *, email: str, role=models.UserRole.ADMIN, permissions=None):
    user = models.User(
        email=email,
        hashed_password=get_password_hash("TestPass123!"),
        role=role,
        nom_complet="SEC1 Test",
        is_active=True,
        is_licensed=True,
        permissions=permissions or {},
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _auth_headers(client, email: str):
    response = client.post(
        "/api/auth/login",
        data={"username": email, "password": "TestPass123!"},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_sales_admin_can_create_trial_but_cannot_grant_paid(client, db, monkeypatch):
    monkeypatch.setattr(settings, "PLATFORM_CONTROL_PLANE_ENABLED", True)
    monkeypatch.setattr(settings, "SUPERADMIN_USER_ID", 999999)
    sales = _create_user(
        db,
        email="sales-sec1@example.com",
        permissions={
            "license.read": True,
            "license.create_trial": True,
        },
    )
    target = _create_user(
        db,
        email="target-sec1@example.com",
        role=models.UserRole.DENTISTE,
    )
    headers = _auth_headers(client, sales.email)

    created = client.post(
        "/api/superadmin/trial-codes",
        headers=headers,
        json={
            "email": "prospect-sec1@example.com",
            "nom_complet": "Dr Prospect",
            "cabinet_name": "Cabinet Prospect",
            "trial_days": 30,
            "expires_in_days": 14,
        },
    )
    assert created.status_code == 200, created.text
    assert created.json()["email"] == "prospect-sec1@example.com"

    paid = client.post(
        f"/api/superadmin/clients/{target.id}/grant-license?action=1m",
        headers=headers,
    )
    assert paid.status_code == 403


def test_superadmin_identity_is_user_id_not_display_email(client, db, monkeypatch):
    monkeypatch.setattr(settings, "PLATFORM_CONTROL_PLANE_ENABLED", True)
    owner = _create_user(db, email="owner-renamed@example.com")
    imposter = _create_user(db, email=settings.SUPERADMIN_DISPLAY_EMAIL)
    monkeypatch.setattr(settings, "SUPERADMIN_USER_ID", owner.id)

    owner_headers = _auth_headers(client, owner.email)
    owner_me = client.get("/api/auth/me", headers=owner_headers)
    assert owner_me.status_code == 200
    assert owner_me.json()["is_superadmin"] is True

    imposter_headers = _auth_headers(client, imposter.email)
    imposter_me = client.get("/api/auth/me", headers=imposter_headers)
    assert imposter_me.status_code == 200
    assert imposter_me.json()["is_superadmin"] is False

    forbidden = client.get("/api/superadmin/clients", headers=imposter_headers)
    assert forbidden.status_code == 403


def test_superadmin_routes_fail_closed_when_control_plane_is_disabled(client, db, monkeypatch):
    owner = _create_user(db, email="owner-disabled-plane@example.com")
    monkeypatch.setattr(settings, "PLATFORM_CONTROL_PLANE_ENABLED", False)
    monkeypatch.setattr(settings, "SUPERADMIN_USER_ID", owner.id)
    headers = _auth_headers(client, owner.email)

    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["is_superadmin"] is False

    response = client.get("/api/superadmin/clients", headers=headers)
    assert response.status_code == 403
