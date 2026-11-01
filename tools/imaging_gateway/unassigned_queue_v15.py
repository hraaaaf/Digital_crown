"""LOT06 B02 — verified encrypted-spool read model, strictly NO patient binding.

Reads the existing HotFolder AES-GCM spool; never scans directories directly,
transfers bytes, signs a receipt or claims to authenticate a Windows peer.
NOT an HTTP route and NOT a substitute for the native IPC/TPM authority.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import re

from tools.imaging_gateway.gateway import GatewayError, HotFolder, SUPPORTED
from tools.imaging_gateway.media_validation import validated_mime

_DIGEST = re.compile(r"^[a-f0-9]{64}$")


@dataclass(frozen=True)
class UnassignedCapture:
    """Only non-PHI opaque metadata. No patient/appointment/filename."""
    id: int
    digest: str
    size: int
    mime: str
    category: str


def read_unassigned(collector: HotFolder, *, limit: int = 25) -> tuple[UnassignedCapture, ...]:
    """Fail closed on any integrity/race failure; no side effects or approval.

    Source is the existing encrypted HotFolder DB and checked ciphertext, not
    a client-supplied list, filename, device claim, or appointment guess.
    """
    if not isinstance(collector, HotFolder) or type(limit) is not int or not 1 <= limit <= 25:
        raise GatewayError("INVALID_UNASSIGNED_QUEUE_REQUEST")
    before = collector.items()
    pending = [row for row in before if row["state"] == "PENDING_CONFIRMATION"][:limit]
    checked: list[UnassignedCapture] = []
    for row in pending:
        item_id, digest, size = row["id"], row["digest"], row["size"]
        mime, category = row["mime"], row["category"]
        if (
            type(item_id) is not int or item_id <= 0
            or not isinstance(digest, str) or _DIGEST.fullmatch(digest) is None
            or type(size) is not int or not 0 < size <= 50 * 1024 * 1024
            or mime not in SUPPORTED or category not in {"PHOTO", "RADIOGRAPH"}
        ):
            raise GatewayError("UNASSIGNED_QUEUE_METADATA_INVALID")
        plaintext = collector.read_verified(item_id)  # checks AES-GCM at rest
        if (len(plaintext) != size
                or hashlib.sha256(plaintext).hexdigest() != digest
                or not validated_mime(plaintext, mime)):
            raise GatewayError("UNASSIGNED_QUEUE_MEDIA_INTEGRITY_DENIED")
        checked.append(UnassignedCapture(item_id, digest, size, mime, category))
    # Another worker may change states or ciphertext while we read. Do not
    # report a snapshot that is already observed to be inconsistent.
    after = {row["id"]: row for row in collector.items()}
    for capture in checked:
        row = after.get(capture.id)
        if (row is None or row["state"] != "PENDING_CONFIRMATION"
                or row["digest"] != capture.digest or row["size"] != capture.size
                or row["mime"] != capture.mime or row["category"] != capture.category):
            raise GatewayError("UNASSIGNED_QUEUE_CHANGED_DURING_READ")
    return tuple(checked)
