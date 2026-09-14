"""Référentiel documentaire national des médicaments (Maroc)."""
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from backend import models
from backend.routers.auth import get_current_user
from backend.services import medication_dict

router = APIRouter(tags=["Medications (national dictionary)"])


def _parse_mg(dosage: str) -> Optional[float]:
    """'350 mg' / '1g' / '500MG' -> mg. Les concentrations complexes restent non comparables."""
    if not dosage:
        return None
    norm = dosage.upper().replace(" ", "").replace(",", ".")
    match = re.search(r"(\d+(?:\.\d+)?)(MG|G)\b", norm)
    if not match:
        return None
    value = float(match.group(1))
    return value * 1000 if match.group(2) == "G" else value


@router.get("/metadata")
def medication_catalog_metadata(
    current_user: models.User = Depends(get_current_user),
):
    """Expose provenance/fraîcheur du snapshot utilisé par Prescription Intelligence."""
    return medication_dict.catalog_metadata()


@router.get("/search")
def search_medications(
    q: str = Query(..., min_length=2),
    current_user: models.User = Depends(get_current_user),
):
    """Retourne des présentations documentaires exactes par nom commercial ou DCI."""
    return medication_dict.search(q, limit=15)


@router.get("/presentations/{presentation_id:path}")
def get_medication_presentation(
    presentation_id: str,
    current_user: models.User = Depends(get_current_user),
):
    """Résout l'identité exacte d'une présentation sélectionnée explicitement."""
    presentation = medication_dict.get_presentation(presentation_id)
    if presentation is None:
        raise HTTPException(status_code=404, detail="Présentation absente du référentiel documentaire")
    return presentation


@router.get("/validate")
def validate_medication(
    name: str = Query(...),
    dosage: Optional[str] = Query(None),
    current_user: models.User = Depends(get_current_user),
):
    """Vérifie une correspondance documentaire de dosage dans le snapshot, sans décision clinique."""
    return medication_dict.validate_dosage(name, _parse_mg(dosage) if dosage else None)
