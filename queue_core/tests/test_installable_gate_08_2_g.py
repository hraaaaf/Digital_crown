"""LOT08.2-G: no certificate is ever invented by these negative tests."""
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.quality.lot08_2_g_installable_gate import (
    GateRefusal, VERDICT_BLOCKED, VERDICT_REHEARSAL, decide, main,
)

MASTER = "bb3c92b9b8c7a56ecd5f60bf9c1d52c578f2f3a4"
OLD_CERTIFIED = "98f0199dde54123d1caf3b41443c47a000c3b39f"


def test_absent_exact_master_installable_fail_closed():
    report = decide(None, MASTER)
    assert report["verdict"] == VERDICT_BLOCKED
    assert report["reason"] == "NO_INSTALLABLE_CANDIDATE_SUPPLIED"
    assert report["installable_go"] is False
    assert report["candidate_installable_verified"] is False


@pytest.mark.parametrize("sha", ["master", "HEAD", "bb3c92b9", "", MASTER.upper(), OLD_CERTIFIED[:39]])
def test_moving_or_nonexact_sha_fails(sha):
    with pytest.raises(GateRefusal, match="EXACT_MASTER_SHA_REQUIRED"):
        decide(None, sha)


def test_absent_or_empty_candidate_does_not_become_certified(tmp_path):
    candidate = tmp_path / "code-certified-artifact-do-not-trust"
    candidate.mkdir()
    assert decide(candidate, MASTER)["reason"] == "CANONICAL_INSTALLABLE_VERIFIER_REFUSED"
    assert decide(tmp_path / "absent", MASTER)["reason"] == "CANDIDATE_DIR_MISSING_OR_SYMLINK"


def test_fake_named_installable_certificate_is_insufficient(tmp_path):
    root = tmp_path / "INSTALLABLE_CERTIFIED"
    root.mkdir()
    (root / "installable-certification.json").write_text(json.dumps({
        "installable": True, "certification_level": "INSTALLABLE_CERTIFIED",
        "commit_sha": MASTER, "github_attestation_verified": True,
    }))
    assert decide(root, MASTER)["reason"] == "CANONICAL_INSTALLABLE_VERIFIER_REFUSED"


def test_code_certified_alone_is_not_installable(tmp_path):
    root = tmp_path / "old-code-cert"
    root.mkdir()
    (root / "release-certification.json").write_text(json.dumps({
        "certification_level": "CODE_CERTIFIED",
        "commit_sha": OLD_CERTIFIED, "certified_packs": ["BASIC", "GOLD", "ELITE"],
    }))
    assert decide(root, MASTER)["verdict"] == VERDICT_BLOCKED


def test_symlink_candidate_rejected(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    alias = tmp_path / "link"
    try:
        alias.symlink_to(target, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("Symlink creation not permitted on this test host")
    assert decide(alias, MASTER)["reason"] == "CANDIDATE_DIR_MISSING_OR_SYMLINK"


def test_historical_successful_code_sha_does_not_match_current_master(tmp_path):
    # Mock here tests ONLY post-verifier exact-master binding, not a real cert.
    root = tmp_path / "fake-positive-verifier"
    root.mkdir()
    synthetic_stub = {
        "certification_level": "INSTALLABLE_CERTIFIED",
        "installable": True, "commit_sha": OLD_CERTIFIED,
    }
    with patch("scripts.quality.lot08_2_g_installable_gate.verify_installable_release_directory", return_value=synthetic_stub):
        report = decide(root, MASTER)
    assert report["reason"] == "CERTIFIED_SHA_NOT_CURRENT_MASTER"
    assert report["candidate_installable_verified"] is False


@pytest.mark.parametrize("injected", [
    {"certification_level": "CODE_CERTIFIED", "installable": True},
    {"certification_level": "INSTALLABLE_CERTIFIED", "installable": False},
    {"certification_level": "INSTALLABLE_CERTIFIED", "installable": True, "commit_sha": "x" * 40},
])
def test_mocked_verifier_payload_still_requires_exact_final_state(tmp_path, injected):
    # A mocked verifier cannot prove authentic provenance; only the post-check is tested.
    root = tmp_path / "mocked"
    root.mkdir()
    stub = {"commit_sha": MASTER, **injected}
    with patch("scripts.quality.lot08_2_g_installable_gate.verify_installable_release_directory", return_value=stub):
        report = decide(root, MASTER)
    assert report["verdict"] == VERDICT_BLOCKED


def test_cli_no_artifact_returns_nonzero_without_secrets(capsys):
    assert main(["--expected-master-sha", MASTER]) == 3
    report = json.loads(capsys.readouterr().out)
    assert report["verdict"] == VERDICT_BLOCKED
    assert report["actual_installer_executed"] is False
    assert report["clinical_go"] is False


def test_mocked_valid_metadata_is_only_vm_rehearsal_eligibility(tmp_path):
    # This MOCK is not a certification test: canonical verification is excluded.
    root = tmp_path / "mocked"
    root.mkdir()
    stub = {"certification_level": "INSTALLABLE_CERTIFIED", "installable": True, "commit_sha": MASTER}
    with patch("scripts.quality.lot08_2_g_installable_gate.verify_installable_release_directory", return_value=stub):
        report = decide(root, MASTER)
    assert report["verdict"] == VERDICT_REHEARSAL
    assert report["installable_go"] is False
    assert report["clinical_go"] is False
    assert report["actual_installer_executed"] is False
