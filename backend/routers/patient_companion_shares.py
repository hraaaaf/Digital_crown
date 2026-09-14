from __future__ import annotations

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend import models
from backend.models_media_core import ClinicalAsset
from backend.models_patient_companion import (
    PatientCompanionAccess,
    PatientCompanionIdentity,
    PatientCompanionShareGrant,
)
from backend.routers.auth import get_current_user, has_permission
from backend.routers.patient_companion_common import (
    get_db,
    patient_identity,
    principal_for_access,
    staff_patient_or_404,
)
from backend.services.audit_service import audit_service

router = APIRouter()


class ShareGrantRequest(BaseModel):
    resource_type: Literal["document", "media"]
    resource_id: int = Field(gt=0)


def _shareable_resource_or_404(
    db: Session,
    *,
    employer_id: int,
    patient_id: int,
    resource_type: str,
    resource_id: int,
):
    if resource_type == "document":
        resource = (
            db.query(models.DocumentArchive)
            .join(models.Patient, models.Patient.id == models.DocumentArchive.patient_id)
            .filter(
                models.DocumentArchive.id == resource_id,
                models.DocumentArchive.patient_id == patient_id,
                models.DocumentArchive.status == models.DocumentStatus.ACTIF,
                models.Patient.id == patient_id,
                models.Patient.employer_id == employer_id,
                models.Patient.deleted_at.is_(None),
            )
            .first()
        )
    elif resource_type == "media":
        resource = db.query(ClinicalAsset).filter(
            ClinicalAsset.id == resource_id,
            ClinicalAsset.employer_id == employer_id,
            ClinicalAsset.patient_id == patient_id,
        ).first()
    else:
        resource = None
    if resource is None:
        raise HTTPException(status_code=404, detail="Ressource introuvable.")
    return resource


@router.post("/admin/patients/{patient_id}/shares", status_code=201)
def grant_patient_share(
    patient_id: int,
    body: ShareGrantRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    patient = staff_patient_or_404(db, current_user, patient_id)
    employer_id = int(current_user.get_employer_id())
    resource = _shareable_resource_or_404(
        db,
        employer_id=employer_id,
        patient_id=patient.id,
        resource_type=body.resource_type,
        resource_id=body.resource_id,
    )
    if body.resource_type == "document":
        from backend.routers.documents import require_document_permission
        doc_type = getattr(resource.document_type, "value", resource.document_type)
        require_document_permission(str(doc_type), current_user)

    grant = db.query(PatientCompanionShareGrant).filter(
        PatientCompanionShareGrant.employer_id == employer_id,
        PatientCompanionShareGrant.patient_id == patient.id,
        PatientCompanionShareGrant.resource_type == body.resource_type,
        PatientCompanionShareGrant.resource_id == body.resource_id,
    ).first()
    if grant is None:
        grant = PatientCompanionShareGrant(
            employer_id=employer_id,
            patient_id=patient.id,
            resource_type=body.resource_type,
            resource_id=body.resource_id,
            granted_by_user_id=current_user.id,
        )
        db.add(grant)
    else:
        grant.revoked_at = None
        grant.granted_by_user_id = current_user.id
    db.commit()
    db.refresh(grant)

    audit_service.log(
        db=db,
        user_id=current_user.id,
        employer_id=employer_id,
        action="PATIENT_COMPANION_SHARE_GRANTED",
        resource_type=body.resource_type,
        resource_id=str(body.resource_id),
    )
    return {
        "share_id": grant.public_id,
        "resource_type": grant.resource_type,
        "resource_id": grant.resource_id,
    }


@router.delete("/admin/patients/{patient_id}/shares/{share_id}")
def revoke_patient_share(
    patient_id: int,
    share_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    patient = staff_patient_or_404(db, current_user, patient_id)
    employer_id = int(current_user.get_employer_id())
    grant = db.query(PatientCompanionShareGrant).filter(
        PatientCompanionShareGrant.public_id == share_id,
        PatientCompanionShareGrant.employer_id == employer_id,
        PatientCompanionShareGrant.patient_id == patient.id,
    ).first()
    if grant is None:
        raise HTTPException(status_code=404, detail="Partage introuvable.")
    if grant.revoked_at is None:
        grant.revoked_at = datetime.utcnow()
        db.commit()
    audit_service.log(
        db=db,
        user_id=current_user.id,
        employer_id=employer_id,
        action="PATIENT_COMPANION_SHARE_REVOKED",
        resource_type=grant.resource_type,
        resource_id=str(grant.resource_id),
    )
    return {"status": "revoked", "share_id": grant.public_id}


@router.get("/contexts/{access_id}/shares")
def list_patient_shares(
    access_id: str,
    identity: PatientCompanionIdentity = Depends(patient_identity),
    db: Session = Depends(get_db),
):
    principal, _patient = principal_for_access(db, identity, access_id)
    grants = db.query(PatientCompanionShareGrant).filter(
        PatientCompanionShareGrant.employer_id == principal.employer_id,
        PatientCompanionShareGrant.patient_id == principal.patient_id,
        PatientCompanionShareGrant.revoked_at.is_(None),
    ).order_by(PatientCompanionShareGrant.created_at.desc()).all()

    items = []
    for grant in grants:
        try:
            resource = _shareable_resource_or_404(
                db,
                employer_id=principal.employer_id,
                patient_id=principal.patient_id,
                resource_type=grant.resource_type,
                resource_id=grant.resource_id,
            )
        except HTTPException:
            continue
        if grant.resource_type == "document":
            items.append({
                "share_id": grant.public_id,
                "resource_type": "document",
                "resource_id": resource.id,
                "title": resource.title or resource.original_filename,
                "document_type": getattr(resource.document_type, "value", resource.document_type),
                "created_at": resource.created_at,
            })
        else:
            items.append({
                "share_id": grant.public_id,
                "resource_type": "media",
                "resource_id": resource.id,
                "asset_type": resource.asset_type,
                "mime_type": resource.mime_type,
                "captured_at": resource.captured_at,
                "created_at": resource.created_at,
            })
    return {"items": items}


@router.post("/admin/accesses/{access_id}/revoke")
def revoke_patient_access(
    access_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not has_permission(current_user, "patients"):
        raise HTTPException(status_code=403, detail="Permission patients requise.")
    employer_id = int(current_user.get_employer_id())
    access = db.query(PatientCompanionAccess).filter(
        PatientCompanionAccess.public_id == access_id,
        PatientCompanionAccess.employer_id == employer_id,
    ).first()
    if access is None:
        raise HTTPException(status_code=404, detail="Accès patient introuvable.")
    staff_patient_or_404(db, current_user, access.patient_id)
    if access.revoked_at is None:
        access.revoked_at = datetime.utcnow()
        db.commit()
    audit_service.log(
        db=db,
        user_id=current_user.id,
        employer_id=employer_id,
        action="PATIENT_COMPANION_ACCESS_REVOKED",
        resource_type="PatientCompanionAccess",
        resource_id=access.public_id,
    )
    return {"status": "revoked", "access_id": access.public_id}
