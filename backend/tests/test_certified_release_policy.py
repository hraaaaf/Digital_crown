import hashlib
import json
from pathlib import Path

import pytest

from backend.release_certification import (
    ATTESTATION_EVIDENCE_FILENAME,
    CERTIFICATE_FILENAME,
    CODE_CERTIFICATION_LEVEL,
    CONTENT_MANIFEST_FILENAME,
    GITHUB_SIGNER_WORKFLOW,
    INSTALLABLE_CERTIFICATE_FILENAME,
    REQUIRED_PACKS,
    SHA_MARKER_FILENAME,
    ReleaseCertificationError,
    verify_installable_release_directory,
    verify_release_directory,
)
from backend.runtime_asset_certification import (
    ASSET_CERTIFICATE_FILENAME,
    ASSET_MANIFEST_FILENAME,
    RuntimeAssetCertificationError,
    inspect_registry_coverage,
    sha256_file,
)


CERTIFIED_SHA = "a" * 40


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_code_release(tmp_path: Path, *, packs=None, sha=CERTIFIED_SHA, marker=None):
    backend = tmp_path / "backend"
    backend.mkdir(parents=True, exist_ok=True)
    payload_file = tmp_path / "backend-payload.txt"
    payload_file.write_text("certified-payload", encoding="utf-8")

    pinned_bytes = b"pinned-runtime-model"
    registry = {
        "schema_version": 2,
        "p5_certification_scope": "native-runtime-and-fail-closed",
        "asset_policy": "external-not-versioned",
        "assets": [
            {
                "id": "pinned-model",
                "kind": "model",
                "lifecycle": "external",
                "p5_required": False,
                "canonical_path": "backend/ai_models/pinned.onnx",
                "sha256": _digest(pinned_bytes),
                "size_bytes": len(pinned_bytes),
                "next_gate": "installable release",
            },
            {
                "id": "legacy-model",
                "kind": "model",
                "lifecycle": "external",
                "p5_required": False,
                "next_gate": "scientific provenance completion",
            },
        ],
    }
    registry_path = backend / "scientific_assets.json"
    registry_path.write_text(json.dumps(registry), encoding="utf-8")

    lines = []
    for path in (payload_file, registry_path):
        lines.append(f"{sha256_file(path)}  {path.relative_to(tmp_path).as_posix()}")
    manifest = tmp_path / CONTENT_MANIFEST_FILENAME
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    manifest_digest = sha256_file(manifest)

    release_id = f"dc-cabinet-{sha[:12]}-run123"
    payload = {
        "certificate_version": 1,
        "artifact_type": "cabinet-certified-release",
        "certification_level": CODE_CERTIFICATION_LEVEL,
        "repository": "hraaaaf/Digital_crown",
        "commit_sha": sha,
        "release_id": release_id,
        "certified_packs": list(packs if packs is not None else REQUIRED_PACKS),
        "certification_run_id": 123,
        "certified_at": "2026-09-12T12:00:00Z",
        "content_manifest_sha256": manifest_digest,
        "installable": False,
    }
    (tmp_path / CERTIFICATE_FILENAME).write_text(json.dumps(payload), encoding="utf-8")
    (tmp_path / SHA_MARKER_FILENAME).write_text(marker or sha, encoding="utf-8")
    return payload, pinned_bytes


def _make_installable(tmp_path: Path):
    code_payload, pinned_bytes = _write_code_release(tmp_path)
    ai_models = tmp_path / "backend" / "ai_models"
    ai_models.mkdir(parents=True, exist_ok=True)
    pinned = ai_models / "pinned.onnx"
    pinned.write_bytes(pinned_bytes)
    legacy = ai_models / "legacy.bin"
    legacy.write_bytes(b"legacy-deployment-bytes")

    asset_lines = [
        f"{sha256_file(pinned)}  backend/ai_models/pinned.onnx",
        f"{sha256_file(legacy)}  backend/ai_models/legacy.bin",
    ]
    asset_manifest = tmp_path / ASSET_MANIFEST_FILENAME
    asset_manifest.write_text("\n".join(asset_lines) + "\n", encoding="utf-8")
    registry_digest = sha256_file(tmp_path / "backend" / "scientific_assets.json")
    asset_payload = {
        "certificate_version": 1,
        "artifact_type": "cabinet-runtime-assets",
        "selection_policy_version": 1,
        "target_commit_sha": CERTIFIED_SHA,
        "scientific_assets_registry_sha256": registry_digest,
        "content_manifest_sha256": sha256_file(asset_manifest),
        "file_count": 2,
        "total_bytes": pinned.stat().st_size + legacy.stat().st_size,
        "pinned_registry_assets_verified": ["pinned-model"],
        "unpinned_registry_assets": ["legacy-model"],
    }
    (tmp_path / ASSET_CERTIFICATE_FILENAME).write_text(json.dumps(asset_payload), encoding="utf-8")

    evidence = tmp_path / ATTESTATION_EVIDENCE_FILENAME
    evidence.write_text(json.dumps([{"verificationResult": {"statement": {}}}]), encoding="utf-8")
    installable = {
        "certificate_version": 1,
        "artifact_type": "cabinet-installable-release",
        "certification_level": "INSTALLABLE_CERTIFIED",
        "commit_sha": CERTIFIED_SHA,
        "release_id": code_payload["release_id"],
        "certified_packs": list(REQUIRED_PACKS),
        "code_certification_run_id": code_payload["certification_run_id"],
        "code_content_manifest_sha256": code_payload["content_manifest_sha256"],
        "code_artifact_sha256": "c" * 64,
        "runtime_asset_bundle_sha256": "d" * 64,
        "scientific_assets_registry_sha256": registry_digest,
        "runtime_assets_content_manifest_sha256": asset_payload["content_manifest_sha256"],
        "runtime_assets_file_count": 2,
        "runtime_assets_total_bytes": asset_payload["total_bytes"],
        "pinned_registry_assets_verified": ["pinned-model"],
        "unpinned_registry_assets": ["legacy-model"],
        "github_attestation_verified": True,
        "github_attestation_repository": "hraaaaf/Digital_crown",
        "github_attestation_signer_workflow": GITHUB_SIGNER_WORKFLOW,
        "github_attestation_source_digest": CERTIFIED_SHA,
        "github_attestation_source_ref": "refs/heads/master",
        "github_attestation_evidence_sha256": sha256_file(evidence),
        "installable": True,
    }
    (tmp_path / INSTALLABLE_CERTIFICATE_FILENAME).write_text(json.dumps(installable), encoding="utf-8")
    (tmp_path / "release-manifest.json").write_text(
        json.dumps(
            {
                "environment": "cabinet-real",
                "release_id": code_payload["release_id"],
                "commit": CERTIFIED_SHA,
                "certification_level": "INSTALLABLE_CERTIFIED",
            }
        ),
        encoding="utf-8",
    )
    return code_payload, installable


def test_code_certificate_accepts_every_release_profile(tmp_path):
    expected, _ = _write_code_release(tmp_path)
    for pack in REQUIRED_PACKS:
        assert verify_release_directory(tmp_path, expected_pack=pack) == expected


def test_release_without_certificate_is_refused(tmp_path):
    (tmp_path / SHA_MARKER_FILENAME).write_text(CERTIFIED_SHA, encoding="utf-8")
    with pytest.raises(ReleaseCertificationError, match="Missing release-certification.json"):
        verify_release_directory(tmp_path)


def test_release_sha_mismatch_is_refused(tmp_path):
    _write_code_release(tmp_path, marker="b" * 40)
    with pytest.raises(ReleaseCertificationError, match="Release SHA mismatch"):
        verify_release_directory(tmp_path)


def test_release_missing_one_pack_is_refused(tmp_path):
    _write_code_release(tmp_path, packs=["BASIC", "GOLD"])
    with pytest.raises(ReleaseCertificationError, match="missing certified pack.*ELITE"):
        verify_release_directory(tmp_path)


def test_release_requires_exact_immutable_sha(tmp_path):
    _write_code_release(tmp_path, sha="master", marker="master")
    with pytest.raises(ReleaseCertificationError, match="exact 40-char SHA"):
        verify_release_directory(tmp_path)


def test_certified_code_payload_mutation_is_refused(tmp_path):
    _write_code_release(tmp_path)
    (tmp_path / "backend-payload.txt").write_text("mutated", encoding="utf-8")
    with pytest.raises(ReleaseCertificationError, match="Certified release file changed"):
        verify_release_directory(tmp_path)


def test_code_certified_alone_is_not_installable(tmp_path):
    _write_code_release(tmp_path)
    with pytest.raises(ReleaseCertificationError, match="installable-certification.json"):
        verify_installable_release_directory(tmp_path)


def test_installable_certificate_accepts_basic_gold_elite(tmp_path):
    _, expected = _make_installable(tmp_path)
    for pack in REQUIRED_PACKS:
        assert verify_installable_release_directory(tmp_path, expected_pack=pack) == expected


def test_installable_runtime_asset_mutation_is_refused(tmp_path):
    _make_installable(tmp_path)
    (tmp_path / "backend" / "ai_models" / "legacy.bin").write_bytes(b"changed")
    with pytest.raises(RuntimeAssetCertificationError, match="Runtime asset changed"):
        verify_installable_release_directory(tmp_path)


def test_installable_attestation_evidence_mutation_is_refused(tmp_path):
    _make_installable(tmp_path)
    (tmp_path / ATTESTATION_EVIDENCE_FILENAME).write_text("[]", encoding="utf-8")
    with pytest.raises(ReleaseCertificationError, match="attestation verification evidence changed"):
        verify_installable_release_directory(tmp_path)


def test_installable_unlisted_file_is_refused(tmp_path):
    _make_installable(tmp_path)
    (tmp_path / "backend" / "appended_evil.py").write_text("raise SystemExit('nope')\n", encoding="utf-8")
    with pytest.raises(ReleaseCertificationError, match="file-set mismatch.*appended_evil"):
        verify_installable_release_directory(tmp_path)


def test_current_scientific_registry_does_not_overclaim_unpinned_models():
    root = Path(__file__).resolve().parents[2]
    pinned, unpinned = inspect_registry_coverage(root)
    assert "cephalo_sota" in pinned
    assert "cephalo_legacy" in unpinned
    assert "panoramic" in unpinned


def test_repo_guards_cannot_fall_back_to_master_or_working_tree():
    root = Path(__file__).resolve().parents[2]
    creator = (root / "backend/scripts/create_release.ps1").read_text(encoding="utf-8-sig")
    launcher = (root / "backend/scripts/run_real_backend.ps1").read_text(encoding="utf-8-sig")
    frozen_launcher = (root / "run.py").read_text(encoding="utf-8-sig")
    spec = (root / "DigitalCrown.spec").read_text(encoding="utf-8-sig")
    installer = (root / "installer/DigitalCrown.iss").read_text(encoding="utf-8-sig")

    assert "CertifiedArtifactZip" in creator
    assert "RuntimeAssetsZip" in creator
    assert "rev-parse HEAD" not in creator
    assert "robocopy \"$RepoRoot\\backend\"" not in creator
    assert "gh" in creator.lower() and "attestation" in creator.lower()
    assert "--source-digest" in creator
    assert "--signer-workflow" in creator
    assert "--deny-self-hosted-runners" in creator
    assert "unlisted appended CODE file refused" in creator
    assert "compose_installable_release.py" in creator

    assert "verify_installable_release.py" in launcher
    assert "INSTALLABLE_CERTIFIED" in launcher
    assert "runtime-assets-certification.json" in launcher

    assert "verify_installable_release_directory(_CERTIFIED_RELEASE_ROOT)" in spec
    assert "iter_runtime_asset_files" in spec
    assert "installable-certification.json" in spec
    assert "runtime-assets-content.sha256" in spec

    verify_call = frozen_launcher.index("\n_verify_frozen_release_certification()")
    bootstrap_call = frozen_launcher.index("\n_first_boot_bootstrap()")
    assert verify_call < bootstrap_call
    assert "verify_installable_release_identity(bundle_root)" in frozen_launcher

    assert "FileExists" in installer
    assert "installable-certification.json" in installer
    assert "runtime-assets-certification.json" in installer
    assert "github-attestation-verification.json" in installer


def test_future_prs_cannot_skip_cabinet_upgrade_gate_by_path_filter():
    root = Path(__file__).resolve().parents[2]
    workflow = (root / ".github/workflows/cabinet-upgrade-postgres-cert.yml").read_text(
        encoding="utf-8-sig"
    )
    assert "pull_request:\n    paths:" not in workflow
    assert "test_certified_release_policy.py" in workflow
    assert "Parse PowerShell release guards" in workflow


def test_release_certification_workflow_is_exact_master_sha_attested_and_code_only():
    root = Path(__file__).resolve().parents[2]
    workflow = (root / ".github/workflows/cabinet-release-certification.yml").read_text(
        encoding="utf-8-sig"
    )
    assert "commit_sha" in workflow
    assert "^[0-9a-f]{40}$" in workflow
    assert 'GITHUB_REF" != "refs/heads/master' in workflow
    assert 'MASTER_SHA="$(git rev-parse origin/master)"' in workflow
    assert '"$CERTIFIED_SHA" != "$MASTER_SHA"' in workflow
    assert "id-token: write" in workflow
    assert "attestations: write" in workflow
    assert "actions/attest@v4" in workflow
    assert '"certification_level": "CODE_CERTIFIED"' in workflow
    assert '"installable": False' in workflow
    assert "steps.materialize.outputs.release_id" in workflow
    assert "runner.temp" in workflow
    assert "BASIC" in workflow and "GOLD" in workflow and "ELITE" in workflow
    assert "release-content.sha256" in workflow
