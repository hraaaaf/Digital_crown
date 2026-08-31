"""Marketplace P9 — audit persistant et sémantique snapshot fournisseur."""

import pytest
from fastapi import HTTPException

from backend import models
from backend.models_marketplace_sync import PartnerSupplierSyncAudit
from backend.routers import partner_sync


def _make_user(db, email: str):
    user = models.User(
        email=email,
        hashed_password="test-only",
        role=models.UserRole.DENTISTE,
        nom_complet="Dr Sync Audit",
        is_active=True,
        is_licensed=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_supplier(db, user, key: str):
    supplier = models.PartnerSupplier(
        employer_id=user.get_employer_id(),
        supplier_key=key,
        name="Supplier Audit",
        api_base_url="https://supplier.example.test/api",
        sync_mode="api",
        is_active=True,
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


def _product_payload(*, external_id="EXT-A", sku="SKU-A", availability="AVAILABLE"):
    return {
        "externalProductId": external_id,
        "sku": sku,
        "name": "Produit API",
        "dentalCategory": "Consommables",
        "dentalSpecialty": "Omnipratique",
        "unit": "boite",
        "price": 123.0,
        "availability": availability,
        "shortDescription": "Sync",
        "longDescription": None,
        "benefits": ["API"],
    }


def _make_local_product(
    db,
    user,
    supplier,
    *,
    external_id: str,
    sku: str,
    availability=models.PartnerProductAvailability.AVAILABLE,
    source_json=None,
):
    product = models.PartnerCatalogProduct(
        employer_id=user.get_employer_id(),
        supplier_id=supplier.id,
        external_product_id=external_id,
        name=f"Local {sku}",
        sku=sku,
        dental_category="Consommables",
        dental_specialty="Omnipratique",
        unit="boite",
        price=100.0,
        availability=availability,
        benefits_json=[],
        is_featured=False,
        sort_order=0,
        source_json=source_json,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def test_sync_persists_applied_and_no_change_audits(db, monkeypatch):
    user = _make_user(db, "sync-audit-success@test.ma")
    supplier = _make_supplier(db, user, "sync-audit-success")
    payload = {"version": "v1", "products": [_product_payload()]}
    monkeypatch.setattr(partner_sync, "_fetch_supplier_catalog", lambda endpoint: payload)

    first = partner_sync.sync_supplier_catalog(supplier.id, force=False, db=db, current_user=user)
    second = partner_sync.sync_supplier_catalog(supplier.id, force=False, db=db, current_user=user)

    assert first["idempotentReplay"] is False
    assert second["idempotentReplay"] is True
    audits = (
        db.query(PartnerSupplierSyncAudit)
        .filter(PartnerSupplierSyncAudit.supplier_id == supplier.id)
        .order_by(PartnerSupplierSyncAudit.id.asc())
        .all()
    )
    assert [audit.event_type for audit in audits] == [
        "SUPPLIER_SYNC_APPLIED",
        "SUPPLIER_SYNC_NO_CHANGE",
    ]
    assert all(audit.outcome == "SUCCESS" for audit in audits)
    assert all(audit.actor_user_id == user.id for audit in audits)
    assert audits[0].payload_sha256 == audits[1].payload_sha256
    assert audits[0].changes_json == {"created": 1, "updated": 0, "received": 1}


def test_failed_sync_persists_failure_audit(db, monkeypatch):
    user = _make_user(db, "sync-audit-failure@test.ma")
    supplier = _make_supplier(db, user, "sync-audit-failure")

    def _fail(endpoint):
        raise partner_sync.SupplierSyncError("TIMEOUT", "Fournisseur indisponible")

    monkeypatch.setattr(partner_sync, "_fetch_supplier_catalog", _fail)

    with pytest.raises(HTTPException) as exc:
        partner_sync.sync_supplier_catalog(supplier.id, force=False, db=db, current_user=user)
    assert exc.value.status_code == 502

    audit = (
        db.query(PartnerSupplierSyncAudit)
        .filter(PartnerSupplierSyncAudit.supplier_id == supplier.id)
        .one()
    )
    assert audit.event_type == "SUPPLIER_SYNC_FAILED"
    assert audit.outcome == "FAILED"
    assert audit.actor_user_id == user.id
    assert audit.error_code == "TIMEOUT"
    assert audit.error_detail == "Fournisseur indisponible"


def test_snapshot_discontinues_only_missing_sync_managed_products(db, monkeypatch):
    user = _make_user(db, "sync-snapshot-missing@test.ma")
    supplier = _make_supplier(db, user, "sync-snapshot-missing")
    managed = _make_local_product(
        db,
        user,
        supplier,
        external_id="EXT-MANAGED",
        sku="SKU-MANAGED",
        source_json={
            "localNote": "preserve",
            partner_sync.SYNC_SOURCE_KEY: {"managed": True, "supplierId": supplier.id},
        },
    )
    manual = _make_local_product(
        db,
        user,
        supplier,
        external_id="EXT-MANUAL",
        sku="SKU-MANUAL",
        source_json={"localOnly": True},
    )
    monkeypatch.setattr(
        partner_sync,
        "_fetch_supplier_catalog",
        lambda endpoint: {"version": "empty-v2", "products": []},
    )

    result = partner_sync.sync_supplier_catalog(supplier.id, force=False, db=db, current_user=user)

    assert result["changes"] == {"created": 0, "updated": 0, "received": 0, "discontinued": 1}
    db.refresh(managed)
    db.refresh(manual)
    assert managed.availability == models.PartnerProductAvailability.DISCONTINUED
    assert managed.source_json["localNote"] == "preserve"
    assert manual.availability == models.PartnerProductAvailability.AVAILABLE
    assert manual.source_json == {"localOnly": True}

    audit = (
        db.query(PartnerSupplierSyncAudit)
        .filter(PartnerSupplierSyncAudit.supplier_id == supplier.id)
        .one()
    )
    assert audit.changes_json["discontinued"] == 1


def test_discontinued_managed_product_reappears_from_supplier(db, monkeypatch):
    user = _make_user(db, "sync-snapshot-return@test.ma")
    supplier = _make_supplier(db, user, "sync-snapshot-return")
    product = _make_local_product(
        db,
        user,
        supplier,
        external_id="EXT-A",
        sku="SKU-A",
        availability=models.PartnerProductAvailability.DISCONTINUED,
        source_json={
            "localNote": "keep-me",
            partner_sync.SYNC_SOURCE_KEY: {"managed": True, "supplierId": supplier.id},
        },
    )
    monkeypatch.setattr(
        partner_sync,
        "_fetch_supplier_catalog",
        lambda endpoint: {"version": "return-v1", "products": [_product_payload()]},
    )

    result = partner_sync.sync_supplier_catalog(supplier.id, force=False, db=db, current_user=user)

    assert result["changes"] == {"created": 0, "updated": 1, "received": 1}
    db.refresh(product)
    assert product.availability == models.PartnerProductAvailability.AVAILABLE
    assert product.price == 123.0
    assert product.source_json["localNote"] == "keep-me"
    assert product.source_json[partner_sync.SYNC_SOURCE_KEY]["managed"] is True
