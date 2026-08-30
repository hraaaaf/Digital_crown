"""Marketplace P6 — réception partielle, idempotence et réconciliation commande ↔ réception."""

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


def _payload(
    key="receipt-001",
    *,
    quantity_a=2,
    include_a=True,
    quantity_b=1,
    include_b=True,
    note="Réception",
):
    lines = []
    if include_a:
        lines.append(
            {
                "productId": "101",
                "quantityReceived": quantity_a,
                "lotNumber": "LOT-A",
                "expiresAt": "2028-12-31T00:00:00",
            }
        )
    if include_b:
        lines.append({"productId": "102", "quantityReceived": quantity_b})
    return PartnerReceiptCreateIn(idempotencyKey=key, lines=lines, note=note)


def _events(db, order_id):
    return (
        db.query(models.PartnerOrderEvent)
        .filter(models.PartnerOrderEvent.order_id == order_id)
        .order_by(models.PartnerOrderEvent.id.asc())
        .all()
    )


def test_full_receipt_fulfills_order_and_records_complete_audit(db):
    user = _make_user(db, "receipt-full@test.ma")
    order = _make_order(db, user)

    result = create_partner_order_receipt(order.id, _payload(), db=db, current_user=user)

    assert result["idempotentReplay"] is False
    assert result["order"]["status"] == "FULFILLED"
    assert result["order"]["recognizedBaseAmount"] == 200.0
    assert result["order"]["recognizedRevenueAmount"] == 20.0
    assert result["progress"]["isComplete"] is True
    assert result["progress"]["receiptCount"] == 1
    assert all(line["quantityOutstanding"] == 0 for line in result["progress"]["lines"])
    assert result["receipt"]["idempotencyKey"] == "receipt-001"
    assert result["receipt"]["lines"][0]["quantityPreviouslyReceived"] == 0

    event = _events(db, order.id)[0]
    assert event.event_type == "RECEIPT_COMPLETED"
    assert event.previous_status == "CONFIRMED"
    assert event.new_status == "FULFILLED"
    assert event.payload_json["isComplete"] is True


def test_partial_then_complete_receipts_reconcile_cumulatively(db):
    user = _make_user(db, "receipt-partial@test.ma")
    order = _make_order(db, user)

    first = create_partner_order_receipt(
        order.id,
        _payload("partial-001", quantity_a=1, include_b=False, note="Premier colis"),
        db=db,
        current_user=user,
    )

    assert first["order"]["status"] == "CONFIRMED"
    assert first["progress"]["isComplete"] is False
    progress_by_product = {line["productId"]: line for line in first["progress"]["lines"]}
    assert progress_by_product["101"]["quantityReceived"] == 1
    assert progress_by_product["101"]["quantityOutstanding"] == 1
    assert progress_by_product["102"]["quantityOutstanding"] == 1
    assert _events(db, order.id)[0].event_type == "RECEIPT_PARTIAL_RECORDED"

    second = create_partner_order_receipt(
        order.id,
        _payload("partial-002", quantity_a=1, quantity_b=1, note="Solde"),
        db=db,
        current_user=user,
    )

    assert second["order"]["status"] == "FULFILLED"
    assert second["progress"]["isComplete"] is True
    assert second["progress"]["receiptCount"] == 2
    assert second["receipt"]["lines"][0]["quantityPreviouslyReceived"] == 1
    assert [event.event_type for event in _events(db, order.id)] == [
        "RECEIPT_PARTIAL_RECORDED",
        "RECEIPT_COMPLETED",
    ]


def test_over_receipt_is_rejected_without_mutating_progress(db):
    user = _make_user(db, "receipt-over@test.ma")
    order = _make_order(db, user)
    create_partner_order_receipt(
        order.id,
        _payload("over-001", quantity_a=1, include_b=False),
        db=db,
        current_user=user,
    )

    with pytest.raises(HTTPException) as exc:
        create_partner_order_receipt(
            order.id,
            _payload("over-002", quantity_a=2, include_b=False),
            db=db,
            current_user=user,
        )

    assert exc.value.status_code == 422
    assert "Sur-reception interdite" in exc.value.detail
    db.refresh(order)
    assert order.status == models.PartnerOrderStatus.CONFIRMED
    assert db.query(PartnerOrderReceipt).filter(PartnerOrderReceipt.order_id == order.id).count() == 1


def test_receipt_rejects_product_absent_from_order(db):
    user = _make_user(db, "receipt-product@test.ma")
    order = _make_order(db, user)
    payload = PartnerReceiptCreateIn(
        idempotencyKey="unknown-001",
        lines=[{"productId": "999", "quantityReceived": 1}],
    )

    with pytest.raises(HTTPException) as exc:
        create_partner_order_receipt(order.id, payload, db=db, current_user=user)

    assert exc.value.status_code == 422
    assert "Produit absent de la commande" in exc.value.detail
    assert db.query(PartnerOrderReceipt).count() == 0


def test_exact_replay_is_idempotent_and_does_not_duplicate_event(db):
    user = _make_user(db, "receipt-replay@test.ma")
    order = _make_order(db, user)
    payload = _payload("replay-001", quantity_a=1, include_b=False, note="Colis A")

    first = create_partner_order_receipt(order.id, payload, db=db, current_user=user)
    replay = create_partner_order_receipt(order.id, payload, db=db, current_user=user)

    assert first["idempotentReplay"] is False
    assert replay["idempotentReplay"] is True
    assert replay["receipt"]["id"] == first["receipt"]["id"]
    assert db.query(PartnerOrderReceipt).filter(PartnerOrderReceipt.order_id == order.id).count() == 1
    assert len(_events(db, order.id)) == 1


def test_same_idempotency_key_with_different_content_is_rejected(db):
    user = _make_user(db, "receipt-conflict@test.ma")
    order = _make_order(db, user)
    create_partner_order_receipt(
        order.id,
        _payload("conflict-001", quantity_a=1, include_b=False),
        db=db,
        current_user=user,
    )

    with pytest.raises(HTTPException) as exc:
        create_partner_order_receipt(
            order.id,
            _payload("conflict-001", quantity_a=1, include_b=False, note="Autre contenu"),
            db=db,
            current_user=user,
        )

    assert exc.value.status_code == 409
    assert "Cle d'idempotence" in exc.value.detail
    assert len(_events(db, order.id)) == 1


def test_new_receipt_requires_confirmed_order(db):
    user = _make_user(db, "receipt-status@test.ma")
    order = _make_order(db, user, status=models.PartnerOrderStatus.SENT_TO_PARTNER)

    with pytest.raises(HTTPException) as exc:
        create_partner_order_receipt(order.id, _payload("status-001"), db=db, current_user=user)

    assert exc.value.status_code == 422
    assert "CONFIRMED requis" in exc.value.detail
    assert db.query(PartnerOrderReceipt).count() == 0


def test_receipt_is_scoped_to_current_cabinet(db):
    owner = _make_user(db, "receipt-owner@test.ma")
    outsider = _make_user(db, "receipt-outsider@test.ma")
    order = _make_order(db, owner)

    with pytest.raises(HTTPException) as exc:
        create_partner_order_receipt(order.id, _payload("scope-001"), db=db, current_user=outsider)

    assert exc.value.status_code == 404
    assert db.query(PartnerOrderReceipt).count() == 0


def test_http_receipt_routes_expose_partial_progress(client, db):
    user = _make_user(db, "receipt-http@test.ma")
    order = _make_order(db, user)

    def _get_db():
        yield db

    app.dependency_overrides[database.get_db] = _get_db
    app.dependency_overrides[require_superadmin] = lambda: user
    try:
        created = client.post(
            f"/api/partner-orders/{order.id}/receipt",
            json={
                "idempotencyKey": "http-partial-001",
                "lines": [{"productId": "101", "quantityReceived": 1}],
                "note": "HTTP partial",
            },
        )
        summary = client.get(f"/api/partner-orders/{order.id}/receipts")
    finally:
        app.dependency_overrides.pop(database.get_db, None)
        app.dependency_overrides.pop(require_superadmin, None)

    assert created.status_code == 201, created.text
    assert created.json()["order"]["status"] == "CONFIRMED"
    assert created.json()["progress"]["isComplete"] is False
    assert summary.status_code == 200, summary.text
    assert summary.json()["progress"]["receiptCount"] == 1
    progress = {line["productId"]: line for line in summary.json()["progress"]["lines"]}
    assert progress["101"]["quantityOutstanding"] == 1
    assert progress["102"]["quantityOutstanding"] == 1
