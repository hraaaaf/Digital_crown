from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend import database, models
from backend.models_clinic_p2 import PatientPractitionerAssignment
from backend.routers.auth import require_permission
from backend.services.practitioner_policy import (
    is_assignable_practitioner,
    practitioner_payload,
    validate_practitioner,
)
from backend.utils.access_control import assert_patient_access


router = APIRouter()


class PatientPractitionerAssignmentIn(BaseModel):
    practitioner_id: Optional[int] = None


def _is_assignable_practitioner(user: models.User, employer_id: int) -> bool:
    """Backward-compatible alias for the shared P3 practitioner policy."""
    return is_assignable_practitioner(user, employer_id)


def _validate_practitioner(db: Session, employer_id: int, practitioner_id: int) -> models.User:
    """Backward-compatible alias for the shared P3 practitioner policy."""
    return validate_practitioner(db, employer_id, practitioner_id)


def _practitioner_payload(user: models.User) -> dict:
    """Backward-compatible alias for the shared P3 practitioner payload."""
    return practitioner_payload(user)


@router.get("/_clinic/practitioners")
def list_patient_practitioners(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients")),
):
    """Plan-independent practitioner directory for patient clinical attribution."""
    employer_id = current_user.get_employer_id()
    candidates = db.query(models.User).filter(
        (models.User.id == employer_id) | (models.User.employer_id == employer_id)
    ).all()
    practitioners = [user for user in candidates if is_assignable_practitioner(user, employer_id)]
    practitioners.sort(key=lambda user: (0 if user.id == employer_id else 1, (user.nom_complet or user.email or "").lower()))
    return [practitioner_payload(user) for user in practitioners]


@router.get("/{patient_id}/practitioner")
def get_patient_practitioner(
    patient_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients")),
):
    assert_patient_access(patient_id, current_user, db)
    assignment = db.query(PatientPractitionerAssignment).filter(
        PatientPractitionerAssignment.patient_id == patient_id,
        PatientPractitionerAssignment.employer_id == current_user.get_employer_id(),
    ).first()
    if not assignment or assignment.practitioner_id is None:
        return {"patient_id": patient_id, "practitioner": None}
    practitioner = db.query(models.User).filter(models.User.id == assignment.practitioner_id).first()
    return {
        "patient_id": patient_id,
        "practitioner": practitioner_payload(practitioner) if practitioner else None,
    }


@router.put("/{patient_id}/practitioner")
def set_patient_practitioner(
    patient_id: int,
    payload: PatientPractitionerAssignmentIn,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients")),
):
    """Assign or clear a patient referent without altering the canonical patient row."""
    assert_patient_access(patient_id, current_user, db)
    employer_id = current_user.get_employer_id()
    practitioner = None
    if payload.practitioner_id is not None:
        practitioner = validate_practitioner(db, employer_id, payload.practitioner_id)

    assignment = db.query(PatientPractitionerAssignment).filter(
        PatientPractitionerAssignment.patient_id == patient_id,
    ).first()
    if assignment is None:
        assignment = PatientPractitionerAssignment(
            patient_id=patient_id,
            employer_id=employer_id,
            practitioner_id=payload.practitioner_id,
            updated_by=current_user.id,
        )
        db.add(assignment)
    else:
        if assignment.employer_id != employer_id:
            raise HTTPException(status_code=403, detail="Attribution patient hors cabinet")
        assignment.practitioner_id = payload.practitioner_id
        assignment.updated_by = current_user.id

    db.commit()
    return {
        "patient_id": patient_id,
        "practitioner": practitioner_payload(practitioner) if practitioner else None,
    }
