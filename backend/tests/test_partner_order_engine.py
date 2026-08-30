"""Marketplace P2 — machine d'état et vérité financière des commandes partenaire."""

import pytest
from fastapi import HTTPException

from backend import models
from backend.routers.partner_orders import (
    PartnerOrderCreateIn,
    PartnerOrderUpdateIn,
    create_partner_order,
    get_partner_order_meta,
    update_partner_order,
)


def _make_user(db, email: str = "marketplace-p2@test.ma"):
    user = models.User(
        email=email,
        hashed_password="test-only",
        role=models.UserRole.DENTISTE,
        nom_complet="Dr Marketplace P2",
        is_active=True,
        is_licensed=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_supplier(db, user, *, name: str = "Supplier P2"):
    supplier = models.PartnerSupplier(
        employer_id=user.get_employer_id(),
        supplier_key=name.lower().replace(" ", "-"),
        name=name,
        is_active=True,
        sync_mode="manual",
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


def _make_product(db, user, supplier, *, price: float = 100.0):
    product = models.PartnerCatalogProduct(
        employer_id=user.get_employer_id(),
        supplier_id=supplier.id,
        name="Produit P2",
        sku="P2-001",
        dental_category="Consommables",
        dental_specialty="Omnipratique",
        unit="boite",
        price=price,
        availability=models.PartnerProductAvailability.AVAILABLE,
        benefits_json=[],
        is_featured=False,
        sort_order=0,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def _payload(product, *, quantity: int = 1):
    return PartnerOrderCreateIn(
        partnerId="client-value-ignored",
        partnerName="client-value-ignored",
        strategyLabel="client-value-ignored",
        settlementBasis="SENT_TO_PARTNER",
        revenueModel="COMMISSION_PERCENT",
        commissionRate=10.0,
        discountRate=0.0,
        fixedFeeAmount=0.0,
        customer={
            "fullName": "Acheteur P2",
            "clinic": "Cabinet P2",
            "phone": "0600000000",
            "email": "buyer-p2@test.ma",
            "city": "Rabat",
            "note": "p2",
        },
        lines=[
            {
                "productId": str(product.id),
                "name": "client-value-ignored",
                "sku": "client-value-ignored",
                "quantity": quantity,
                "unitPrice": 0.01,
                "lineTotal": 0.01,
            }
        ],
        estimatedTotal=0.01,
    )


def _create_order(db, user, *, price: float = 100.0):
    supplier = _make_supplier(db, user)
    product = _make_product(db, user, supplier, price=price)
    return create_partner_order(_payload(product), db=db, current_user=user)


def _update(db, user, order_id: int, status: str, *, current_total=None, partner_reference=None, note=None):
    return update_partner_order(
        order_id,
        PartnerOrderUpdateIn(
            status=status,
            currentTotal=current_total,
            partnerReference=partner_reference,
            note=note,
        ),
        db=db,
        current_user=user,
    )


def test_draft_exposes_only_send_or_cancel_and_rejects_direct_confirmation(db):
    user = _make_user(db)
    order = _create_order(db, user)

    assert order["status"] == "DRAFT"
    assert order["allowedTransitions"] == ["SENT_TO_PARTNER", "CANCELLED"]

    with pytest.raises(HTTPException) as exc:
        _update(db, user, order["id"], "CONFIRMED", current_total=order["currentTotal"])

    assert exc.value.status_code == 422
    assert "DRAFT -> CONFIRMED" in exc.value.detail


def test_send_snapshots_total_and_recognizes_sent_basis_revenue(db):
    user = _make_user(db)
    order = _create_order(db, user, price=125.5)

    sent = _update(
        db,
        user,
        order["id"],
        "SENT_TO_PARTNER",
        current_total=125.5,
        partner_reference="SUP-REF-1",
    )

    assert sent["status"] == "SENT_TO_PARTNER"
    assert sent["sentTotal"] == 125.5
    assert sent["currentTotal"] == 125.5
    assert sent["recognizedBaseAmount"] == 125.5
    assert sent["recognizedRevenueAmount"] == 12.55
    assert sent["partnerReference"] == "SUP-REF-1"
    assert sent["sentAt"] is not None


def test_modified_total_persists_through_confirmation_and_fulfillment(db):
    user = _make_user(db)
    order = _create_order(db, user, price=100.0)
    sent = _update(db, user, order["id"], "SENT_TO_PARTNER", current_total=100.0)

    modified = _update(db, user, sent["id"], "MODIFIED_AFTER_SEND", current_total=150.0, note="supplier adjustment")
    assert modified["sentTotal"] == 100.0
    assert modified["currentTotal"] == 150.0
    assert modified["recognizedBaseAmount"] == 150.0
    assert modified["recognizedRevenueAmount"] == 15.0

    confirmed = _update(db, user, modified["id"], "CONFIRMED", current_total=150.0)
    assert confirmed["recognizedBaseAmount"] == 150.0
    assert confirmed["recognizedRevenueAmount"] == 15.0
    assert confirmed["allowedTransitions"] == ["FULFILLED", "CANCELLED"]

    fulfilled = _update(db, user, confirmed["id"], "FULFILLED", current_total=150.0)
    assert fulfilled["recognizedBaseAmount"] == 150.0
    assert fulfilled["recognizedRevenueAmount"] == 15.0
    assert fulfilled["allowedTransitions"] == []


def test_total_change_is_rejected_outside_modified_after_send(db):
    user = _make_user(db)
    order = _create_order(db, user, price=100.0)
    sent = _update(db, user, order["id"], "SENT_TO_PARTNER", current_total=100.0)

    with pytest.raises(HTTPException) as exc:
        _update(db, user, sent["id"], "CONFIRMED", current_total=110.0)

    assert exc.value.status_code == 422
    assert "currentTotal ne peut changer" in exc.value.detail


def test_modified_after_send_requires_a_real_total_change(db):
    user = _make_user(db)
    order = _create_order(db, user, price=100.0)
    sent = _update(db, user, order["id"], "SENT_TO_PARTNER", current_total=100.0)

    with pytest.raises(HTTPException) as missing_total_exc:
        _update(db, user, sent["id"], "MODIFIED_AFTER_SEND")
    assert missing_total_exc.value.status_code == 422
    assert "currentTotal est requis" in missing_total_exc.value.detail

    with pytest.raises(HTTPException) as unchanged_total_exc:
        _update(db, user, sent["id"], "MODIFIED_AFTER_SEND", current_total=100.0)
    assert unchanged_total_exc.value.status_code == 422
    assert "doit differer" in unchanged_total_exc.value.detail


def test_cancelled_and_fulfilled_orders_are_terminal(db):
    user = _make_user(db)
    cancelled_order = _create_order(db, user, price=80.0)
    cancelled = _update(db, user, cancelled_order["id"], "CANCELLED", current_total=80.0)
    assert cancelled["allowedTransitions"] == []

    with pytest.raises(HTTPException) as cancelled_exc:
        _update(db, user, cancelled["id"], "SENT_TO_PARTNER", current_total=80.0)
    assert cancelled_exc.value.status_code == 422

    second_user = _make_user(db, "marketplace-p2-terminal@test.ma")
    fulfilled_order = _create_order(db, second_user, price=90.0)
    sent = _update(db, second_user, fulfilled_order["id"], "SENT_TO_PARTNER", current_total=90.0)
    confirmed = _update(db, second_user, sent["id"], "CONFIRMED", current_total=90.0)
    fulfilled = _update(db, second_user, confirmed["id"], "FULFILLED", current_total=90.0)

    with pytest.raises(HTTPException) as fulfilled_exc:
        _update(db, second_user, fulfilled["id"], "CANCELLED", current_total=90.0)
    assert fulfilled_exc.value.status_code == 422


def test_cancellation_reverses_recognized_revenue_and_records_negative_delta(db):
    user = _make_user(db)
    order = _create_order(db, user, price=200.0)
    sent = _update(db, user, order["id"], "SENT_TO_PARTNER", current_total=200.0)
    assert sent["recognizedRevenueAmount"] == 20.0

    cancelled = _update(db, user, sent["id"], "CANCELLED", current_total=200.0, note="supplier cancelled")

    assert cancelled["recognizedBaseAmount"] == 0.0
    assert cancelled["recognizedRevenueAmount"] == 0.0
    assert cancelled["revenueDeltaAmount"] == -20.0
    latest_event = (
        db.query(models.PartnerOrderEvent)
        .filter(models.PartnerOrderEvent.order_id == order["id"])
        .order_by(models.PartnerOrderEvent.id.desc())
        .first()
    )
    assert latest_event is not None
    assert latest_event.previous_status == "SENT_TO_PARTNER"
    assert latest_event.new_status == "CANCELLED"
    assert latest_event.revenue_before == 20.0
    assert latest_event.revenue_after == 0.0
    assert latest_event.delta_amount == -20.0


def test_order_event_history_tracks_each_accepted_transition(db):
    user = _make_user(db)
    order = _create_order(db, user, price=100.0)
    sent = _update(db, user, order["id"], "SENT_TO_PARTNER", current_total=100.0)
    modified = _update(db, user, sent["id"], "MODIFIED_AFTER_SEND", current_total=120.0, note="price update")
    _update(db, user, modified["id"], "CONFIRMED", current_total=120.0, partner_reference="REF-120")

    events = (
        db.query(models.PartnerOrderEvent)
        .filter(models.PartnerOrderEvent.order_id == order["id"])
        .order_by(models.PartnerOrderEvent.id.asc())
        .all()
    )
    assert [(event.previous_status, event.new_status) for event in events] == [
        (None, "DRAFT"),
        ("DRAFT", "SENT_TO_PARTNER"),
        ("SENT_TO_PARTNER", "MODIFIED_AFTER_SEND"),
        ("MODIFIED_AFTER_SEND", "CONFIRMED"),
    ]
    assert events[-1].payload_json == {"partnerReference": "REF-120"}


def test_meta_exposes_server_transition_contract(db):
    user = _make_user(db)
    meta = get_partner_order_meta(current_user=user)

    assert meta["allowedTransitions"] == {
        "DRAFT": ["SENT_TO_PARTNER", "CANCELLED"],
        "SENT_TO_PARTNER": ["MODIFIED_AFTER_SEND", "CONFIRMED", "CANCELLED"],
        "MODIFIED_AFTER_SEND": ["MODIFIED_AFTER_SEND", "CONFIRMED", "CANCELLED"],
        "CONFIRMED": ["FULFILLED", "CANCELLED"],
        "FULFILLED": [],
        "CANCELLED": [],
    }
