"""Dictionnaire national des médicaments (Maroc) — recherche + validation de dosage."""
import re
from typing import Optional
from fastapi import APIRouter, Depends, Query

from backend import models
from backend.routers.auth import get_current_user
from backend.services import medication_dict

router = APIRouter(tags=["Medications (national dictionary)"])


def _parse_mg(dosage: str) -> Optional[float]:
    """'350 mg' / '1g' / '500MG' -> mg."""
    if not dosage:
        return None
    norm = dosage.upper().replace(" ", "").replace(",", ".")
    m = re.search(r"(\d+(?:\.\d+)?)(MG|G)\b", norm)
    if not m:
        return None
    val = float(m.group(1))
    return val * 1000 if m.group(2) == "G" else val


@router.get("/search")
def search_medications(
    q: str = Query(..., min_length=2),
    current_user: models.User = Depends(get_current_user),
):
    """Autocomplétion sur le référentiel national (nom commercial ou DCI)."""
    return medication_dict.search(q, limit=15)


@router.get("/validate")
def validate_medication(
    name: str = Query(...),
    dosage: Optional[str] = Query(None),
    current_user: models.User = Depends(get_current_user),
):
    """Le dosage saisi existe-t-il pour ce médicament ? (référentiel national)."""
    return medication_dict.validate_dosage(name, _parse_mg(dosage) if dosage else None)
