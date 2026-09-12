"""Fail-closed certification for Digital Crown cabinet releases.

Two levels are intentionally distinct:
- CODE_CERTIFIED: GitHub Actions validated one exact immutable 40-char Git SHA.
- INSTALLABLE_CERTIFIED: that code proof was composed with the exact external runtime
  assets and provenance verification required for cabinet installation/startup.

Only INSTALLABLE_CERTIFIED is allowed to reach a real cabinet runtime or installer.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from backend.runtime_asset_certification import (
    ASSET_CERTIFICATE_FILENAME,
    ASSET_MANIFEST_FILENAME,
    verify_runtime_assets,
)

CERTIFICATE_FILENAME = "release-certification.json"
SHA_MARKER_FILENAME = ".digitalcrown-release-sha"
CONTENT_MANIFEST_FILENAME = "release-content.sha256"
INSTALLABLE_CERTIFICATE_FILENAME = "installable-certification.json"
ATTESTATION_EVIDENCE_FILENAME = "github-attestation-verification.json"
CERTIFICATE_VERSION = 1
INSTALLABLE_CERTIFICATE_VERSION = 1
REPOSITORY = "hraaaaf/Digital_crown"
REQUIRED_PACKS = ("BASIC", "GOLD", "ELITE")
CODE_CERTIFICATION_LEVEL = "CODE_CERTIFIED"
INSTALLABLE_CERTIFICATION_LEVEL = "INSTALLABLE_CERTIFIED"
GITHUB_SIGNER_WORKFLOW = "hraaaaf/Digital_crown/.github/workflows/cabinet-release-certification.yml"
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


def _load_json(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise ReleaseCertificationError(f"Missing {path.name}; {label} refused")
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReleaseCertificationError(f"Invalid {path.name}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ReleaseCertificationError(f"{path.name} must be a JSON object")
    return payload


def _load_certificate(release_dir: Path) -> dict[str, Any]:
    return _load_json(release_dir / CERTIFICATE_FILENAME, "uncertified cabinet release")


def _normalize_packs(value: object) -> set[str]:
    if not isinstance(value, list):
        raise ReleaseCertificationError("certified_packs must be a list")
    return {str(pack).strip().upper() for pack in value}


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
    if payload.get("certification_level") != CODE_CERTIFICATION_LEVEL:
        raise ReleaseCertificationError("Release certificate is not CODE_CERTIFIED")

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

    packs = _normalize_packs(payload.get("certified_packs"))
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


def _verify_content_manifest(root: Path, payload: dict[str, Any]) -> set[str]:
    manifest = root / CONTENT_MANIFEST_FILENAME
    if not manifest.is_file():
        raise ReleaseCertificationError(
            f"Missing {CONTENT_MANIFEST_FILENAME}; certified payload integrity cannot be proven"
        )

    expected_manifest_digest = str(payload.get("content_manifest_sha256", "")).strip().lower()
    if not _DIGEST_RE.fullmatch(expected_manifest_digest):
        raise ReleaseCertificationError("content_manifest_sha256 must be a SHA-256 digest")
    if _sha256(manifest) != expected_manifest_digest:
        raise ReleaseCertificationError(
            "Content manifest digest mismatch; certified release metadata was altered"
        )

    lines = manifest.read_text(encoding="utf-8").splitlines()
    if not lines:
        raise ReleaseCertificationError("Content manifest is empty")

    seen: set[str] = set()
    for line in lines:
        try:
            expected_digest, relative = line.split("  ", 1)
        except ValueError as exc:
            raise ReleaseCertificationError(f"Malformed content manifest line: {line!r}") from exc
        expected_digest = expected_digest.strip().lower()
        relative = relative.replace("\\", "/")
        if not _DIGEST_RE.fullmatch(expected_digest):
            raise ReleaseCertificationError(f"Malformed file digest for {relative!r}")
        if relative in seen:
            raise ReleaseCertificationError(f"Duplicate content manifest path: {relative}")
        seen.add(relative)

        rel_path = Path(relative)
        if rel_path.is_absolute() or ".." in rel_path.parts:
            raise ReleaseCertificationError(f"Unsafe content manifest path: {relative!r}")
        path = root / rel_path
        if not path.is_file() or path.is_symlink():
            raise ReleaseCertificationError(f"Certified release file missing/unsafe: {relative}")
        if _sha256(path) != expected_digest:
            raise ReleaseCertificationError(f"Certified release file changed: {relative}")
    return seen


def _runtime_asset_manifest_paths(root: Path) -> set[str]:
    manifest = root / ASSET_MANIFEST_FILENAME
    paths: set[str] = set()
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            _, relative = line.split("  ", 1)
        except ValueError as exc:
            raise ReleaseCertificationError(f"Malformed runtime asset manifest line: {line!r}") from exc
        normalized = relative.replace("\\", "/")
        if normalized in paths:
            raise ReleaseCertificationError(f"Duplicate runtime asset manifest path: {normalized}")
        paths.add(normalized)
    return paths


def _verify_exact_installable_file_set(root: Path, code_paths: set[str]) -> None:
    """Reject appended/unlisted files in a composed source release.

    This closes the gap where an attacker could preserve all attested hashes while
    appending a new executable/importable file beside them.
    """

    allowed = set(code_paths)
    allowed.update(_runtime_asset_manifest_paths(root))
    allowed.update(
        {
            CERTIFICATE_FILENAME,
            SHA_MARKER_FILENAME,
            CONTENT_MANIFEST_FILENAME,
            INSTALLABLE_CERTIFICATE_FILENAME,
            ASSET_CERTIFICATE_FILENAME,
            ASSET_MANIFEST_FILENAME,
            ATTESTATION_EVIDENCE_FILENAME,
            "release-manifest.json",
            # Runtime audit generated only after a successful activation.
            "runtime-activation.json",
        }
    )

    actual: set[str] = set()
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.is_symlink():
            raise ReleaseCertificationError(f"Symlink file refused in installable release: {path}")
        actual.add(path.relative_to(root).as_posix())

    unexpected = sorted(actual - allowed)
    missing = sorted(allowed - actual - {"runtime-activation.json"})
    if unexpected or missing:
        raise ReleaseCertificationError(
            f"INSTALLABLE file-set mismatch unexpected={unexpected!r} missing={missing!r}"
        )


def _verify_installable_metadata(
    root: Path,
    code_payload: dict[str, Any],
    *,
    expected_pack: str | None = None,
) -> dict[str, Any]:
    installable = _load_json(
        root / INSTALLABLE_CERTIFICATE_FILENAME,
        "non-installable cabinet release",
    )
    if installable.get("certificate_version") != INSTALLABLE_CERTIFICATE_VERSION:
        raise ReleaseCertificationError("Unsupported installable certificate version")
    if installable.get("artifact_type") != "cabinet-installable-release":
        raise ReleaseCertificationError("Installable certificate artifact_type is invalid")
    if installable.get("certification_level") != INSTALLABLE_CERTIFICATION_LEVEL:
        raise ReleaseCertificationError("Release is not INSTALLABLE_CERTIFIED")
    if installable.get("installable") is not True:
        raise ReleaseCertificationError("Installable certificate is not marked installable=true")

    commit_sha = str(code_payload["commit_sha"]).lower()
    if str(installable.get("commit_sha", "")).strip().lower() != commit_sha:
        raise ReleaseCertificationError("Installable certificate/code SHA mismatch")
    if str(installable.get("release_id", "")).strip() != str(code_payload["release_id"]):
        raise ReleaseCertificationError("Installable certificate release_id mismatch")
    if installable.get("code_certification_run_id") != code_payload.get("certification_run_id"):
        raise ReleaseCertificationError("Installable/code certification run mismatch")
    if str(installable.get("code_content_manifest_sha256", "")).lower() != str(
        code_payload.get("content_manifest_sha256", "")
    ).lower():
        raise ReleaseCertificationError("Installable/code content manifest mismatch")

    for digest_field in ("code_artifact_sha256", "runtime_asset_bundle_sha256"):
        if not _DIGEST_RE.fullmatch(str(installable.get(digest_field, "")).lower()):
            raise ReleaseCertificationError(f"Invalid {digest_field}")

    packs = _normalize_packs(installable.get("certified_packs"))
    if packs != set(REQUIRED_PACKS):
        raise ReleaseCertificationError("INSTALLABLE certificate must cover exactly BASIC/GOLD/ELITE")
    if expected_pack is not None and expected_pack.strip().upper() not in packs:
        raise ReleaseCertificationError(f"Installable release does not cover {expected_pack!r}")

    if installable.get("github_attestation_verified") is not True:
        raise ReleaseCertificationError("GitHub/Sigstore provenance was not verified")
    if installable.get("github_attestation_repository") != REPOSITORY:
        raise ReleaseCertificationError("GitHub attestation repository mismatch")
    if installable.get("github_attestation_signer_workflow") != GITHUB_SIGNER_WORKFLOW:
        raise ReleaseCertificationError("GitHub attestation signer workflow mismatch")
    if str(installable.get("github_attestation_source_digest", "")).lower() != commit_sha:
        raise ReleaseCertificationError("GitHub attestation source digest mismatch")
    if installable.get("github_attestation_source_ref") != "refs/heads/master":
        raise ReleaseCertificationError("GitHub attestation source ref mismatch")

    evidence_path = root / ATTESTATION_EVIDENCE_FILENAME
    evidence_digest = str(installable.get("github_attestation_evidence_sha256", "")).lower()
    if not _DIGEST_RE.fullmatch(evidence_digest):
        raise ReleaseCertificationError("Invalid GitHub attestation evidence digest")
    if not evidence_path.is_file() or evidence_path.is_symlink() or _sha256(evidence_path) != evidence_digest:
        raise ReleaseCertificationError("GitHub attestation verification evidence changed/missing")
    try:
        evidence_payload = json.loads(evidence_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReleaseCertificationError(f"Invalid GitHub attestation evidence JSON: {exc}") from exc
    if not isinstance(evidence_payload, list) or not evidence_payload:
        raise ReleaseCertificationError("GitHub attestation evidence must be a non-empty JSON array")

    registry_digest = str(installable.get("scientific_assets_registry_sha256", "")).lower()
    asset_manifest_digest = str(installable.get("runtime_assets_content_manifest_sha256", "")).lower()
    if not _DIGEST_RE.fullmatch(registry_digest):
        raise ReleaseCertificationError("Invalid scientific asset registry digest")
    if not _DIGEST_RE.fullmatch(asset_manifest_digest):
        raise ReleaseCertificationError("Invalid runtime asset manifest digest")

    asset_payload = verify_runtime_assets(
        root,
        expected_commit_sha=commit_sha,
        expected_registry_sha256=registry_digest,
    )
    if str(asset_payload.get("content_manifest_sha256", "")).lower() != asset_manifest_digest:
        raise ReleaseCertificationError("Installable/runtime asset manifest mismatch")
    if installable.get("runtime_assets_file_count") != asset_payload.get("file_count"):
        raise ReleaseCertificationError("Installable/runtime asset file_count mismatch")
    if installable.get("runtime_assets_total_bytes") != asset_payload.get("total_bytes"):
        raise ReleaseCertificationError("Installable/runtime asset total_bytes mismatch")
    if sorted(installable.get("pinned_registry_assets_verified") or []) != sorted(
        asset_payload.get("pinned_registry_assets_verified") or []
    ):
        raise ReleaseCertificationError("Installable/pinned registry coverage mismatch")
    if sorted(installable.get("unpinned_registry_assets") or []) != sorted(
        asset_payload.get("unpinned_registry_assets") or []
    ):
        raise ReleaseCertificationError("Installable/unpinned registry coverage mismatch")

    return installable


def verify_release_identity(
    release_dir: str | Path,
    *,
    expected_pack: str | None = None,
) -> dict[str, Any]:
    """Verify portable CODE_CERTIFIED identity only."""
    root = Path(release_dir).resolve()
    if not root.is_dir():
        raise ReleaseCertificationError(f"Release directory does not exist: {root}")
    return _verify_identity(root, expected_pack)


def verify_release_directory(
    release_dir: str | Path,
    *,
    expected_pack: str | None = None,
) -> dict[str, Any]:
    """Verify complete CODE_CERTIFIED source payload hashes."""
    root = Path(release_dir).resolve()
    if not root.is_dir():
        raise ReleaseCertificationError(f"Release directory does not exist: {root}")
    payload = _verify_identity(root, expected_pack)
    _verify_content_manifest(root, payload)
    return payload


def verify_installable_release_directory(
    release_dir: str | Path,
    *,
    expected_pack: str | None = None,
) -> dict[str, Any]:
    """Verify code + provenance + external assets + exact composed source file-set."""
    root = Path(release_dir).resolve()
    if not root.is_dir():
        raise ReleaseCertificationError(f"Release directory does not exist: {root}")
    code_payload = _verify_identity(root, expected_pack)
    code_paths = _verify_content_manifest(root, code_payload)
    installable = _verify_installable_metadata(root, code_payload, expected_pack=expected_pack)
    _verify_exact_installable_file_set(root, code_paths)
    return installable


def verify_installable_release_identity(
    release_dir: str | Path,
    *,
    expected_pack: str | None = None,
) -> dict[str, Any]:
    """Verify packaged identity + exact external asset bytes before first-boot writes.

    PyInstaller transforms Python/source files and adds runtime files, so exact source
    file-set validation occurs before packaging in DigitalCrown.spec. External model
    files remain data files and are re-hashed here inside the frozen bundle.
    """
    root = Path(release_dir).resolve()
    code_payload = _verify_identity(root, expected_pack)
    return _verify_installable_metadata(root, code_payload, expected_pack=expected_pack)
