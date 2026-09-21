from __future__ import annotations

import pathlib

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.models_patient_companion import PatientCompanionAccess, PatientCompanionIdentity
from backend.routers.patient_companion_common import get_db, patient_identity, principal_for_access
from backend.services.audit_service import audit_service
from backend.services.patient_companion_finance import project_finance, resolve_shared_invoice
from backend.core.media_paths import get_media_root

router = APIRouter()
_BACKEND_DIR = pathlib.Path(__file__).parent.parent
_MEDIA_DIR = get_media_root()


def _active_access(
    db: Session,
    identity: PatientCompanionIdentity,
    access_id: str,
) -> PatientCompanionAccess:
    principal, _patient = principal_for_access(db, identity, access_id)
    access = db.query(PatientCompanionAccess).filter(
        PatientCompanionAccess.public_id == principal.access_id,
        PatientCompanionAccess.identity_id == principal.identity_id,
        PatientCompanionAccess.employer_id == principal.employer_id,
        PatientCompanionAccess.patient_id == principal.patient_id,
        PatientCompanionAccess.revoked_at.is_(None),
    ).first()
    if access is None:
        raise HTTPException(status_code=404, detail="Contexte patient introuvable.")
    return access


@router.get("/contexts/{access_id}/finance")
def patient_finance(
    access_id: str,
    response: Response,
    identity: PatientCompanionIdentity = Depends(patient_identity),
    db: Session = Depends(get_db),
):
    access = _active_access(db, identity, access_id)
    response.headers["Cache-Control"] = "no-store"
    return project_finance(db, access)


def _absolute_document_path(raw_path: str) -> pathlib.Path:
    path = pathlib.Path(raw_path)
    if path.is_absolute():
        return path
    if raw_path.startswith("static/archives/") or raw_path.startswith("static/documents/"):
        return _MEDIA_DIR / raw_path.replace("static/", "", 1)
    return _BACKEND_DIR / raw_path


@router.get("/contexts/{access_id}/finance/invoices/{share_id}/download")
def patient_finance_invoice_download(
    access_id: str,
    share_id: str,
    identity: PatientCompanionIdentity = Depends(patient_identity),
    db: Session = Depends(get_db),
):
    access = _active_access(db, identity, access_id)
    resolved = resolve_shared_invoice(db, access, share_id)
    if resolved is None:
        raise HTTPException(status_code=404, detail="Facture introuvable.")
    _share, document = resolved
    path = _absolute_document_path(document.file_path)
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Fichier de facture introuvable.")

    audit_service.log(
        db=db,
        user_id=None,
        employer_id=access.employer_id,
        action="PATIENT_COMPANION_INVOICE_DOWNLOADED",
        resource_type="DocumentArchive",
        resource_id=str(document.id),
        details=f"patient={access.patient_id} access={access.public_id}",
    )
    file_response = FileResponse(path=str(path), filename=document.original_filename or document.filename)
    file_response.headers["Cache-Control"] = "no-store"
    return file_response
