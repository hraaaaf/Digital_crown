"""Non-authorizing operator triage of Pocket archive inventory (local FUE-0).

Consumes only the existing read-only inventory. Does not access a database,
media, patient records or network; does not approve repairs, replay or restore.
Never copies source paths, clinical IDs or hashes into its returned report.
"""
from __future__ import annotations

from collections import Counter

_ALLOWED_SOURCE = {"SQL", "ZIP", "RECEIPT"}
_ALLOWED_STATUS = {"MATCHED", "REVIEW_REQUIRED"}
_ALLOWED_MANIFEST = {"REVIEW_REQUIRED", "BYTE_INVENTORY_MATCHED_NOT_RESTORE_APPROVED"}
_ALLOWED_REASONS = {
    "NO_ARCHIVE_TABLE", "ENTRY_LIMIT", "UNSUPPORTED_SQL_PATH", "AMBIGUOUS_PATH",
    "MISSING_MEDIA", "CASE_ALIAS", "UNSAFE_MEMBER", "FILE_TOO_LARGE",
    "UNREADABLE_MEMBER", "SIZE_DISAGREEMENT", "INVALID_PDF_HEADER",
    "BAD_SQL_METADATA", "SIZE_MISMATCH", "SHA256_MISMATCH",
    "INCOMPLETE_RECEIPT", "AMBIGUOUS_ZIP_MEMBER", "UNLINKED_MEDIA",
    "AMBIGUOUS_OR_UNSAFE_MEMBER",
}
_MAX_ENTRIES = 40000


def _decision(kind: str, *, matched: int = 0, flagged: int = 0,
              reasons: tuple[str, ...] = ()) -> dict:
    """Strictly non-authorizing projection; no clinical identifiers escape."""
    return {
        "decision": kind,
        "operator_gate": "HUMAN_REVIEW_REQUIRED",
        "allow_archive_replay": False,
        "allow_sql_mutation": False,
        "allow_media_delete": False,
        "allow_reassociation": False,
        "allow_restore": False,
        "allow_clinical_release": False,
        "matched_count": matched,
        "review_count": flagged,
        "reason_codes": list(reasons),
    }


def triage_pocket_document_inventory(manifest: object) -> dict:
    """Classify a *diagnostic* inventory, never grant automatic clearance.

    Invalid, incomplete or contradictory input stays HOLD. Not an API endpoint.
    Even all byte-level matches are evidence-only, NOT proof of clinical safety.
    """
    if (not isinstance(manifest, dict) or not isinstance(manifest.get("status"), str)
            or manifest.get("status") not in _ALLOWED_MANIFEST):
        return _decision("HOLD_MANUAL_REVIEW", reasons=("INVALID_MANIFEST",))
    entries = manifest.get("entries")
    if not isinstance(entries, list) or not 0 < len(entries) <= _MAX_ENTRIES:
        return _decision("HOLD_MANUAL_REVIEW", reasons=("EMPTY_OR_OVERSIZED_INVENTORY",))
    counts = Counter()
    reasons = set()
    for entry in entries:
        if not isinstance(entry, dict):
            return _decision("HOLD_MANUAL_REVIEW", reasons=("INVALID_ENTRY",))
        source, status = entry.get("source"), entry.get("status")
        if (not isinstance(source, str) or not isinstance(status, str)
                or source not in _ALLOWED_SOURCE or status not in _ALLOWED_STATUS):
            return _decision("HOLD_MANUAL_REVIEW", reasons=("INVALID_ENTRY",))
        reason = entry.get("reason")
        if status == "MATCHED":
            if source != "SQL" or reason is not None:
                return _decision("HOLD_MANUAL_REVIEW", reasons=("INCONSISTENT_ENTRY",))
            counts["matched"] += 1
        else:
            counts["flagged"] += 1
            reasons.add(reason if isinstance(reason, str) and reason in _ALLOWED_REASONS
                        else "UNKNOWN_ANOMALY")
    if manifest.get("status") == "REVIEW_REQUIRED":
        if counts["flagged"] == 0:
            reasons.add("INCONSISTENT_MANIFEST")
        # A top-level reason can be ENTRY_LIMIT or another generic string;
        # never expose free-form source content as an error message.
        return _decision("HOLD_MANUAL_REVIEW", matched=counts["matched"],
                         flagged=counts["flagged"], reasons=tuple(sorted(reasons)))
    if counts["flagged"] or manifest.get("reason") is not None:
        return _decision("HOLD_MANUAL_REVIEW", matched=counts["matched"],
                         flagged=counts["flagged"], reasons=("INCONSISTENT_MANIFEST",))
    return _decision("BYTE_MATCH_EVIDENCE_ONLY", matched=counts["matched"])
