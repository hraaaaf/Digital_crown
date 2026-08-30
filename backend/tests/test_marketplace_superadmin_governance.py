"""Marketplace P10 — supervision globale, accords, incidents et audit."""

from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException

from backend import models
from backend.models_marketplace_governance import MarketplaceGovernanceEvent, PartnerSupplierAgreement
from backend.models_marketplace_sync import PartnerSupplierSyncState
from backend.routers.partner_superadmin import (
    SupplierGovernanceIn,
    _agreement_payload,
    global_orders,
    governance_audit,
    overview,
    sync_incidents,
    update_governance,
)


def _user(db, email):
    item = models.User(
        email=email,
        hashed_password="test-only",
        role=models.UserRole.DENTISTE,
        nom_complet=email.split("@")[0],
        is_active=True,
        is_licensed=True,
    )
    db.add(item); db.commit(); db.refresh(item); return item


def _supplier(db, owner, key, active=True):
    item = models.PartnerSupplier(
        employer_id=owner.get_employer_id(), supplier_key=key, name=f"Supplier {key}",
        sync_mode="api", api_base_url="https://supplier.example.com/api", is_active=active,
    )
    db.add(item); db.commit(); db.refresh(item); return item


def _order(db, owner, suffix, revenue=20.0):
    item = models.PartnerOrder(
        employer_id=owner.get_employer_id(), order_number=f"GOV-{owner.id}-{suffix}",
        partner_id="1", partner_name="Supplier", status=models.PartnerOrderStatus.CONFIRMED,
        settlement_basis=models.PartnerSettlementBasis.CONFIRMED,
        revenue_model=models.PartnerRevenueModel.COMMISSION_PERCENT,
        strategy_label="Commission", commission_rate=10.0, discount_rate=0.0, fixed_fee_amount=0.0,
        customer_full_name="Acheteur", customer_clinic="Cabinet", customer_phone="0600000000",
        customer_email="buyer@test.ma", customer_city="Rabat", lines_json=[],
        estimated_total=200.0, sent_total=200.0, current_total=200.0,
        recognized_base_amount=200.0, recognized_revenue_amount=revenue, revenue_delta_amount=0.0,
    )
    db.add(item); db.commit(); db.refresh(item); return item


def test_overview_is_cross_cabinet_and_aggregates_marketplace_metrics(db):
    admin = _user(db, "gov-admin@test.ma")
    owner_a = _user(db, "gov-a@test.ma")
    owner_b = _user(db, "gov-b@test.ma")
    _supplier(db, owner_a, "a")
    _supplier(db, owner_b, "b", active=False)
    _order(db, owner_a, "a", revenue=20.0)
    _order(db, owner_b, "b", revenue=30.0)

    result = overview(db=db, admin=admin)

    assert result["cabinetsCount"] == 2
    assert result["suppliersCount"] == 2
    assert result["activeSuppliersCount"] == 1
    assert result["ordersCount"] == 2
    assert result["ordersByStatus"]["CONFIRMED"] == 2
    assert result["recognizedRevenueAmount"] == 50.0


def test_global_order_supervision_filters_cabinet_without_exposing_customer_payload(db):
    admin = _user(db, "gov-orders-admin@test.ma")
    owner_a = _user(db, "gov-orders-a@test.ma")
    owner_b = _user(db, "gov-orders-b@test.ma")
    order_a = _order(db, owner_a, "a")
    _order(db, owner_b, "b")

    rows = global_orders(employerId=owner_a.id, status="CONFIRMED", limit=100, db=db, admin=admin)

    assert len(rows) == 1
    assert rows[0]["id"] == order_a.id
    assert rows[0]["employerId"] == owner_a.id
    assert "customerEmail" not in rows[0]
    assert "customerPhone" not in rows[0]


def test_sensitive_governance_requires_confirmation_and_writes_audit(db):
    admin = _user(db, "gov-mutation-admin@test.ma")
    owner = _user(db, "gov-mutation-owner@test.ma")
    supplier = _supplier(db, owner, "mutation")

    with pytest.raises(HTTPException) as unconfirmed:
        update_governance(
            supplier.id,
            SupplierGovernanceIn(confirm=False, isActive=False),
            db=db,
            admin=admin,
        )
    assert unconfirmed.value.status_code == 409

    result = update_governance(
        supplier.id,
        SupplierGovernanceIn(
            confirm=True,
            isActive=False,
            agreementStatus="ACTIVE",
            agreementReference="AGR-001",
            effectiveAt=datetime.utcnow(),
            expiresAt=datetime.utcnow() + timedelta(days=365),
        ),
        db=db,
        admin=admin,
    )

    assert result["isActive"] is False
    assert result["agreement"]["status"] == "ACTIVE"
    event = db.query(MarketplaceGovernanceEvent).one()
    assert event.admin_user_id == admin.id
    assert event.employer_id == owner.id
    assert event.action == "SUPPLIER_GOVERNANCE_UPDATED"
    assert event.payload_json["before"]["isActive"] is True
    assert event.payload_json["after"]["isActive"] is False


def test_expired_active_agreement_is_reported_effectively_expired(db):
    owner = _user(db, "gov-expired-owner@test.ma")
    supplier = _supplier(db, owner, "expired")
    agreement = PartnerSupplierAgreement(
        employer_id=owner.id,
        supplier_id=supplier.id,
        status="ACTIVE",
        reference="AGR-EXPIRED",
        expires_at=datetime.utcnow() - timedelta(days=1),
    )
    db.add(agreement); db.commit(); db.refresh(agreement)

    assert _agreement_payload(agreement)["status"] == "EXPIRED"
    assert _agreement_payload(agreement)["storedStatus"] == "ACTIVE"


def test_sync_incidents_surface_degraded_supplier_cross_cabinet(db):
    admin = _user(db, "gov-sync-admin@test.ma")
    owner = _user(db, "gov-sync-owner@test.ma")
    supplier = _supplier(db, owner, "incident")
    state = PartnerSupplierSyncState(
        employer_id=owner.id,
        supplier_id=supplier.id,
        last_outcome="FAILED",
        last_success_at=datetime.utcnow() - timedelta(minutes=5),
        last_error_code="TIMEOUT",
        last_error_detail="timeout",
        consecutive_failures=2,
        next_retry_at=datetime.utcnow() + timedelta(minutes=2),
    )
    db.add(state); db.commit()

    rows = sync_incidents(db=db, admin=admin)

    assert len(rows) == 1
    assert rows[0]["employerId"] == owner.id
    assert rows[0]["supplierId"] == supplier.id
    assert rows[0]["freshness"]["status"] == "DEGRADED"
    assert rows[0]["lastErrorCode"] == "TIMEOUT"


def test_governance_audit_can_be_filtered_by_cabinet(db):
    admin = _user(db, "gov-audit-admin@test.ma")
    owner_a = _user(db, "gov-audit-a@test.ma")
    owner_b = _user(db, "gov-audit-b@test.ma")
    supplier_a = _supplier(db, owner_a, "audit-a")
    supplier_b = _supplier(db, owner_b, "audit-b")
    update_governance(supplier_a.id, SupplierGovernanceIn(confirm=True, isActive=False), db=db, admin=admin)
    update_governance(supplier_b.id, SupplierGovernanceIn(confirm=True, isActive=False), db=db, admin=admin)

    rows = governance_audit(employerId=owner_a.id, limit=100, db=db, admin=admin)

    assert len(rows) == 1
    assert rows[0]["employerId"] == owner_a.id
    assert rows[0]["entityId"] == str(supplier_a.id)
