"""LOT06 C05B-03N — reviewable on-prem policy contract, NOT Windows security.

This is a PURE TEST model. Inputs are synthetic evidence; an attacker can forge
these dataclasses. No production importer may turn them into authentication.
A real Windows SCM/ACL/CNG adapter and authenticated UI must be independently
implemented and validated before any clinical route can call this policy.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import re


class PolicyDenied(ValueError):
    """A deliberately non-PHI fail-closed decision code."""


@dataclass(frozen=True)
class LocalIpcEvidence:
    transport: str
    endpoint: str
    os_name: str
    source: str
    remote_clients_rejected: bool
    explicit_dacl: bool
    authenticated_peer_token: bool
    logon_sid: str
    service_sid: str
    permitted_client_sid: str
    allow_everyone: bool = False
    allow_anonymous: bool = False


@dataclass(frozen=True)
class KeyPolicyEvidence:
    algorithm: str
    ksp: str
    key_name: str
    public_fingerprint: str
    generation: int
    private_export_allowed: bool
    hardware_backed: bool
    revoked: bool
    enrolled_by_admin: bool


@dataclass(frozen=True)
class CaptureBinding:
    tenant_id: int
    patient_id: int
    staff_id: int
    station_id: str
    device_id: str
    capture_id: str
    digest: str
    byte_size: int
    version: int
    device_generation: int


@dataclass(frozen=True)
class StaffReviewEvidence:
    captured: CaptureBinding
    confirmed: bool
    source: str
    user_id: int
    workstation_id: str
    session_jti: str
    selected_patient_id: int
    patient_identity_displayed: bool
    chosen_by_staff: bool
    confirmed_capture_digest: str
    reason_code: str
    challenge_bound: bool
    created_at_s: int
    expires_at_s: int
    now_s: int
    revoked: bool = False


@dataclass(frozen=True)
class ReceiptReconciliation:
    source: str
    method: str
    receipt_committed: bool
    signature_valid: bool
    pinned_key_matches: bool
    tenant_id: int
    patient_id: int
    capture_id: str
    digest: str
    device_id: str
    asset_id: int
    staff_session_active: bool
    device_active: bool
    station_active: bool


def _must(cond: bool, code: str) -> None:
    if not cond:
        raise PolicyDenied(code)


def validate_ipc(e: LocalIpcEvidence) -> str:
    """Shape gate only: OS peer attestation MUST come from future Win32 adapter."""
    _must(e.os_name == "Windows" and e.source == "OS_ADAPTER_ATTESTED",
          "N_IPC_REAL_WINDOWS_ATTESTATION_REQUIRED")
    _must(e.transport == "NAMED_PIPE" and
          re.fullmatch(r"\\\\\.\\pipe\\DigitalCrown-LOT06-[a-zA-Z0-9_-]{1,40}", e.endpoint) is not None,
          "N_IPC_NO_HTTP_OR_UNSCOPED_PIPE")
    _must(e.remote_clients_rejected is True and e.explicit_dacl is True,
          "N_IPC_REJECT_REMOTE_AND_EXPLICIT_DACL_REQUIRED")
    _must(e.authenticated_peer_token is True,
          "N_IPC_OS_PEER_TOKEN_REQUIRED")
    _must(e.allow_everyone is False and e.allow_anonymous is False,
          "N_IPC_BROAD_PRINCIPAL_FORBIDDEN")
    _must(re.fullmatch(r"S-1-5-(?:\d+-){1,14}\d+", e.logon_sid) is not None
          and e.logon_sid == e.permitted_client_sid,
          "N_IPC_CLIENT_LOGON_SID_MISMATCH")
    _must(e.service_sid.startswith("S-1-5-80-") and
          re.fullmatch(r"S-1-5-80-(?:\d+-){4}\d+", e.service_sid) is not None
          and e.service_sid != e.logon_sid,
          "N_IPC_SERVICE_IDENTITY_MISSING")
    return "SHAPE_ONLY_NOT_WIN32_VERIFIED"


def validate_key(e: KeyPolicyEvidence) -> str:
    """CNG ECDSA P-256 is the *target*, not a tested hardware integration."""
    _must(e.algorithm == "ECDSA_P256_SHA256",
          "N_KEY_NO_ALGORITHM_DOWNGRADE")
    _must(e.ksp == "MICROSOFT_PLATFORM_CRYPTO_PROVIDER",
          "N_KEY_HARDWARE_PROVIDER_REQUIRED_OR_OWNER_EXCEPTION")
    _must(e.hardware_backed is True and e.private_export_allowed is False,
          "N_KEY_NONEXPORTABLE_TPM_REQUIRED")
    _must(e.enrolled_by_admin is True and e.revoked is False,
          "N_KEY_ENROLLMENT_OR_REVOCATION_DENIED")
    _must(type(e.generation) is int and e.generation > 0,
          "N_KEY_GENERATION_INVALID")
    _must(re.fullmatch(r"[a-zA-Z0-9_-]{8,80}", e.key_name) is not None
          and re.fullmatch(r"[0-9a-f]{64}", e.public_fingerprint) is not None,
          "N_KEY_IDENTITY_INVALID")
    return "SHAPE_ONLY_NOT_CNG_VERIFIED"


def validate_binding(c: CaptureBinding) -> None:
    for field in ("tenant_id", "patient_id", "staff_id", "byte_size",
                  "version", "device_generation"):
        v = getattr(c, field)
        _must(type(v) is int and v > 0, "N_CAPTURE_INVALID_" + field.upper())
    _must(re.fullmatch(r"[a-zA-Z0-9_-]{1,128}", c.capture_id) is not None
          and re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", c.device_id) is not None
          and re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", c.station_id) is not None
          and re.fullmatch(r"[0-9a-f]{64}", c.digest) is not None,
          "N_CAPTURE_INVALID_BOUND_IDS")


def validate_staff_review(review: StaffReviewEvidence, claim: CaptureBinding) -> str:
    """Synthetic approved UI shape; never infer patient from files or RDV."""
    validate_binding(claim)
    _must(review.source == "SERVER_SESSION_BOUND_UI_EVENT"
          and review.confirmed is True and review.revoked is False,
          "N_REVIEW_AUTHENTICATED_CONFIRMATION_REQUIRED")
    _must(review.captured == claim and review.user_id == claim.staff_id
          and review.workstation_id == claim.station_id
          and review.selected_patient_id == claim.patient_id,
          "N_REVIEW_CAPTURE_PATIENT_STAFF_STATION_CONFLICT")
    _must(review.patient_identity_displayed is True
          and review.chosen_by_staff is True
          and review.confirmed_capture_digest == claim.digest,
          "N_REVIEW_VISIBLE_EXPLICIT_PATIENT_AND_MEDIA_REQUIRED")
    _must(re.fullmatch(r"[a-zA-Z0-9_-]{12,128}", review.session_jti) is not None
          and review.challenge_bound is True
          and review.reason_code in {
              "CLINICAL_CAPTURE", "DOCUMENT_TRANSFER", "CORRECTED_PATIENT_LINK",
          }, "N_REVIEW_SESSION_CHALLENGE_OR_REASON_REQUIRED")
    _must(all(type(n) is int for n in (
        review.created_at_s, review.expires_at_s, review.now_s,
    )), "N_REVIEW_INVALID_CLOCK")
    _must(0 < review.expires_at_s - review.created_at_s <= 120
          and review.created_at_s <= review.now_s < review.expires_at_s,
          "N_REVIEW_EXPIRED_OR_OVERLONG")
    return "SHAPE_ONLY_NOT_REAL_HUMAN_CLICK"


STATES = (
    "STAGED_ENCRYPTED", "AWAITING_STAFF", "STAFF_APPROVED",
    "RECEIPT_COMMITTED", "ACK_DURABLE", "PUBLISHED",
)
_NEXT = dict(zip(STATES, STATES[1:]))


def next_state(current: str, next_requested: str, *, server_receipt: bool = False,
               ack_signature_verified: bool = False,
               original_preserved: bool = True) -> str:
    """Fake crash automaton; not a transaction engine nor a clinical publisher."""
    _must(current in STATES and next_requested in STATES,
          "N_RECOVERY_UNKNOWN_STATE")
    _must(_NEXT.get(current) == next_requested,
          "N_RECOVERY_SKIP_OR_REWIND_FORBIDDEN")
    if next_requested == "RECEIPT_COMMITTED":
        _must(server_receipt is True, "N_RECOVERY_SERVER_COMMIT_REQUIRED")
    if next_requested == "ACK_DURABLE":
        _must(server_receipt is True and ack_signature_verified is True,
              "N_RECOVERY_SIGNED_ACK_REQUIRED")
    if next_requested == "PUBLISHED":
        _must(server_receipt is True and ack_signature_verified is True
              and original_preserved is True,
              "N_RECOVERY_NO_PREMATURE_PUBLICATION_OR_ORIGINAL_DELETE")
    return next_requested


def recovery_action(state: str) -> str:
    _must(state in STATES, "N_RECOVERY_UNKNOWN_STATE")
    if state in ("STAGED_ENCRYPTED", "AWAITING_STAFF", "STAFF_APPROVED"):
        return "BLOCK_UPLOAD_PENDING_SERVER_REVALIDATION"
    if state == "RECEIPT_COMMITTED":
        return "READ_ONLY_SIGNED_RECEIPT_QUERY_NO_UPLOAD"
    if state == "ACK_DURABLE":
        return "PUBLISH_ONLY_AFTER_SCOPE_RECHECK"
    return "NO_REPLAY"


def validate_receipt_reconciliation(r: ReceiptReconciliation,
                                    claim: CaptureBinding) -> str:
    """A read-only future RPC, not a media retransmission after review expiry."""
    validate_binding(claim)
    _must(r.source == "ATTESTED_LOCAL_IPC" and r.method == "GET_RECEIPT_READ_ONLY",
          "N_RECONCILE_MUTATING_REPLAY_FORBIDDEN")
    _must(r.receipt_committed is True and r.signature_valid is True
          and r.pinned_key_matches is True,
          "N_RECONCILE_SIGNED_COMMITTED_RECEIPT_REQUIRED")
    _must(r.staff_session_active is True and r.device_active is True
          and r.station_active is True,
          "N_RECONCILE_CURRENT_AUTHORITY_REQUIRED")
    _must(r.tenant_id == claim.tenant_id
          and r.patient_id == claim.patient_id
          and r.capture_id == claim.capture_id
          and r.digest == claim.digest
          and r.device_id == claim.device_id
          and type(r.asset_id) is int and r.asset_id > 0,
          "N_RECONCILE_IMMUTABLE_SCOPE_MISMATCH")
    return "SHAPE_ONLY_READ_ONLY_RECONCILIATION"
