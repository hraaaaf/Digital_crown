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


def _user(db, email, *, employer_id=None):
    item = models.User(
        email=email,
        hashed_password="test-only",
        role=models.UserRole.DENTISTE,
        nom_complet=email.split("@")[0],
        is_active=True,
        is_licensed=True,
        employer_id=employer_id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def _create_supplier(db, admin, owner, key="global-a"):
    return create_global_supplier(
        GlobalSupplierCreateIn(
            confirm=True,
            employerId=owner.id,
            supplierKey=key,
            name=f"Supplier {key}",
        ),
        db=db,
        admin=admin,
    )


def _product_payload(owner, supplier_id, *, sku="GLOBAL-1", external_id="EXT-GLOBAL-1"):
    return GlobalProductCreateIn(
        confirm=True,
        employerId=owner.id,
        supplierId=supplier_id,
        externalProductId=external_id,
        name="Produit Global",
        sku=sku,
        dentalCategory="Consommables",
        dentalSpecialty="Omnipratique",
        unit="boite",
        price=150.0,
        availability="AVAILABLE",
        benefits=[],
    )


def test_global_supplier_create_update_list_are_cross_cabinet_and_audited(db):
    admin = _user(db, "catalog-admin@test.ma")
    owner_a = _user(db, "catalog-owner-a@test.ma")
    owner_b = _user(db, "catalog-owner-b@test.ma")

    created = _create_supplier(db, admin, owner_a, "global-a")
    _create_supplier(db, admin, owner_b, "global-b")

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


def test_global_target_must_be_cabinet_owner_not_employee(db):
    admin = _user(db, "catalog-owner-guard-admin@test.ma")
    owner = _user(db, "catalog-real-owner@test.ma")
    employee = _user(db, "catalog-employee@test.ma", employer_id=owner.id)

    with pytest.raises(HTTPException) as exc:
        create_global_supplier(
            GlobalSupplierCreateIn(
                confirm=True,
                employerId=employee.id,
                supplierKey="employee-scope",
                name="Wrong Scope",
            ),
            db=db,
            admin=admin,
        )
    assert exc.value.status_code == 404
    assert db.query(models.PartnerSupplier).filter(models.PartnerSupplier.employer_id == employee.id).count() == 0


def test_supplier_key_is_trimmed_and_case_insensitive_unique(db):
    admin = _user(db, "catalog-key-admin@test.ma")
    owner = _user(db, "catalog-key-owner@test.ma")
    first = _create_supplier(db, admin, owner, "Canonical-Key")
    assert first["supplierKey"] == "Canonical-Key"

    with pytest.raises(HTTPException) as duplicate:
        create_global_supplier(
            GlobalSupplierCreateIn(
                confirm=True,
                employerId=owner.id,
                supplierKey="  canonical-key  ",
                name="Duplicate",
            ),
            db=db,
            admin=admin,
        )
    assert duplicate.value.status_code == 409


def test_global_product_crud_enforces_cabinet_supplier_boundary_and_audit(db):
    admin = _user(db, "product-admin@test.ma")
    owner_a = _user(db, "product-owner-a@test.ma")
    owner_b = _user(db, "product-owner-b@test.ma")
    supplier_a = _create_supplier(db, admin, owner_a, "prod-a")
    supplier_b = _create_supplier(db, admin, owner_b, "prod-b")

    created = create_global_product(
        _product_payload(owner_a, supplier_a["id"]),
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


def test_product_identity_guard_matches_p9_case_insensitive_contract(db):
    admin = _user(db, "product-identity-admin@test.ma")
    owner = _user(db, "product-identity-owner@test.ma")
    supplier = _create_supplier(db, admin, owner, "identity")
    first = create_global_product(
        _product_payload(owner, supplier["id"], sku="SKU-Guard", external_id="EXT-Guard"),
        db=db,
        admin=admin,
    )

    with pytest.raises(HTTPException) as sku_duplicate:
        create_global_product(
            _product_payload(owner, supplier["id"], sku="  sku-guard  ", external_id="EXT-OTHER"),
            db=db,
            admin=admin,
        )
    assert sku_duplicate.value.status_code == 409

    with pytest.raises(HTTPException) as external_duplicate:
        create_global_product(
            _product_payload(owner, supplier["id"], sku="SKU-OTHER", external_id="ext-guard"),
            db=db,
            admin=admin,
        )
    assert external_duplicate.value.status_code == 409

    second = create_global_product(
        _product_payload(owner, supplier["id"], sku="SKU-SECOND", external_id="EXT-SECOND"),
        db=db,
        admin=admin,
    )
    with pytest.raises(HTTPException) as update_duplicate:
        update_global_product(
            second["id"],
            GlobalProductUpdateIn(confirm=True, sku="sku-guard"),
            db=db,
            admin=admin,
        )
    assert update_duplicate.value.status_code == 409

    persisted = db.query(models.PartnerCatalogProduct).filter(models.PartnerCatalogProduct.id == first["id"]).one()
    assert persisted.sku == "SKU-Guard"
