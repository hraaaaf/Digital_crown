import hashlib
import json
from pathlib import Path

import pytest

from backend.release_certification import (
    CERTIFICATE_FILENAME,
    CONTENT_MANIFEST_FILENAME,
    REQUIRED_PACKS,
    SHA_MARKER_FILENAME,
    ReleaseCertificationError,
    verify_release_directory,
)


CERTIFIED_SHA = "a" * 40


def _write_release(tmp_path: Path, *, packs=None, sha=CERTIFIED_SHA, marker=None):
    payload_file = tmp_path / "backend-payload.txt"
    payload_file.write_text("certified-payload", encoding="utf-8")
    payload_digest = hashlib.sha256(payload_file.read_bytes()).hexdigest()
    manifest = tmp_path / CONTENT_MANIFEST_FILENAME
    manifest.write_text(f"{payload_digest}  backend-payload.txt\n", encoding="utf-8")
    manifest_digest = hashlib.sha256(manifest.read_bytes()).hexdigest()

    release_id = f"dc-cabinet-{sha[:12]}-run123"
    payload = {
        "certificate_version": 1,
        "artifact_type": "cabinet-certified-release",
        "repository": "hraaaaf/Digital_crown",
        "commit_sha": sha,
        "release_id": release_id,
        "certified_packs": list(packs if packs is not None else REQUIRED_PACKS),
        "certification_run_id": 123,
        "certified_at": "2026-09-12T12:00:00Z",
        "content_manifest_sha256": manifest_digest,
    }
    (tmp_path / CERTIFICATE_FILENAME).write_text(json.dumps(payload), encoding="utf-8")
    (tmp_path / SHA_MARKER_FILENAME).write_text(marker or sha, encoding="utf-8")
    return payload


def test_universal_certificate_accepts_every_commercial_pack(tmp_path):
    expected = _write_release(tmp_path)

    for pack in REQUIRED_PACKS:
        payload = verify_release_directory(tmp_path, expected_pack=pack)
        assert payload == expected


def test_release_without_certificate_is_refused(tmp_path):
    (tmp_path / SHA_MARKER_FILENAME).write_text(CERTIFIED_SHA, encoding="utf-8")
    with pytest.raises(ReleaseCertificationError, match="Missing release-certification.json"):
        verify_release_directory(tmp_path)


def test_release_sha_mismatch_is_refused(tmp_path):
    _write_release(tmp_path, marker="b" * 40)
    with pytest.raises(ReleaseCertificationError, match="Release SHA mismatch"):
        verify_release_directory(tmp_path)


def test_release_missing_one_pack_is_refused(tmp_path):
    _write_release(tmp_path, packs=["BASIC", "GOLD"])
    with pytest.raises(ReleaseCertificationError, match="missing certified pack.*ELITE"):
        verify_release_directory(tmp_path)


def test_release_requires_exact_immutable_sha(tmp_path):
    _write_release(tmp_path, sha="master", marker="master")
    with pytest.raises(ReleaseCertificationError, match="exact 40-char SHA"):
        verify_release_directory(tmp_path)


def test_certified_payload_mutation_is_refused(tmp_path):
    _write_release(tmp_path)
    (tmp_path / "backend-payload.txt").write_text("mutated", encoding="utf-8")
    with pytest.raises(ReleaseCertificationError, match="Certified release file changed"):
        verify_release_directory(tmp_path)


def test_repo_guards_cannot_fall_back_to_master_or_working_tree():
    root = Path(__file__).resolve().parents[2]
    creator = (root / "backend/scripts/create_release.ps1").read_text(encoding="utf-8-sig")
    launcher = (root / "backend/scripts/run_real_backend.ps1").read_text(encoding="utf-8-sig")
    spec = (root / "DigitalCrown.spec").read_text(encoding="utf-8-sig")
    installer = (root / "installer/DigitalCrown.iss").read_text(encoding="utf-8-sig")

    assert "CertifiedArtifactZip" in creator
    assert "rev-parse HEAD" not in creator
    assert "robocopy \"$RepoRoot\\backend\"" not in creator
    assert "release-certification.json" in creator
    assert ".digitalcrown-release-sha" in creator
    assert "release-content.sha256" in creator

    assert "verify_certified_release.py" in launcher
    assert "release-certification.json" in launcher
    assert ".digitalcrown-release-sha" in launcher

    assert "release-certification.json" in spec
    assert ".digitalcrown-release-sha" in spec
    assert "release-content.sha256" in spec
    assert "FileExists" in installer
    assert "release-certification.json" in installer
    assert ".digitalcrown-release-sha" in installer


def test_future_prs_cannot_skip_cabinet_upgrade_gate_by_path_filter():
    root = Path(__file__).resolve().parents[2]
    workflow = (root / ".github/workflows/cabinet-upgrade-postgres-cert.yml").read_text(
        encoding="utf-8-sig"
    )
    assert "pull_request:\n    paths:" not in workflow
    assert "test_certified_release_policy.py" in workflow


def test_release_certification_workflow_is_exact_sha_and_universal():
    root = Path(__file__).resolve().parents[2]
    workflow = (root / ".github/workflows/cabinet-release-certification.yml").read_text(
        encoding="utf-8-sig"
    )
    assert "commit_sha" in workflow
    assert "^[0-9a-f]{40}$" in workflow
    assert "BASIC" in workflow
    assert "GOLD" in workflow
    assert "ELITE" in workflow
    assert "release-certification.json" in workflow
    assert ".digitalcrown-release-sha" in workflow
    assert "release-content.sha256" in workflow
