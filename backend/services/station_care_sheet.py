from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from backend import models
from backend.services.archive_service import ArchiveService
from backend.services.insurance_submission import INSURANCE_ARCHIVE_KIND

AUTHORIZE_ACTION = "STATION_CARE_SHEET_WITHDRAWAL_AUTHORIZED"
WITHDRAW_ACTION = "STATION_CARE_SHEET_WITHDRAWN"


def _authorization_detail(file_hash: str) -> str:
    return f"Finalized care sheet explicitly authorized for station withdrawal; file_hash={file_hash}."


@dataclass(frozen=True)
class CareSheetState:
    finalized: bool
    withdrawal_authorized: bool


def is_finalized_care_sheet(document: models.DocumentArchive) -> bool:
    clinical_data = document.clinical_data if isinstance(document.clinical_data, dict) else {}
    draft = clinical_data.get("draft") if isinstance(clinical_data.get("draft"), dict) else {}
    render_evidence = (
        clinical_data.get("render_evidence")
        if isinstance(clinical_data.get("render_evidence"), dict)
        else {}
    )
    rendered_hash = str(render_evidence.get("rendered_pdf_sha256") or "")
    return bool(
        document.status == models.DocumentStatus.ACTIF
        and document.is_latest_version is True
        and clinical_data.get("kind") == INSURANCE_ARCHIVE_KIND
        and str(draft.get("status") or "").upper() == "VALIDATED"
        and clinical_data.get("validated_by_practitioner_id") is not None
        and bool(str(clinical_data.get("validated_at") or "").strip())
        and render_evidence.get("renderer") == "PDF_OVERLAY_V1"
        and bool(rendered_hash)
        and rendered_hash == str(document.file_hash or "")
        and str(document.original_filename or document.filename or "").lower().endswith(".pdf")
    )


def withdrawal_authorized(
    db: Session,
    *,
    employer_id: int,
    document_id: int,
) -> bool:
    document = db.query(models.DocumentArchive).filter(
        models.DocumentArchive.id == document_id,
    ).first()
    if document is None or not document.file_hash:
        return False
    return db.query(models.AuditLog.id).filter(
        models.AuditLog.employer_id == employer_id,
        models.AuditLog.action == AUTHORIZE_ACTION,
        models.AuditLog.resource_type == "DocumentArchive",
        models.AuditLog.resource_id == str(document_id),
        models.AuditLog.details == _authorization_detail(str(document.file_hash)),
    ).first() is not None


def authorize_withdrawal(
    db: Session,
    *,
    employer_id: int,
    document: models.DocumentArchive,
    user_id: int,
    ip_address: str | None = None,
) -> bool:
    if not is_finalized_care_sheet(document):
        raise ValueError("CARE_SHEET_NOT_FINALIZED")

    if not document.file_hash:
        raise ValueError("CARE_SHEET_HASH_MISSING")
    detail = _authorization_detail(str(document.file_hash))
    existing = db.query(models.AuditLog.id).filter(
        models.AuditLog.employer_id == employer_id,
        models.AuditLog.action == AUTHORIZE_ACTION,
        models.AuditLog.resource_type == "DocumentArchive",
        models.AuditLog.resource_id == str(document.id),
        models.AuditLog.details == detail,
    ).first()
    if existing is not None:
        return False

    db.add(models.AuditLog(
        user_id=user_id,
        employer_id=employer_id,
        action=AUTHORIZE_ACTION,
        resource_type="DocumentArchive",
        resource_id=str(document.id),
        details=detail,
        ip_address=ip_address,
    ))
    db.commit()
    return True


def care_sheet_state(
    db: Session,
    *,
    employer_id: int,
    document: models.DocumentArchive,
) -> CareSheetState:
    return CareSheetState(
        finalized=is_finalized_care_sheet(document),
        withdrawal_authorized=withdrawal_authorized(
            db,
            employer_id=employer_id,
            document_id=int(document.id),
        ),
    )


def care_sheet_path(db: Session, document: models.DocumentArchive) -> Path:
    path = ArchiveService(db)._resolve_archive_storage_path(document)
    if not path.is_file():
        raise FileNotFoundError(str(path))
    return path
