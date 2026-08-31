"""Marketplace P1 — intégrité serveur et RBAC des commandes partenaire."""

import pytest
from fastapi import HTTPException

from backend import models
from backend.config import settings
from backend.security import get_password_hash
from backend.routers.partner_orders import (
    PartnerOrderCreateIn,
    _build_canonical_order_lines,
    create_partner_order,
)


def _make_user(db, email: str = "marketplace-owner@test.ma", *, password_hash: str = "test-only"):
    user = models.User(
        email=email,
        hashed_password=password_hash,
        role=models.UserRole.DENTISTE,
        nom_complet="Dr Marketplace",
        is_active=True,
        is_licensed=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_http_user(db, email: str):
    return _make_user(db, email, password_hash=get_password_hash("TestPass123!"))


def _headers(client, email: str):
    response = client.post(
        "/api/auth/login",
        data={"username": email, "password": "TestPass123!"},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _make_supplier(db, user, *, name: str = "Supplier A", active: bool = True):
    supplier = models.PartnerSupplier(
        employer_id=user.get_employer_id(),
        supplier_key=name.lower().replace(" ", "-"),
        name=name,
        is_active=active,
        sync_mode="manual",
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


def _make_product(
    db,
    user,
    supplier,
    *,
    name: str = "Produit A",
    sku: str = "SKU-A",
    price: float = 125.5,
    availability=models.PartnerProductAvailability.AVAILABLE,
):
    product = models.PartnerCatalogProduct(
        employer_id=user.get_employer_id(),
        supplier_id=supplier.id,
        name=name,
        sku=sku,
        dental_category="Consommables",
        dental_specialty="Omnipratique",
        unit="boite",
        price=price,
        availability=availability,
        benefits_json=[],
        is_featured=False,
        sort_order=0,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def _payload(*products, quantities=None, commission_rate: float = 10.0):
    quantities = quantities or [1] * len(products)
    return PartnerOrderCreateIn(
        partnerId="999999",
        partnerName="Nom falsifie client",
        strategyLabel="Libelle falsifie client",
        settlementBasis="SENT_TO_PARTNER",
        revenueModel="COMMISSION_PERCENT",
        commissionRate=commission_rate,
        discountRate=0.0,
        fixedFeeAmount=0.0,
        customer={
            "fullName": "Acheteur Test",
            "clinic": "Cabinet Test",
            "phone": "0600000000",
            "email": "buyer@test.ma",
            "city": "Rabat",
            "note": "test",
        },
        lines=[
            {
                "productId": str(product.id),
                "name": "Nom ligne falsifie",
                "sku": "SKU-FALSIFIE",
                "quantity": quantity,
                "unitPrice": 0.01,
                "lineTotal": 0.01,
            }
            for product, quantity in zip(products, quantities)
        ],
        estimatedTotal=0.01,
    )


def test_create_order_rebuilds_supplier_lines_prices_and_total_from_server_catalog(db):
    user = _make_user(db)
    supplier = _make_supplier(db, user, name="Supplier Canonique")
    product = _make_product(db, user, supplier, name="Composite Canonique", sku="CMP-42", price=125.50)

    result = create_partner_order(_payload(product, quantities=[2]), db=db, current_user=user)

    assert result["partnerId"] == str(supplier.id)
    assert result["partnerName"] == "Supplier Canonique"
    assert result["strategyLabel"] == "Commission sur commande envoyée"
    assert result["commissionRate"] == 10.0
    assert result["estimatedTotal"] == 251.0
    assert result["currentTotal"] == 251.0
    assert result["lines"] == [
        {
            "productId": str(product.id),
            "name": "Composite Canonique",
            "sku": "CMP-42",
            "quantity": 2,
            "unitPrice": 125.5,
            "lineTotal": 251.0,
        }
    ]


def test_create_order_rejects_non_preset_commercial_terms(db):
    user = _make_user(db)
    supplier = _make_supplier(db, user)
    product = _make_product(db, user, supplier)

    with pytest.raises(HTTPException) as exc:
        create_partner_order(_payload(product, commission_rate=99.0), db=db, current_user=user)

    assert exc.value.status_code == 422
    assert "Strategie commerciale non autorisee" in exc.value.detail
    assert db.query(models.PartnerOrder).count() == 0


def test_single_order_builder_rejects_mixed_suppliers(db):
    user = _make_user(db)
    supplier_a = _make_supplier(db, user, name="Supplier A")
    supplier_b = _make_supplier(db, user, name="Supplier B")
    product_a = _make_product(db, user, supplier_a, name="A", sku="A")
    product_b = _make_product(db, user, supplier_b, name="B", sku="B")
    payload = _payload(product_a, product_b)

    with pytest.raises(HTTPException) as exc:
        _build_canonical_order_lines(db, user.get_employer_id(), payload.lines)

    assert exc.value.status_code == 422
    assert "un seul fournisseur" in exc.value.detail
    assert db.query(models.PartnerOrder).count() == 0


def test_create_order_rejects_inactive_supplier(db):
    user = _make_user(db)
    supplier = _make_supplier(db, user, active=False)
    product = _make_product(db, user, supplier)

    with pytest.raises(HTTPException) as exc:
        create_partner_order(_payload(product), db=db, current_user=user)

    assert exc.value.status_code == 422
    assert "inactif" in exc.value.detail


def test_create_order_rejects_discontinued_product(db):
    user = _make_user(db)
    supplier = _make_supplier(db, user)
    product = _make_product(
        db,
        user,
        supplier,
        availability=models.PartnerProductAvailability.DISCONTINUED,
    )

    with pytest.raises(HTTPException) as exc:
        create_partner_order(_payload(product), db=db, current_user=user)

    assert exc.value.status_code == 422
    assert "retire du catalogue" in exc.value.detail


def test_create_order_rejects_product_from_another_cabinet(db):
    owner = _make_user(db, "owner-a@test.ma")
    other_owner = _make_user(db, "owner-b@test.ma")
    other_supplier = _make_supplier(db, other_owner, name="Other Supplier")
    other_product = _make_product(db, other_owner, other_supplier)

    with pytest.raises(HTTPException) as exc:
        create_partner_order(_payload(other_product), db=db, current_user=owner)

    assert exc.value.status_code == 422
    assert "catalogue du cabinet" in exc.value.detail
    assert db.query(models.PartnerOrder).count() == 0


def test_create_order_rejects_duplicate_product_lines(db):
    user = _make_user(db)
    supplier = _make_supplier(db, user)
    product = _make_product(db, user, supplier)

    with pytest.raises(HTTPException) as exc:
        create_partner_order(_payload(product, product), db=db, current_user=user)

    assert exc.value.status_code == 422
    assert "duplique" in exc.value.detail


def test_regular_cabinet_user_cannot_list_or_patch_commercial_orders(client, db, monkeypatch):
    regular = _make_http_user(db, "regular-marketplace@test.ma")
    monkeypatch.setattr(settings, "PLATFORM_CONTROL_PLANE_ENABLED", True)
    monkeypatch.setattr(settings, "SUPERADMIN_USER_ID", regular.id + 999999)
    supplier = _make_supplier(db, regular)
    product = _make_product(db, regular, supplier)
    order = create_partner_order(_payload(product), db=db, current_user=regular)
    headers = _headers(client, regular.email)

    list_response = client.get("/api/partner-orders", headers=headers)
    patch_response = client.patch(
        f"/api/partner-orders/{order['id']}",
        json={"status": "CANCELLED", "note": "forbidden"},
        headers=headers,
    )

    assert list_response.status_code == 403
    assert patch_response.status_code == 403


def test_superadmin_can_list_and_patch_own_marketplace_orders(client, db, monkeypatch):
    superadmin_email = "superadmin-marketplace@test.ma"
    superadmin = _make_http_user(db, superadmin_email)
    monkeypatch.setattr(settings, "PLATFORM_CONTROL_PLANE_ENABLED", True)
    monkeypatch.setattr(settings, "SUPERADMIN_USER_ID", superadmin.id)
    supplier = _make_supplier(db, superadmin, name="Supplier Superadmin")
    product = _make_product(db, superadmin, supplier, price=200.0)
    order = create_partner_order(_payload(product), db=db, current_user=superadmin)
    headers = _headers(client, superadmin.email)

    list_response = client.get("/api/partner-orders", headers=headers)
    patch_response = client.patch(
        f"/api/partner-orders/{order['id']}",
        json={"status": "CANCELLED", "note": "admin correction"},
        headers=headers,
    )

    assert list_response.status_code == 200, list_response.text
    assert any(item["id"] == order["id"] for item in list_response.json())
    assert patch_response.status_code == 200, patch_response.text
    assert patch_response.json()["status"] == "CANCELLED"
