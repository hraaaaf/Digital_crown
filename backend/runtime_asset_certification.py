"""Deployment-integrity certification for external runtime assets.

Scientific/model bytes are intentionally not stored in Git. A cabinet release only
becomes INSTALLABLE_CERTIFIED after the exact CODE_CERTIFIED SHA is composed with an
immutable runtime-asset bundle whose packaged bytes are fully hashed.

This module certifies deployment integrity, not scientific validity. Scientific
provenance remains governed by ``backend/scientific_assets.json`` and the dedicated
clinical/scientific gates.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable

ASSET_CERTIFICATE_FILENAME = "runtime-assets-certification.json"
ASSET_MANIFEST_FILENAME = "runtime-assets-content.sha256"
ASSET_CERTIFICATE_VERSION = 1
ASSET_ARTIFACT_TYPE = "cabinet-runtime-assets"
ASSET_SELECTION_POLICY_VERSION = 1
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")

# Must remain the single source of truth for both asset-bundle creation and
# DigitalCrown.spec packaging. These directories are historical/training material,
# not runtime inputs.
AI_MODELS_EXCLUDE_DIRNAMES = frozenset(
    {
        "CLdetection2023-master",
        "dentex_repo",
        "CL-Detection2023",
        "cephalometric-master",
        "cephmark",
        "__pycache__",
        ".pytest_cache",
    }
)
AI_MODELS_EXCLUDE_RELPATHS = frozenset({("cephld_cca", "model")})


class RuntimeAssetCertificationError(RuntimeError):
    """Raised when runtime assets cannot be proven immutable/compatible."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_selected_relative(parts: tuple[str, ...]) -> bool:
    if any(part in AI_MODELS_EXCLUDE_DIRNAMES for part in parts):
        return False
    return not any(parts[: len(prefix)] == prefix for prefix in AI_MODELS_EXCLUDE_RELPATHS)


def iter_runtime_asset_files(ai_models_root: str | Path) -> Iterable[Path]:
    """Yield exactly the external model files that production packaging may include."""

    root = Path(ai_models_root).resolve()
    if not root.is_dir():
        raise RuntimeAssetCertificationError(f"Runtime asset root missing: {root}")
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        parts = path.relative_to(root).parts
        if _is_selected_relative(parts):
            files.append(path)
    yield from sorted(files, key=lambda item: item.relative_to(root).as_posix())


def runtime_asset_manifest_relpath(path: Path, ai_models_root: Path) -> str:
    return "backend/ai_models/" + path.relative_to(ai_models_root).as_posix()


def _load_scientific_registry(release_root: Path) -> tuple[dict[str, Any], str]:
    registry_path = release_root / "backend" / "scientific_assets.json"
    if not registry_path.is_file():
        raise RuntimeAssetCertificationError("backend/scientific_assets.json is missing")
    digest = sha256_file(registry_path)
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeAssetCertificationError(f"Invalid scientific asset registry: {exc}") from exc
    if not isinstance(registry, dict) or registry.get("asset_policy") != "external-not-versioned":
        raise RuntimeAssetCertificationError("Scientific asset registry policy is not external-not-versioned")
    return registry, digest


def inspect_registry_coverage(release_root: str | Path) -> tuple[list[str], list[str]]:
    """Return (pinned ids, unpinned ids) without claiming scientific certification."""

    root = Path(release_root).resolve()
    registry, _ = _load_scientific_registry(root)
    assets = registry.get("assets")
    if not isinstance(assets, list) or not assets:
        raise RuntimeAssetCertificationError("Scientific asset registry is empty")

    pinned: list[str] = []
    unpinned: list[str] = []
    for item in assets:
        if not isinstance(item, dict) or not str(item.get("id", "")).strip():
            raise RuntimeAssetCertificationError("Scientific asset registry contains an invalid entry")
        asset_id = str(item["id"]).strip()
        has_pin = all(
            [
                isinstance(item.get("canonical_path"), str) and bool(item["canonical_path"].strip()),
                isinstance(item.get("sha256"), str) and bool(_DIGEST_RE.fullmatch(item["sha256"].lower())),
                isinstance(item.get("size_bytes"), int) and item["size_bytes"] > 0,
            ]
        )
        (pinned if has_pin else unpinned).append(asset_id)
    return sorted(pinned), sorted(unpinned)


def verify_pinned_registry_assets(release_root: str | Path) -> tuple[list[str], list[str]]:
    """Require every scientifically pinned external asset to match its registry pin."""

    root = Path(release_root).resolve()
    registry, _ = _load_scientific_registry(root)
    pinned, unpinned = inspect_registry_coverage(root)
    by_id = {str(item["id"]): item for item in registry["assets"] if isinstance(item, dict) and item.get("id")}

    for asset_id in pinned:
        item = by_id[asset_id]
        canonical = Path(str(item["canonical_path"]))
        if canonical.is_absolute() or ".." in canonical.parts or canonical.parts[:2] != ("backend", "ai_models"):
            raise RuntimeAssetCertificationError(f"Unsafe scientific canonical_path for {asset_id}")
        path = root / canonical
        if not path.is_file():
            raise RuntimeAssetCertificationError(f"Pinned scientific asset missing: {asset_id}")
        if path.stat().st_size != int(item["size_bytes"]):
            raise RuntimeAssetCertificationError(f"Pinned scientific asset size mismatch: {asset_id}")
        if sha256_file(path) != str(item["sha256"]).lower():
            raise RuntimeAssetCertificationError(f"Pinned scientific asset SHA256 mismatch: {asset_id}")

    return pinned, unpinned


def verify_runtime_assets(
    root: str | Path,
    *,
    expected_commit_sha: str,
    expected_registry_sha256: str,
    require_files: bool = True,
) -> dict[str, Any]:
    """Verify an extracted/composed runtime-asset bundle fail-closed."""

    release_root = Path(root).resolve()
    cert_path = release_root / ASSET_CERTIFICATE_FILENAME
    manifest_path = release_root / ASSET_MANIFEST_FILENAME
    if not cert_path.is_file() or not manifest_path.is_file():
        raise RuntimeAssetCertificationError("Runtime asset certificate/manifest missing")

    try:
        payload = json.loads(cert_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeAssetCertificationError(f"Invalid runtime asset certificate: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeAssetCertificationError("Runtime asset certificate must be a JSON object")

    if payload.get("certificate_version") != ASSET_CERTIFICATE_VERSION:
        raise RuntimeAssetCertificationError("Unsupported runtime asset certificate version")
    if payload.get("artifact_type") != ASSET_ARTIFACT_TYPE:
        raise RuntimeAssetCertificationError("Unexpected runtime asset artifact_type")
    if payload.get("selection_policy_version") != ASSET_SELECTION_POLICY_VERSION:
        raise RuntimeAssetCertificationError("Unsupported runtime asset selection policy")

    target_sha = str(payload.get("target_commit_sha", "")).strip().lower()
    if not _SHA_RE.fullmatch(target_sha) or target_sha != expected_commit_sha.lower():
        raise RuntimeAssetCertificationError("Runtime assets are not certified for this exact code SHA")

    registry, actual_registry_digest = _load_scientific_registry(release_root)
    del registry
    registry_digest = str(payload.get("scientific_assets_registry_sha256", "")).strip().lower()
    if (
        registry_digest != expected_registry_sha256.lower()
        or registry_digest != actual_registry_digest
        or not _DIGEST_RE.fullmatch(registry_digest)
    ):
        raise RuntimeAssetCertificationError("Runtime asset registry digest mismatch")

    manifest_digest = str(payload.get("content_manifest_sha256", "")).strip().lower()
    if not _DIGEST_RE.fullmatch(manifest_digest) or sha256_file(manifest_path) != manifest_digest:
        raise RuntimeAssetCertificationError("Runtime asset manifest digest mismatch")

    lines = [line for line in manifest_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        raise RuntimeAssetCertificationError("Runtime asset manifest is empty")

    total_bytes = 0
    manifest_relpaths: set[str] = set()
    for line in lines:
        try:
            expected_digest, relative = line.split("  ", 1)
        except ValueError as exc:
            raise RuntimeAssetCertificationError(f"Malformed runtime asset manifest line: {line!r}") from exc
        expected_digest = expected_digest.strip().lower()
        relative = relative.replace("\\", "/")
        rel = Path(relative)
        if not _DIGEST_RE.fullmatch(expected_digest):
            raise RuntimeAssetCertificationError(f"Malformed runtime asset digest: {relative!r}")
        if rel.is_absolute() or ".." in rel.parts or rel.parts[:2] != ("backend", "ai_models"):
            raise RuntimeAssetCertificationError(f"Unsafe runtime asset path: {relative!r}")
        if relative in manifest_relpaths:
            raise RuntimeAssetCertificationError(f"Duplicate runtime asset path: {relative}")
        manifest_relpaths.add(relative)

        path = release_root / rel
        if require_files:
            if not path.is_file() or path.is_symlink():
                raise RuntimeAssetCertificationError(f"Runtime asset missing: {relative}")
            if sha256_file(path) != expected_digest:
                raise RuntimeAssetCertificationError(f"Runtime asset changed: {relative}")
            total_bytes += path.stat().st_size

    if require_files:
        ai_models_root = release_root / "backend" / "ai_models"
        selected_relpaths = {
            runtime_asset_manifest_relpath(path, ai_models_root)
            for path in iter_runtime_asset_files(ai_models_root)
        }
        if selected_relpaths != manifest_relpaths:
            missing = sorted(manifest_relpaths - selected_relpaths)
            extra = sorted(selected_relpaths - manifest_relpaths)
            raise RuntimeAssetCertificationError(
                f"Runtime asset manifest/file-set mismatch missing={missing!r} extra={extra!r}"
            )

    declared_count = payload.get("file_count")
    if declared_count != len(lines):
        raise RuntimeAssetCertificationError("Runtime asset file_count mismatch")
    if require_files and payload.get("total_bytes") != total_bytes:
        raise RuntimeAssetCertificationError("Runtime asset total_bytes mismatch")

    pinned, unpinned = verify_pinned_registry_assets(release_root) if require_files else inspect_registry_coverage(release_root)
    if sorted(payload.get("pinned_registry_assets_verified") or []) != pinned:
        raise RuntimeAssetCertificationError("Pinned scientific registry coverage mismatch")
    if sorted(payload.get("unpinned_registry_assets") or []) != unpinned:
        raise RuntimeAssetCertificationError("Unpinned scientific registry coverage mismatch")

    return payload
