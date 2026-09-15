"""Authenticated insurance-submission preparation facade.

The UI never becomes an authority for clinical, financial, NGAP or template facts.
Preparation is rebuilt from the archived Honoraires source on every request.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from backend import database, models
from backend.routers.auth import has_permission, require_permission
from backend.schemas.insurance_submission import InsuranceOrganization, InsuranceSubmissionDraft
from backend.services.insurance_preparation import prepare_insurance_draft_from_honoraires
from backend.services.insurance_source_store import load_stored_insurance_source
from backend.services.insurance_template_registry import LockedInsuranceTemplate, CNSS_610_1_04
from backend.services.insurance_cnss_610_1_04_profile import CNSS_610_1_04_TEMPLATE_SHA256
from backend.services.ngap_reference import DENTAL_NGAP_PRIMARY_PENDING
from backend.utils.access_control import assert_patient_access
from backend.core.paths import AppPaths

router = APIRouter(tags=["Insurance submissions"])


class InsurancePrepareRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    honoraires_document_id: int
    organization: InsuranceOrganization


def get_insurance_source_store_root() -> Path:
    """Canonical private cabinet store for locked insurer and NGAP source binaries."""
    return AppPaths.get_user_data_dir() / "insurance_sources"


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
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
