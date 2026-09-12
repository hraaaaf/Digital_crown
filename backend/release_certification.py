"""Fail-closed verification for installable Digital Crown cabinet releases.

A cabinet release is installable only when it carries a CI-issued certificate tied
exactly to one immutable 40-character Git commit SHA and certified for every
commercial pack supported by the universal binary.

This module intentionally uses only the Python standard library so it can run before
the application imports database/configuration code.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

CERTIFICATE_FILENAME = "release-certification.json"
SHA_MARKER_FILENAME = ".digitalcrown-release-sha"
CERTIFICATE_VERSION = 1
REPOSITORY = "hraaaaf/Digital_crown"
REQUIRED_PACKS = ("BASIC", "GOLD", "ELITE")
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class ReleaseCertificationError(RuntimeError):
    """Raised when a release is not eligible for cabinet installation/startup."""


def _load_certificate(release_dir: Path) -> dict[str, Any]:
    path = release_dir / CERTIFICATE_FILENAME
    if not path.is_file():
        raise ReleaseCertificationError(
            f"Missing {CERTIFICATE_FILENAME}; uncertified cabinet release refused"
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReleaseCertificationError(f"Invalid release certificate: {exc}") from exc
    if not isinstance(payload, dict):
        raise ReleaseCertificationError("Release certificate must be a JSON object")
    return payload


def verify_release_directory(
    release_dir: str | Path,
    *,
    expected_pack: str | None = None,
) -> dict[str, Any]:
    """Validate the immutable release certificate and SHA marker.

    This is a provenance/integrity gate for our release workflow, not a substitute for
    OS code-signing. It fails closed if the certificate, exact SHA marker, repository,
    policy version, or BASIC/GOLD/ELITE coverage is missing or inconsistent.
    """

    root = Path(release_dir).resolve()
    if not root.is_dir():
        raise ReleaseCertificationError(f"Release directory does not exist: {root}")

    payload = _load_certificate(root)

    if payload.get("certificate_version") != CERTIFICATE_VERSION:
        raise ReleaseCertificationError(
            f"Unsupported certificate_version={payload.get('certificate_version')!r}"
        )
    if payload.get("repository") != REPOSITORY:
        raise ReleaseCertificationError(
            f"Unexpected certificate repository={payload.get('repository')!r}"
        )
    if payload.get("artifact_type") != "cabinet-certified-release":
        raise ReleaseCertificationError("Certificate is not a cabinet-certified-release")

    commit_sha = str(payload.get("commit_sha", "")).strip().lower()
    if not _SHA_RE.fullmatch(commit_sha):
        raise ReleaseCertificationError("Certificate commit_sha must be an exact 40-char SHA")

    marker_path = root / SHA_MARKER_FILENAME
    if not marker_path.is_file():
        raise ReleaseCertificationError(
            f"Missing {SHA_MARKER_FILENAME}; exact release SHA cannot be proven"
        )
    marker_sha = marker_path.read_text(encoding="utf-8-sig").strip().lower()
    if marker_sha != commit_sha:
        raise ReleaseCertificationError(
            f"Release SHA mismatch: marker={marker_sha!r}, certificate={commit_sha!r}"
        )

    release_id = str(payload.get("release_id", "")).strip()
    if not release_id or commit_sha[:12] not in release_id:
        raise ReleaseCertificationError("release_id must include the certified SHA prefix")

    packs_raw = payload.get("certified_packs")
    if not isinstance(packs_raw, list):
        raise ReleaseCertificationError("certified_packs must be a list")
    packs = {str(pack).strip().upper() for pack in packs_raw}
    missing = set(REQUIRED_PACKS) - packs
    if missing:
        raise ReleaseCertificationError(
            "Release is not universal: missing certified pack(s): " + ", ".join(sorted(missing))
        )

    run_id = payload.get("certification_run_id")
    if not isinstance(run_id, int) or run_id <= 0:
        raise ReleaseCertificationError("certification_run_id must be a positive integer")

    if expected_pack is not None:
        pack = expected_pack.strip().upper()
        if pack not in REQUIRED_PACKS:
            raise ReleaseCertificationError(f"Unknown commercial pack: {expected_pack!r}")
        if pack not in packs:
            raise ReleaseCertificationError(f"Release is not certified for pack {pack}")

    return payload
