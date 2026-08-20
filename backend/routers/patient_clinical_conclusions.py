from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend import database, models
from backend.models_clinical_p3 import ClinicalConclusion
from backend.routers.auth import is_superadmin_user, require_permission
from backend.schemas.clinical_conclusion import ClinicalConclusionCreate, ClinicalConclusionOut
from backend.services.audit_service import audit_service
from backend.utils.access_control import assert_patient_access


router = APIRouter()


def _require_practitioner(current_user: models.User) -> None:
    if is_superadmin_user(current_user):
        return
    role = current_user.role.value if hasattr(current_user.role, "value") else current_user.role
    if role not in ("DENTISTE", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seul un dentiste/admin peut retenir une conclusion clinique.",
        )


@router.get("/{patient_id}/clinical-conclusions", response_model=List[ClinicalConclusionOut])
def list_clinical_conclusions(
    patient_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("clinical")),
):
    assert_patient_access(patient_id, current_user, db)
    return (
        db.query(ClinicalConclusion)
        .filter(ClinicalConclusion.patient_id == patient_id)
        .order_by(ClinicalConclusion.created_at.desc(), ClinicalConclusion.id.desc())
        .limit(limit)
        .all()
    )


@router.post(
    "/{patient_id}/clinical-conclusions",
    response_model=ClinicalConclusionOut,
    status_code=status.HTTP_201_CREATED,
)
def create_clinical_conclusion(
    patient_id: int,
    payload: ClinicalConclusionCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("clinical")),
):
    """Persist a conclusion only after an explicit practitioner submission.

    There is intentionally no endpoint that auto-promotes assistant output, and no
    update/delete route: corrections are new append-only conclusions so history remains
    reconstructible.
    """
    assert_patient_access(patient_id, current_user, db)
    _require_practitioner(current_user)

    record = ClinicalConclusion(
        patient_id=patient_id,
        conclusion_text=payload.conclusion_text,
        proposal_text=payload.proposal_text,
        proposal_source=payload.proposal_source,
        validated_by=current_user.id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    audit_service.log(
        db=db,
        user_id=current_user.id,
        employer_id=current_user.get_employer_id(),
        action="CREATE",
        resource_type="ClinicalConclusion",
        resource_id=str(record.id),
        details=(
            f"patient_id={patient_id} proposal_present={bool(payload.proposal_text)} "
            f"proposal_source={payload.proposal_source or 'none'} conclusion_length={len(payload.conclusion_text)}"
        ),
    )
    return record
