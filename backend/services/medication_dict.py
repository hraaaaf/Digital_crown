"""
Référentiel documentaire des médicaments au Maroc.

Prescription Intelligence V1 traite ces fichiers comme des SOURCES DOCUMENTAIRES :
- utiles pour identifier un médicament / une présentation explicitement publiée ;
- jamais une preuve de disponibilité instantanée en pharmacie ;
- aucune posologie, contre-indication ou règle thérapeutique n'est fournie ici.

Sources intégrées :
- CNOPS Open Data, snapshot historique du 2021-12-13 ;
- AMMPS, Répertoire Marocain des Médicaments Génériques, édition projet janvier 2026 ;
- AMMPS, base courante des médicaments, snapshot réglementaire daté.
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
_AMMPS_CURRENT_DATA_PATH = os.path.join(_DATA_DIR, "medications_ma_ammps_current_2026.json")

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

AMMPS_CURRENT_SOURCE: Dict[str, Any] = {
    "id": "ammps-medications-current-2026-09-15",
    "label": "AMMPS — Base de données des médicaments, snapshot courant",
    "license": "non_specifiee",
    "source_url": "https://www.ammps.gov.ma/recherche-medicaments",
    "snapshot_date": "2026-09-15",
    "freshness": "current_snapshot",
    "current_marketing_status_verified": True,
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
        (_AMMPS_CURRENT_DATA_PATH, AMMPS_CURRENT_SOURCE),
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


def _legacy_records() -> List[Dict[str, Any]]:
    """Legacy APIs must ignore the M1 current snapshot until explicitly migrated."""
    current_source_id = AMMPS_CURRENT_SOURCE["id"]
    return [rec for rec in _MEDS if _record_source(rec).get("id") != current_source_id]


def _regulatory_records() -> List[Dict[str, Any]]:
    """Regulatory APIs are fail-closed to the dated current AMMPS snapshot only."""
    current_source_id = AMMPS_CURRENT_SOURCE["id"]
    return [rec for rec in _MEDS if _record_source(rec).get("id") == current_source_id]


def catalog_metadata() -> Dict[str, Any]:
    """Métadonnées multi-source, avec contrat historique CNOPS préservé au premier niveau."""
    _load()
    source_counts: Dict[str, int] = {}
    for rec in _MEDS:
        source_id = _record_source(rec).get("id", "unknown")
        source_counts[source_id] = source_counts.get(source_id, 0) + 1

    sources = [
        {**source, "record_count": source_counts.get(source["id"], 0)}
        for source in (AMMPS_CURRENT_SOURCE, AMMPS_RMMG_SOURCE, CATALOG_SOURCE)
    ]
    cnops_count = source_counts.get(CATALOG_SOURCE["id"], 0)

    return {
        **CATALOG_SOURCE,
        "record_count": cnops_count,
        "available": cnops_count > 0,
        "total_record_count": len(_MEDS),
        "sources": sources,
        "additional_sources": sources[:-1],
    }


def _presentation_id(rec: Dict[str, Any]) -> str:
    """Identifiant historique stable ; son contrat ne doit pas changer en M1."""
    canonical = "|".join(
        str(rec.get(field) or "").strip().upper()
        for field in ("nom", "dci", "dosage", "unite", "forme")
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:20]
    source_id = _record_source(rec).get("id", "")
    prefix = "ammps" if source_id.startswith("ammps-") else "cnops"
    return f"{prefix}:{digest}"


def _regulatory_presentation_id(rec: Dict[str, Any]) -> str:
    """Identifiant réglementaire package-level, sans modifier l'ID historique."""
    canonical = "|".join(
        str(rec.get(field) or "").strip().upper()
        for field in ("nom", "dci", "dosage", "unite", "forme", "presentation", "epi")
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]
    source_id = _record_source(rec).get("id", "")
    prefix = "ammps-reg" if source_id.startswith("ammps-") else "cnops-reg"
    return f"{prefix}:{digest}"


def _canonical_presentation_key(rec: Dict[str, Any]) -> str:
    return "|".join(
        str(rec.get(field) or "").strip().upper()
        for field in ("nom", "dci", "dosage", "unite", "forme")
    )


def _regulatory_presentation_key(rec: Dict[str, Any]) -> str:
    return "|".join(
        str(rec.get(field) or "").strip().upper()
        for field in ("nom", "dci", "dosage", "unite", "forme", "presentation", "epi")
    )


def _public_presentation(rec: Dict[str, Any]) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "presentation_id": _presentation_id(rec),
        "regulatory_presentation_id": _regulatory_presentation_id(rec),
        "nom": rec.get("nom", ""),
        "dci": rec.get("dci", ""),
        "dosage": rec.get("dosage", ""),
        "unite": rec.get("unite", ""),
        "forme": rec.get("forme", ""),
        "source": _record_source(rec),
    }
    for field in (
        "voie_administration",
        "epi",
        "ean13",
        "presentation",
        "amm_status",
        "market_status",
        "market_status_checked_at",
        "therapeutic_class",
        "source_page_url",
        "rcp_link_observed",
        "rcp_url",
        "rcp_snapshot_status",
        "rcp_sha256",
        "rcp_checked_at",
    ):
        if field in rec:
            result[field] = rec[field]
    return result


def _to_mg(value: str, unit: str) -> Optional[float]:
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
    return re.split(r"\s|\d", (name or "").upper().strip(), 1)[0]


def _matches_query(rec: Dict[str, Any], query: str) -> bool:
    return query in str(rec.get("nom", "")).upper() or query in str(rec.get("dci", "")).upper()


def search(q: str, limit: int = 30) -> List[Dict[str, Any]]:
    """Recherche documentaire historique par nom commercial ou DCI."""
    _load()
    query = (q or "").upper().strip()
    if len(query) < 2:
        return []

    hits: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for rec in _legacy_records():
        if not _matches_query(rec, query):
            continue
        canonical_key = _canonical_presentation_key(rec)
        if canonical_key in seen:
            continue
        seen.add(canonical_key)
        hits.append(_public_presentation(rec))
        if len(hits) >= max(1, min(limit, 100)):
            break
    return hits


def search_regulatory_presentations(q: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Recherche package-level dans le snapshot AMMPS courant uniquement."""
    _load()
    query = (q or "").upper().strip()
    if len(query) < 2:
        return []

    hits: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for rec in _regulatory_records():
        if not _matches_query(rec, query):
            continue
        regulatory_key = _regulatory_presentation_key(rec)
        if regulatory_key in seen:
            continue
        seen.add(regulatory_key)
        hits.append(_public_presentation(rec))
        if len(hits) >= max(1, min(limit, 500)):
            break
    return hits


def get_presentation(presentation_id: str) -> Optional[Dict[str, Any]]:
    _load()
    wanted = (presentation_id or "").strip()
    if not wanted:
        return None
    for rec in _legacy_records():
        if _presentation_id(rec) == wanted:
            return _public_presentation(rec)
    return None


def get_regulatory_presentation(regulatory_presentation_id: str) -> Optional[Dict[str, Any]]:
    _load()
    wanted = (regulatory_presentation_id or "").strip()
    if not wanted:
        return None
    for rec in _regulatory_records():
        if _regulatory_presentation_id(rec) == wanted:
            return _public_presentation(rec)
    return None


def _matching_records(name: str) -> List[Dict[str, Any]]:
    upper = (name or "").upper().strip()
    if not upper:
        return []
    records = _legacy_records()
    root = _brand_root(upper)
    by_brand = [rec for rec in records if str(rec.get("nom", "")).upper().startswith(root)] if len(root) >= 3 else []
    if by_brand:
        return by_brand
    return [rec for rec in records if upper in str(rec.get("dci", "")).upper()]


def validate_dosage(name: str, dosage_mg: Optional[float]) -> Dict[str, Any]:
    """Correspondance documentaire historique uniquement ; aucune preuve clinique."""
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
