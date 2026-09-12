"""Create an immutable runtime-asset bundle for one CODE_CERTIFIED SHA.

This script is intentionally local: model bytes remain outside Git. It copies only
the exact asset set used by DigitalCrown.spec, hashes every byte, validates all
scientific registry pins that already exist, and binds the bundle to one exact code
SHA + one exact scientific_assets.json digest.
"""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from backend.release_certification import verify_release_directory
from backend.runtime_asset_certification import (
    ASSET_ARTIFACT_TYPE,
    ASSET_CERTIFICATE_FILENAME,
    ASSET_CERTIFICATE_VERSION,
    ASSET_MANIFEST_FILENAME,
    ASSET_SELECTION_POLICY_VERSION,
    inspect_registry_coverage,
    iter_runtime_asset_files,
    runtime_asset_manifest_relpath,
    sha256_file,
    verify_runtime_assets,
)


def _copy_assets(ai_models_dir: Path, bundle_root: Path) -> tuple[list[str], int]:
    target_root = bundle_root / "backend" / "ai_models"
    lines: list[str] = []
    total_bytes = 0
    for source in iter_runtime_asset_files(ai_models_dir):
        relative = source.relative_to(ai_models_dir)
        target = target_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        digest = sha256_file(target)
        rel = runtime_asset_manifest_relpath(target, target_root)
        lines.append(f"{digest}  {rel}")
        total_bytes += target.stat().st_size
    if not lines:
        raise SystemExit("No runtime assets selected; INSTALLABLE certification refused")
    return lines, total_bytes


def build_bundle(code_release_dir: Path, ai_models_dir: Path, output_zip: Path) -> None:
    code_release_dir = code_release_dir.resolve()
    ai_models_dir = ai_models_dir.resolve()
    output_zip = output_zip.resolve()

    code_cert = verify_release_directory(code_release_dir)
    commit_sha = str(code_cert["commit_sha"]).lower()
    registry_source = code_release_dir / "backend" / "scientific_assets.json"
    if not registry_source.is_file():
        raise SystemExit("CODE_CERTIFIED artifact is missing backend/scientific_assets.json")
    registry_digest = sha256_file(registry_source)

    with tempfile.TemporaryDirectory(prefix="digitalcrown-runtime-assets-") as tmp:
        root = Path(tmp)
        (root / "backend").mkdir(parents=True, exist_ok=True)
        shutil.copy2(registry_source, root / "backend" / "scientific_assets.json")

        lines, total_bytes = _copy_assets(ai_models_dir, root)
        manifest = root / ASSET_MANIFEST_FILENAME
        manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
        manifest_digest = sha256_file(manifest)

        pinned, unpinned = inspect_registry_coverage(root)
        certificate = {
            "certificate_version": ASSET_CERTIFICATE_VERSION,
            "artifact_type": ASSET_ARTIFACT_TYPE,
            "selection_policy_version": ASSET_SELECTION_POLICY_VERSION,
            "target_commit_sha": commit_sha,
            "scientific_assets_registry_sha256": registry_digest,
            "content_manifest_sha256": manifest_digest,
            "file_count": len(lines),
            "total_bytes": total_bytes,
            "pinned_registry_assets_verified": pinned,
            "unpinned_registry_assets": unpinned,
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "scientific_claim": "deployment-integrity-only",
        }
        (root / ASSET_CERTIFICATE_FILENAME).write_text(
            json.dumps(certificate, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

        # Full proof before producing the archive.
        verify_runtime_assets(
            root,
            expected_commit_sha=commit_sha,
            expected_registry_sha256=registry_digest,
        )

        output_zip.parent.mkdir(parents=True, exist_ok=True)
        output_zip.unlink(missing_ok=True)
        with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as archive:
            for path in sorted(p for p in root.rglob("*") if p.is_file()):
                archive.write(path, path.relative_to(root).as_posix())

    print(f"RUNTIME_ASSET_BUNDLE={output_zip}")
    print(f"TARGET_SHA={commit_sha}")
    print(f"FILE_COUNT={len(lines)}")
    print(f"TOTAL_BYTES={total_bytes}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Certify Digital Crown external runtime assets")
    parser.add_argument("--code-release-dir", required=True, type=Path)
    parser.add_argument("--ai-models-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    build_bundle(args.code_release_dir, args.ai_models_dir, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
