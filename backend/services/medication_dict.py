"""
Dictionnaire national des médicaments (Maroc) — référentiel CNOPS (Open Data, ODbL).
Chargé une fois en mémoire au premier accès. Sert :
  - l'autocomplétion nationale (nom commercial / DCI)
  - le contrôle d'existence d'un dosage ("doliprane 350 mg" existe-t-il ?)

Ne contient PAS de posologie pédiatrique ni de contre-indications : ces jugements
cliniques restent dans le référentiel curé (clinical_rules côté front).
"""
import json
import os
import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "medications_ma.json")

_MEDS: List[Dict[str, str]] = []
_LOADED = False


def _load() -> None:
    global _MEDS, _LOADED
    if _LOADED:
        return
    try:
        with open(_DATA_PATH, encoding="utf-8") as f:
            _MEDS = json.load(f)
        logger.info("Dictionnaire médicaments chargé : %d entrées", len(_MEDS))
    except Exception as e:
        logger.warning("Dictionnaire médicaments indisponible (%s)", e)
        _MEDS = []
    _LOADED = True


def _to_mg(value: str, unit: str) -> Optional[float]:
    """Convertit un couple (dosage, unité) en mg. Ignore les concentrations (/ML, %)."""
    if not value:
        return None
    u = (unit or "").upper().strip()
    try:
        v = float(value.replace(",", "."))
    except ValueError:
        return None
    if u == "G":
        return v * 1000
    if u == "MG":
        return v
    return None  # MG/ML, %, UI… : non comparable en mg simple


def _strengths_mg(rec: Dict[str, str]) -> List[float]:
    """Tous les composants en mg d'une présentation (gère les associations '1 / 60')."""
    doses = [d.strip() for d in (rec.get("dosage") or "").split("/")]
    units = [u.strip() for u in (rec.get("unite") or "").split("/")]
    out: List[float] = []
    for i, d in enumerate(doses):
        u = units[i] if i < len(units) else (units[0] if units else "")
        mg = _to_mg(d, u)
        if mg is not None:
            out.append(mg)
    return out


def _brand_root(name: str) -> str:
    """Racine du nom commercial (1er mot, sans le dosage). 'DOLIPRANE 1000 MG' -> 'DOLIPRANE'."""
    return re.split(r"\s|\d", (name or "").upper().strip(), 1)[0]


def search(q: str, limit: int = 30) -> List[Dict[str, str]]:
    """Recherche nationale par nom commercial OU DCI. Retourne les présentations
    (nom, dci, dosage, unité, forme) — données déjà dédupliquées à la conversion."""
    _load()
    qq = (q or "").upper().strip()
    if len(qq) < 2:
        return []
    hits = []
    for r in _MEDS:
        if qq in r["nom"] or qq in r.get("dci", ""):
            hits.append({
                "nom": r["nom"],
                "dci": r.get("dci", ""),
                "dosage": r.get("dosage", ""),
                "unite": r.get("unite", ""),
                "forme": r.get("forme", ""),
            })
            if len(hits) >= limit:
                break
    return hits


def _matching_records(name: str) -> List[Dict[str, str]]:
    """Présentations correspondant à un médicament saisi (par marque, puis par DCI)."""
    upper = (name or "").upper().strip()
    if not upper:
        return []
    root = _brand_root(upper)
    by_brand = [r for r in _MEDS if r["nom"].startswith(root)] if len(root) >= 3 else []
    if by_brand:
        return by_brand
    # fallback : la saisie est peut-être une DCI (molécule)
    return [r for r in _MEDS if upper in r.get("dci", "")]


def validate_dosage(name: str, dosage_mg: Optional[float]) -> Dict[str, Any]:
    """
    Vérifie l'existence d'un dosage pour un médicament du référentiel national.
    Retourne known=False si le médicament est introuvable (aucune alerte trompeuse).
    """
    _load()
    recs = _matching_records(name)
    if not recs:
        return {"known": False}

    strengths = sorted({mg for r in recs for mg in _strengths_mg(r)})
    dci = next((r.get("dci", "") for r in recs if r.get("dci")), "")
    result: Dict[str, Any] = {
        "known": True,
        "dci": dci,
        "available_mg": strengths,
    }
    if dosage_mg is not None and strengths:
        result["exists"] = any(abs(dosage_mg - s) < 0.01 for s in strengths)
    return result
