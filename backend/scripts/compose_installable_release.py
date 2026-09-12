"""Compose one INSTALLABLE_CERTIFIED release from already verified inputs.

Security boundary:
- the caller must first verify GitHub/Sigstore provenance for the CODE_CERTIFIED
  content manifest;
- this script then re-verifies all code hashes and all external runtime assets;
- composition occurs in staging and is atomically promoted only after the final
  INSTALLABLE verifier succeeds.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from backend.release_certification import (
    GITHUB_SIGNER_WORKFLOW,
    INSTALLABLE_CERTIFICATE_FILENAME,
    INSTALLABLE_CERTIFICATION_LEVEL,
    REPOSITORY,
    REQUIRED_PACKS,
    verify_installable_release_directory,
    verify_release_directory,
)
from backend.runtime_asset_certification import (
    ASSET_CERTIFICATE_FILENAME,
    ASSET_MANIFEST_FILENAME,
    sha256_file,
    verify_runtime_assets,
)

ATTESTATION_EVIDENCE_FILENAME = "github-attestation-verification.json"


def _copy_code_payload(source: Path, target: Path) -> None:
    if target.exists():
        raise RuntimeError(f"Composition target already exists: {target}")
    shutil.copytree(source, target, symlinks=False)
    ai_models = target / "backend" / "ai_models"
    if ai_models.exists() and any(path.is_file() for path in ai_models.rglob("*")):
        raise RuntimeError("CODE_CERTIFIED payload unexpectedly already contains runtime model bytes")


def _copy_runtime_assets(asset_root: Path, target: Path) -> None:
    source_models = asset_root / "backend" / "ai_models"
    if not source_models.is_dir():
        raise RuntimeError("Runtime asset bundle has no backend/ai_models directory")
    target_models = target / "backend" / "ai_models"
    shutil.copytree(source_models, target_models, symlinks=False)
    for name in (ASSET_CERTIFICATE_FILENAME, ASSET_MANIFEST_FILENAME):
        shutil.copy2(asset_root / name, target / name)


def _load_attestation_evidence(path: Path) -> object:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Invalid GitHub attestation verification evidence: {exc}") from exc
    if not isinstance(payload, list) or not payload:
        raise RuntimeError("GitHub attestation verification evidence must be a non-empty JSON array")
    return payload


def compose(
    *,
    code_release_dir: Path,
    runtime_assets_dir: Path,
    runtime_root: Path,
    attestation_evidence: Path,
    code_artifact_sha256: str,
    runtime_asset_bundle_sha256: str,
) -> Path:
    code_release_dir = code_release_dir.resolve()
    runtime_assets_dir = runtime_assets_dir.resolve()
    runtime_root = runtime_root.resolve()
    attestation_evidence = attestation_evidence.resolve()

    _load_attestation_evidence(attestation_evidence)
    code_payload = verify_release_directory(code_release_dir)
    commit_sha = str(code_payload["commit_sha"]).lower()
    release_id = str(code_payload["release_id"])

    registry_path = code_release_dir / "backend" / "scientific_assets.json"
    registry_digest = sha256_file(registry_path)
    asset_payload = verify_runtime_assets(
        runtime_assets_dir,
        expected_commit_sha=commit_sha,
        expected_registry_sha256=registry_digest,
    )

    releases_dir = runtime_root / "releases"
    staging_dir = runtime_root / ".installable-compose"
    releases_dir.mkdir(parents=True, exist_ok=True)
    staging_dir.mkdir(parents=True, exist_ok=True)
    final_dir = releases_dir / release_id
    if final_dir.exists():
        raise RuntimeError(f"Immutable release already exists and will not be overwritten: {final_dir}")

    with tempfile.TemporaryDirectory(prefix=f"{release_id}-", dir=staging_dir) as tmp:
        candidate = Path(tmp) / release_id
        _copy_code_payload(code_release_dir, candidate)
        _copy_runtime_assets(runtime_assets_dir, candidate)
        shutil.copy2(attestation_evidence, candidate / ATTESTATION_EVIDENCE_FILENAME)

        installable = {
            "certificate_version": 1,
            "artifact_type": "cabinet-installable-release",
            "certification_level": INSTALLABLE_CERTIFICATION_LEVEL,
            "commit_sha": commit_sha,
            "release_id": release_id,
            "certified_packs": list(REQUIRED_PACKS),
            "code_certification_run_id": int(code_payload["certification_run_id"]),
            "code_content_manifest_sha256": str(code_payload["content_manifest_sha256"]).lower(),
            "code_artifact_sha256": code_artifact_sha256.lower(),
            "runtime_asset_bundle_sha256": runtime_asset_bundle_sha256.lower(),
            "scientific_assets_registry_sha256": registry_digest,
            "runtime_assets_content_manifest_sha256": str(asset_payload["content_manifest_sha256"]).lower(),
            "runtime_assets_file_count": int(asset_payload["file_count"]),
            "runtime_assets_total_bytes": int(asset_payload["total_bytes"]),
            "pinned_registry_assets_verified": asset_payload.get("pinned_registry_assets_verified", []),
            "unpinned_registry_assets": asset_payload.get("unpinned_registry_assets", []),
            "github_attestation_verified": True,
            "github_attestation_repository": REPOSITORY,
            "github_attestation_signer_workflow": GITHUB_SIGNER_WORKFLOW,
            "github_attestation_source_digest": commit_sha,
            "github_attestation_source_ref": "refs/heads/master",
            "github_attestation_evidence_sha256": sha256_file(attestation_evidence),
            "composed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "installable": True,
        }
        (candidate / INSTALLABLE_CERTIFICATE_FILENAME).write_text(
            json.dumps(installable, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

        release_manifest = {
            "environment": "cabinet-real",
            "release_id": release_id,
            "commit": commit_sha,
            "certification_level": INSTALLABLE_CERTIFICATION_LEVEL,
            "certified_packs": list(REQUIRED_PACKS),
            "certification_run_id": int(code_payload["certification_run_id"]),
            "composed_at": installable["composed_at"],
            "backend_path": str(candidate / "backend"),
            "frontend_dist_path": str(candidate / "frontend" / "dist"),
            "code_artifact_sha256": code_artifact_sha256.lower(),
            "runtime_asset_bundle_sha256": runtime_asset_bundle_sha256.lower(),
            "created_by_script": "compose_installable_release.py",
        }
        (candidate / "release-manifest.json").write_text(
            json.dumps(release_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

        # Last gate before promotion.
        verify_installable_release_directory(candidate)

        # release-manifest paths must reference the immutable final directory, not staging.
        release_manifest["backend_path"] = str(final_dir / "backend")
        release_manifest["frontend_dist_path"] = str(final_dir / "frontend" / "dist")
        (candidate / "release-manifest.json").write_text(
            json.dumps(release_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

        os.replace(candidate, final_dir)

    return final_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Compose a Digital Crown INSTALLABLE_CERTIFIED release")
    parser.add_argument("--code-release-dir", required=True, type=Path)
    parser.add_argument("--runtime-assets-dir", required=True, type=Path)
    parser.add_argument("--runtime-root", required=True, type=Path)
    parser.add_argument("--attestation-evidence", required=True, type=Path)
    parser.add_argument("--code-artifact-sha256", required=True)
    parser.add_argument("--runtime-asset-bundle-sha256", required=True)
    args = parser.parse_args()

    final_dir = compose(
        code_release_dir=args.code_release_dir,
        runtime_assets_dir=args.runtime_assets_dir,
        runtime_root=args.runtime_root,
        attestation_evidence=args.attestation_evidence,
        code_artifact_sha256=args.code_artifact_sha256,
        runtime_asset_bundle_sha256=args.runtime_asset_bundle_sha256,
    )
    print(f"INSTALLABLE_RELEASE={final_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
