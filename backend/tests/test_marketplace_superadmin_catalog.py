"""P10 — CRUD global fournisseurs/produits avec cabinet explicite et audit."""

import pytest
from fastapi import HTTPException

from backend import models
from backend.models_marketplace_governance import MarketplaceGovernanceEvent
from backend.routers.partner_superadmin_catalog import (
    GlobalProductCreateIn,
    GlobalProductUpdateIn,
    GlobalSupplierCreateIn,
    GlobalSupplierUpdateIn,
    create_global_product,
    create_global_supplier,
    global_products,
    global_suppliers,
    update_global_product,
    update_global_supplier,
)


def _user(db, email):
    item = models.User(
        email=email,
        hashed_password="test-only",
        role=models.UserRole.DENTISTE,
        nom_complet=email.split("@")[0],
        is_active=True,
        is_licensed=True,
    )
    db.add(item); db.commit(); db.refresh(item); return item


def test_global_supplier_create_update_list_are_cross_cabinet_and_audited(db):
    admin = _user(db, "catalog-admin@test.ma")
    owner_a = _user(db, "catalog-owner-a@test.ma")
    owner_b = _user(db, "catalog-owner-b@test.ma")

    created = create_global_supplier(
        GlobalSupplierCreateIn(
            confirm=True,
            employerId=owner_a.id,
            supplierKey="global-a",
            name="Global Supplier A",
        ),
        db=db,
        admin=admin,
    )
    create_global_supplier(
        GlobalSupplierCreateIn(
            confirm=True,
            employerId=owner_b.id,
            supplierKey="global-b",
            name="Global Supplier B",
        ),
        db=db,
        admin=admin,
    )

    updated = update_global_supplier(
        created["id"],
        GlobalSupplierUpdateIn(confirm=True, name="Supplier A Updated", isActive=False),
        db=db,
        admin=admin,
    )
    rows = global_suppliers(employerId=owner_a.id, limit=200, db=db, admin=admin)

    assert updated["employerId"] == owner_a.id
    assert updated["name"] == "Supplier A Updated"
    assert updated["isActive"] is False
    assert len(rows) == 1
    assert rows[0]["supplierKey"] == "global-a"
    events = db.query(MarketplaceGovernanceEvent).filter(MarketplaceGovernanceEvent.employer_id == owner_a.id).all()
    assert [event.action for event in events] == ["SUPPLIER_CREATED", "SUPPLIER_UPDATED"]


def test_global_mutation_requires_explicit_confirmation(db):
    admin = _user(db, "catalog-confirm-admin@test.ma")
    owner = _user(db, "catalog-confirm-owner@test.ma")

    with pytest.raises(HTTPException) as exc:
        create_global_supplier(
            GlobalSupplierCreateIn(
                confirm=False,
                employerId=owner.id,
                supplierKey="unconfirmed",
                name="Unconfirmed",
            ),
            db=db,
            admin=admin,
        )
    assert exc.value.status_code == 409


def test_global_product_crud_enforces_cabinet_supplier_boundary_and_audit(db):
    admin = _user(db, "product-admin@test.ma")
    owner_a = _user(db, "product-owner-a@test.ma")
    owner_b = _user(db, "product-owner-b@test.ma")
    supplier_a = create_global_supplier(
        GlobalSupplierCreateIn(confirm=True, employerId=owner_a.id, supplierKey="prod-a", name="Supplier A"),
        db=db, admin=admin,
    )
    supplier_b = create_global_supplier(
        GlobalSupplierCreateIn(confirm=True, employerId=owner_b.id, supplierKey="prod-b", name="Supplier B"),
        db=db, admin=admin,
    )

    created = create_global_product(
        GlobalProductCreateIn(
            confirm=True,
            employerId=owner_a.id,
            supplierId=supplier_a["id"],
            externalProductId="EXT-GLOBAL-1",
            name="Produit Global",
            sku="GLOBAL-1",
            dentalCategory="Consommables",
            dentalSpecialty="Omnipratique",
            unit="boite",
            price=150.0,
            availability="AVAILABLE",
            benefits=[],
        ),
        db=db,
        admin=admin,
    )
    updated = update_global_product(
        created["id"],
        GlobalProductUpdateIn(confirm=True, price=175.0, availability="ON_REQUEST", isFeatured=True),
        db=db,
        admin=admin,
    )

    assert updated["employerId"] == owner_a.id
    assert updated["price"] == 175.0
    assert updated["availability"] == "ON_REQUEST"
    assert updated["isFeatured"] is True
    rows = global_products(employerId=owner_a.id, supplierId=None, limit=500, db=db, admin=admin)
    assert len(rows) == 1
    assert rows[0]["sku"] == "GLOBAL-1"

    with pytest.raises(HTTPException) as cross:
        update_global_product(
            created["id"],
            GlobalProductUpdateIn(confirm=True, supplierId=supplier_b["id"]),
            db=db,
            admin=admin,
        )
    assert cross.value.status_code == 409
    events = db.query(MarketplaceGovernanceEvent).filter(MarketplaceGovernanceEvent.employer_id == owner_a.id).all()
    actions = [event.action for event in events]
    assert "PRODUCT_CREATED" in actions
    assert "PRODUCT_UPDATED" in actions
