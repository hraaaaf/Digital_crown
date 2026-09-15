"""Lecture documentaire du manifest RCP AMMPS local.

Cette couche ne fournit aucune posologie ni décision clinique. Elle expose uniquement
l'état de capture d'un RCP officiel lié à une présentation réglementaire exacte.
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_MANIFEST_PATH = Path(__file__).resolve().parents[1] / "data" / "medications_ma_ammps_rcp_manifest_2026.json"
_ALLOWED_STATUSES = {"PENDING_DOWNLOAD", "SNAPSHOT_VERIFIED", "UNAVAILABLE_VERIFIED"}
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_MANIFEST: Optional[Dict[str, Any]] = None


def _load_manifest() -> Dict[str, Any]:
    global _MANIFEST
    if _MANIFEST is not None:
        return _MANIFEST

    try:
        raw = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("Manifest RCP AMMPS indisponible (%s)", exc)
        _MANIFEST = {}
        return _MANIFEST

    if not isinstance(raw, dict) or not isinstance(raw.get("entries"), list):
        logger.warning("Manifest RCP AMMPS invalide")
        _MANIFEST = {}
        return _MANIFEST

    _MANIFEST = raw
    return _MANIFEST


def manifest_metadata() -> Dict[str, Any]:
    manifest = _load_manifest()
    entries = manifest.get("entries") if isinstance(manifest.get("entries"), list) else []
    return {
        "schema_version": manifest.get("schema_version"),
        "verified_at": manifest.get("verified_at"),
        "authority": manifest.get("authority"),
        "entry_count": len(entries),
        "available": bool(manifest),
    }


def get_rcp_evidence(regulatory_presentation_id: str) -> Optional[Dict[str, Any]]:
    """Retourne la preuve RCP package-level exacte, sans fallback historique."""
    wanted = (regulatory_presentation_id or "").strip()
    if not wanted:
        return None

    manifest = _load_manifest()
    entries = manifest.get("entries") if isinstance(manifest.get("entries"), list) else []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if entry.get("regulatory_presentation_id") == wanted:
            return dict(entry)
    return None


def snapshot_is_verified(entry: Dict[str, Any]) -> bool:
    """Vrai uniquement si le statut, le hash, la date, l'URL et l'artefact concordent."""
    if entry.get("capture_status") != "SNAPSHOT_VERIFIED":
        return False
    sha256 = entry.get("rcp_sha256")
    return bool(
        isinstance(sha256, str)
        and _SHA256_RE.fullmatch(sha256)
        and entry.get("rcp_url")
        and entry.get("rcp_checked_at")
        and entry.get("local_artifact_path")
    )


def entry_is_fail_closed(entry: Dict[str, Any]) -> bool:
    """Contrôle minimal de cohérence sans interprétation clinique."""
    status = entry.get("capture_status")
    if status not in _ALLOWED_STATUSES:
        return False

    extracted = entry.get("extracted_clinical_fields")
    if not isinstance(extracted, dict):
        return False

    if status == "SNAPSHOT_VERIFIED":
        return snapshot_is_verified(entry)

    if status == "PENDING_DOWNLOAD":
        return (
            entry.get("rcp_sha256") is None
            and entry.get("rcp_checked_at") is None
            and entry.get("local_artifact_path") is None
            and extracted == {}
        )

    # UNAVAILABLE_VERIFIED exige une vérification officielle datée et aucune extraction.
    return bool(entry.get("rcp_checked_at") and entry.get("source_page_url") and extracted == {})
