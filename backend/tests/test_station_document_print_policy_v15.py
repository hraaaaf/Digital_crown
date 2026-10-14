"""04.8-A laboratory-only policy tests. No real printer is exercised."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from backend.services.station_document_eligibility import (
    SelfServiceDocumentCandidate, StationEligibilityContext,
)
from backend.services.station_document_print_policy import (
    CabinetPrintPolicy, PrinterTarget, can_offer_print, delivery_identity,
)


@pytest.fixture
def case():
    now = datetime(2026, 10, 12, tzinfo=timezone.utc)
    ctx = StationEligibilityContext(
        tenant_id=2, patient_id=77, station_id="station-1", session_id="sess",
        session_tenant_id=2, session_patient_id=77, session_station_id="station-1",
        session_created_at=now-timedelta(seconds=40),
        session_claimed_at=now-timedelta(seconds=20),
        session_expires_at=now+timedelta(seconds=80),
        session_purged_at=None, station_tenant_id=2,
        station_experience="station", station_revoked_at=None, now=now,
    )
    doc = SelfServiceDocumentCandidate(
        document_id="123", tenant_id=2, patient_id=77, kind="care_sheet",
        is_active=True, is_latest_version=True, finalized=True,
        withdrawal_authorized=True,
    )
    near = PrinterTarget(
        "near", 2, "near_station", station_id="station-1", enabled=True,
        secure_release_verified=True, private_channel_verified=True,
    )
    staff = PrinterTarget(
        "desk", 2, "reception", enabled=True, staff_supervised=True,
    )
    policy = CabinetPrintPolicy(2, "both", ("station-1",), (near, staff))
    return ctx, doc, policy


def test_printing_disabled_by_default(case):
    ctx, doc, policy = case
    assert can_offer_print(ctx, doc, replace(policy, mode="disabled"), "desk").reason == "printing_disabled"
    assert not can_offer_print(ctx, doc, replace(policy, mode="unknown"), "desk").allowed


@pytest.mark.parametrize("mode,printer,allowed", [
    ("both", "near", True), ("both", "desk", True),
    ("near_station", "near", True), ("near_station", "desk", False),
    ("reception", "near", False), ("reception", "desk", True),
])
def test_configured_destinations(case, mode, printer, allowed):
    ctx, doc, policy = case
    assert can_offer_print(ctx, doc, replace(policy, mode=mode), printer).allowed is allowed


@pytest.mark.parametrize("updates", [
    {"tenant_id": 3}, {"patient_id": 3}, {"is_active": False},
    {"is_latest_version": False}, {"finalized": False},
    {"withdrawal_authorized": False},
])
def test_untrusted_document_is_rejected(case, updates):
    ctx, doc, policy = case
    assert not can_offer_print(ctx, replace(doc, **updates), policy, "desk").allowed


def test_wrong_station_tenant_expiry_or_purge_is_rejected(case):
    ctx, doc, policy = case
    mutations = (
        replace(ctx, session_patient_id=8),
        replace(ctx, station_revoked_at=ctx.now),
        replace(ctx, session_purged_at=ctx.now),
        replace(ctx, session_expires_at=ctx.now),
        replace(ctx, session_station_id="station-2"),
    )
    for context in mutations:
        assert not can_offer_print(context, doc, policy, "desk").allowed


def test_target_requires_tenant_and_explicit_unique_allowlist(case):
    ctx, doc, policy = case
    assert not can_offer_print(ctx, doc, policy, "other").allowed
    assert not can_offer_print(ctx, doc, replace(policy, allowed_stations=()), "desk").allowed
    assert not can_offer_print(ctx, doc, replace(policy, tenant_id=3), "desk").allowed
    duplicate = replace(policy, printers=(policy.printers[0], policy.printers[0]))
    assert not can_offer_print(ctx, doc, duplicate, "near").allowed
    mismatched = replace(policy, printers=(replace(policy.printers[0], tenant_id=3),))
    assert not can_offer_print(ctx, doc, mismatched, "near").allowed


def test_private_release_and_staff_attendance_required(case):
    ctx, doc, policy = case
    for change in (
        {"secure_release_verified": False},
        {"private_channel_verified": False},
        {"station_id": "other"},
        {"enabled": False},
    ):
        candidate = replace(policy, printers=(replace(policy.printers[0], **change),))
        assert not can_offer_print(ctx, doc, candidate, "near").allowed
    staff = replace(policy.printers[1], staff_supervised=False)
    assert not can_offer_print(ctx, doc, replace(policy, printers=(staff,)), "desk").allowed


def test_deduplication_key_is_independent_of_printer_destination():
    args = (2, "sess", "care_sheet", "123", "a" * 64)
    assert delivery_identity(*args) == delivery_identity(*args)
    assert delivery_identity(2, "sess2", "care_sheet", "123", "a" * 64) != delivery_identity(*args)


@pytest.mark.parametrize("args", [
    (0, "sess", "care_sheet", "123", "a" * 64),
    (2, "", "care_sheet", "123", "a" * 64),
    (2, "a|b", "care_sheet", "123", "a" * 64),
    (2, "sess", "unknown", "123", "a" * 64),
    (2, "sess", "care_sheet", "123", "A" * 64),
    (2, "sess", "care_sheet", "123", "abc"),
])
def test_invalid_delivery_identity_rejected(args):
    with pytest.raises(ValueError):
        delivery_identity(*args)
