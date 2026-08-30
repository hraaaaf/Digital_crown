"""Marketplace P1 — visibilité catalogue selon statut fournisseur et rôle."""

import pytest
from fastapi import HTTPException

from backend import models
from backend.routers import partner_catalog


def _make_user(db, email: str = "marketplace-catalog@test.ma"):
    user = models.User(
        email=email,
        hashed_password="test-only",
        role=models.UserRole.DENTISTE,
        nom_complet="Dr Marketplace",
        is_active=True,
        is_licensed=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_supplier(db, user, *, key: str, name: str, active: bool):
    supplier = models.PartnerSupplier(
        employer_id=user.get_employer_id(),
        supplier_key=key,
        name=name,
        is_active=active,
        sync_mode="manual",
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


def _make_product(db, user, supplier, *, name: str, sku: str):
    product = models.PartnerCatalogProduct(
        employer_id=user.get_employer_id(),
        supplier_id=supplier.id,
        name=name,
        sku=sku,
        dental_category="Consommables",
        dental_specialty="Omnipratique",
        unit="boite",
        price=100.0,
        availability=models.PartnerProductAvailability.AVAILABLE,
        benefits_json=[],
        is_featured=False,
        sort_order=0,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def test_cabinet_storefront_hides_inactive_supplier_and_its_products(db, monkeypatch):
    user = _make_user(db)
    active = _make_supplier(db, user, key="active", name="Active Supplier", active=True)
    inactive = _make_supplier(db, user, key="inactive", name="Inactive Supplier", active=False)
    active_product = _make_product(db, user, active, name="Visible", sku="VISIBLE")
    inactive_product = _make_product(db, user, inactive, name="Hidden", sku="HIDDEN")
    monkeypatch.setattr(partner_catalog, "is_superadmin_user", lambda _user: False)

    suppliers = partner_catalog.list_suppliers(db=db, current_user=user)
    products = partner_catalog.list_products(db=db, current_user=user)

    assert [item["id"] for item in suppliers] == [active.id]
    assert [item["id"] for item in products] == [active_product.id]

    with pytest.raises(HTTPException) as supplier_exc:
        partner_catalog.get_supplier(inactive.id, db=db, current_user=user)
    assert supplier_exc.value.status_code == 404

    with pytest.raises(HTTPException) as product_exc:
        partner_catalog.get_product(inactive_product.id, db=db, current_user=user)
    assert product_exc.value.status_code == 404


def test_superadmin_can_still_manage_inactive_supplier_and_products(db, monkeypatch):
    user = _make_user(db, "marketplace-superadmin@test.ma")
    active = _make_supplier(db, user, key="active-admin", name="Active Admin", active=True)
    inactive = _make_supplier(db, user, key="inactive-admin", name="Inactive Admin", active=False)
    active_product = _make_product(db, user, active, name="Visible Admin", sku="VISIBLE-ADMIN")
    inactive_product = _make_product(db, user, inactive, name="Hidden Admin", sku="HIDDEN-ADMIN")
    monkeypatch.setattr(partner_catalog, "is_superadmin_user", lambda _user: True)

    suppliers = partner_catalog.list_suppliers(db=db, current_user=user)
    products = partner_catalog.list_products(db=db, current_user=user)

    assert {item["id"] for item in suppliers} == {active.id, inactive.id}
    assert {item["id"] for item in products} == {active_product.id, inactive_product.id}
    assert partner_catalog.get_supplier(inactive.id, db=db, current_user=user)["id"] == inactive.id
    assert partner_catalog.get_product(inactive_product.id, db=db, current_user=user)["id"] == inactive_product.id
