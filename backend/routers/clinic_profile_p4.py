"""P4C atomic Settings profile facade.

`/clinics/me` remains the stable Settings contract, but practitioner-owned values are
read/written from User while organization-owned values remain on CabinetConfig. One
PUT uses one SQLAlchemy transaction, so the UI cannot report a half-saved profile.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend import models, schemas
from backend.database import get_db
from backend.routers.auth import is_superadmin_user, require_permission
from backend.routers.clinics import _normalize_clinic_update_dict

router = APIRouter()


def _resolve_profile(db: Session, actor: models.User):
    owner_id = actor.get_employer_id()
    practitioner = db.query(models.User).filter(models.User.id == owner_id).first()
    organization = db.query(models.CabinetConfig).filter(
        models.CabinetConfig.owner_id == owner_id
    ).first()
    if practitioner is None:
        raise HTTPException(status_code=404, detail="Praticien principal introuvable")
    if organization is None:
        raise HTTPException(status_code=404, detail="Cabinet non configuré")
    return practitioner, organization


def _profile_payload(practitioner: models.User, organization: models.CabinetConfig) -> dict:
    payload = schemas.CabinetConfigOut.model_validate(organization).model_dump()
    # Compatibility facade: these legacy response keys now expose the canonical User
    # values. CabinetConfig's historical copies remain untouched until P5 migration.
    payload["nom"] = practitioner.nom_complet or ""
    payload["nom_praticien"] = practitioner.nom_complet or ""
    payload["nom_praticien_ar"] = getattr(practitioner, "nom_complet_ar", None) or ""
    payload["inpe"] = getattr(practitioner, "inpe_professionnel", None) or ""
    payload["inpe_professionnel"] = getattr(practitioner, "inpe_professionnel", None)
    return payload


def _normalized_optional(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = value.strip()
    return value or None


@router.get("/me")
def get_settings_profile(
    db: Session = Depends(get_db),
    actor: models.User = Depends(require_permission("settings")),
):
    practitioner, organization = _resolve_profile(db, actor)
    return _profile_payload(practitioner, organization)


@router.put("/me")
def update_settings_profile(
    update: schemas.CabinetConfigUpdate,
    db: Session = Depends(get_db),
    actor: models.User = Depends(require_permission("settings")),
):
    practitioner, organization = _resolve_profile(db, actor)
    raw = update.model_dump(exclude_unset=True)
    provided = set(update.model_fields_set)

    # Flat compatibility aliases used by the existing Settings store. They are routed
    # to User and removed before any CabinetConfig mutation.
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
        "nom_complet": candidate_name,
        "nom_complet_ar": candidate_ar,
        "inpe_professionnel": candidate_inpe,
    }
    practitioner_fields = {
        "nom_complet": practitioner_name is not None,
        "nom_complet_ar": practitioner_name_ar is not None,
        "inpe_professionnel": practitioner_inpe is not None,
    }

    # A permitted team member may edit the organization, but never alter the principal
    # practitioner's identity. Unchanged full-form echoes are tolerated for backwards
    # compatibility; a real difference fails the whole transaction before mutation.
    if actor.id != practitioner.id and not is_superadmin_user(actor):
        current_values = {
            "nom_complet": practitioner.nom_complet,
            "nom_complet_ar": getattr(practitioner, "nom_complet_ar", None),
            "inpe_professionnel": getattr(practitioner, "inpe_professionnel", None),
        }
        for field, was_provided in practitioner_fields.items():
            if was_provided and practitioner_changes[field] != current_values[field]:
                raise HTTPException(
                    status_code=403,
                    detail="Seul le praticien principal peut modifier son identité professionnelle.",
                )
        practitioner_fields = {field: False for field in practitioner_fields}

    organization_update = _normalize_clinic_update_dict(raw, config=organization)
    if "cabinet_type" in organization_update:
        organization_update["cabinet_type"] = models.CabinetType(organization_update["cabinet_type"])

    for field, value in organization_update.items():
        if hasattr(organization, field):
            setattr(organization, field, value)

    for field, was_provided in practitioner_fields.items():
        if was_provided:
            setattr(practitioner, field, practitioner_changes[field])

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(organization)
    db.refresh(practitioner)
    return _profile_payload(practitioner, organization)
