"""Marketplace P9 — synchronisation fournisseur, idempotence, backoff et fraîcheur."""

from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException

from backend import models
from backend.models_marketplace_sync import PartnerSupplierSyncState
from backend.routers import partner_sync


def _make_user(db, email: str):
    user = models.User(
        email=email,
        hashed_password="test-only",
        role=models.UserRole.DENTISTE,
        nom_complet="Dr Sync",
        is_active=True,
        is_licensed=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_supplier(db, user, *, key="supplier-sync", api_url="https://supplier.example.test/api"):
    supplier = models.PartnerSupplier(
        employer_id=user.get_employer_id(),
        supplier_key=key,
        name="Supplier Sync",
        api_base_url=api_url,
        sync_mode="api",
        is_active=True,
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


def _make_product(db, user, supplier):
    product = models.PartnerCatalogProduct(
        employer_id=user.get_employer_id(),
        supplier_id=supplier.id,
        external_product_id="EXT-1",
        name="Ancien nom",
        sku="SKU-1",
        dental_category="Consommables",
        dental_specialty="Omnipratique",
        unit="boite",
        price=100.0,
        availability=models.PartnerProductAvailability.AVAILABLE,
        short_description="Ancien",
        long_description="Ancien long",
        benefits_json=["Local"],
        is_featured=True,
        sort_order=7,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def _snapshot(*, price=120.0, availability="ON_REQUEST", version="v1"):
    return {
        "version": version,
        "products": [
            {
                "externalProductId": "EXT-1",
                "sku": "SKU-1",
                "name": "Produit synchronisé",
                "dentalCategory": "Consommables",
                "dentalSpecialty": "Omnipratique",
                "unit": "boite",
                "price": price,
                "availability": availability,
                "shortDescription": "Sync",
                "longDescription": "Sync long",
                "benefits": ["API"],
            },
            {
                "externalProductId": "EXT-2",
                "sku": "SKU-2",
                "name": "Nouveau produit",
                "dentalCategory": "Restauration",
                "dentalSpecialty": "Omnipratique",
                "unit": "kit",
                "price": 250.0,
                "availability": "AVAILABLE",
                "shortDescription": "Nouveau",
                "longDescription": None,
                "benefits": [],
            },
        ],
    }


def test_sync_updates_price_availability_and_imports_without_overwriting_merchandising(db, monkeypatch):
    user = _make_user(db, "sync-success@test.ma")
    supplier = _make_supplier(db, user)
    existing = _make_product(db, user, supplier)
    monkeypatch.setattr(partner_sync, "_fetch_supplier_catalog", lambda endpoint: _snapshot())

    result = partner_sync.sync_supplier_catalog(supplier.id, force=False, db=db, current_user=user)

    assert result["idempotentReplay"] is False
    assert result["changes"] == {"created": 1, "updated": 1, "received": 2}
    db.refresh(existing)
    assert existing.name == "Produit synchronisé"
    assert existing.price == 120.0
    assert existing.availability == models.PartnerProductAvailability.ON_REQUEST
    assert existing.is_featured is True
    assert existing.sort_order == 7
    imported = (
        db.query(models.PartnerCatalogProduct)
        .filter(
            models.PartnerCatalogProduct.supplier_id == supplier.id,
            models.PartnerCatalogProduct.external_product_id == "EXT-2",
        )
        .one()
    )
    assert imported.price == 250.0
    assert imported.is_featured is False
    assert imported.sort_order == 0


def test_same_logical_snapshot_is_idempotent_even_if_product_order_changes(db, monkeypatch):
    user = _make_user(db, "sync-replay@test.ma")
    supplier = _make_supplier(db, user, key="sync-replay")
    first_payload = _snapshot()
    second_payload = {"version": "v1", "products": list(reversed(first_payload["products"]))}
    payloads = iter([first_payload, second_payload])
    monkeypatch.setattr(partner_sync, "_fetch_supplier_catalog", lambda endpoint: next(payloads))

    first = partner_sync.sync_supplier_catalog(supplier.id, force=False, db=db, current_user=user)
    second = partner_sync.sync_supplier_catalog(supplier.id, force=False, db=db, current_user=user)

    assert first["idempotentReplay"] is False
    assert second["idempotentReplay"] is True
    assert second["changes"] == {"created": 0, "updated": 0, "received": 2}
    assert db.query(models.PartnerCatalogProduct).filter(models.PartnerCatalogProduct.supplier_id == supplier.id).count() == 2
    state = db.query(PartnerSupplierSyncState).filter(PartnerSupplierSyncState.supplier_id == supplier.id).one()
    assert state.consecutive_failures == 0
    assert state.last_outcome == "SUCCESS"


def test_failed_sync_preserves_last_catalog_and_enters_backoff_degraded_mode(db, monkeypatch):
    user = _make_user(db, "sync-failure@test.ma")
    supplier = _make_supplier(db, user, key="sync-failure")
    existing = _make_product(db, user, supplier)
    state = PartnerSupplierSyncState(
        employer_id=user.get_employer_id(),
        supplier_id=supplier.id,
        last_success_at=datetime.utcnow() - timedelta(minutes=5),
        last_outcome="SUCCESS",
        consecutive_failures=0,
        last_product_count=1,
    )
    db.add(state)
    db.commit()

    def _fail(endpoint):
        raise partner_sync.SupplierSyncError("TIMEOUT", "Fournisseur indisponible")

    monkeypatch.setattr(partner_sync, "_fetch_supplier_catalog", _fail)

    with pytest.raises(HTTPException) as failure:
        partner_sync.sync_supplier_catalog(supplier.id, force=False, db=db, current_user=user)
    assert failure.value.status_code == 502

    db.refresh(existing)
    db.refresh(state)
    assert existing.price == 100.0
    assert state.last_outcome == "FAILED"
    assert state.consecutive_failures == 1
    assert state.next_retry_at is not None
    assert partner_sync._freshness(state)["status"] == "DEGRADED"
    assert partner_sync._freshness(state)["hasUsableBaseline"] is True

    with pytest.raises(HTTPException) as backoff:
        partner_sync.sync_supplier_catalog(supplier.id, force=False, db=db, current_user=user)
    assert backoff.value.status_code == 429
    assert backoff.value.detail["code"] == "SYNC_BACKOFF"


def test_force_retry_bypasses_backoff_and_success_resets_failure_state(db, monkeypatch):
    user = _make_user(db, "sync-force@test.ma")
    supplier = _make_supplier(db, user, key="sync-force")
    state = PartnerSupplierSyncState(
        employer_id=user.get_employer_id(),
        supplier_id=supplier.id,
        last_outcome="FAILED",
        consecutive_failures=3,
        next_retry_at=datetime.utcnow() + timedelta(hours=1),
        last_error_code="TIMEOUT",
        last_error_detail="timeout",
    )
    db.add(state)
    db.commit()
    monkeypatch.setattr(partner_sync, "_fetch_supplier_catalog", lambda endpoint: _snapshot())

    result = partner_sync.sync_supplier_catalog(supplier.id, force=True, db=db, current_user=user)

    db.refresh(state)
    assert result["sync"]["freshness"]["status"] == "FRESH"
    assert state.last_outcome == "SUCCESS"
    assert state.consecutive_failures == 0
    assert state.next_retry_at is None
    assert state.last_error_code is None


def test_freshness_transitions_are_deterministic(db):
    user = _make_user(db, "sync-freshness@test.ma")
    supplier = _make_supplier(db, user, key="sync-freshness")
    now = datetime(2026, 8, 30, 20, 0, 0)
    state = PartnerSupplierSyncState(
        employer_id=user.get_employer_id(),
        supplier_id=supplier.id,
        last_outcome="SUCCESS",
        last_success_at=now - timedelta(minutes=10),
    )

    assert partner_sync._freshness(state, now)["status"] == "FRESH"
    state.last_success_at = now - timedelta(minutes=16)
    assert partner_sync._freshness(state, now)["status"] == "STALE"
    state.last_outcome = "FAILED"
    assert partner_sync._freshness(state, now)["status"] == "DEGRADED"
    state.last_outcome = None
    state.last_success_at = None
    assert partner_sync._freshness(state, now)["status"] == "NEVER_SYNCED"


def test_duplicate_snapshot_identity_is_rejected_without_product_mutation(db, monkeypatch):
    user = _make_user(db, "sync-duplicate@test.ma")
    supplier = _make_supplier(db, user, key="sync-duplicate")
    existing = _make_product(db, user, supplier)
    payload = _snapshot()
    payload["products"][1]["sku"] = "SKU-1"
    monkeypatch.setattr(partner_sync, "_fetch_supplier_catalog", lambda endpoint: payload)

    with pytest.raises(HTTPException) as exc:
        partner_sync.sync_supplier_catalog(supplier.id, force=False, db=db, current_user=user)

    assert exc.value.status_code == 502
    db.refresh(existing)
    assert existing.price == 100.0
    assert db.query(models.PartnerCatalogProduct).filter(models.PartnerCatalogProduct.supplier_id == supplier.id).count() == 1


def test_sync_is_tenant_scoped_and_requires_active_api_supplier(db, monkeypatch):
    owner = _make_user(db, "sync-owner@test.ma")
    outsider = _make_user(db, "sync-outsider@test.ma")
    supplier = _make_supplier(db, owner, key="sync-scope")
    monkeypatch.setattr(partner_sync, "_fetch_supplier_catalog", lambda endpoint: _snapshot())

    with pytest.raises(HTTPException) as scope:
        partner_sync.sync_supplier_catalog(supplier.id, force=False, db=db, current_user=outsider)
    assert scope.value.status_code == 404

    supplier.is_active = False
    db.commit()
    with pytest.raises(HTTPException) as inactive:
        partner_sync.sync_supplier_catalog(supplier.id, force=False, db=db, current_user=owner)
    assert inactive.value.status_code == 422

    supplier.is_active = True
    supplier.sync_mode = "manual"
    db.commit()
    with pytest.raises(HTTPException) as manual:
        partner_sync.sync_supplier_catalog(supplier.id, force=False, db=db, current_user=owner)
    assert manual.value.status_code == 422


def test_catalog_endpoint_reuses_p6_https_ssrf_contract():
    assert partner_sync._catalog_endpoint("https://supplier.example.com/api") == "https://supplier.example.com/api/catalog"
    for unsafe in (
        "http://supplier.example.com/api",
        "https://localhost/api",
        "https://127.0.0.1/api",
        "https://supplier.example.com/api?token=secret",
    ):
        with pytest.raises(HTTPException):
            partner_sync._catalog_endpoint(unsafe)
