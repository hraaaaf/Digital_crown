from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend import database, models
from backend.models_clinical_p3 import PatientOdontogram
from backend.routers.auth import require_permission
from backend.schemas.odontogram import OdontogramOut, OdontogramUpdate
from backend.services.audit_service import audit_service
from backend.utils.access_control import assert_patient_access


router = APIRouter()


@router.get("/{patient_id}/odontogram", response_model=Optional[OdontogramOut])
def get_patient_odontogram(
    patient_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("clinical")),
):
    """Return the persisted odontogram, or null when none has been recorded."""
    assert_patient_access(patient_id, current_user, db)
    return (
        db.query(PatientOdontogram)
        .filter(PatientOdontogram.patient_id == patient_id)
        .first()
    )


@router.put("/{patient_id}/odontogram", response_model=OdontogramOut)
def put_patient_odontogram(
    patient_id: int,
    payload: OdontogramUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("clinical")),
):
    """Create/update the patient odontogram with optimistic concurrency control.

    `expected_revision=0` means the caller expects no persisted odontogram yet.
    Existing records require the exact current revision. A stale client receives 409
    instead of silently overwriting a clinical record edited elsewhere.
    """
    assert_patient_access(patient_id, current_user, db)

    record = (
        db.query(PatientOdontogram)
        .filter(PatientOdontogram.patient_id == patient_id)
        .with_for_update()
        .first()
    )

    if record is None:
        if payload.expected_revision != 0:
            raise HTTPException(
                status_code=409,
                detail="Odontogramme absent ou modifié. Rechargez avant d’enregistrer.",
            )
        record = PatientOdontogram(
            patient_id=patient_id,
            dentition_type=payload.dentition_type.value,
            state={
                str(tooth): surfaces.model_dump(mode="json")
                for tooth, surfaces in payload.state.items()
            },
            revision=1,
            updated_by=current_user.id,
        )
        db.add(record)
        action = "CREATE"
    else:
        if payload.expected_revision != record.revision:
            raise HTTPException(
                status_code=409,
                detail="Odontogramme modifié ailleurs. Rechargez avant d’enregistrer.",
            )
        record.dentition_type = payload.dentition_type.value
        record.state = {
            str(tooth): surfaces.model_dump(mode="json")
            for tooth, surfaces in payload.state.items()
        }
        record.revision += 1
        record.updated_by = current_user.id
        action = "UPDATE"

    try:
        db.commit()
        db.refresh(record)
    except Exception:
        db.rollback()
        raise

    audit_service.log(
        db=db,
        user_id=current_user.id,
        employer_id=current_user.get_employer_id(),
        action=action,
        resource_type="PatientOdontogram",
        resource_id=str(record.id),
        details=f"Odontogramme patient {patient_id} enregistré, révision {record.revision}.",
    )
    return record
