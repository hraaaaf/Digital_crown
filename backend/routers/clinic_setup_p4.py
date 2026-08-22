"""P4D atomic two-phase onboarding persistence.

The setup wizard must write the same ownership model as Settings:
- User owns practitioner identity;
- CabinetConfig owns organization identity and presentation settings.

POST /clinics/ persists the draft but deliberately leaves is_initialized=False.
POST /clinics/complete-setup is the only operation that marks setup complete, so a
logo/letterhead upload failure cannot masquerade as a successful installation.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend import models, schemas
from backend.database import get_db
from backend.routers.clinics import _normalize_clinic_update_dict, _require_setup_owner
from backend.routers.clinic_profile_p4 import _normalized_optional, _profile_payload

router = APIRouter()


def _split_setup_payload(config: schemas.CabinetConfigCreate):
    raw = config.model_dump(exclude_unset=True)
    provided = set(config.model_fields_set)

    practitioner_name = raw.pop("nom", None) if "nom" in provided else None
    explicit_legacy_name = raw.pop("nom_praticien", None) if "nom_praticien" in provided else None
    practitioner_name_ar = raw.pop("nom_praticien_ar", None) if "nom_praticien_ar" in provided else None
    practitioner_inpe = raw.pop("inpe", None) if "inpe" in provided else None

    if practitioner_name is None and explicit_legacy_name is not None:
        practitioner_name = explicit_legacy_name

    candidate_name = _normalized_optional(practitioner_name)
    candidate_ar = _normalized_optional(practitioner_name_ar)
    candidate_inpe = _normalized_optional(practitioner_inpe)

    if practitioner_name is not None and candidate_name is None:
        raise HTTPException(status_code=422, detail="Le nom du praticien ne peut pas être vide.")

    practitioner_changes = {
        "nom_complet": (practitioner_name is not None, candidate_name),
        "nom_complet_ar": (practitioner_name_ar is not None, candidate_ar),
        "inpe_professionnel": (practitioner_inpe is not None, candidate_inpe),
    }
    return raw, practitioner_changes


def _required_setup_truth(practitioner: models.User, organization: models.CabinetConfig) -> None:
    missing = []
    if not (practitioner.nom_complet or "").strip():
        missing.append("nom_praticien")
    if not (organization.nom_cabinet or "").strip():
        missing.append("nom_cabinet")
    if not (organization.footer_address or "").strip():
        missing.append("adresse")
    if missing:
        raise HTTPException(
            status_code=422,
            detail={"message": "Configuration minimale incomplète.", "fields": missing},
        )


@router.post("/")
def save_setup_draft(
    config: schemas.CabinetConfigCreate,
    db: Session = Depends(get_db),
    practitioner: models.User = Depends(_require_setup_owner),
):
    """Persist setup draft atomically without claiming installation is complete."""
    organization = db.query(models.CabinetConfig).filter(
        models.CabinetConfig.owner_id == practitioner.id
    ).first()
    if organization is not None and organization.is_initialized:
        raise HTTPException(status_code=400, detail="Un cabinet initialisé existe déjà.")

    raw, practitioner_changes = _split_setup_payload(config)
    organization_update = _normalize_clinic_update_dict(raw, config=organization)
    if "cabinet_type" in organization_update:
        organization_update["cabinet_type"] = models.CabinetType(organization_update["cabinet_type"])

    if organization is None:
        organization = models.CabinetConfig(
            owner_id=practitioner.id,
            is_initialized=False,
        )
        db.add(organization)

    for field, value in organization_update.items():
        if hasattr(organization, field):
            setattr(organization, field, value)

    # Setup draft creation must never populate the historical duplicate practitioner
    # columns on CabinetConfig. Existing legacy values, if any, are left untouched for
    # the explicit P5 migration rather than silently reclassified here.
    for field, (was_provided, value) in practitioner_changes.items():
        if was_provided:
            setattr(practitioner, field, value)

    organization.is_initialized = False
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(organization)
    db.refresh(practitioner)
    return _profile_payload(practitioner, organization)


@router.post("/complete-setup")
def complete_setup(
    db: Session = Depends(get_db),
    practitioner: models.User = Depends(_require_setup_owner),
):
    """Mark setup complete only after all previous setup operations succeeded."""
    organization = db.query(models.CabinetConfig).filter(
        models.CabinetConfig.owner_id == practitioner.id
    ).first()
    if organization is None:
        raise HTTPException(status_code=404, detail="Aucun brouillon de cabinet à finaliser.")

    _required_setup_truth(practitioner, organization)
    if not organization.is_initialized:
        organization.is_initialized = True
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        db.refresh(organization)

    return _profile_payload(practitioner, organization)
