"""P6 — cas limites d'idempotence des réceptions Marketplace."""

import pytest
from fastapi import HTTPException

from backend import models
from backend.routers.partner_receipts import PartnerReceiptCreateIn, create_partner_order_receipt


def _make_user(db, email: str):
    user = models.User(
        email=email,
        hashed_password="test-only",
        role=models.UserRole.DENTISTE,
        nom_complet="Dr Receipt Hardening",
        is_active=True,
        is_licensed=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_order(db, user):
    order = models.PartnerOrder(
        employer_id=user.get_employer_id(),
        order_number=f"RECEIPT-HARD-{user.id}",
        partner_id="11",
        partner_name="Supplier Receipt",
        status=models.PartnerOrderStatus.CONFIRMED,
        settlement_basis=models.PartnerSettlementBasis.CONFIRMED,
        revenue_model=models.PartnerRevenueModel.COMMISSION_PERCENT,
        strategy_label="Commission",
        commission_rate=10.0,
        discount_rate=0.0,
        fixed_fee_amount=0.0,
        customer_full_name="Acheteur",
        customer_clinic="Cabinet",
        customer_phone="0600000000",
        customer_email="buyer@test.ma",
        customer_city="Rabat",
        lines_json=[{
            "productId": "101",
            "name": "Produit A",
            "sku": "SKU-A",
            "quantity": 2,
            "unitPrice": 75.0,
            "lineTotal": 150.0,
        }],
        estimated_total=150.0,
        sent_total=150.0,
        current_total=150.0,
        recognized_base_amount=150.0,
        recognized_revenue_amount=15.0,
        revenue_delta_amount=0.0,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def test_whitespace_only_idempotency_key_is_rejected_after_normalization(db):
    user = _make_user(db, "receipt-key-space@test.ma")
    order = _make_order(db, user)
    payload = PartnerReceiptCreateIn(
        idempotencyKey="        ",
        lines=[{"productId": "101", "quantityReceived": 1}],
    )

    with pytest.raises(HTTPException) as exc:
        create_partner_order_receipt(order.id, payload, db=db, current_user=user)

    assert exc.value.status_code == 422
    assert "8 caracteres utiles" in exc.value.detail


def test_duplicate_lines_cannot_masquer_a_conflicting_idempotent_replay(db):
    user = _make_user(db, "receipt-key-duplicate@test.ma")
    order = _make_order(db, user)
    initial = PartnerReceiptCreateIn(
        idempotencyKey="duplicate-001",
        lines=[{"productId": "101", "quantityReceived": 1}],
    )
    create_partner_order_receipt(order.id, initial, db=db, current_user=user)

    duplicate_replay = PartnerReceiptCreateIn(
        idempotencyKey="duplicate-001",
        lines=[
            {"productId": "101", "quantityReceived": 1},
            {"productId": "101", "quantityReceived": 1},
        ],
    )
    with pytest.raises(HTTPException) as exc:
        create_partner_order_receipt(order.id, duplicate_replay, db=db, current_user=user)

    assert exc.value.status_code == 409
    assert "contenu different" in exc.value.detail
