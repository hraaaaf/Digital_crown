from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend import database, models
from backend.models_patient_clinical_context import PatientClinicalContext
from backend.routers.auth import require_permission
from backend.schemas.patient_clinical_context import (
    PatientClinicalContextOut,
    PatientClinicalContextUpdate,
)
from backend.services.audit_service import audit_service
from backend.utils.access_control import assert_patient_access


router = APIRouter(tags=["Patients - Clinical Context"])


def _empty_context(patient_id: int, employer_id: int) -> PatientClinicalContextOut:
    return PatientClinicalContextOut(
        patient_id=patient_id,
        employer_id=employer_id,
        weight_kg=None,
        medication_allergy_status="UNKNOWN",
        medication_allergies=None,
        penicillin_allergy_status="UNKNOWN",
        ie_cardiac_risk_category="UNKNOWN",
        renal_context_status="UNKNOWN",
        renal_context_note=None,
        hepatic_context_status="UNKNOWN",
        hepatic_context_note=None,
        pregnancy_status="UNKNOWN",
        breastfeeding_status="UNKNOWN",
        current_medications_status="UNKNOWN",
        current_medications=None,
        updated_at=None,
        updated_by_user_id=None,
    )


@router.get("/{patient_id}/clinical-context", response_model=PatientClinicalContextOut)
def read_patient_clinical_context(
    patient_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients")),
):
    assert_patient_access(patient_id, current_user, db)
    employer_id = current_user.get_employer_id()
    context = db.query(PatientClinicalContext).filter(
        PatientClinicalContext.patient_id == patient_id,
        PatientClinicalContext.employer_id == employer_id,
    ).first()
    if context is None:
        return _empty_context(patient_id, employer_id)
    return context


@router.put("/{patient_id}/clinical-context", response_model=PatientClinicalContextOut)
def update_patient_clinical_context(
    patient_id: int,
    payload: PatientClinicalContextUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients")),
):
    assert_patient_access(patient_id, current_user, db)
    employer_id = current_user.get_employer_id()

    context = db.query(PatientClinicalContext).filter(
        PatientClinicalContext.patient_id == patient_id,
    ).first()
    if context is not None and context.employer_id != employer_id:
        raise HTTPException(status_code=409, detail="Contexte clinique rattaché à un autre cabinet")

    # Preserve fields omitted by older/partial clients; explicit values still update.
    values = payload.model_dump(exclude_unset=True)
    if context is None:
        context = PatientClinicalContext(
            patient_id=patient_id,
            employer_id=employer_id,
            updated_by_user_id=current_user.id,
            **values,
        )
        db.add(context)
    else:
        # Validate the complete post-update state before mutating/persisting it.
        merged = {
            field: getattr(context, field)
            for field in PatientClinicalContextUpdate.model_fields
        }
        merged.update(values)
        validated = PatientClinicalContextUpdate(**merged)
        for field in values:
            setattr(context, field, getattr(validated, field))
        context.updated_by_user_id = current_user.id

    audit_service.log(
        db=db,
        user_id=current_user.id,
        employer_id=employer_id,
        action="UPDATE",
        resource_type="PatientClinicalContext",
        resource_id=str(patient_id),
        details="Mise à jour du contexte clinique structuré de prescription",
    )

    db.commit()
    db.refresh(context)
    return context
