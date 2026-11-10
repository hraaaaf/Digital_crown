"""B-6 read-only installable readiness criteria (not installable certification)."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys

import pytest


REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts/v15_08_2_b_desktop_installable_preflight.py"
SPEC = importlib.util.spec_from_file_location("b6_source_preflight", SCRIPT)
assert SPEC and SPEC.loader
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)


def test_real_source_guard_contracts_are_present():
    rules = GATE.inspect_sources(REPO)
    assert len(rules) == 10
    assert [r for r in rules if r["source_status"] != "PRESENT"] == []


def test_missing_source_guard_fails_closed_in_synthetic_repository(tmp_path):
    for _gate, relative, tokens in GATE.RULES:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("\n".join(tokens), encoding="utf-8")
    assert all(r["source_status"] == "PRESENT" for r in GATE.inspect_sources(tmp_path))
    (tmp_path / "DigitalCrown.spec").write_text("UNSAFE_PACKAGE_ALLOWED", encoding="utf-8")
    statuses = {r["gate"]: r["source_status"] for r in GATE.inspect_sources(tmp_path)}
    assert statuses["pyinstaller_certificate"] == "MISSING"
    assert "MISSING" in statuses.values()


def test_clinical_waiting_room_lab_coupling_is_rejected(tmp_path):
    for _gate, relative, tokens in GATE.RULES:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("\n".join(tokens), encoding="utf-8")
    waiting = tmp_path / "frontend/src/pages/WaitingRoomPage.tsx"
    waiting.write_text("/appointments/\nqueue-core-lab\n", encoding="utf-8")
    assert any(
        r["gate"] == "clinical_waiting_room_still_legacy"
        and r["source_status"] == "MISSING"
        for r in GATE.inspect_sources(tmp_path)
    )


def test_exact_sha_and_no_go_are_non_negotiable():
    expected_sha = "b" * 40
    with pytest.raises(GATE.PreflightError, match="40_HEX"):
        GATE.build_report(REPO, "master", expected_sha, "feature")
    with pytest.raises(GATE.PreflightError, match="SOURCE_SHA_MISMATCH"):
        GATE.build_report(REPO, "a" * 40, expected_sha, "feature")
    report = GATE.build_report(REPO, expected_sha, expected_sha, "feature")
    assert report["source_status"] == "PRESENT"
    assert report["installable_ready"] is False
    assert report["clinical_go"] is False
    assert report["actual_native_package"] == "NOT_BUILT"
    assert report["exact_master_code_certified_artifact"] == "NOT_VERIFIED"
    assert report["clinical_appointment_migration"] == "NOT_AUTHORIZED"


def test_real_cli_is_strictly_read_only_and_json_is_stdout_only():
    import json

    sha = subprocess.run(
        ["git", "-C", str(REPO), "rev-parse", "HEAD"],
        check=True, text=True, capture_output=True,
    ).stdout.strip()
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--repo-root", str(REPO), "--expected-sha", sha],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "SOURCE_GATE_PRESENT_NO_INSTALLABLE_GO" in result.stdout
    assert "installable_ready=false" in result.stdout
    # An output path is deliberately not a supported argument.
    denied = subprocess.run(
        [
            sys.executable, str(SCRIPT), "--repo-root", str(REPO),
            "--expected-sha", sha, "--output", str(REPO / "STATE.md"),
        ], capture_output=True, text=True, timeout=30,
    )
    assert denied.returncode == 2 and "unrecognized arguments" in denied.stderr
    machine = subprocess.run(
        [
            sys.executable, str(SCRIPT), "--repo-root", str(REPO),
            "--expected-sha", sha, "--json",
        ], capture_output=True, text=True, timeout=30,
    )
    assert machine.returncode == 0
    report = json.loads(machine.stdout)
    assert report["installable_ready"] is False
    assert report["clinical_go"] is False
    assert report["source_status"] == "PRESENT"
    assert report["source_sha"] == sha
