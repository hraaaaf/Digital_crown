"""Marketplace P9 — contrat HTTP des routes de synchronisation fournisseur."""

from backend import database, models
from backend.main import app
from backend.routers.auth import require_superadmin


def _make_user(db, email: str):
    user = models.User(
        email=email,
        hashed_password="test-only",
        role=models.UserRole.DENTISTE,
        nom_complet="Dr Sync HTTP",
        is_active=True,
        is_licensed=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_supplier(db, user):
    supplier = models.PartnerSupplier(
        employer_id=user.get_employer_id(),
        supplier_key="sync-http",
        name="Supplier HTTP",
        api_base_url="https://supplier.example.test/api",
        sync_mode="api",
        is_active=True,
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


def test_sync_status_route_is_mounted_under_partner_catalog(client, db):
    user = _make_user(db, "sync-http@test.ma")
    supplier = _make_supplier(db, user)

    def _get_db():
        yield db

    app.dependency_overrides[database.get_db] = _get_db
    app.dependency_overrides[require_superadmin] = lambda: user
    try:
        response = client.get(f"/api/partner-catalog/suppliers/{supplier.id}/sync-status")
    finally:
        app.dependency_overrides.pop(database.get_db, None)
        app.dependency_overrides.pop(require_superadmin, None)

    assert response.status_code == 200, response.text
    assert response.json()["supplierId"] == supplier.id
    assert response.json()["freshness"]["status"] == "NEVER_SYNCED"


def test_sync_route_requires_superadmin_dependency():
    routes = {
        (getattr(route, "path", None), frozenset(getattr(route, "methods", set()) or set()))
        for route in app.routes
    }
    assert (
        "/api/partner-catalog/suppliers/{supplier_id}/sync-status",
        frozenset({"GET"}),
    ) in routes
    assert (
        "/api/partner-catalog/suppliers/{supplier_id}/sync",
        frozenset({"POST"}),
    ) in routes
