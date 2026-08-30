"""Marketplace P6 — accusé fournisseur, ETA et backorders canoniques."""

from datetime import datetime

import pytest
from fastapi import HTTPException

from backend import database, models
from backend.main import app
from backend.models_marketplace_procurement import PartnerOrderProcurement
from backend.models_marketplace_receipts import PartnerOrderReceipt
from backend.routers.auth import require_superadmin
from backend.routers.partner_procurement import (
    PartnerProcurementAckIn,
    acknowledge_partner_order_procurement,
)


def _make_user(db, email: str):
    user = models.User(
        email=email,
        hashed_password="test-only",
        role=models.UserRole.DENTISTE,
        nom_complet="Dr Procurement",
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
        order_number=f"PROC-{user.id}-{status.value}",
        partner_id="11",
        partner_name="Supplier Procurement",
        status=status,
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
                "quantity": 3,
                "unitPrice": 50.0,
                "lineTotal": 150.0,
            },
        ],
        estimated_total=300.0,
        sent_total=300.0,
        current_total=300.0,
        recognized_base_amount=300.0 if status == models.PartnerOrderStatus.CONFIRMED else 0.0,
        recognized_revenue_amount=30.0 if status == models.PartnerOrderStatus.CONFIRMED else 0.0,
        revenue_delta_amount=0.0,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def _payload(*, reference="SUP-REF-001", backorders=None, note="Accusé", eta=None):
    return PartnerProcurementAckIn(
        supplierReference=reference,
        expectedDeliveryAt=eta or datetime(2026, 9, 5, 12, 0, 0),
        backorderedLines=backorders or [{"productId": "102", "quantityBackordered": 2}],
        note=note,
    )


def _events(db, order_id):
    return (
        db.query(models.PartnerOrderEvent)
        .filter(models.PartnerOrderEvent.order_id == order_id)
        .order_by(models.PartnerOrderEvent.id.asc())
        .all()
    )


def test_supplier_ack_persists_reference_eta_backorder_and_audit(db):
    user = _make_user(db, "procurement-ack@test.ma")
    order = _make_order(db, user)

    result = acknowledge_partner_order_procurement(order.id, _payload(), db=db, current_user=user)

    assert result["idempotentReplay"] is False
    assert result["order"]["status"] == "CONFIRMED"
    assert result["order"]["partnerReference"] == "SUP-REF-001"
    assert result["procurement"]["supplierReference"] == "SUP-REF-001"
    assert result["procurement"]["expectedDeliveryAt"] == "2026-09-05T12:00:00"
    assert result["procurement"]["backorderedLines"] == [
        {
            "productId": "102",
            "name": "Produit B",
            "sku": "SKU-B",
            "quantityOrdered": 3,
            "quantityReceived": 0,
            "quantityOutstanding": 3,
            "quantityBackordered": 2,
        }
    ]
    event = _events(db, order.id)[0]
    assert event.event_type == "PROCUREMENT_ACKNOWLEDGED"
    assert event.previous_status == "CONFIRMED"
    assert event.new_status == "CONFIRMED"
    assert event.payload_json["partnerReference"] == "SUP-REF-001"


def test_exact_supplier_ack_replay_is_idempotent(db):
    user = _make_user(db, "procurement-replay@test.ma")
    order = _make_order(db, user)
    payload = _payload()

    first = acknowledge_partner_order_procurement(order.id, payload, db=db, current_user=user)
    replay = acknowledge_partner_order_procurement(order.id, payload, db=db, current_user=user)

    assert first["idempotentReplay"] is False
    assert replay["idempotentReplay"] is True
    assert replay["procurement"]["id"] == first["procurement"]["id"]
    assert db.query(PartnerOrderProcurement).filter(PartnerOrderProcurement.order_id == order.id).count() == 1
    assert len(_events(db, order.id)) == 1


def test_backorder_order_does_not_break_idempotence(db):
    user = _make_user(db, "procurement-order@test.ma")
    order = _make_order(db, user)
    first_payload = _payload(
        backorders=[
            {"productId": "102", "quantityBackordered": 2},
            {"productId": "101", "quantityBackordered": 1},
        ]
    )
    replay_payload = _payload(
        backorders=[
            {"productId": "101", "quantityBackordered": 1},
            {"productId": "102", "quantityBackordered": 2},
        ]
    )

    acknowledge_partner_order_procurement(order.id, first_payload, db=db, current_user=user)
    replay = acknowledge_partner_order_procurement(order.id, replay_payload, db=db, current_user=user)

    assert replay["idempotentReplay"] is True
    assert [line["productId"] for line in replay["procurement"]["backorderedLines"]] == ["101", "102"]
    assert len(_events(db, order.id)) == 1


def test_backorder_cannot_exceed_outstanding_after_partial_receipt(db):
    user = _make_user(db, "procurement-outstanding@test.ma")
    order = _make_order(db, user)
    receipt = PartnerOrderReceipt(
        employer_id=user.get_employer_id(),
        order_id=order.id,
        receipt_key="proc-partial-001",
        received_by_user_id=user.id,
        lines_json=[
            {
                "productId": "102",
                "name": "Produit B",
                "sku": "SKU-B",
                "quantityOrdered": 3,
                "quantityPreviouslyReceived": 0,
                "quantityReceived": 2,
                "unitPrice": 50.0,
                "lotNumber": None,
                "expiresAt": None,
            }
        ],
        note="Partiel",
    )
    db.add(receipt)
    db.commit()

    with pytest.raises(HTTPException) as exc:
        acknowledge_partner_order_procurement(
            order.id,
            _payload(backorders=[{"productId": "102", "quantityBackordered": 2}]),
            db=db,
            current_user=user,
        )

    assert exc.value.status_code == 422
    assert "reste 1" in exc.value.detail
    assert db.query(PartnerOrderProcurement).count() == 0


def test_duplicate_or_unknown_backorder_lines_are_rejected(db):
    user = _make_user(db, "procurement-lines@test.ma")
    order = _make_order(db, user)

    with pytest.raises(HTTPException) as duplicate:
        acknowledge_partner_order_procurement(
            order.id,
            _payload(
                backorders=[
                    {"productId": "101", "quantityBackordered": 1},
                    {"productId": "101", "quantityBackordered": 1},
                ]
            ),
            db=db,
            current_user=user,
        )
    assert duplicate.value.status_code == 422
    assert "duplique" in duplicate.value.detail

    with pytest.raises(HTTPException) as unknown:
        acknowledge_partner_order_procurement(
            order.id,
            _payload(backorders=[{"productId": "999", "quantityBackordered": 1}]),
            db=db,
            current_user=user,
        )
    assert unknown.value.status_code == 422
    assert "absent de la commande" in unknown.value.detail


def test_supplier_ack_requires_confirmed_order(db):
    user = _make_user(db, "procurement-status@test.ma")
    order = _make_order(db, user, status=models.PartnerOrderStatus.SENT_TO_PARTNER)

    with pytest.raises(HTTPException) as exc:
        acknowledge_partner_order_procurement(order.id, _payload(), db=db, current_user=user)

    assert exc.value.status_code == 422
    assert "CONFIRMED requis" in exc.value.detail
    assert db.query(PartnerOrderProcurement).count() == 0


def test_supplier_ack_is_tenant_scoped(db):
    owner = _make_user(db, "procurement-owner@test.ma")
    outsider = _make_user(db, "procurement-outsider@test.ma")
    order = _make_order(db, owner)

    with pytest.raises(HTTPException) as exc:
        acknowledge_partner_order_procurement(order.id, _payload(), db=db, current_user=outsider)

    assert exc.value.status_code == 404
    assert db.query(PartnerOrderProcurement).count() == 0


def test_http_procurement_put_and_get_are_mounted(client, db):
    user = _make_user(db, "procurement-http@test.ma")
    order = _make_order(db, user)

    def _get_db():
        yield db

    app.dependency_overrides[database.get_db] = _get_db
    app.dependency_overrides[require_superadmin] = lambda: user
    try:
        updated = client.put(
            f"/api/partner-orders/{order.id}/procurement",
            json={
                "supplierReference": "HTTP-REF-001",
                "expectedDeliveryAt": "2026-09-10T10:30:00",
                "backorderedLines": [{"productId": "101", "quantityBackordered": 1}],
                "note": "Retard fournisseur",
            },
        )
        loaded = client.get(f"/api/partner-orders/{order.id}/procurement")
    finally:
        app.dependency_overrides.pop(database.get_db, None)
        app.dependency_overrides.pop(require_superadmin, None)

    assert updated.status_code == 200, updated.text
    assert updated.json()["procurement"]["supplierReference"] == "HTTP-REF-001"
    assert loaded.status_code == 200, loaded.text
    assert loaded.json()["procurement"]["expectedDeliveryAt"] == "2026-09-10T10:30:00"
    assert loaded.json()["procurement"]["backorderedLines"][0]["quantityOutstanding"] == 2
