"""P10 — routes globales Marketplace montées sous Superadmin et refusées aux cabinets."""

from backend import models
from backend.main import app
from backend.security import get_password_hash


def _regular_user(db):
    item = models.User(
        email="marketplace-p10-regular@test.ma",
        hashed_password=get_password_hash("TestPass123!"),
        role=models.UserRole.DENTISTE,
        nom_complet="Dr Regular",
        is_active=True,
        is_licensed=True,
    )
    db.add(item); db.commit(); db.refresh(item); return item


def test_p10_routes_are_mounted_under_superadmin_prefix():
    routes = {
        (getattr(route, "path", None), frozenset(getattr(route, "methods", set()) or set()))
        for route in app.routes
    }
    assert ("/api/superadmin/marketplace/overview", frozenset({"GET"})) in routes
    assert ("/api/superadmin/marketplace/orders", frozenset({"GET"})) in routes
    assert ("/api/superadmin/marketplace/sync-incidents", frozenset({"GET"})) in routes
    assert ("/api/superadmin/marketplace/suppliers/{supplier_id}/governance", frozenset({"GET"})) in routes
    assert ("/api/superadmin/marketplace/suppliers/{supplier_id}/governance", frozenset({"PATCH"})) in routes
    assert ("/api/superadmin/marketplace/audit", frozenset({"GET"})) in routes


def test_regular_cabinet_user_cannot_access_global_marketplace_overview(client, db):
    regular = _regular_user(db)
    login = client.post(
        "/api/auth/login",
        data={"username": regular.email, "password": "TestPass123!"},
    )
    assert login.status_code == 200, login.text
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = client.get("/api/superadmin/marketplace/overview", headers=headers)

    assert response.status_code == 403, response.text
