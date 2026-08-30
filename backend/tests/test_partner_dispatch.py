"""Marketplace P6 — transport fournisseur prouvé et idempotent."""

import pytest
from fastapi import HTTPException

from backend import database, models
from backend.main import app
from backend.models_marketplace_dispatch import PartnerOrderDispatch
from backend.routers.auth import require_superadmin
from backend.routers import partner_dispatch


def _make_user(db, email: str):
    user = models.User(
        email=email,
        hashed_password="test-only",
        role=models.UserRole.DENTISTE,
        nom_complet="Dr Dispatch",
        is_active=True,
        is_licensed=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_supplier(db, user, *, mode="api", api_base_url="https://supplier.example/api", active=True):
    supplier = models.PartnerSupplier(
        employer_id=user.get_employer_id(),
        supplier_key=f"dispatch-{user.id}",
        name="Supplier Dispatch",
        api_base_url=api_base_url,
        sync_mode=mode,
        is_active=active,
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


def _make_order(db, user, supplier, *, status=models.PartnerOrderStatus.DRAFT):
    order = models.PartnerOrder(
        employer_id=user.get_employer_id(),
        order_number=f"DISPATCH-{user.id}",
        partner_id=str(supplier.id),
        partner_name=supplier.name,
        status=status,
        settlement_basis=models.PartnerSettlementBasis.SENT_TO_PARTNER,
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
        customer_note="Livrer matin",
        lines_json=[
            {
                "productId": "101",
                "name": "Produit A",
                "sku": "SKU-A",
                "quantity": 2,
                "unitPrice": 75.0,
                "lineTotal": 150.0,
            }
        ],
        estimated_total=150.0,
        sent_total=0.0,
        current_total=150.0,
        recognized_base_amount=0.0,
        recognized_revenue_amount=0.0,
        revenue_delta_amount=0.0,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def test_successful_dispatch_transitions_order_and_records_minimal_evidence(db, monkeypatch):
    user = _make_user(db, "dispatch-success@test.ma")
    supplier = _make_supplier(db, user)
    order = _make_order(db, user, supplier)
    captured = {}

    def fake_post(endpoint, payload, idempotency_key):
        captured.update(endpoint=endpoint, payload=payload, idempotency_key=idempotency_key)
        return 201, "SUP-ORDER-001"

    monkeypatch.setattr(partner_dispatch, "_post_supplier_order", fake_post)
    result = partner_dispatch.dispatch_partner_order(order.id, db=db, current_user=user)

    assert result["idempotentReplay"] is False
    assert result["order"]["status"] == "SENT_TO_PARTNER"
    assert result["order"]["partnerReference"] == "SUP-ORDER-001"
    assert result["order"]["sentTotal"] == 150.0
    assert result["order"]["recognizedRevenueAmount"] == 15.0
    assert result["dispatch"]["outcome"] == "SUCCEEDED"
    assert result["dispatch"]["attemptCount"] == 1
    assert captured["endpoint"] == "https://supplier.example/api/orders"
    assert captured["idempotency_key"] == f"digitalcrown:{order.order_number}"
    assert captured["payload"]["total"] == 150.0
    assert captured["payload"]["currency"] == "MAD"
    assert "commissionRate" not in captured["payload"]

    evidence = db.query(PartnerOrderDispatch).filter(PartnerOrderDispatch.order_id == order.id).one()
    assert len(evidence.request_sha256) == 64
    event = (
        db.query(models.PartnerOrderEvent)
        .filter(models.PartnerOrderEvent.order_id == order.id)
        .order_by(models.PartnerOrderEvent.id.desc())
        .first()
    )
    assert event.event_type == "ORDER_DISPATCHED"
    assert event.payload_json["dispatchId"] == evidence.id
    assert event.payload_json["supplierReference"] == "SUP-ORDER-001"


def test_failed_transport_keeps_order_draft_and_persists_failure_evidence(db, monkeypatch):
    user = _make_user(db, "dispatch-failure@test.ma")
    supplier = _make_supplier(db, user)
    order = _make_order(db, user, supplier)

    def fake_post(*_args, **_kwargs):
        raise partner_dispatch.SupplierDispatchError("TIMEOUT", "Delai d'envoi fournisseur depasse.")

    monkeypatch.setattr(partner_dispatch, "_post_supplier_order", fake_post)
    with pytest.raises(HTTPException) as exc:
        partner_dispatch.dispatch_partner_order(order.id, db=db, current_user=user)

    assert exc.value.status_code == 502
    db.refresh(order)
    assert order.status == models.PartnerOrderStatus.DRAFT
    evidence = db.query(PartnerOrderDispatch).filter(PartnerOrderDispatch.order_id == order.id).one()
    assert evidence.outcome == "FAILED"
    assert evidence.attempt_count == 1
    assert evidence.error_code == "TIMEOUT"
    assert db.query(models.PartnerOrderEvent).filter(models.PartnerOrderEvent.order_id == order.id).count() == 0


def test_retry_reuses_same_idempotency_record_then_succeeds(db, monkeypatch):
    user = _make_user(db, "dispatch-retry@test.ma")
    supplier = _make_supplier(db, user)
    order = _make_order(db, user, supplier)
    calls = []

    def fake_post(_endpoint, _payload, idempotency_key):
        calls.append(idempotency_key)
        if len(calls) == 1:
            raise partner_dispatch.SupplierDispatchError("NETWORK_ERROR", "Connexion API fournisseur impossible.")
        return 200, "SUP-RETRY-001"

    monkeypatch.setattr(partner_dispatch, "_post_supplier_order", fake_post)
    with pytest.raises(HTTPException):
        partner_dispatch.dispatch_partner_order(order.id, db=db, current_user=user)
    result = partner_dispatch.dispatch_partner_order(order.id, db=db, current_user=user)

    assert result["order"]["status"] == "SENT_TO_PARTNER"
    assert result["dispatch"]["attemptCount"] == 2
    assert calls == [f"digitalcrown:{order.order_number}", f"digitalcrown:{order.order_number}"]
    assert db.query(PartnerOrderDispatch).filter(PartnerOrderDispatch.order_id == order.id).count() == 1


def test_success_replay_never_calls_supplier_twice(db, monkeypatch):
    user = _make_user(db, "dispatch-replay@test.ma")
    supplier = _make_supplier(db, user)
    order = _make_order(db, user, supplier)
    calls = {"count": 0}

    def first_post(*_args, **_kwargs):
        calls["count"] += 1
        return 201, "SUP-IDEMP-001"

    monkeypatch.setattr(partner_dispatch, "_post_supplier_order", first_post)
    first = partner_dispatch.dispatch_partner_order(order.id, db=db, current_user=user)
    replay = partner_dispatch.dispatch_partner_order(order.id, db=db, current_user=user)

    assert first["idempotentReplay"] is False
    assert replay["idempotentReplay"] is True
    assert replay["dispatch"]["id"] == first["dispatch"]["id"]
    assert calls["count"] == 1


def test_dispatch_requires_active_api_supplier_with_https_public_destination(db):
    user = _make_user(db, "dispatch-config@test.ma")
    manual = _make_supplier(db, user, mode="manual")
    order = _make_order(db, user, manual)

    with pytest.raises(HTTPException) as mode_exc:
        partner_dispatch.dispatch_partner_order(order.id, db=db, current_user=user)
    assert mode_exc.value.status_code == 422
    assert "mode API" in mode_exc.value.detail

    assert partner_dispatch._build_supplier_endpoint("https://supplier.example/base") == "https://supplier.example/base/orders"
    for invalid in [
        "http://supplier.example/api",
        "https://127.0.0.1/api",
        "https://10.0.0.1/api",
        "https://localhost/api",
        "https://supplier.local/api",
        "https://user:pass@supplier.example/api",
    ]:
        with pytest.raises(HTTPException):
            partner_dispatch._build_supplier_endpoint(invalid)


def test_dispatch_rejects_changed_payload_after_failed_attempt(db, monkeypatch):
    user = _make_user(db, "dispatch-drift@test.ma")
    supplier = _make_supplier(db, user)
    order = _make_order(db, user, supplier)

    def fail(*_args, **_kwargs):
        raise partner_dispatch.SupplierDispatchError("TIMEOUT", "timeout")

    monkeypatch.setattr(partner_dispatch, "_post_supplier_order", fail)
    with pytest.raises(HTTPException):
        partner_dispatch.dispatch_partner_order(order.id, db=db, current_user=user)

    order.current_total = 160.0
    db.commit()
    with pytest.raises(HTTPException) as drift:
        partner_dispatch.dispatch_partner_order(order.id, db=db, current_user=user)
    assert drift.value.status_code == 409
    assert "a change" in drift.value.detail


def test_http_manual_sent_patch_is_blocked_by_p6_dispatch_gate(client, db):
    user = _make_user(db, "dispatch-manual-gate@test.ma")
    supplier = _make_supplier(db, user)
    order = _make_order(db, user, supplier)

    def _get_db():
        yield db

    app.dependency_overrides[database.get_db] = _get_db
    app.dependency_overrides[require_superadmin] = lambda: user
    try:
        response = client.patch(
            f"/api/partner-orders/{order.id}",
            json={"status": "SENT_TO_PARTNER", "currentTotal": 150.0},
        )
    finally:
        app.dependency_overrides.pop(database.get_db, None)
        app.dependency_overrides.pop(require_superadmin, None)

    assert response.status_code == 422, response.text
    assert "preuve de transport" in response.json()["detail"]
    db.refresh(order)
    assert order.status == models.PartnerOrderStatus.DRAFT


def test_http_dispatch_route_is_mounted_and_returns_transport_proof(client, db, monkeypatch):
    user = _make_user(db, "dispatch-http@test.ma")
    supplier = _make_supplier(db, user)
    order = _make_order(db, user, supplier)
    monkeypatch.setattr(partner_dispatch, "_post_supplier_order", lambda *_args, **_kwargs: (202, "HTTP-SUP-001"))

    def _get_db():
        yield db

    app.dependency_overrides[database.get_db] = _get_db
    app.dependency_overrides[require_superadmin] = lambda: user
    try:
        sent = client.post(f"/api/partner-orders/{order.id}/dispatch")
        loaded = client.get(f"/api/partner-orders/{order.id}/dispatch")
    finally:
        app.dependency_overrides.pop(database.get_db, None)
        app.dependency_overrides.pop(require_superadmin, None)

    assert sent.status_code == 200, sent.text
    assert sent.json()["order"]["status"] == "SENT_TO_PARTNER"
    assert sent.json()["dispatch"]["supplierReference"] == "HTTP-SUP-001"
    assert loaded.status_code == 200, loaded.text
    assert loaded.json()["dispatch"]["outcome"] == "SUCCEEDED"
