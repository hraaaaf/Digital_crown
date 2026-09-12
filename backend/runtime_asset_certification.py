"""Deployment certification for external runtime assets.

Scientific/model bytes are intentionally not stored in Git.  A cabinet release is
therefore installable only after the exact code-certified SHA is composed with an
immutable runtime-asset bundle whose bytes are fully hashed.

This is a deployment-integrity certificate.  It does NOT claim scientific validation
of a model; scientific provenance/validation remains governed by scientific_assets.json
and the corresponding clinical/scientific gates.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

ASSET_CERTIFICATE_FILENAME = "runtime-assets-certification.json"
ASSET_MANIFEST_FILENAME = "runtime-assets-content.sha256"
ASSET_CERTIFICATE_VERSION = 1
ASSET_ARTIFACT_TYPE = "cabinet-runtime-assets"
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


class RuntimeAssetCertificationError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_runtime_assets(
    root: str | Path,
    *,
    expected_commit_sha: str,
    expected_registry_sha256: str,
    require_files: bool = True,
) -> dict[str, Any]:
    """Verify an extracted or composed runtime-asset bundle."""

    release_root = Path(root).resolve()
    cert_path = release_root / ASSET_CERTIFICATE_FILENAME
    manifest_path = release_root / ASSET_MANIFEST_FILENAME
    if not cert_path.is_file() or not manifest_path.is_file():
        raise RuntimeAssetCertificationError("Runtime asset certificate/manifest missing")

    try:
        payload = json.loads(cert_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeAssetCertificationError(f"Invalid runtime asset certificate: {exc}") from exc

    if payload.get("certificate_version") != ASSET_CERTIFICATE_VERSION:
        raise RuntimeAssetCertificationError("Unsupported runtime asset certificate version")
    if payload.get("artifact_type") != ASSET_ARTIFACT_TYPE:
        raise RuntimeAssetCertificationError("Unexpected runtime asset artifact_type")

    target_sha = str(payload.get("target_commit_sha", "")).strip().lower()
    if not _SHA_RE.fullmatch(target_sha) or target_sha != expected_commit_sha.lower():
        raise RuntimeAssetCertificationError("Runtime assets are not certified for this exact code SHA")

    registry_digest = str(payload.get("scientific_assets_registry_sha256", "")).strip().lower()
    if registry_digest != expected_registry_sha256.lower() or not _DIGEST_RE.fullmatch(registry_digest):
        raise RuntimeAssetCertificationError("Runtime asset registry digest mismatch")

    manifest_digest = str(payload.get("content_manifest_sha256", "")).strip().lower()
    if not _DIGEST_RE.fullmatch(manifest_digest) or sha256_file(manifest_path) != manifest_digest:
        raise RuntimeAssetCertificationError("Runtime asset manifest digest mismatch")

    lines = [line for line in manifest_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        raise RuntimeAssetCertificationError("Runtime asset manifest is empty")

    total_bytes = 0
    for line in lines:
        try:
            expected_digest, relative = line.split("  ", 1)
        except ValueError as exc:
            raise RuntimeAssetCertificationError(f"Malformed runtime asset manifest line: {line!r}") from exc
        expected_digest = expected_digest.strip().lower()
        rel = Path(relative)
        if not _DIGEST_RE.fullmatch(expected_digest):
            raise RuntimeAssetCertificationError(f"Malformed runtime asset digest: {relative!r}")
        if rel.is_absolute() or ".." in rel.parts or rel.parts[:2] != ("backend", "ai_models"):
            raise RuntimeAssetCertificationError(f"Unsafe runtime asset path: {relative!r}")
        path = release_root / rel
        if require_files:
            if not path.is_file():
                raise RuntimeAssetCertificationError(f"Runtime asset missing: {relative}")
            if sha256_file(path) != expected_digest:
                raise RuntimeAssetCertificationError(f"Runtime asset changed: {relative}")
            total_bytes += path.stat().st_size

    declared_count = payload.get("file_count")
    if declared_count != len(lines):
        raise RuntimeAssetCertificationError("Runtime asset file_count mismatch")
    if require_files and payload.get("total_bytes") != total_bytes:
        raise RuntimeAssetCertificationError("Runtime asset total_bytes mismatch")

    return payload
