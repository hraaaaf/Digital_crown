from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from backend.services.station_document_eligibility import (
    EligibilityReason,
    SelfServiceDocumentCandidate,
    StationEligibilityContext,
    eligible_documents,
    evaluate_document_eligibility,
)


NOW = datetime(2026, 10, 6, 10, 0, tzinfo=timezone.utc)


@pytest.fixture
def context() -> StationEligibilityContext:
    return StationEligibilityContext(
        tenant_id=10,
        patient_id=20,
        station_id="station-a",
        session_id="session-a",
        session_tenant_id=10,
        session_patient_id=20,
        session_station_id="station-a",
        session_created_at=NOW - timedelta(seconds=60),
        session_claimed_at=NOW - timedelta(seconds=10),
        session_expires_at=NOW + timedelta(seconds=60),
        session_purged_at=None,
        station_tenant_id=10,
        station_experience="station",
        station_revoked_at=None,
        now=NOW,
    )


def presence(**overrides) -> SelfServiceDocumentCandidate:
    base = SelfServiceDocumentCandidate(
        document_id="presence-1",
        tenant_id=10,
        patient_id=20,
        kind="presence_receipt",
        is_active=True,
        is_latest_version=True,
        presence_confirmed=True,
        presence_proof_source="staff",
    )
    return replace(base, **overrides)


def care_sheet(**overrides) -> SelfServiceDocumentCandidate:
    base = SelfServiceDocumentCandidate(
        document_id="care-1",
        tenant_id=10,
        patient_id=20,
        kind="care_sheet",
        is_active=True,
        is_latest_version=True,
        finalized=True,
        withdrawal_authorized=True,
    )
    return replace(base, **overrides)


@pytest.mark.parametrize("candidate", [presence(), care_sheet()])
def test_whitelisted_documents_are_eligible_with_complete_evidence(context, candidate):
    decision = evaluate_document_eligibility(context, candidate)
    assert decision.eligible is True
    assert decision.reason is EligibilityReason.ELIGIBLE


def test_unknown_or_sensitive_document_type_is_denied_by_default(context):
    candidate = replace(care_sheet(), kind="ordonnance")
    decision = evaluate_document_eligibility(context, candidate)
    assert decision.eligible is False
    assert decision.reason is EligibilityReason.NOT_WHITELISTED


@pytest.mark.parametrize(
    ("changed", "expected"),
    [
        ({"station_id": ""}, EligibilityReason.STATION_NOT_REGISTERED),
        ({"station_revoked_at": NOW}, EligibilityReason.STATION_REVOKED),
        ({"station_experience": "cabinet"}, EligibilityReason.STATION_NOT_KIOSK),
        ({"station_experience": None}, EligibilityReason.STATION_NOT_KIOSK),
        ({"session_id": ""}, EligibilityReason.SESSION_NOT_IDENTIFIED),
        ({"session_claimed_at": None}, EligibilityReason.SESSION_NOT_IDENTIFIED),
        ({"session_patient_id": None}, EligibilityReason.SESSION_NOT_IDENTIFIED),
        ({"session_purged_at": NOW}, EligibilityReason.SESSION_PURGED),
        ({"session_created_at": NOW + timedelta(seconds=1)}, EligibilityReason.SESSION_INVALID_WINDOW),
        ({"session_claimed_at": NOW - timedelta(seconds=61)}, EligibilityReason.SESSION_INVALID_WINDOW),
        ({"session_claimed_at": NOW + timedelta(seconds=1)}, EligibilityReason.SESSION_INVALID_WINDOW),
        ({"session_expires_at": NOW + timedelta(seconds=61)}, EligibilityReason.SESSION_INVALID_WINDOW),
        ({"session_expires_at": NOW - timedelta(seconds=20)}, EligibilityReason.SESSION_INVALID_WINDOW),
        ({"session_expires_at": NOW}, EligibilityReason.SESSION_EXPIRED),
        ({"session_expires_at": NOW - timedelta(seconds=1)}, EligibilityReason.SESSION_EXPIRED),
        ({"session_tenant_id": 999}, EligibilityReason.TENANT_MISMATCH),
        ({"station_tenant_id": 999}, EligibilityReason.TENANT_MISMATCH),
        ({"session_patient_id": 999}, EligibilityReason.PATIENT_MISMATCH),
        ({"session_station_id": "station-b"}, EligibilityReason.STATION_MISMATCH),
    ],
)
def test_station_and_session_context_fail_closed(context, changed, expected):
    decision = evaluate_document_eligibility(replace(context, **changed), care_sheet())
    assert decision.eligible is False
    assert decision.reason is expected


@pytest.mark.parametrize(
    ("candidate", "expected"),
    [
        (care_sheet(document_id=""), EligibilityReason.DOCUMENT_ID_INVALID),
        (care_sheet(document_id="   "), EligibilityReason.DOCUMENT_ID_INVALID),
        (care_sheet(tenant_id=11), EligibilityReason.TENANT_MISMATCH),
        (care_sheet(patient_id=21), EligibilityReason.PATIENT_MISMATCH),
        (care_sheet(is_active=False), EligibilityReason.DOCUMENT_NOT_ACTIVE),
        (care_sheet(is_latest_version=False), EligibilityReason.DOCUMENT_NOT_LATEST),
    ],
)
def test_document_identity_and_lifecycle_fail_closed(context, candidate, expected):
    decision = evaluate_document_eligibility(context, candidate)
    assert decision.eligible is False
    assert decision.reason is expected


@pytest.mark.parametrize("source", [None, "", "self_reported", "remote_form", "patient"])
def test_presence_receipt_rejects_untrusted_presence_proof(context, source):
    decision = evaluate_document_eligibility(
        context,
        presence(presence_proof_source=source),
    )
    assert decision.eligible is False
    assert decision.reason is EligibilityReason.PRESENCE_PROOF_UNTRUSTED


def test_presence_receipt_requires_confirmed_presence(context):
    decision = evaluate_document_eligibility(context, presence(presence_confirmed=False))
    assert decision.eligible is False
    assert decision.reason is EligibilityReason.PRESENCE_NOT_PROVEN


def test_queue_core_is_an_explicit_reliable_presence_source(context):
    decision = evaluate_document_eligibility(
        context,
        presence(presence_proof_source="queue_core"),
    )
    assert decision.eligible is True


@pytest.mark.parametrize(
    ("candidate", "expected"),
    [
        (care_sheet(finalized=False), EligibilityReason.CARE_SHEET_NOT_FINALIZED),
        (care_sheet(withdrawal_authorized=False), EligibilityReason.WITHDRAWAL_NOT_AUTHORIZED),
    ],
)
def test_care_sheet_requires_finalization_and_explicit_withdrawal_authorization(
    context, candidate, expected
):
    decision = evaluate_document_eligibility(context, candidate)
    assert decision.eligible is False
    assert decision.reason is expected


def test_naive_utc_database_timestamps_are_compared_safely(context):
    naive = NOW.replace(tzinfo=None)
    naive_context = replace(
        context,
        now=naive,
        session_created_at=naive - timedelta(seconds=60),
        session_claimed_at=naive - timedelta(seconds=10),
        session_expires_at=naive + timedelta(seconds=30),
    )
    assert evaluate_document_eligibility(naive_context, care_sheet()).eligible is True


def test_filter_returns_only_candidates_that_pass_full_gate(context):
    candidates = [
        presence(),
        care_sheet(),
        replace(care_sheet(), document_id="care-denied", withdrawal_authorized=False),
        replace(care_sheet(), document_id="rx", kind="ordonnance"),
        replace(presence(), document_id="wrong-tenant", tenant_id=999),
    ]
    assert [item.document_id for item in eligible_documents(context, candidates)] == [
        "presence-1",
        "care-1",
    ]
