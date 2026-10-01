from dataclasses import asdict
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend import database, models
from backend.models_patient_clinical_context import PatientClinicalContext
from backend.routers.auth import require_permission
from backend.schemas.patient_clinical_context import (
    PatientClinicalContextOut,
    PatientClinicalContextUpdate,
    PatientProcedureSafetyContextOut,
    PatientProcedureSafetyContextUpdate,
)
from backend.services.audit_service import audit_service
from backend.services.neo_medication_evidence import resolve_medication_identity
from backend.services.neo_prescription_safety import evaluate_neo_prescription_safety
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


def _age_years(date_naissance: datetime | date | None, *, today: date | None = None) -> int | None:
    if date_naissance is None:
        return None
    born = date_naissance.date() if isinstance(date_naissance, datetime) else date_naissance
    ref = today or date.today()
    if born > ref:
        return None
    return ref.year - born.year - ((ref.month, ref.day) < (born.month, born.day))


@router.get("/{patient_id}/neo-prescription-safety")
def read_neo_prescription_safety(
    patient_id: int,
    presentation_id: str = Query(..., min_length=1),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("prescriptions")),
):
    """Read-only Neo safety evaluation; never mutates patient or prescription state."""
    assert_patient_access(patient_id, current_user, db)
    employer_id = current_user.get_employer_id()
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id, models.Patient.employer_id == employer_id,
    ).first()
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient introuvable")
    context = db.query(PatientClinicalContext).filter(
        PatientClinicalContext.patient_id == patient_id,
        PatientClinicalContext.employer_id == employer_id,
    ).first()
    patient_context = context if context is not None else _empty_context(patient_id, employer_id)
    age_years = _age_years(patient.date_naissance)
    result = evaluate_neo_prescription_safety(
        presentation_id=presentation_id, patient_context=patient_context, age_years=age_years,
    )
    current_meds = getattr(patient_context, "current_medications", None) or []
    medication_resolution = []
    for value in current_meds:
        identity = resolve_medication_identity(value)
        medication_resolution.append({"input": value, "identity": identity, "resolved": identity is not None})
    return {
        **asdict(result), "patient_id": patient_id, "age_years": age_years,
        "current_medication_resolution": medication_resolution, "read_only": True,
    }


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
        validated = PatientClinicalContextUpdate(**payload.model_dump())
        context = PatientClinicalContext(
            patient_id=patient_id,
            employer_id=employer_id,
            updated_by_user_id=current_user.id,
            **validated.model_dump(),
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


def _empty_procedure_safety_context(
    patient_id: int,
    employer_id: int,
) -> PatientProcedureSafetyContextOut:
    return PatientProcedureSafetyContextOut(
        patient_id=patient_id,
        employer_id=employer_id,
        anticoagulant_status="UNKNOWN",
        anticoagulants=None,
        antiplatelet_status="UNKNOWN",
        antiplatelets=None,
        antithrombotic_classes=None,
        antithrombotic_combination_status="UNKNOWN",
        warfarin_inr=None,
        warfarin_inr_checked_at=None,
        warfarin_inr_current=None,
        lmwh_dose_class="UNKNOWN",
        updated_at=None,
        updated_by_user_id=None,
    )


@router.get(
    "/{patient_id}/procedure-safety-context",
    response_model=PatientProcedureSafetyContextOut,
)
def read_patient_procedure_safety_context(
    patient_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("prescriptions")),
):
    """Backoffice-only N4.3B context; not part of the practitioner-facing context payload."""
    assert_patient_access(patient_id, current_user, db)
    employer_id = current_user.get_employer_id()
    context = db.query(PatientClinicalContext).filter(
        PatientClinicalContext.patient_id == patient_id,
        PatientClinicalContext.employer_id == employer_id,
    ).first()
    if context is None:
        return _empty_procedure_safety_context(patient_id, employer_id)
    return context


@router.put(
    "/{patient_id}/procedure-safety-context",
    response_model=PatientProcedureSafetyContextOut,
)
def update_patient_procedure_safety_context(
    patient_id: int,
    payload: PatientProcedureSafetyContextUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("prescriptions")),
):
    """Persist explicit antithrombotic facts without exposing them in the normal UI contract."""
    assert_patient_access(patient_id, current_user, db)
    employer_id = current_user.get_employer_id()

    context = db.query(PatientClinicalContext).filter(
        PatientClinicalContext.patient_id == patient_id,
    ).first()
    if context is not None and context.employer_id != employer_id:
        raise HTTPException(status_code=409, detail="Contexte clinique rattaché à un autre cabinet")

    values = payload.model_dump(exclude_unset=True)
    if context is None:
        validated = PatientProcedureSafetyContextUpdate(**payload.model_dump())
        context = PatientClinicalContext(
            patient_id=patient_id,
            employer_id=employer_id,
            updated_by_user_id=current_user.id,
            **validated.model_dump(),
        )
        db.add(context)
    else:
        merged = {
            field: getattr(context, field)
            for field in PatientProcedureSafetyContextUpdate.model_fields
        }
        merged.update(values)
        validated = PatientProcedureSafetyContextUpdate(**merged)
        for field in values:
            setattr(context, field, getattr(validated, field))
        context.updated_by_user_id = current_user.id

    audit_service.log(
        db=db,
        user_id=current_user.id,
        employer_id=employer_id,
        action="UPDATE",
        resource_type="PatientProcedureSafetyContext",
        resource_id=str(patient_id),
        details="Mise à jour du contexte N4.3B backoffice",
    )

    db.commit()
    db.refresh(context)
    return context
