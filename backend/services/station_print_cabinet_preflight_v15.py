"""04.8-C: read canonical Cabinet/Station/archived-document identity (NO print permit).

A STRICT read-only, internal SQL boundary sourced from existing Digital Crown
tables. It does not accept browser-supplied tenant, proof, finalized, consent or
certification flags, doesn't return PDF bytes, and never reserves a held claim.

This is a *structural* check, not complete patient authorisation: archived
care-sheet finalisation and withdrawal evidence must still be independently
rechecked with station_care_sheet.care_sheet_state in the final transaction.
Until then this routine ALWAYS returns allowed=False, even on structurally
valid records, and there is no route that uses it to print.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re

from sqlalchemy import text
from sqlalchemy.engine import Connection

from backend.services.station_document_eligibility import (
    EligibilityReason,
    SelfServiceDocumentCandidate,
    StationEligibilityContext,
    evaluate_document_eligibility,
)

_SHA256 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class CabinetPrintPreflight:
    allowed: bool
    reason: str
    # No patient name, session bearer token, medical data or raw file path.
    session_id: str | None = None
    document_id: int | None = None
    document_sha256: str | None = None


def _datetime(raw: object) -> datetime | None:
    if isinstance(raw, datetime):
        return raw if raw.tzinfo is not None else raw.replace(tzinfo=timezone.utc)
    if isinstance(raw, str):
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


def inspect_cabinet_care_sheet_preflight(
    connection: Connection,
    *,
    tenant_id: int,
    actor_user_id: int,
    actor_employer_id: int | None,
    cabinet_workstation_id: str,
    session_id: str,
    document_id: int,
    expected_archive_sha256: str,
    now: datetime,
) -> CabinetPrintPreflight:
    """Check immutable identities from real DB rows and deny release always.

    Invoker MUST be a trusted Cabinet server, never Station or an exposed
    print endpoint. Schema errors propagate, no fake success or stale cache.
    Inputs are selectors, not authorisation/attestation facts. In particular
    any caller can supply a known SHA, but it cannot enable a print claim.
    """
    deny = lambda reason: CabinetPrintPreflight(False, reason)
    if (
        type(tenant_id) is not int or tenant_id <= 0
        or type(actor_user_id) is not int or actor_user_id != tenant_id
        or actor_employer_id is not None
    ):
        return deny("OWNER_REQUIRED")
    if (
        type(session_id) is not str or len(session_id) != 36
        or type(cabinet_workstation_id) is not str
        or not cabinet_workstation_id
        or type(document_id) is not int or document_id <= 0
        or type(expected_archive_sha256) is not str
        or _SHA256.fullmatch(expected_archive_sha256) is None
        or not isinstance(now, datetime)
    ):
        return deny("INVALID_SELECTOR")

    cabinet = connection.execute(text("""
        SELECT id, employer_id, default_experience, revoked_at
        FROM workstation_modes
        WHERE id = :cabinet_id AND employer_id = :tenant_id
    """), {"cabinet_id": cabinet_workstation_id, "tenant_id": tenant_id}).mappings().one_or_none()
    if (
        cabinet is None or cabinet["revoked_at"] is not None
        or cabinet["default_experience"] not in ("cabinet", "reception")
    ):
        return deny("STAFF_WORKSTATION_REQUIRED")

    session = connection.execute(text("""
        SELECT s.id, s.employer_id, s.workstation_id, s.patient_id,
               s.created_at, s.claimed_at, s.expires_at, s.purged_at,
               w.employer_id AS station_tenant_id,
               w.default_experience AS station_experience,
               w.revoked_at AS station_revoked_at
        FROM workstation_patient_sessions AS s
        JOIN workstation_modes AS w ON w.id = s.workstation_id
        JOIN patients AS p ON p.id = s.patient_id
        WHERE s.id = :session_id AND s.employer_id = :tenant_id
          AND w.employer_id = :tenant_id AND p.employer_id = :tenant_id
          AND p.deleted_at IS NULL
    """), {"session_id": session_id, "tenant_id": tenant_id}).mappings().one_or_none()
    if session is None:
        return deny("SESSION_NOT_FOUND_OR_CROSS_TENANT")

    created = _datetime(session["created_at"])
    claimed = _datetime(session["claimed_at"])
    expires = _datetime(session["expires_at"])
    moment = _datetime(now)
    if created is None or expires is None or moment is None:
        return deny("SESSION_INVALID")
    # Canonical document_eligibility engine handles station type,
    # tenant/patient binding, revocation and short TTL + purge/expiry.
    context = StationEligibilityContext(
        tenant_id=tenant_id,
        patient_id=int(session["patient_id"]),
        station_id=str(session["workstation_id"]),
        session_id=str(session["id"]),
        session_tenant_id=int(session["employer_id"]),
        session_patient_id=int(session["patient_id"]),
        session_station_id=str(session["workstation_id"]),
        session_created_at=created,
        session_claimed_at=claimed,
        session_expires_at=expires,
        session_purged_at=_datetime(session["purged_at"]),
        station_tenant_id=int(session["station_tenant_id"]),
        station_experience=session["station_experience"],
        station_revoked_at=_datetime(session["station_revoked_at"]),
        now=moment,
    )

    doc = connection.execute(text("""
        SELECT id, patient_id, file_hash, file_size, filename,
               status, is_latest_version, deleted_at
        FROM document_archives
        WHERE id = :document_id AND patient_id = :patient_id
    """), {
        "document_id": document_id,
        "patient_id": context.patient_id,
    }).mappings().one_or_none()
    if doc is None:
        return deny("ARCHIVE_NOT_FOUND_OR_CROSS_PATIENT")
    if (
        doc["deleted_at"] is not None
        or str(doc["status"]).lower() not in ("actif", "documentstatus.actif")
        or not bool(doc["is_latest_version"])
        or type(doc["file_hash"]) is not str
        or _SHA256.fullmatch(doc["file_hash"]) is None
        or doc["file_hash"] != expected_archive_sha256
        or type(doc["file_size"]) is not int or doc["file_size"] <= 0
        or not str(doc["filename"] or "").lower().endswith(".pdf")
    ):
        return deny("ARCHIVE_INACTIVE_OR_SHA_MISMATCH")

    candidate = SelfServiceDocumentCandidate(
        document_id=str(document_id), tenant_id=tenant_id,
        patient_id=int(doc["patient_id"]), kind="care_sheet",
        is_active=True, is_latest_version=True,
        # NEVER infer finalisation from filename/hash/state. The canonical
        # clinical archive authorisation still needs its own audit proof.
        finalized=False, withdrawal_authorized=False,
    )
    decision = evaluate_document_eligibility(context, candidate)
    if decision.reason != EligibilityReason.CARE_SHEET_NOT_FINALIZED:
        return deny("ELIGIBILITY_" + decision.reason.value.upper())

    # This is the ONLY positive structural state: still DENIED for printing.
    return CabinetPrintPreflight(
        allowed=False,
        reason="FINALIZATION_WITHDRAWAL_POLICY_AND_PHYSICAL_PROOF_REQUIRED",
        session_id=session_id,
        document_id=document_id,
        document_sha256=doc["file_hash"],
    )
