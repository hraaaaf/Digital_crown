"""LOT06 C05B-03N synthetic policy FUE; no real Windows security claims.

Runs on Ubuntu and Windows. These dataclasses model *assumed* trusted evidence:
they are not a Win32 DACL probe, real human UI event or CNG attestation.
"""
from dataclasses import replace
from pathlib import Path
import sys

import pytest

from isolated_fue_lot06c.c05b03n_onprem_policy_contract import (
    CaptureBinding, KeyPolicyEvidence, LocalIpcEvidence, PolicyDenied,
    ReceiptReconciliation, StaffReviewEvidence, STATES,
    next_state, recovery_action, validate_binding, validate_ipc,
    validate_key, validate_receipt_reconciliation, validate_staff_review,
)


@pytest.fixture
def claim():
    return CaptureBinding(
        tenant_id=8, patient_id=74, staff_id=6, station_id="station-demo",
        device_id="device-demo", capture_id="capture-5678",
        digest="a" * 64, byte_size=12345, version=1,
        device_generation=2,
    )


@pytest.fixture
def ipc():
    return LocalIpcEvidence(
        transport="NAMED_PIPE", endpoint=r"\\.\pipe\DigitalCrown-LOT06-imaging",
        os_name="Windows", source="OS_ADAPTER_ATTESTED",
        remote_clients_rejected=True, explicit_dacl=True,
        authenticated_peer_token=True,
        logon_sid="S-1-5-21-123-456-789-1001",
        service_sid="S-1-5-80-123-456-789-234-567",
        permitted_client_sid="S-1-5-21-123-456-789-1001",
    )


@pytest.fixture
def key():
    return KeyPolicyEvidence(
        algorithm="ECDSA_P256_SHA256", ksp="MICROSOFT_PLATFORM_CRYPTO_PROVIDER",
        key_name="digital-crown-device-key-v2", public_fingerprint="b" * 64,
        generation=2, private_export_allowed=False, hardware_backed=True,
        revoked=False, enrolled_by_admin=True,
    )


@pytest.fixture
def review(claim):
    return StaffReviewEvidence(
        captured=claim, confirmed=True, source="SERVER_SESSION_BOUND_UI_EVENT",
        user_id=claim.staff_id, workstation_id=claim.station_id,
        session_jti="session-0123456789", selected_patient_id=claim.patient_id,
        patient_identity_displayed=True, chosen_by_staff=True,
        confirmed_capture_digest=claim.digest, reason_code="CLINICAL_CAPTURE",
        challenge_bound=True, created_at_s=1000, expires_at_s=1120,
        now_s=1001, revoked=False,
    )


@pytest.fixture
def recon(claim):
    return ReceiptReconciliation(
        source="ATTESTED_LOCAL_IPC", method="GET_RECEIPT_READ_ONLY",
        receipt_committed=True, signature_valid=True, pinned_key_matches=True,
        tenant_id=claim.tenant_id, patient_id=claim.patient_id,
        capture_id=claim.capture_id, digest=claim.digest,
        device_id=claim.device_id, asset_id=2001,
        staff_session_active=True, device_active=True, station_active=True,
    )


def deny(code, fn):
    with pytest.raises(PolicyDenied, match=code):
        fn()


def test_c05b03n_valid_contract_shapes_are_not_os_security(ipc, key, review, claim, recon):
    assert validate_ipc(ipc) == "SHAPE_ONLY_NOT_WIN32_VERIFIED"
    assert validate_key(key) == "SHAPE_ONLY_NOT_CNG_VERIFIED"
    assert validate_staff_review(review, claim) == "SHAPE_ONLY_NOT_REAL_HUMAN_CLICK"
    assert validate_receipt_reconciliation(recon, claim) == (
        "SHAPE_ONLY_READ_ONLY_RECONCILIATION"
    )
    print("C05B03N_SHAPES_ONLY_NOT_OS_SECURITY_OR_HUMAN_CERTIFICATION")


@pytest.mark.parametrize("field,value", [
    ("transport", "HTTP"),
    ("transport", "HTTPS"),
    ("endpoint", "http://127.0.0.1:8000"),
    ("endpoint", r"\\.\pipe\Generic"),
])
def test_c05b03n_no_direct_http_or_unscoped_pipe(ipc, field, value):
    deny("N_IPC_NO_HTTP", lambda: validate_ipc(replace(ipc, **{field:value})))


@pytest.mark.parametrize("field,value,reason", [
    ("os_name", "Linux", "REAL_WINDOWS"),
    ("source", "REQUEST_HEADER", "REAL_WINDOWS"),
    ("remote_clients_rejected", False, "REJECT_REMOTE"),
    ("explicit_dacl", False, "REJECT_REMOTE"),
    ("authenticated_peer_token", False, "OS_PEER_TOKEN"),
    ("allow_everyone", True, "BROAD_PRINCIPAL"),
    ("allow_anonymous", True, "BROAD_PRINCIPAL"),
    ("logon_sid", "S-1-5-21-123-456-789-1002", "CLIENT_LOGON"),
    ("service_sid", "S-1-5-18", "SERVICE_IDENTITY"),
])
def test_c05b03n_bad_peer_security_shape_denied(ipc, field, value, reason):
    deny(reason, lambda: validate_ipc(replace(ipc, **{field:value})))


@pytest.mark.parametrize("field,value,reason", [
    ("algorithm", "ED25519_LAB", "ALGORITHM_DOWNGRADE"),
    ("algorithm", "RSA_SHA1", "ALGORITHM_DOWNGRADE"),
    ("ksp", "MICROSOFT_SOFTWARE_KEY_STORAGE_PROVIDER", "HARDWARE_PROVIDER"),
    ("private_export_allowed", True, "NONEXPORTABLE"),
    ("hardware_backed", False, "NONEXPORTABLE"),
    ("enrolled_by_admin", False, "ENROLLMENT"),
    ("revoked", True, "ENROLLMENT"),
    ("generation", 0, "GENERATION"),
])
def test_c05b03n_no_weak_cng_fallback_or_revoked_key(key, field, value, reason):
    deny(reason, lambda: validate_key(replace(key, **{field:value})))


@pytest.mark.parametrize("field,value,reason", [
    ("confirmed", False, "AUTHENTICATED_CONFIRMATION"),
    ("source", "AUTO_BY_APPOINTMENT", "AUTHENTICATED_CONFIRMATION"),
    ("source", "FILENAME_HEURISTIC", "AUTHENTICATED_CONFIRMATION"),
    ("patient_identity_displayed", False, "VISIBLE_EXPLICIT"),
    ("chosen_by_staff", False, "VISIBLE_EXPLICIT"),
    ("confirmed_capture_digest", "b"*64, "VISIBLE_EXPLICIT"),
    ("user_id", 999, "CAPTURE_PATIENT"),
    ("selected_patient_id", 75, "CAPTURE_PATIENT"),
    ("workstation_id", "wrong-station", "CAPTURE_PATIENT"),
    ("challenge_bound", False, "SESSION_CHALLENGE"),
    ("session_jti", "", "SESSION_CHALLENGE"),
    ("reason_code", "AUTO_ASSIGNMENT", "SESSION_CHALLENGE"),
    ("revoked", True, "AUTHENTICATED_CONFIRMATION"),
    ("expires_at_s", 1121, "EXPIRED_OR_OVERLONG"),
    ("now_s", 1120, "EXPIRED_OR_OVERLONG"),
])
def test_c05b03n_no_implicit_patient_selection_or_expired_review(
    review, claim, field, value, reason,
):
    deny(reason, lambda: validate_staff_review(replace(review, **{field:value}),claim))


@pytest.mark.parametrize("field,value", [
    ("patient_id", True), ("tenant_id", 0), ("byte_size", 0),
    ("capture_id", "../traversal"), ("digest", "0"*63),
])
def test_c05b03n_malformed_capture_rejected(claim, field, value):
    deny("N_CAPTURE_INVALID", lambda: validate_binding(replace(claim, **{field:value})))


def test_c05b03n_crash_state_machine_blocks_premature_visibility():
    state = "STAGED_ENCRYPTED"
    assert recovery_action(state) == "BLOCK_UPLOAD_PENDING_SERVER_REVALIDATION"
    for target in STATES[2:]:
        deny("SKIP_OR_REWIND", lambda: next_state(state, target))
    state = next_state(state, "AWAITING_STAFF")
    state = next_state(state, "STAFF_APPROVED")
    deny("SERVER_COMMIT", lambda: next_state(state, "RECEIPT_COMMITTED"))
    state = next_state(state, "RECEIPT_COMMITTED", server_receipt=True)
    assert recovery_action(state) == "READ_ONLY_SIGNED_RECEIPT_QUERY_NO_UPLOAD"
    deny("SIGNED_ACK", lambda: next_state(state, "ACK_DURABLE",server_receipt=True))
    state = next_state(
        state, "ACK_DURABLE", server_receipt=True, ack_signature_verified=True,
    )
    assert recovery_action(state) == "PUBLISH_ONLY_AFTER_SCOPE_RECHECK"
    deny("ORIGINAL_DELETE", lambda: next_state(
        state,"PUBLISHED",server_receipt=True,ack_signature_verified=True,
        original_preserved=False,
    ))
    state=next_state(
        state,"PUBLISHED",server_receipt=True,ack_signature_verified=True,
        original_preserved=True,
    )
    assert state=="PUBLISHED" and recovery_action(state)=="NO_REPLAY"
    print("C05B03N_CRASH_BOUNDARY_ACK_BEFORE_PUBLICATION_POLICY_PASS")


@pytest.mark.parametrize("field,value,reason", [
    ("source", "HTTP_LOOPBACK", "MUTATING_REPLAY"),
    ("method", "POST_UPLOAD_AGAIN", "MUTATING_REPLAY"),
    ("receipt_committed", False, "SIGNED_COMMITTED"),
    ("signature_valid", False, "SIGNED_COMMITTED"),
    ("pinned_key_matches", False, "SIGNED_COMMITTED"),
    ("patient_id", 75, "IMMUTABLE_SCOPE"),
    ("tenant_id", 9, "IMMUTABLE_SCOPE"),
    ("capture_id", "other-capture", "IMMUTABLE_SCOPE"),
    ("digest", "f"*64, "IMMUTABLE_SCOPE"),
    ("device_id", "foreign-device", "IMMUTABLE_SCOPE"),
    ("staff_session_active", False, "CURRENT_AUTHORITY"),
    ("station_active", False, "CURRENT_AUTHORITY"),
    ("device_active", False, "CURRENT_AUTHORITY"),
])
def test_c05b03n_lost_ack_is_read_only_scoped_reconciliation_only(
    recon, claim, field, value, reason,
):
    deny(reason, lambda: validate_receipt_reconciliation(
        replace(recon, **{field:value}), claim,
    ))


def test_c05b03n_no_product_backend_hook_or_live_activation():
    main=(Path(__file__).resolve().parents[1]/"backend"/"main.py").read_text(encoding="utf8")
    assert "c05b03n_onprem_policy_contract" not in main
    assert "c05b03n_device" not in main
    assert "windows_pipe_probe_lab" not in main
    print("C05B03N_CONTRACT_TEST_NOT_PRODUCT_ROUTE")


def test_c05b03n_windows_runner_is_declared_not_native_security_validation():
    # This test runs on both Linux and Windows. Native pipe/CNG/SCM ACL security
    # cannot be inferred from the platform label alone, including on Windows CI.
    assert sys.platform in {"linux", "win32", "darwin"}
    assert "SHAPE_ONLY" in validate_ipc(LocalIpcEvidence(
        transport="NAMED_PIPE",
        endpoint=r"\\.\pipe\DigitalCrown-LOT06-fue",
        os_name="Windows", source="OS_ADAPTER_ATTESTED",
        remote_clients_rejected=True, explicit_dacl=True,
        authenticated_peer_token=True,
        logon_sid="S-1-5-21-123-456-789-1001",
        service_sid="S-1-5-80-123-456-789-234-567",
        permitted_client_sid="S-1-5-21-123-456-789-1001",
    ))
