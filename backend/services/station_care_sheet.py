"""V1.5-04.3 — audited, byte-verified withdrawal of a finalized care sheet.

Station never generates, edits or signs a clinical document. No raw archive path
or clinical approval flag from a patient/device may grant retrieval.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from sqlalchemy.orm import Session

from backend import models
from backend.core.media_paths import get_media_root
from backend.services.insurance_submission import INSURANCE_ARCHIVE_KIND

FINALIZED_ACTION = "STATION_CARE_SHEET_TRUSTED_FINALIZATION_V1"
AUTHORIZE_ACTION = "STATION_CARE_SHEET_WITHDRAWAL_AUTHORIZED"
WITHDRAW_ACTION = "STATION_CARE_SHEET_WITHDRAWN"
MAX_PDF_BYTES = 20 * 1024 * 1024
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _claim(document: models.DocumentArchive) -> str:
    return f"document_id={int(document.id)};patient_id={int(document.patient_id)};sha256={document.file_hash}"


def record_trusted_finalization(db: Session, document: models.DocumentArchive, *, employer_id: int, practitioner_id: int) -> None:
    """Only call from the canonical insurance finalize endpoint *after* DB-backed rerender."""
    if document.uploaded_by_id != practitioner_id or not _SHA256_RE.fullmatch(str(document.file_hash or "")):
        raise ValueError("CARE_SHEET_FINALIZATION_SOURCE_MISMATCH")
    db.add(models.AuditLog(
        employer_id=employer_id, user_id=practitioner_id,
        action=FINALIZED_ACTION, resource_type="DocumentArchive",
        resource_id=str(document.id), details=_claim(document),
    ))
    db.commit()


@dataclass(frozen=True)
class CareSheetState:
    finalized: bool
    withdrawal_authorized: bool


def _finalizer_id(document: models.DocumentArchive) -> int | None:
    data = document.clinical_data if isinstance(document.clinical_data, dict) else {}
    draft = data.get("draft") if isinstance(data.get("draft"), dict) else {}
    evidence = data.get("render_evidence") if isinstance(data.get("render_evidence"), dict) else {}
    raw = data.get("validated_by_practitioner_id")
    if isinstance(raw, bool) or not isinstance(raw, int) or raw <= 0:
        return None
    if not (
        document.document_type == models.DocumentType.AUTRE
        and document.status == models.DocumentStatus.ACTIF
        and document.is_latest_version is True
        and document.deleted_at is None
        and data.get("kind") == INSURANCE_ARCHIVE_KIND
        and draft.get("status") == "VALIDATED"
        and data.get("validated_at")
        and evidence.get("renderer") == "PDF_OVERLAY_V1"
        and evidence.get("rendered_pdf_sha256") == document.file_hash
        and _SHA256_RE.fullmatch(str(document.file_hash or ""))
        and document.uploaded_by_id == raw
        and str(document.filename or "").lower().endswith(".pdf")
    ):
        return None
    return raw


def _has_event(db: Session, document: models.DocumentArchive, *, employer_id: int, action: str, user_id: int | None = None) -> bool:
    q = db.query(models.AuditLog.id).filter(
        models.AuditLog.employer_id == employer_id,
        models.AuditLog.action == action,
        models.AuditLog.resource_type == "DocumentArchive",
        models.AuditLog.resource_id == str(document.id),
        models.AuditLog.details == _claim(document),
    )
    if user_id is not None:
        q = q.filter(models.AuditLog.user_id == user_id)
    return q.first() is not None


def is_finalized_care_sheet(db: Session, document: models.DocumentArchive, *, employer_id: int) -> bool:
    validator = _finalizer_id(document)
    if validator is None:
        return False
    patient = db.query(models.Patient.id).filter(
        models.Patient.id == document.patient_id,
        models.Patient.employer_id == employer_id,
        models.Patient.deleted_at.is_(None),
    ).first()
    return patient is not None and _has_event(
        db, document, employer_id=employer_id, action=FINALIZED_ACTION, user_id=validator,
    )


def care_sheet_state(db: Session, document: models.DocumentArchive, *, employer_id: int) -> CareSheetState:
    finalized = is_finalized_care_sheet(db, document, employer_id=employer_id)
    return CareSheetState(
        finalized=finalized,
        withdrawal_authorized=finalized and _has_event(
            db, document, employer_id=employer_id, action=AUTHORIZE_ACTION,
        ),
    )


def authorize_withdrawal(db: Session, document: models.DocumentArchive, *, employer_id: int, user_id: int, ip_address: str | None = None) -> bool:
    if not is_finalized_care_sheet(db, document, employer_id=employer_id):
        raise ValueError("CARE_SHEET_NOT_FINALIZED")
    if _finalizer_id(document) != user_id:
        raise ValueError("CARE_SHEET_AUTHORIZER_NOT_FINALIZER")
    if _has_event(db, document, employer_id=employer_id, action=AUTHORIZE_ACTION):
        return False
    db.add(models.AuditLog(
        user_id=user_id, employer_id=employer_id, action=AUTHORIZE_ACTION,
        resource_type="DocumentArchive", resource_id=str(document.id),
        details=_claim(document), ip_address=ip_address,
    ))
    db.commit()
    return True


def verified_care_sheet_bytes(document: models.DocumentArchive) -> bytes:
    """Read once and serve those exact verified bytes, never a deferred FileResponse."""
    stored = str(document.file_path or "")
    if "\\" in stored or not stored.startswith("static/archives/"):
        raise ValueError("CARE_SHEET_PATH_NOT_CANONICAL")
    relative = PurePosixPath(stored[len("static/archives/"):])
    if not relative.parts or any(part in ("", ".", "..") for part in relative.parts):
        raise ValueError("CARE_SHEET_PATH_TRAVERSAL")
    root = (get_media_root() / "archives").resolve()
    file_path = root.joinpath(*relative.parts)
    if file_path.is_symlink() or any(parent.is_symlink() for parent in (file_path, *file_path.parents) if parent != root and parent != root.parent):
        raise ValueError("CARE_SHEET_SYMLINK_REJECTED")
    resolved = file_path.resolve()
    if not resolved.is_relative_to(root):
        raise ValueError("CARE_SHEET_PATH_TRAVERSAL")
    if not resolved.is_file():
        raise ValueError("CARE_SHEET_FILE_MISSING")
    size = resolved.stat().st_size
    if size <= 0 or size > MAX_PDF_BYTES or size != document.file_size:
        raise ValueError("CARE_SHEET_FILE_SIZE_INVALID")
    if not _SHA256_RE.fullmatch(str(document.file_hash or "")):
        raise ValueError("CARE_SHEET_HASH_INVALID")
    # open/read into an immutable byte snapshot; response is generated from this
    # snapshot, and is not subject to FileResponse reopen/swap after auth.
    with resolved.open("rb") as handle:
        contents = handle.read(MAX_PDF_BYTES + 1)
    if len(contents) != size or not contents.startswith(b"%PDF") or hashlib.sha256(contents).hexdigest() != document.file_hash:
        raise ValueError("CARE_SHEET_CONTENT_HASH_MISMATCH")
    return contents
