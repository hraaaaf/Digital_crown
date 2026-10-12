"""04.8-A: fail-closed print destination policy, never a PDF delivery API.

This is a pure policy helper. A Cabinet-side authorized worker and a real
physical printer are still required before any paper can be released.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from backend.services.station_document_eligibility import (
    SelfServiceDocumentCandidate,
    StationEligibilityContext,
    evaluate_document_eligibility,
)

MODES = frozenset({"disabled", "reception", "near_station", "both"})


@dataclass(frozen=True)
class PrinterTarget:
    printer_id: str
    tenant_id: int
    location: str
    station_id: str | None = None
    enabled: bool = False
    secure_release_verified: bool = False
    private_channel_verified: bool = False
    staff_supervised: bool = False


@dataclass(frozen=True)
class CabinetPrintPolicy:
    tenant_id: int
    mode: str = "disabled"
    allowed_stations: tuple[str, ...] = ()
    printers: tuple[PrinterTarget, ...] = ()


@dataclass(frozen=True)
class PrintDecision:
    allowed: bool
    reason: str


def can_offer_print(
    context: StationEligibilityContext,
    document: SelfServiceDocumentCandidate,
    policy: CabinetPrintPolicy,
    printer_id: str,
) -> PrintDecision:
    """Check only whether UI may offer a destination, NOT permission to print.

    The trusted Cabinet worker must still re-check session, document, tenant,
    consent and destination atomically before issuing or releasing any job.
    """
    if not evaluate_document_eligibility(context, document).eligible:
        return PrintDecision(False, "document_ineligible")
    if policy.mode not in MODES or policy.mode == "disabled":
        return PrintDecision(False, "printing_disabled")
    if policy.tenant_id != context.tenant_id:
        return PrintDecision(False, "tenant_mismatch")
    if not context.station_id or context.station_id not in policy.allowed_stations:
        return PrintDecision(False, "station_not_allowed")
    matches = [p for p in policy.printers if p.printer_id == printer_id and p.printer_id]
    if len(matches) != 1:
        return PrintDecision(False, "printer_not_allowed")
    p = matches[0]
    if not p.enabled or p.tenant_id != policy.tenant_id:
        return PrintDecision(False, "printer_not_allowed")
    if p.location == "reception":
        if policy.mode not in ("reception", "both"):
            return PrintDecision(False, "destination_disabled")
        if not p.staff_supervised:
            return PrintDecision(False, "staff_required")
    elif p.location == "near_station":
        if policy.mode not in ("near_station", "both"):
            return PrintDecision(False, "destination_disabled")
        if p.station_id != context.station_id:
            return PrintDecision(False, "station_mismatch")
        if not (p.secure_release_verified and p.private_channel_verified):
            return PrintDecision(False, "private_release_required")
    else:
        return PrintDecision(False, "printer_not_allowed")
    return PrintDecision(True, "eligible")


def delivery_identity(
    tenant_id: int, session_id: str, document_kind: str,
    document_id: str, document_sha256: str,
) -> str:
    """Printer-independent idempotency *identifier*, not an atomic DB lock."""
    if tenant_id <= 0 or not session_id or not document_id:
        raise ValueError("INVALID_DELIVERY_IDENTITY")
    if any("|" in value for value in (session_id, document_kind, document_id)):
        raise ValueError("INVALID_DELIVERY_IDENTITY")
    if document_kind not in ("care_sheet", "presence_receipt"):
        raise ValueError("INVALID_DOCUMENT_KIND")
    if not re.fullmatch(r"[a-f0-9]{64}", document_sha256):
        raise ValueError("INVALID_DOCUMENT_SHA256")
    raw = f"print-v1|{tenant_id}|{session_id}|{document_kind}|{document_id}|{document_sha256}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
