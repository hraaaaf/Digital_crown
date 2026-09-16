"""Authenticated CNSS insurance-submission facade.

The UI never becomes an authority for clinical, financial, NGAP or template facts.
Preparation is rebuilt from the archived Honoraires source, practitioner validation
rechecks the authoritative DB/store state, and finalization renders only the exact
hash-bound CNSS profile before archiving the PDF.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from backend import database, models
from backend.core.media_paths import get_media_root
from backend.routers.auth import require_permission
from backend.schemas.insurance_submission import InsuranceOrganization, InsuranceSubmissionDraft
from backend.services.insurance_cnss_610_1_04_profile import (
    CNSS_610_1_04_PROFILE_V1,
    CNSS_610_1_04_TEMPLATE_SHA256,
)
from backend.services.insurance_finalization import finalize_insurance_submission_pdf
from backend.services.insurance_preparation import prepare_insurance_draft_from_honoraires
from backend.services.insurance_source_store import load_stored_insurance_source
from backend.services.insurance_template_registry import CNSS_610_1_04, LockedInsuranceTemplate
from backend.services.insurance_validation import validate_insurance_draft_by_practitioner
from backend.services.ngap_reference import DENTAL_NGAP_PRIMARY_PENDING
from backend.utils.access_control import assert_patient_access

router = APIRouter(tags=["Insurance submissions"])


class InsurancePrepareRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    honoraires_document_id: int
    organization: InsuranceOrganization


class InsuranceFinalizeResponse(BaseModel):
    document_id: int
    is_new_version: bool
    file_hash: str
    original_filename: str


def get_insurance_source_store_root() -> Path:
    """Use the same canonical private store as ``scripts/lock_insurance_source.py``."""
    return get_media_root() / "insurance_sources"


def _locked_cnss_template(root: Path) -> LockedInsuranceTemplate:
    loaded = load_stored_insurance_source(
        root=root,
        namespace="template-cnss",
        version=CNSS_610_1_04.version,
        sha256=CNSS_610_1_04_TEMPLATE_SHA256,
    )
    manifest = loaded.manifest
    if manifest.get("kind") != "INSURANCE_TEMPLATE":
        raise ValueError("CNSS stored source kind mismatch")
    if manifest.get("organization") != "CNSS":
        raise ValueError("CNSS stored source organization mismatch")
    if manifest.get("trust") != CNSS_610_1_04.trust.value:
        raise ValueError("CNSS stored source trust mismatch")
    if not str(manifest.get("cabinet_validated_by") or "").strip():
        raise ValueError("CNSS cabinet-validated source has no validator identity")
    return LockedInsuranceTemplate(
        definition=CNSS_610_1_04,
        source_url=str(manifest.get("source_url") or ""),
        sha256=loaded.stored.sha256,
        page_count=int(manifest.get("page_count") or 0),
    )


def _prepare_from_authoritative_sources(
    db: Session,
    *,
    honoraires_document_id: int,
    organization: InsuranceOrganization,
    source_store_root: Path,
) -> InsuranceSubmissionDraft:
    if organization != InsuranceOrganization.CNSS:
        raise ValueError("Insurance UI preparation is currently enabled for CNSS only")
    locked_template = _locked_cnss_template(source_store_root)
    return prepare_insurance_draft_from_honoraires(
        db,
        honoraires_document_id=honoraires_document_id,
        organization=organization,
        locked_template=locked_template,
        ngap_reference_version=DENTAL_NGAP_PRIMARY_PENDING.version,
    )


def _http_422(exc: ValueError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.post("/prepare", response_model=InsuranceSubmissionDraft)
def prepare_insurance_submission(
    request: InsurancePrepareRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("accounting")),
):
    document = db.query(models.DocumentArchive).filter(
        models.DocumentArchive.id == int(request.honoraires_document_id),
        models.DocumentArchive.document_type == models.DocumentType.NOTE_HONORAIRES,
    ).first()
    if document is None:
        raise HTTPException(status_code=404, detail="Note d'honoraires introuvable")
    assert_patient_access(document.patient_id, current_user, db)
    try:
        return _prepare_from_authoritative_sources(
            db,
            honoraires_document_id=document.id,
            organization=request.organization,
            source_store_root=get_insurance_source_store_root(),
        )
    except ValueError as exc:
        raise _http_422(exc) from exc


@router.post("/validate", response_model=InsuranceSubmissionDraft)
def validate_insurance_submission(
    draft: InsuranceSubmissionDraft,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("accounting")),
):
    assert_patient_access(draft.patient_id, current_user, db)
    try:
        return validate_insurance_draft_by_practitioner(
            db,
            draft=draft,
            practitioner_id=current_user.id,
            source_store_root=get_insurance_source_store_root(),
        )
    except ValueError as exc:
        raise _http_422(exc) from exc


@router.post("/finalize", response_model=InsuranceFinalizeResponse)
def finalize_insurance_submission(
    draft: InsuranceSubmissionDraft,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("accounting")),
):
    assert_patient_access(draft.patient_id, current_user, db)
    if draft.validated_by_practitioner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seul le praticien ayant validé la feuille peut la finaliser",
        )
    if draft.organization != InsuranceOrganization.CNSS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Insurance PDF finalization is currently enabled for CNSS only",
        )

    filename = f"Feuille_soins_CNSS_{draft.patient_id}_{draft.honoraires_document_id}.pdf"
    try:
        document, is_new_version, _ = finalize_insurance_submission_pdf(
            db,
            draft=draft,
            source_store_root=get_insurance_source_store_root(),
            overlay_profile=CNSS_610_1_04_PROFILE_V1,
            filename=filename,
            uploaded_by_id=current_user.id,
        )
    except ValueError as exc:
        raise _http_422(exc) from exc

    return InsuranceFinalizeResponse(
        document_id=int(document.id),
        is_new_version=bool(is_new_version),
        file_hash=str(document.file_hash),
        original_filename=str(document.original_filename),
    )
