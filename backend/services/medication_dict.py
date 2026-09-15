"""
Dictionnaire national des médicaments (Maroc) issu du référentiel CNOPS Open Data,
avec suppléments documentaires explicitement sourcés quand une présentation vérifiée
est absente du snapshot historique.

Prescription Intelligence V1 traite ces données comme un SNAPSHOT DOCUMENTAIRE :
- utile pour identifier un médicament / une présentation connue dans une source ;
- jamais une preuve que la présentation est encore commercialisée aujourd'hui ;
- aucune posologie, contre-indication ou règle thérapeutique n'est fournie ici.

Source de base : Portail Open Data du Maroc, producteur CNOPS.
Licence base : Open Data Commons Open Database License (ODbL).
Dernière modification publiée du jeu source de base : 2021-12-13.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
)
_DATA_PATH = os.path.join(_DATA_DIR, "medications_ma.json")
_SUPPLEMENT_PATH = os.path.join(_DATA_DIR, "medications_ma_verified_supplement.json")

CATALOG_SOURCE: Dict[str, Any] = {
    "id": "cnops-open-data-medications",
    "label": "CNOPS Open Data — Référentiel des médicaments",
    "license": "ODbL",
    "source_url": "https://www.data.gov.ma/data/fr/dataset/referentiel-des-medicaments",
    "snapshot_date": "2021-12-13",
    "freshness": "historical_snapshot",
    "current_marketing_status_verified": False,
}

_MEDS: List[Dict[str, Any]] = []
_SUPPLEMENT_COUNT = 0
_SUPPLEMENT_SOURCES: List[Dict[str, Any]] = []
_LOADED = False


def _presentation_id(rec: Dict[str, Any]) -> str:
    """Identifiant stable dérivé uniquement des champs documentaires de la présentation."""
    canonical = "|".join(
        str(rec.get(field) or "").strip().upper()
        for field in ("nom", "dci", "dosage", "unite", "forme")
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:20]
    return f"cnops:{digest}"


def _load() -> None:
    global _MEDS, _SUPPLEMENT_COUNT, _SUPPLEMENT_SOURCES, _LOADED
    if _LOADED:
        return

    try:
        with open(_DATA_PATH, encoding="utf-8") as f:
            raw = json.load(f)
        base_records = raw if isinstance(raw, list) else []
    except Exception as exc:
        logger.warning("Dictionnaire médicaments de base indisponible (%s)", exc)
        base_records = []

    try:
        with open(_SUPPLEMENT_PATH, encoding="utf-8") as f:
            supplement_raw = json.load(f)
        supplement_records = supplement_raw if isinstance(supplement_raw, list) else []
    except FileNotFoundError:
        supplement_records = []
    except Exception as exc:
        logger.warning("Supplément médicaments indisponible (%s)", exc)
        supplement_records = []

    merged: Dict[str, Dict[str, Any]] = {}
    for rec in base_records:
        if isinstance(rec, dict):
            merged[_presentation_id(rec)] = rec
    for rec in supplement_records:
        if isinstance(rec, dict):
            merged[_presentation_id(rec)] = rec

    _MEDS = list(merged.values())
    _SUPPLEMENT_COUNT = len([rec for rec in supplement_records if isinstance(rec, dict)])

    sources: Dict[str, Dict[str, Any]] = {}
    for rec in supplement_records:
        if not isinstance(rec, dict):
            continue
        source = rec.get("_source")
        if isinstance(source, dict) and source.get("id"):
            sources[str(source["id"])] = dict(source)
    _SUPPLEMENT_SOURCES = list(sources.values())

    logger.info(
        "Dictionnaire médicaments chargé : %d entrées (%d supplément(s) sourcé(s))",
        len(_MEDS),
        _SUPPLEMENT_COUNT,
    )
    _LOADED = True


def _source_for_record(rec: Dict[str, Any]) -> Dict[str, Any]:
    source = rec.get("_source")
    return dict(source) if isinstance(source, dict) else dict(CATALOG_SOURCE)


def catalog_metadata() -> Dict[str, Any]:
    """Métadonnées de provenance exposées sans sur-promettre la fraîcheur clinique."""
    _load()
    return {
        **CATALOG_SOURCE,
        "record_count": len(_MEDS),
        "supplement_record_count": _SUPPLEMENT_COUNT,
        "sources": [dict(CATALOG_SOURCE), *[dict(source) for source in _SUPPLEMENT_SOURCES]],
        "available": bool(_MEDS),
    }


def _public_presentation(rec: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "presentation_id": _presentation_id(rec),
        "nom": rec.get("nom", ""),
        "dci": rec.get("dci", ""),
        "dosage": rec.get("dosage", ""),
        "unite": rec.get("unite", ""),
        "forme": rec.get("forme", ""),
        "source": _source_for_record(rec),
    }


def _to_mg(value: str, unit: str) -> Optional[float]:
    """Convertit un couple (dosage, unité) en mg. Ignore les concentrations (/ML, %, UI...)."""
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
    return None


def _strengths_mg(rec: Dict[str, Any]) -> List[float]:
    """Tous les composants en mg d'une présentation (gère les associations '1 / 60')."""
    doses = [d.strip() for d in (rec.get("dosage") or "").split("/")]
    units = [u.strip() for u in (rec.get("unite") or "").split("/")]
    out: List[float] = []
    for i, dose in enumerate(doses):
        unit = units[i] if i < len(units) else (units[0] if units else "")
        mg = _to_mg(dose, unit)
        if mg is not None:
            out.append(mg)
    return out


def _brand_root(name: str) -> str:
    """Racine du nom commercial historique utilisée uniquement pour la validation documentaire."""
    return re.split(r"\s|\d", (name or "").upper().strip(), 1)[0]


def search(q: str, limit: int = 30) -> List[Dict[str, Any]]:
    """Recherche documentaire par nom commercial ou DCI.

    Chaque résultat est une présentation explicite. La sélection d'un résultat ne doit
    jamais être interprétée comme une recommandation thérapeutique ou une confirmation
    de commercialisation actuelle.
    """
    _load()
    query = (q or "").upper().strip()
    if len(query) < 2:
        return []

    hits: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for rec in _MEDS:
        if query not in str(rec.get("nom", "")).upper() and query not in str(rec.get("dci", "")).upper():
            continue
        public = _public_presentation(rec)
        presentation_id = public["presentation_id"]
        if presentation_id in seen:
            continue
        seen.add(presentation_id)
        hits.append(public)
        if len(hits) >= max(1, min(limit, 100)):
            break
    return hits


def get_presentation(presentation_id: str) -> Optional[Dict[str, Any]]:
    """Résout une présentation par son identifiant documentaire stable."""
    _load()
    wanted = (presentation_id or "").strip()
    if not wanted:
        return None
    for rec in _MEDS:
        if _presentation_id(rec) == wanted:
            return _public_presentation(rec)
    return None


def _matching_records(name: str) -> List[Dict[str, Any]]:
    """Présentations documentaires correspondant à un nom commercial ou une DCI."""
    upper = (name or "").upper().strip()
    if not upper:
        return []
    root = _brand_root(upper)
    by_brand = [
        rec for rec in _MEDS
        if str(rec.get("nom", "")).upper().startswith(root)
    ] if len(root) >= 3 else []
    if by_brand:
        return by_brand
    return [rec for rec in _MEDS if upper in str(rec.get("dci", "")).upper()]


def validate_dosage(name: str, dosage_mg: Optional[float]) -> Dict[str, Any]:
    """Vérifie une correspondance documentaire de dosage dans les sources chargées.

    `exists=True` signifie seulement que le dosage apparaît dans une source documentaire.
    Cela ne certifie ni disponibilité actuelle, ni indication, ni posologie.
    Le contrat historique `{"known": False}` reste inchangé pour un médicament inconnu.
    """
    _load()
    recs = _matching_records(name)
    if not recs:
        return {"known": False}

    strengths = sorted({mg for rec in recs for mg in _strengths_mg(rec)})
    dci = next((str(rec.get("dci", "")) for rec in recs if rec.get("dci")), "")
    result: Dict[str, Any] = {
        "known": True,
        "dci": dci,
        "available_mg": strengths,
        "source": _source_for_record(recs[0]),
    }
    if dosage_mg is not None and strengths:
        result["exists"] = any(abs(dosage_mg - strength) < 0.01 for strength in strengths)
    return result
