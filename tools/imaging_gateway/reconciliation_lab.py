"""LOT06-M: read-only synthetic divergence classifier; NOT reconciliation.

Caller-provided anchor/epoch are NOT authenticated here. No I/O, services, SQL,
disk persistence, anti-rollback proof, human authorization or clinical ACK.
"""
from dataclasses import dataclass
import hmac

from . import journal_lab as journal


@dataclass(frozen=True)
class Finding:
    code: str
    matching_phase: str | None = None


def inspect(local: journal.Journal | None,
            assumed_anchor: journal.TrustedAnchor | None, *,
            expected_epoch: str, supplied_epoch: str | None,
            journal_key: bytes, legacy_key: bytes, keys: dict) -> Finding:
    """Classify only. No mutation, promotion, receipt or auto-recovery."""
    if (type(expected_epoch) is not str or not expected_epoch
            or type(supplied_epoch) is not str or not supplied_epoch
            or type(assumed_anchor) is not journal.TrustedAnchor):
        return Finding("AUTHORITY_UNKNOWN")
    if not hmac.compare_digest(expected_epoch, supplied_epoch):
        return Finding("EPOCH_CONFLICT")
    head = assumed_anchor
    if (type(head.sequence) is not int or head.sequence < 1
            or type(head.mac) is not str or len(head.mac) != 64
            or any(c not in "0123456789abcdef" for c in head.mac)):
        return Finding("AUTHORITY_UNKNOWN")
    if (type(local) is not journal.Journal or type(local.records) is not tuple
            or not 1 <= len(local.records) <= 256):
        return Finding("LOCAL_INVALID")
    count = len(local.records)
    if count < head.sequence:
        return Finding("AUTHORITY_AHEAD")
    if count > head.sequence:
        return Finding("LOCAL_AHEAD")
    last = local.records[-1]
    if (type(last) is not journal.Record or type(last.mac) is not str
            or len(last.mac) != 64):
        return Finding("LOCAL_INVALID")
    if not hmac.compare_digest(last.mac, head.mac):
        return Finding("HEAD_MISMATCH")
    try:
        state = journal.verify_chain(local, head, journal_key=journal_key,
                                     legacy_key=legacy_key, keys=keys)
    except (journal.JournalLabError, TypeError, ValueError, AttributeError):
        return Finding("INTEGRITY_OR_KEY_FAILURE")
    return Finding("VERIFIED_MATCH", state.phase)
