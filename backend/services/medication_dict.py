"""
Référentiel documentaire des médicaments au Maroc.

Prescription Intelligence V1 traite ces fichiers comme des SOURCES DOCUMENTAIRES :
- utiles pour identifier un médicament / une présentation explicitement publiée ;
- jamais une preuve de disponibilité instantanée en pharmacie ;
- aucune posologie, contre-indication ou règle thérapeutique n'est fournie ici.

Sources intégrées :
- CNOPS Open Data, snapshot historique du 2021-12-13 ;
- AMMPS, Répertoire Marocain des Médicaments Génériques, édition projet janvier 2026.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
_DATA_PATH = os.path.join(_DATA_DIR, "medications_ma.json")
_AMMPS_DATA_PATH = os.path.join(_DATA_DIR, "medications_ma_ammps_2026.json")

CATALOG_SOURCE: Dict[str, Any] = {
    "id": "cnops-open-data-medications",
    "label": "CNOPS Open Data — Référentiel des médicaments",
    "license": "ODbL",
    "source_url": "https://www.data.gov.ma/data/fr/dataset/referentiel-des-medicaments",
    "snapshot_date": "2021-12-13",
    "freshness": "historical_snapshot",
    "current_marketing_status_verified": False,
}

AMMPS_RMMG_SOURCE: Dict[str, Any] = {
    "id": "ammps-rmmg-2026-01",
    "label": "AMMPS — Répertoire Marocain des Médicaments Génériques",
    "license": "non_specifiee",
    "source_url": "https://ammps.gov.ma/repertoire-medicaments-generiques",
    "snapshot_date": "2026-01",
    "freshness": "official_project_edition",
    "current_marketing_status_verified": False,
}

_MEDS: List[Dict[str, Any]] = []
_LOADED = False


def _read_records(path: str, source: Dict[str, Any]) -> List[Dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    if not isinstance(raw, list):
        return []
    return [
        {**record, "_source": dict(source)}
        for record in raw
        if isinstance(record, dict)
    ]


def _load() -> None:
    global _MEDS, _LOADED
    if _LOADED:
        return

    records: List[Dict[str, Any]] = []
    for path, source in (
        (_AMMPS_DATA_PATH, AMMPS_RMMG_SOURCE),
        (_DATA_PATH, CATALOG_SOURCE),
    ):
        try:
            records.extend(_read_records(path, source))
        except Exception as exc:
            logger.warning("Source médicaments indisponible %s (%s)", source["id"], exc)

    _MEDS = records
    logger.info("Dictionnaire médicaments chargé : %d entrées", len(_MEDS))
    _LOADED = True


def _record_source(rec: Dict[str, Any]) -> Dict[str, Any]:
    source = rec.get("_source")
    return dict(source) if isinstance(source, dict) else dict(CATALOG_SOURCE)


def catalog_metadata() -> Dict[str, Any]:
    """Métadonnées multi-source, avec contrat historique CNOPS préservé au premier niveau."""
    _load()
    source_counts: Dict[str, int] = {}
    for rec in _MEDS:
        source_id = _record_source(rec).get("id", "unknown")
        source_counts[source_id] = source_counts.get(source_id, 0) + 1

    sources = [
        {**source, "record_count": source_counts.get(source["id"], 0)}
        for source in (AMMPS_RMMG_SOURCE, CATALOG_SOURCE)
    ]
    cnops_count = source_counts.get(CATALOG_SOURCE["id"], 0)

    return {
        **CATALOG_SOURCE,
        # Compatibilité : `record_count` et `available` décrivent toujours la source
        # historique CNOPS exposée au premier niveau, comme avant l'ajout multi-source.
        "record_count": cnops_count,
        "available": cnops_count > 0,
        "total_record_count": len(_MEDS),
        "sources": sources,
        "additional_sources": [sources[0]],
    }


def _presentation_id(rec: Dict[str, Any]) -> str:
    """Identifiant stable dérivé uniquement des champs documentaires de la présentation."""
    canonical = "|".join(
        str(rec.get(field) or "").strip().upper()
        for field in ("nom", "dci", "dosage", "unite", "forme")
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:20]
    source_id = _record_source(rec).get("id", "")
    prefix = "ammps" if source_id.startswith("ammps-") else "cnops"
    return f"{prefix}:{digest}"


def _canonical_presentation_key(rec: Dict[str, Any]) -> str:
    return "|".join(
        str(rec.get(field) or "").strip().upper()
        for field in ("nom", "dci", "dosage", "unite", "forme")
    )


def _public_presentation(rec: Dict[str, Any]) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "presentation_id": _presentation_id(rec),
        "nom": rec.get("nom", ""),
        "dci": rec.get("dci", ""),
        "dosage": rec.get("dosage", ""),
        "unite": rec.get("unite", ""),
        "forme": rec.get("forme", ""),
        "source": _record_source(rec),
    }
    for field in ("voie_administration", "epi", "ean13"):
        if rec.get(field):
            result[field] = rec[field]
    return result


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
    """Racine du nom commercial utilisée uniquement pour la validation documentaire."""
    return re.split(r"\s|\d", (name or "").upper().strip(), 1)[0]


def search(q: str, limit: int = 30) -> List[Dict[str, Any]]:
    """Recherche documentaire par nom commercial ou DCI.

    Chaque résultat est une présentation explicite. La sélection d'un résultat ne doit
    jamais être interprétée comme une recommandation thérapeutique ou une confirmation
    de disponibilité actuelle.
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
        canonical_key = _canonical_presentation_key(rec)
        if canonical_key in seen:
            continue
        seen.add(canonical_key)
        hits.append(_public_presentation(rec))
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
    by_brand = [rec for rec in _MEDS if str(rec.get("nom", "")).upper().startswith(root)] if len(root) >= 3 else []
    if by_brand:
        return by_brand
    return [rec for rec in _MEDS if upper in str(rec.get("dci", "")).upper()]


def validate_dosage(name: str, dosage_mg: Optional[float]) -> Dict[str, Any]:
    """Vérifie une correspondance documentaire de dosage dans les sources intégrées.

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
        "source": _record_source(recs[0]),
    }
    if dosage_mg is not None and strengths:
        result["exists"] = any(abs(dosage_mg - strength) < 0.01 for strength in strengths)
    return result
