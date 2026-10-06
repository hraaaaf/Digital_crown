from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Iterable


ENGINE_VERSION = "v1.5-04.1"
MAX_SESSION_TTL_SECONDS = 120


class SelfServiceDocumentKind(str, Enum):
    PRESENCE_RECEIPT = "presence_receipt"
    CARE_SHEET = "care_sheet"


class PresenceProofSource(str, Enum):
    STAFF = "staff"
    QUEUE_CORE = "queue_core"


class EligibilityReason(str, Enum):
    ELIGIBLE = "eligible"
    NOT_WHITELISTED = "not_whitelisted"
    STATION_NOT_REGISTERED = "station_not_registered"
    STATION_REVOKED = "station_revoked"
    STATION_NOT_KIOSK = "station_not_kiosk"
    SESSION_NOT_IDENTIFIED = "session_not_identified"
    SESSION_PURGED = "session_purged"
    SESSION_EXPIRED = "session_expired"
    SESSION_INVALID_WINDOW = "session_invalid_window"
    DOCUMENT_ID_INVALID = "document_id_invalid"
    TENANT_MISMATCH = "tenant_mismatch"
    PATIENT_MISMATCH = "patient_mismatch"
    STATION_MISMATCH = "station_mismatch"
    DOCUMENT_NOT_ACTIVE = "document_not_active"
    DOCUMENT_NOT_LATEST = "document_not_latest"
    PRESENCE_NOT_PROVEN = "presence_not_proven"
    PRESENCE_PROOF_UNTRUSTED = "presence_proof_untrusted"
    CARE_SHEET_NOT_FINALIZED = "care_sheet_not_finalized"
    WITHDRAWAL_NOT_AUTHORIZED = "withdrawal_not_authorized"


@dataclass(frozen=True)
class StationEligibilityContext:
    tenant_id: int
    patient_id: int
    station_id: str
    session_id: str
    session_tenant_id: int
    session_patient_id: int | None
    session_station_id: str
    session_created_at: datetime
    session_claimed_at: datetime | None
    session_expires_at: datetime
    session_purged_at: datetime | None
    station_tenant_id: int
    station_experience: str | None
    station_revoked_at: datetime | None
    now: datetime


@dataclass(frozen=True)
class SelfServiceDocumentCandidate:
    document_id: str
    tenant_id: int
    patient_id: int
    kind: str
    is_active: bool = False
    is_latest_version: bool = False
    presence_confirmed: bool = False
    presence_proof_source: str | None = None
    finalized: bool = False
    withdrawal_authorized: bool = False


@dataclass(frozen=True)
class EligibilityDecision:
    document_id: str
    kind: str
    eligible: bool
    reason: EligibilityReason
    engine_version: str = ENGINE_VERSION


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _deny(candidate: SelfServiceDocumentCandidate, reason: EligibilityReason) -> EligibilityDecision:
    return EligibilityDecision(
        document_id=candidate.document_id,
        kind=candidate.kind,
        eligible=False,
        reason=reason,
    )


def evaluate_document_eligibility(
    context: StationEligibilityContext,
    candidate: SelfServiceDocumentCandidate,
) -> EligibilityDecision:
    """
    Deterministic V1.5-04.1 station document eligibility gate.

    Security contract:
    - explicit whitelist only;
    - deny by default on missing/unknown facts;
    - authorization is based on canonical tenant/patient/station/session IDs,
      never on name, phone number or date of birth;
    - this function never generates, edits or mutates a clinical document.
    """
    try:
        kind = SelfServiceDocumentKind(candidate.kind)
    except ValueError:
        return _deny(candidate, EligibilityReason.NOT_WHITELISTED)

    if not context.station_id or not context.session_station_id:
        return _deny(candidate, EligibilityReason.STATION_NOT_REGISTERED)
    if context.station_revoked_at is not None:
        return _deny(candidate, EligibilityReason.STATION_REVOKED)
    if context.station_experience != "station":
        return _deny(candidate, EligibilityReason.STATION_NOT_KIOSK)
    if (
        not context.session_id
        or context.session_claimed_at is None
        or context.session_patient_id is None
    ):
        return _deny(candidate, EligibilityReason.SESSION_NOT_IDENTIFIED)
    if context.session_purged_at is not None:
        return _deny(candidate, EligibilityReason.SESSION_PURGED)

    created_at = _as_utc(context.session_created_at)
    claimed_at = _as_utc(context.session_claimed_at)
    expires_at = _as_utc(context.session_expires_at)
    now = _as_utc(context.now)
    lifetime_seconds = (expires_at - created_at).total_seconds()
    if (
        created_at > now
        or claimed_at < created_at
        or claimed_at > now
        or expires_at <= claimed_at
        or lifetime_seconds <= 0
        or lifetime_seconds > MAX_SESSION_TTL_SECONDS
    ):
        return _deny(candidate, EligibilityReason.SESSION_INVALID_WINDOW)
    if expires_at <= now:
        return _deny(candidate, EligibilityReason.SESSION_EXPIRED)

    if not candidate.document_id.strip():
        return _deny(candidate, EligibilityReason.DOCUMENT_ID_INVALID)

    if (
        candidate.tenant_id != context.tenant_id
        or context.session_tenant_id != context.tenant_id
        or context.station_tenant_id != context.tenant_id
    ):
        return _deny(candidate, EligibilityReason.TENANT_MISMATCH)
    if (
        candidate.patient_id != context.patient_id
        or context.session_patient_id != context.patient_id
    ):
        return _deny(candidate, EligibilityReason.PATIENT_MISMATCH)
    if context.session_station_id != context.station_id:
        return _deny(candidate, EligibilityReason.STATION_MISMATCH)

    if not candidate.is_active:
        return _deny(candidate, EligibilityReason.DOCUMENT_NOT_ACTIVE)
    if not candidate.is_latest_version:
        return _deny(candidate, EligibilityReason.DOCUMENT_NOT_LATEST)

    if kind is SelfServiceDocumentKind.PRESENCE_RECEIPT:
        if not candidate.presence_confirmed:
            return _deny(candidate, EligibilityReason.PRESENCE_NOT_PROVEN)
        try:
            proof_source = PresenceProofSource(candidate.presence_proof_source or "")
        except ValueError:
            return _deny(candidate, EligibilityReason.PRESENCE_PROOF_UNTRUSTED)
        if proof_source not in {PresenceProofSource.STAFF, PresenceProofSource.QUEUE_CORE}:
            return _deny(candidate, EligibilityReason.PRESENCE_PROOF_UNTRUSTED)
    elif kind is SelfServiceDocumentKind.CARE_SHEET:
        if not candidate.finalized:
            return _deny(candidate, EligibilityReason.CARE_SHEET_NOT_FINALIZED)
        if not candidate.withdrawal_authorized:
            return _deny(candidate, EligibilityReason.WITHDRAWAL_NOT_AUTHORIZED)
    else:  # defensive: enum additions must never become implicitly eligible
        return _deny(candidate, EligibilityReason.NOT_WHITELISTED)

    return EligibilityDecision(
        document_id=candidate.document_id,
        kind=kind.value,
        eligible=True,
        reason=EligibilityReason.ELIGIBLE,
    )


def eligible_documents(
    context: StationEligibilityContext,
    candidates: Iterable[SelfServiceDocumentCandidate],
) -> list[SelfServiceDocumentCandidate]:
    return [
        candidate
        for candidate in candidates
        if evaluate_document_eligibility(context, candidate).eligible
    ]
