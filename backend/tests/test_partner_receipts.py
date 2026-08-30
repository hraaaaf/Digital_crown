"""Marketplace P6 — réception locale idempotente des commandes partenaire."""

import pytest
from fastapi import HTTPException

from backend import database, models
from backend.main import app
from backend.models_marketplace_receipts import PartnerOrderReceipt
from backend.routers.auth import require_superadmin
from backend.routers.partner_receipts import PartnerReceiptCreateIn, create_partner_order_receipt


def _make_user(db, email: str):
    user = models.User(
        email=email,
        hashed_password="test-only",
        role=models.UserRole.DENTISTE,
        nom_complet="Dr Receipt",
        is_active=True,
        is_licensed=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_order(db, user, *, status=models.PartnerOrderStatus.CONFIRMED):
    order = models.PartnerOrder(
        employer_id=user.get_employer_id(),
        order_number=f"RECEIPT-{user.id}-{status.value}",
        partner_id="11",
        partner_name="Supplier Receipt",
        status=status,
        settlement_basis=models.PartnerSettlementBasis.CONFIRMED,
        revenue_model=models.PartnerRevenueModel.COMMISSION_PERCENT,
        strategy_label="Commission sur commande confirmée",
        commission_rate=10.0,
        discount_rate=0.0,
        fixed_fee_amount=0.0,
        customer_full_name="Acheteur",
        customer_clinic="Cabinet",
        customer_phone="0600000000",
        customer_email="buyer@test.ma",
        customer_city="Rabat",
        lines_json=[
            {
                "productId": "101",
                "name": "Produit A",
                "sku": "SKU-A",
                "quantity": 2,
                "unitPrice": 75.0,
                "lineTotal": 150.0,
            },
            {
                "productId": "102",
                "name": "Produit B",
                "sku": "SKU-B",
                "quantity": 1,
                "unitPrice": 50.0,
                "lineTotal": 50.0,
            },
        ],
        estimated_total=200.0,
        sent_total=200.0,
        current_total=200.0,
        recognized_base_amount=200.0 if status == models.PartnerOrderStatus.CONFIRMED else 0.0,
        recognized_revenue_amount=20.0 if status == models.PartnerOrderStatus.CONFIRMED else 0.0,
        revenue_delta_amount=0.0,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def _payload(*, quantity_a=2, include_b=True):
    lines = [
        {
            "productId": "101",
            "quantityReceived": quantity_a,
            "lotNumber": "LOT-A",
            "expiresAt": "2028-12-31T00:00:00",
        }
    ]
    if include_b:
        lines.append({"productId": "102", "quantityReceived": 1})
    return PartnerReceiptCreateIn(lines=lines, note="Réception complète")


def test_receipt_fulfills_confirmed_order_and_records_canonical_audit(db):
    user = _make_user(db, "receipt-success@test.ma")
    order = _make_order(db, user)

    result = create_partner_order_receipt(order.id, _payload(), db=db, current_user=user)

    assert result["order"]["status"] == "FULFILLED"
    assert result["order"]["recognizedBaseAmount"] == 200.0
    assert result["order"]["recognizedRevenueAmount"] == 20.0
    assert result["receipt"]["orderId"] == order.id
    assert result["receipt"]["lines"][0] == {
        "productId": "101",
        "name": "Produit A",
        "sku": "SKU-A",
        "quantityOrdered": 2,
        "quantityReceived": 2,
        "unitPrice": 75.0,
        "lotNumber": "LOT-A",
        "expiresAt": "2028-12-31T00:00:00",
    }

    persisted = db.query(PartnerOrderReceipt).filter(PartnerOrderReceipt.order_id == order.id).one()
    assert persisted.employer_id == user.get_employer_id()
    event = (
        db.query(models.PartnerOrderEvent)
        .filter(models.PartnerOrderEvent.order_id == order.id, models.PartnerOrderEvent.event_type == "RECEIPT_RECORDED")
        .one()
    )
    assert event.previous_status == "CONFIRMED"
    assert event.new_status == "FULFILLED"
    assert event.payload_json["receiptId"] == persisted.id
    assert event.payload_json["lineCount"] == 2


def test_receipt_rejects_order_that_is_not_confirmed(db):
    user = _make_user(db, "receipt-status@test.ma")
    order = _make_order(db, user, status=models.PartnerOrderStatus.SENT_TO_PARTNER)

    with pytest.raises(HTTPException) as exc:
        create_partner_order_receipt(order.id, _payload(), db=db, current_user=user)

    assert exc.value.status_code == 422
    assert "CONFIRMED requis" in exc.value.detail
    assert db.query(PartnerOrderReceipt).count() == 0


def test_receipt_requires_exact_ordered_quantities(db):
    user = _make_user(db, "receipt-quantity@test.ma")
    order = _make_order(db, user)

    with pytest.raises(HTTPException) as exc:
        create_partner_order_receipt(order.id, _payload(quantity_a=1), db=db, current_user=user)

    assert exc.value.status_code == 422
    assert "attendu 2, recu 1" in exc.value.detail
    db.refresh(order)
    assert order.status == models.PartnerOrderStatus.CONFIRMED
    assert db.query(PartnerOrderReceipt).count() == 0


def test_receipt_requires_exact_product_set(db):
    user = _make_user(db, "receipt-products@test.ma")
    order = _make_order(db, user)

    with pytest.raises(HTTPException) as exc:
        create_partner_order_receipt(order.id, _payload(include_b=False), db=db, current_user=user)

    assert exc.value.status_code == 422
    assert "exactement les produits" in exc.value.detail
    assert db.query(PartnerOrderReceipt).count() == 0


def test_receipt_is_idempotent_per_order(db):
    user = _make_user(db, "receipt-idempotent@test.ma")
    order = _make_order(db, user)
    create_partner_order_receipt(order.id, _payload(), db=db, current_user=user)

    with pytest.raises(HTTPException) as exc:
        create_partner_order_receipt(order.id, _payload(), db=db, current_user=user)

    assert exc.value.status_code == 409
    assert "deja ete receptionnee" in exc.value.detail
    assert db.query(PartnerOrderReceipt).filter(PartnerOrderReceipt.order_id == order.id).count() == 1


def test_receipt_is_scoped_to_current_cabinet(db):
    owner = _make_user(db, "receipt-owner@test.ma")
    outsider = _make_user(db, "receipt-outsider@test.ma")
    order = _make_order(db, owner)

    with pytest.raises(HTTPException) as exc:
        create_partner_order_receipt(order.id, _payload(), db=db, current_user=outsider)

    assert exc.value.status_code == 404
    assert db.query(PartnerOrderReceipt).count() == 0


def test_receipt_route_is_mounted_under_partner_orders(client, db):
    user = _make_user(db, "receipt-http@test.ma")
    order = _make_order(db, user)

    def _get_db():
        yield db

    app.dependency_overrides[database.get_db] = _get_db
    app.dependency_overrides[require_superadmin] = lambda: user
    try:
        response = client.post(
            f"/api/partner-orders/{order.id}/receipt",
            json={
                "lines": [
                    {"productId": "101", "quantityReceived": 2},
                    {"productId": "102", "quantityReceived": 1},
                ],
                "note": "HTTP receipt",
            },
        )
    finally:
        app.dependency_overrides.pop(database.get_db, None)
        app.dependency_overrides.pop(require_superadmin, None)

    assert response.status_code == 201, response.text
    assert response.json()["order"]["status"] == "FULFILLED"
    assert response.json()["receipt"]["orderId"] == order.id
