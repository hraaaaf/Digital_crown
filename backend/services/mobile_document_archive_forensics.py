"""Read-only Pocket archive incident assessment, intended for isolated DB copies.

This is NOT a repair endpoint, replay mechanism or cabinet migration. It never
modifies receipt state, the canonical archive row or a PDF. An unresolved
PROCESSING/REVIEW_REQUIRED always requires human reconciliation.
"""
from __future__ import annotations

import hashlib
import hmac
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend import models
from backend.services.mobile_document_archive_receipts import read_scoped_receipt

_DOCUMENT_TYPES = {
    "ordonnance": models.DocumentType.ORDONNANCE,
    "certificat": models.DocumentType.CERTIFICAT,
    "devis": models.DocumentType.DEVIS,
    "libre": models.DocumentType.DOCUMENT_LIBRE,
}
_MAX_PDF_BYTES = 12 * 1024 * 1024


def inspect_archive_receipt_read_only(
    db: Session, *, tenant_id: int, actor_id: int, device_id: str,
    key: str, media_root: Path,
) -> dict[str, str | bool]:
    """Forensic-only entrypoint: isolated DB, clean session, no autoflush."""
    from backend.core.runtime_safety import is_explicitly_isolated

    if not is_explicitly_isolated(str(db.get_bind().url)):
        raise RuntimeError("Inspection refusée : la base n'est pas explicitement isolée.")
    if db.new or db.dirty or db.deleted:
        raise RuntimeError("Inspection refusée : session SQL avec mutations en attente.")
    with db.no_autoflush:
        return _inspect_receipt_snapshot(
            db, tenant_id=tenant_id, actor_id=actor_id, device_id=device_id,
            key=key, media_root=media_root,
        )


def _inspect_receipt_snapshot(
    db: Session, *, tenant_id: int, actor_id: int, device_id: str,
    key: str, media_root: Path,
) -> dict[str, str | bool]:
    """Read-only minimum-necessary verdict, no PHI, path or PDF exported."""

    receipt = read_scoped_receipt(
        db, tenant_id=tenant_id, actor_id=actor_id, device_id=device_id, key=key,
    )
    if receipt is None:
        raise HTTPException(status_code=404, detail="Reçu introuvable dans ce périmètre.")

    evidence: dict[str, str | bool] = {
        "receipt_state": receipt.state,
        "verified_archive": False,
        "automatic_replay_allowed": False,
        "decision": "HOLD_FOR_MANUAL_REVIEW",
    }
    # A PROCESSING file may exist with no committed SQL row. It must NEVER
    # be inferred from a hash scan, as that risks incorrectly linking data.
    if receipt.state in {"PROCESSING", "REVIEW_REQUIRED"}:
        if receipt.archive_id is not None or receipt.archive_sha256 is not None:
            evidence["decision"] = "INCONSISTENT_RECEIPT_MANUAL_REVIEW"
        return evidence
    if receipt.state != "COMPLETED":
        evidence["decision"] = "UNKNOWN_STATE_MANUAL_REVIEW"
        return evidence
    if receipt.archive_id is None or not receipt.archive_sha256:
        evidence["decision"] = "INCONSISTENT_RECEIPT_MANUAL_REVIEW"
        return evidence

    patient = db.query(models.Patient.id).filter(
        models.Patient.id == receipt.patient_id,
        models.Patient.employer_id == tenant_id,
        models.Patient.deleted_at.is_(None),
    ).first()
    if patient is None:
        evidence["decision"] = "PATIENT_SCOPE_MISMATCH"
        return evidence

    doc = db.query(models.DocumentArchive).filter(
        models.DocumentArchive.id == receipt.archive_id,
        models.DocumentArchive.patient_id == receipt.patient_id,
        models.DocumentArchive.uploaded_by_id == actor_id,
        models.DocumentArchive.status == models.DocumentStatus.ACTIF,
    ).first()
    if (
        doc is None
        or doc.document_type != _DOCUMENT_TYPES.get(receipt.document_type)
        or not hmac.compare_digest(str(doc.file_hash or ""), receipt.archive_sha256)
    ):
        evidence["decision"] = "ARCHIVE_ROW_MISMATCH"
        return evidence

    path = str(doc.file_path or "")
    if not path.startswith("static/archives/"):
        evidence["decision"] = "UNSAFE_ARCHIVE_PATH"
        return evidence
    root = (Path(media_root) / "archives").resolve()
    candidate = (root / path[len("static/archives/"):]).resolve()
    if not candidate.is_relative_to(root):
        evidence["decision"] = "UNSAFE_ARCHIVE_PATH"
        return evidence
    try:
        size = candidate.stat().st_size
        if not 5 <= size <= _MAX_PDF_BYTES:
            evidence["decision"] = "MISSING_OR_INVALID_PDF"
            return evidence
        content = candidate.read_bytes()
    except OSError:
        evidence["decision"] = "MISSING_OR_INVALID_PDF"
        return evidence
    if (
        len(content) != size
        or not content.startswith(b"%PDF-")
        or not hmac.compare_digest(hashlib.sha256(content).hexdigest(), receipt.archive_sha256)
    ):
        evidence["decision"] = "PDF_HASH_MISMATCH"
        return evidence
    evidence["verified_archive"] = True
    evidence["decision"] = "EXISTING_ARCHIVE_VERIFIED"
    return evidence
