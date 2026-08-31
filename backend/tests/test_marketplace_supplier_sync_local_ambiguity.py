"""P9 — aucun choix arbitraire si le catalogue local contient des identités dupliquées."""

import pytest
from fastapi import HTTPException

from backend import models
from backend.routers import partner_sync


def _user(db):
    item = models.User(
        email="sync-local-ambiguity@test.ma",
        hashed_password="test-only",
        role=models.UserRole.DENTISTE,
        nom_complet="Dr Ambiguity",
        is_active=True,
        is_licensed=True,
    )
    db.add(item); db.commit(); db.refresh(item); return item


def _supplier(db, user):
    item = models.PartnerSupplier(
        employer_id=user.get_employer_id(),
        supplier_key="sync-local-ambiguity",
        name="Supplier Ambiguity",
        api_base_url="https://supplier.example.test/api",
        sync_mode="api",
        is_active=True,
    )
    db.add(item); db.commit(); db.refresh(item); return item


def _local_product(db, user, supplier, *, external_id, name):
    item = models.PartnerCatalogProduct(
        employer_id=user.get_employer_id(),
        supplier_id=supplier.id,
        external_product_id=external_id,
        name=name,
        sku="DUP-SKU",
        dental_category="Consommables",
        dental_specialty="Omnipratique",
        unit="boite",
        price=100.0,
        availability=models.PartnerProductAvailability.AVAILABLE,
        benefits_json=[],
        is_featured=False,
        sort_order=0,
    )
    db.add(item); db.commit(); db.refresh(item); return item


def test_duplicate_local_sku_blocks_sync_without_mutating_either_row(db, monkeypatch):
    user = _user(db)
    supplier = _supplier(db, user)
    first = _local_product(db, user, supplier, external_id="LOCAL-1", name="Local A")
    second = _local_product(db, user, supplier, external_id="LOCAL-2", name="Local B")

    monkeypatch.setattr(
        partner_sync,
        "_fetch_supplier_catalog",
        lambda endpoint: {
            "version": "v1",
            "products": [{
                "externalProductId": "REMOTE-1",
                "sku": "DUP-SKU",
                "name": "Remote",
                "dentalCategory": "Consommables",
                "dentalSpecialty": "Omnipratique",
                "unit": "boite",
                "price": 999.0,
                "availability": "AVAILABLE",
                "benefits": [],
            }],
        },
    )

    with pytest.raises(HTTPException) as exc:
        partner_sync.sync_supplier_catalog(supplier.id, force=False, db=db, current_user=user)

    assert exc.value.status_code == 409
    assert "SKU locaux dupliques" in str(exc.value.detail)
    db.refresh(first); db.refresh(second)
    assert first.price == 100.0
    assert second.price == 100.0
    assert first.name == "Local A"
    assert second.name == "Local B"
