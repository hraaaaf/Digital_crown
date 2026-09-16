"""Lecture documentaire du manifest RCP AMMPS local.

Cette couche ne fournit aucune posologie ni décision clinique. Elle expose uniquement
l'état de capture d'un RCP officiel lié à une présentation réglementaire exacte.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_MANIFEST_PATH = Path(__file__).resolve().parents[1] / "data" / "medications_ma_ammps_rcp_manifest_2026.json"
_ALLOWED_STATUSES = {"PENDING_DOWNLOAD", "SNAPSHOT_VERIFIED", "UNAVAILABLE_VERIFIED"}
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_OFFICIAL_AMMPS_HOSTS = {"ammps.gov.ma", "www.ammps.gov.ma"}
_UNAVAILABLE_EVIDENCE = "OFFICIAL_SOURCE_EXPLICIT_NO_RCP"
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


def _is_official_ammps_url(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    parsed = urlparse(value.strip())
    return parsed.scheme == "https" and parsed.hostname in _OFFICIAL_AMMPS_HOSTS


def _is_safe_local_artifact_path(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    path = PurePosixPath(value.strip())
    parts = path.parts
    return bool(
        not path.is_absolute()
        and ".." not in parts
        and len(parts) > 3
        and parts[:3] == ("backend", "data", "rcp")
    )


def _is_safe_local_pdf_artifact_path(value: Any) -> bool:
    return bool(
        _is_safe_local_artifact_path(value)
        and PurePosixPath(str(value).strip()).suffix.lower() == ".pdf"
    )


def _read_local_artifact_bytes(value: Any) -> Optional[bytes]:
    """Lit uniquement un artefact réellement contenu sous backend/data/rcp."""
    if not _is_safe_local_artifact_path(value):
        return None

    relative = PurePosixPath(str(value).strip())
    root = _REPO_ROOT.resolve()
    declared_artifact_root = root / "backend" / "data" / "rcp"
    resolved_artifact_root = declared_artifact_root.resolve()

    # Le répertoire canonique lui-même ne doit pas être redirigé par un symlink.
    if resolved_artifact_root != declared_artifact_root or not resolved_artifact_root.is_dir():
        return None

    candidate = root.joinpath(*relative.parts).resolve()
    try:
        candidate.relative_to(resolved_artifact_root)
    except ValueError:
        return None

    if not candidate.is_file():
        return None
    try:
        return candidate.read_bytes()
    except OSError:
        return None


def _is_strict_iso_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    normalized = value.strip()
    if not _ISO_DATE_RE.fullmatch(normalized):
        return False
    try:
        date.fromisoformat(normalized)
    except ValueError:
        return False
    return True


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
    """Vrai uniquement si métadonnées et octets de l'artefact local concordent."""
    if entry.get("capture_status") != "SNAPSHOT_VERIFIED":
        return False
    sha256 = entry.get("rcp_sha256")
    local_artifact_path = entry.get("local_artifact_path")
    if not _is_safe_local_pdf_artifact_path(local_artifact_path):
        return False
    artifact_bytes = _read_local_artifact_bytes(local_artifact_path)
    return bool(
        isinstance(sha256, str)
        and _SHA256_RE.fullmatch(sha256)
        and _is_official_ammps_url(entry.get("source_page_url"))
        and _is_official_ammps_url(entry.get("rcp_url"))
        and _is_strict_iso_date(entry.get("rcp_checked_at"))
        and artifact_bytes is not None
        and artifact_bytes.startswith(b"%PDF-")
        and hashlib.sha256(artifact_bytes).hexdigest() == sha256
    )


def entry_is_fail_closed(entry: Dict[str, Any]) -> bool:
    """Contrôle minimal de cohérence sans interprétation clinique."""
    status = entry.get("capture_status")
    if status not in _ALLOWED_STATUSES:
        return False
    if not _is_official_ammps_url(entry.get("source_page_url")):
        return False

    extracted = entry.get("extracted_clinical_fields")
    if not isinstance(extracted, dict):
        return False

    rcp_url = entry.get("rcp_url")
    if rcp_url is not None and not _is_official_ammps_url(rcp_url):
        return False

    if status == "SNAPSHOT_VERIFIED":
        return snapshot_is_verified(entry)

    if status == "PENDING_DOWNLOAD":
        return (
            entry.get("rcp_sha256") is None
            and entry.get("rcp_checked_at") is None
            and entry.get("local_artifact_path") is None
            and entry.get("unavailability_evidence") is None
            and extracted == {}
        )

    # UNAVAILABLE_VERIFIED : absence explicitement prouvée par la source officielle.
    return bool(
        _is_strict_iso_date(entry.get("rcp_checked_at"))
        and entry.get("unavailability_evidence") == _UNAVAILABLE_EVIDENCE
        and rcp_url is None
        and entry.get("rcp_sha256") is None
        and entry.get("local_artifact_path") is None
        and extracted == {}
    )


def prepare_verified_snapshot_entry(
    entry: Dict[str, Any],
    *,
    pdf_bytes: bytes,
    rcp_url: str,
    checked_at: str,
    local_artifact_path: str,
) -> Dict[str, Any]:
    """Prépare une preuve SNAPSHOT_VERIFIED à partir d'un PDF déjà capturé.

    Cette fonction ne télécharge rien, ne persiste rien et n'extrait aucune donnée
    clinique. Elle exige que l'artefact local existe et corresponde exactement aux
    octets fournis avant de produire une copie de l'entrée prête à être revue.
    """
    if entry.get("capture_status") != "PENDING_DOWNLOAD" or not entry_is_fail_closed(entry):
        raise ValueError("RCP entry must be a valid PENDING_DOWNLOAD record")

    if not isinstance(pdf_bytes, (bytes, bytearray)) or not bytes(pdf_bytes).startswith(b"%PDF-"):
        raise ValueError("Captured RCP artifact must start with a PDF signature")

    if not _is_official_ammps_url(rcp_url):
        raise ValueError("RCP URL must use the official AMMPS HTTPS domain")

    normalized_date = checked_at.strip() if isinstance(checked_at, str) else ""
    if not _is_strict_iso_date(normalized_date):
        raise ValueError("checked_at must be an ISO date (YYYY-MM-DD)")

    if not _is_safe_local_pdf_artifact_path(local_artifact_path):
        raise ValueError("RCP artifact path must be a PDF under backend/data/rcp")
    normalized_path = local_artifact_path.strip()

    artifact_bytes = _read_local_artifact_bytes(normalized_path)
    if artifact_bytes is None:
        raise ValueError("RCP artifact must exist at the declared local path")
    if artifact_bytes != bytes(pdf_bytes):
        raise ValueError("Declared RCP artifact bytes do not match the captured bytes")

    prepared = {
        **entry,
        "capture_status": "SNAPSHOT_VERIFIED",
        "rcp_url": rcp_url.strip(),
        "rcp_sha256": hashlib.sha256(artifact_bytes).hexdigest(),
        "rcp_checked_at": normalized_date,
        "local_artifact_path": normalized_path,
        "unavailability_evidence": None,
        "extracted_clinical_fields": {},
    }
    if not entry_is_fail_closed(prepared):
        raise ValueError("Prepared RCP snapshot failed fail-closed integrity checks")
    return prepared
