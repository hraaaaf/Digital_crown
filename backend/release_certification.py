"""Fail-closed verification for installable Digital Crown cabinet releases.

A cabinet release is installable only when it carries a CI-issued certificate tied
exactly to one immutable 40-character Git commit SHA and certified for every
commercial pack supported by the universal binary.

This module intentionally uses only the Python standard library so it can run before
the application imports database/configuration code.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

CERTIFICATE_FILENAME = "release-certification.json"
SHA_MARKER_FILENAME = ".digitalcrown-release-sha"
CONTENT_MANIFEST_FILENAME = "release-content.sha256"
CERTIFICATE_VERSION = 1
REPOSITORY = "hraaaaf/Digital_crown"
REQUIRED_PACKS = ("BASIC", "GOLD", "ELITE")
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


class ReleaseCertificationError(RuntimeError):
    """Raised when a release is not eligible for cabinet installation/startup."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def _verify_identity(root: Path, expected_pack: str | None = None) -> dict[str, Any]:
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


def _verify_content_manifest(root: Path, payload: dict[str, Any]) -> None:
    manifest = root / CONTENT_MANIFEST_FILENAME
    if not manifest.is_file():
        raise ReleaseCertificationError(
            f"Missing {CONTENT_MANIFEST_FILENAME}; certified payload integrity cannot be proven"
        )

    expected_manifest_digest = str(payload.get("content_manifest_sha256", "")).strip().lower()
    if not _DIGEST_RE.fullmatch(expected_manifest_digest):
        raise ReleaseCertificationError("content_manifest_sha256 must be a SHA-256 digest")
    actual_manifest_digest = _sha256(manifest)
    if actual_manifest_digest != expected_manifest_digest:
        raise ReleaseCertificationError(
            "Content manifest digest mismatch; certified release metadata was altered"
        )

    lines = manifest.read_text(encoding="utf-8").splitlines()
    if not lines:
        raise ReleaseCertificationError("Content manifest is empty")

    for line in lines:
        try:
            expected_digest, relative = line.split("  ", 1)
        except ValueError as exc:
            raise ReleaseCertificationError(f"Malformed content manifest line: {line!r}") from exc
        expected_digest = expected_digest.strip().lower()
        if not _DIGEST_RE.fullmatch(expected_digest):
            raise ReleaseCertificationError(f"Malformed file digest for {relative!r}")

        rel_path = Path(relative)
        if rel_path.is_absolute() or ".." in rel_path.parts:
            raise ReleaseCertificationError(f"Unsafe content manifest path: {relative!r}")
        path = root / rel_path
        if not path.is_file():
            raise ReleaseCertificationError(f"Certified release file missing: {relative}")
        if _sha256(path) != expected_digest:
            raise ReleaseCertificationError(f"Certified release file changed: {relative}")


def verify_release_identity(
    release_dir: str | Path,
    *,
    expected_pack: str | None = None,
) -> dict[str, Any]:
    """Verify portable identity embedded in a packaged/frozen build.

    PyInstaller transforms source files, so the source-content manifest is verified at
    build time by ``DigitalCrown.spec``. The packaged runtime then rechecks the embedded
    certificate + exact SHA marker + universal pack coverage before first-boot writes.
    """

    root = Path(release_dir).resolve()
    if not root.is_dir():
        raise ReleaseCertificationError(f"Release directory does not exist: {root}")
    return _verify_identity(root, expected_pack)


def verify_release_directory(
    release_dir: str | Path,
    *,
    expected_pack: str | None = None,
) -> dict[str, Any]:
    """Verify identity plus all certified source/runtime payload hashes."""

    root = Path(release_dir).resolve()
    if not root.is_dir():
        raise ReleaseCertificationError(f"Release directory does not exist: {root}")
    payload = _verify_identity(root, expected_pack)
    _verify_content_manifest(root, payload)
    return payload
