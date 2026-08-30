"""Marketplace P8 — vérité financière, facture fournisseur, rapprochement et reporting."""

import pytest
from fastapi import HTTPException

from backend import database, models
from backend.config import settings
from backend.main import app
from backend.models_marketplace_finance import PartnerSupplierInvoice
from backend.models_marketplace_receipts import PartnerOrderReceipt
from backend.routers.auth import require_superadmin
from backend.routers.partner_finance import (
    SupplierInvoiceIn,
    _expected_supplier_payable,
    _reconciliation,
    get_marketplace_finance_summary,
    record_supplier_invoice,
)


def _make_user(db, email: str):
    user = models.User(
        email=email,
        hashed_password="test-only",
        role=models.UserRole.DENTISTE,
        nom_complet="Dr Finance",
        is_active=True,
        is_licensed=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_order(
    db,
    user,
    *,
    suffix: str,
    revenue_model=models.PartnerRevenueModel.COMMISSION_PERCENT,
    status=models.PartnerOrderStatus.CONFIRMED,
    current_total: float = 200.0,
    recognized_revenue: float = 20.0,
    commission_rate: float = 10.0,
    discount_rate: float = 0.0,
    fixed_fee_amount: float = 0.0,
):
    order = models.PartnerOrder(
        employer_id=user.get_employer_id(),
        order_number=f"FIN-{user.id}-{suffix}",
        partner_id="supplier-finance",
        partner_name="Supplier Finance",
        status=status,
        settlement_basis=models.PartnerSettlementBasis.CONFIRMED,
        revenue_model=revenue_model,
        strategy_label="P8 finance test",
        commission_rate=commission_rate,
        discount_rate=discount_rate,
        fixed_fee_amount=fixed_fee_amount,
        customer_full_name="Acheteur Finance",
        customer_clinic="Cabinet Finance",
        customer_phone="0600000000",
        customer_email="finance@test.ma",
        customer_city="Rabat",
        lines_json=[
            {
                "productId": "101",
                "name": "Produit A",
                "sku": "SKU-A",
                "quantity": 2,
                "unitPrice": current_total / 2,
                "lineTotal": current_total,
            }
        ],
        estimated_total=current_total,
        sent_total=current_total,
        current_total=current_total,
        recognized_base_amount=current_total if recognized_revenue else 0.0,
        recognized_revenue_amount=recognized_revenue,
        revenue_delta_amount=0.0,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def _add_receipt(db, user, order, *, quantity: int = 2, key: str = "receipt-finance"):
    receipt = PartnerOrderReceipt(
        employer_id=user.get_employer_id(),
        order_id=order.id,
        receipt_key=key,
        received_by_user_id=user.id,
        lines_json=[{"productId": "101", "quantityReceived": quantity}],
        note="P8 receipt",
    )
    db.add(receipt)
    db.commit()
    db.refresh(receipt)
    return receipt


def _invoice(*, key="invoice-key-001", reference="INV-001", amount=200.0):
    return SupplierInvoiceIn(
        invoiceKey=key,
        invoiceReference=reference,
        amountTotal=amount,
        currency="MAD",
    )


def test_expected_supplier_payable_preserves_p2_revenue_models(db):
    user = _make_user(db, "finance-models@test.ma")
    commission = _make_order(
        db,
        user,
        suffix="commission",
        revenue_model=models.PartnerRevenueModel.COMMISSION_PERCENT,
        recognized_revenue=20.0,
        commission_rate=10.0,
    )
    discount = _make_order(
        db,
        user,
        suffix="discount",
        revenue_model=models.PartnerRevenueModel.DISCOUNT_RESALE,
        recognized_revenue=40.0,
        commission_rate=0.0,
        discount_rate=20.0,
    )
    fixed = _make_order(
        db,
        user,
        suffix="fixed",
        revenue_model=models.PartnerRevenueModel.FIXED_FEE_PER_ORDER,
        recognized_revenue=30.0,
        commission_rate=0.0,
        fixed_fee_amount=30.0,
    )

    assert _expected_supplier_payable(commission) == 200.0
    assert _expected_supplier_payable(discount) == 160.0
    assert _expected_supplier_payable(fixed) == 200.0
    assert commission.recognized_revenue_amount == 20.0
    assert discount.recognized_revenue_amount == 40.0
    assert fixed.recognized_revenue_amount == 30.0


def test_exact_invoice_plus_complete_receipt_is_matched(db):
    user = _make_user(db, "finance-match@test.ma")
    order = _make_order(db, user, suffix="match")
    _add_receipt(db, user, order)

    result = record_supplier_invoice(order.id, _invoice(), db=db, current_user=user)

    assert result["idempotentReplay"] is False
    reconciliation = result["reconciliation"]
    assert reconciliation["expectedSupplierPayable"] == 200.0
    assert reconciliation["invoicedAmount"] == 200.0
    assert reconciliation["invoiceVariance"] == 0.0
    assert reconciliation["receipt"]["fullyReceived"] is True
    assert reconciliation["reconciliationStatus"] == "MATCHED"
    event = (
        db.query(models.PartnerOrderEvent)
        .filter(models.PartnerOrderEvent.order_id == order.id)
        .one()
    )
    assert event.event_type == "SUPPLIER_INVOICE_RECORDED"
    assert event.payload_json["amountTotal"] == 200.0


def test_exact_invoice_waits_for_complete_receipt(db):
    user = _make_user(db, "finance-partial@test.ma")
    order = _make_order(db, user, suffix="partial")
    _add_receipt(db, user, order, quantity=1)

    result = record_supplier_invoice(order.id, _invoice(), db=db, current_user=user)

    assert result["reconciliation"]["reconciliationStatus"] == "WAITING_RECEIPT"
    assert result["reconciliation"]["receipt"]["receivedRatio"] == 0.5


def test_wrong_invoice_amount_is_reported_as_mismatch(db):
    user = _make_user(db, "finance-mismatch@test.ma")
    order = _make_order(db, user, suffix="mismatch")
    _add_receipt(db, user, order)

    result = record_supplier_invoice(order.id, _invoice(amount=175.0), db=db, current_user=user)

    assert result["reconciliation"]["reconciliationStatus"] == "AMOUNT_MISMATCH"
    assert result["reconciliation"]["invoiceVariance"] == -25.0


def test_missing_invoice_and_cancelled_order_have_deterministic_statuses(db):
    user = _make_user(db, "finance-statuses@test.ma")
    waiting = _make_order(db, user, suffix="waiting")
    cancelled = _make_order(
        db,
        user,
        suffix="cancelled",
        status=models.PartnerOrderStatus.CANCELLED,
        recognized_revenue=0.0,
    )

    waiting_result = _reconciliation(db, waiting)
    cancelled_result = _reconciliation(db, cancelled)

    assert waiting_result["reconciliationStatus"] == "WAITING_INVOICE"
    assert cancelled_result["reconciliationStatus"] == "CANCELLED"
    assert cancelled_result["expectedSupplierPayable"] == 0.0
    assert cancelled_result["recognizedRevenueAmount"] == 0.0


def test_supplier_invoice_replay_is_idempotent_and_conflicts_are_rejected(db):
    user = _make_user(db, "finance-idempotence@test.ma")
    order = _make_order(db, user, suffix="idempotence")
    payload = _invoice(key="invoice-key-replay", reference="INV-REPLAY")

    first = record_supplier_invoice(order.id, payload, db=db, current_user=user)
    replay = record_supplier_invoice(order.id, payload, db=db, current_user=user)

    assert first["idempotentReplay"] is False
    assert replay["idempotentReplay"] is True
    assert replay["invoice"]["id"] == first["invoice"]["id"]
    assert db.query(PartnerSupplierInvoice).filter(PartnerSupplierInvoice.order_id == order.id).count() == 1
    assert db.query(models.PartnerOrderEvent).filter(models.PartnerOrderEvent.order_id == order.id).count() == 1

    with pytest.raises(HTTPException) as changed_payload:
        record_supplier_invoice(
            order.id,
            _invoice(key="invoice-key-replay", reference="INV-REPLAY", amount=199.0),
            db=db,
            current_user=user,
        )
    assert changed_payload.value.status_code == 409

    with pytest.raises(HTTPException) as duplicate_reference:
        record_supplier_invoice(
            order.id,
            _invoice(key="invoice-key-other", reference="INV-REPLAY", amount=200.0),
            db=db,
            current_user=user,
        )
    assert duplicate_reference.value.status_code == 409


def test_invoice_rejects_draft_cancelled_and_non_mad(db):
    user = _make_user(db, "finance-rejections@test.ma")
    draft = _make_order(db, user, suffix="draft", status=models.PartnerOrderStatus.DRAFT, recognized_revenue=0.0)
    cancelled = _make_order(db, user, suffix="cancel", status=models.PartnerOrderStatus.CANCELLED, recognized_revenue=0.0)
    confirmed = _make_order(db, user, suffix="currency")

    for order in (draft, cancelled):
        with pytest.raises(HTTPException) as exc:
            record_supplier_invoice(order.id, _invoice(), db=db, current_user=user)
        assert exc.value.status_code == 409

    with pytest.raises(HTTPException) as currency_exc:
        record_supplier_invoice(
            confirmed.id,
            SupplierInvoiceIn(
                invoiceKey="invoice-key-eur",
                invoiceReference="INV-EUR",
                amountTotal=200.0,
                currency="EUR",
            ),
            db=db,
            current_user=user,
        )
    assert currency_exc.value.status_code == 422


def test_summary_is_tenant_scoped_and_aggregates_financial_truth(db):
    owner = _make_user(db, "finance-owner@test.ma")
    outsider = _make_user(db, "finance-outsider@test.ma")
    matched = _make_order(db, owner, suffix="summary-match", recognized_revenue=20.0)
    _add_receipt(db, owner, matched, key="receipt-summary")
    record_supplier_invoice(matched.id, _invoice(key="invoice-summary", reference="INV-SUMMARY"), db=db, current_user=owner)
    _make_order(db, owner, suffix="summary-wait", recognized_revenue=10.0, current_total=100.0)
    _make_order(db, outsider, suffix="outsider", recognized_revenue=999.0, current_total=9999.0)

    summary = get_marketplace_finance_summary(includeCancelled=True, db=db, current_user=owner)

    assert summary["ordersCount"] == 2
    assert summary["matchedCount"] == 1
    assert summary["waitingInvoiceCount"] == 1
    assert summary["recognizedRevenueAmount"] == 30.0
    assert summary["currentOrderAmount"] == 300.0
    assert all(row["orderNumber"].startswith(f"FIN-{owner.id}-") for row in summary["orders"])


def test_http_finance_routes_are_mounted_and_superadmin_only(client, db, monkeypatch):
    superadmin_email = "finance-superadmin@test.ma"
    monkeypatch.setattr(settings, "SUPERADMIN_EMAIL", superadmin_email)
    superadmin = _make_user(db, superadmin_email)
    regular = _make_user(db, "finance-regular@test.ma")
    order = _make_order(db, superadmin, suffix="http")

    def _get_db():
        yield db

    app.dependency_overrides[database.get_db] = _get_db
    app.dependency_overrides[require_superadmin] = lambda: superadmin
    try:
        response = client.get(f"/api/partner-orders/finance/orders/{order.id}/reconciliation")
    finally:
        app.dependency_overrides.pop(database.get_db, None)
        app.dependency_overrides.pop(require_superadmin, None)

    assert response.status_code == 200, response.text
    assert response.json()["orderId"] == order.id

    # Vérification RBAC réelle avec la dépendance canonique : l'utilisateur régulier
    # ne doit pas pouvoir lire le reporting financier Superadmin.
    from backend.security import get_password_hash

    superadmin.hashed_password = get_password_hash("TestPass123!")
    regular.hashed_password = get_password_hash("TestPass123!")
    db.commit()

    regular_login = client.post(
        "/api/auth/login",
        data={"username": regular.email, "password": "TestPass123!"},
    )
    assert regular_login.status_code == 200, regular_login.text
    regular_headers = {"Authorization": f"Bearer {regular_login.json()['access_token']}"}
    forbidden = client.get("/api/partner-orders/finance/summary", headers=regular_headers)
    assert forbidden.status_code == 403, forbidden.text
