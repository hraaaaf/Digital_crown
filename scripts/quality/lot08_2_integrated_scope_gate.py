"""LOT08.2 integrated PR source-only exact-scope guard (synthetic LAB).

Runs before tests in E/F/G workflows. A green guard must not be interpreted
as approval for a clinical installable or for merging to master.
"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

BASE = "093e89390d0e4b934d478485ea1ef28a7ce95de4"
ADDED = {
    ".github/workflows/v15-08-2-e-windows-service-snapshot-lab.yml",
    ".github/workflows/v15-08-2-f-user-profile-cold-restore.yml",
    ".github/workflows/v15-08-2-g-installable-vm-readiness-fue.yml",
    "docs/quality/V15_08_2_G_INSTALLABLE_VM_REHEARSAL_GATE.md",
    "queue_core/tests/test_activation_source_08_2_f.py",
    "queue_core/tests/test_installable_gate_08_2_g.py",
    "queue_core/tests/test_snapshot_08_2_e.py",
    "scripts/quality/lot08_2_e_service_probe.py",
    "scripts/quality/lot08_2_e_snapshot_lab.py",
    "scripts/quality/lot08_2_e_windows_service_lab.ps1",
    "scripts/quality/lot08_2_f_activation_source_lab.py",
    "scripts/quality/lot08_2_f_user_process_probe.py",
    "scripts/quality/lot08_2_f_windows_user_profile_lab.ps1",
    "scripts/quality/lot08_2_g_installable_gate.py",
    "scripts/quality/lot08_2_g_sqlcipher_lab.py",
    "scripts/quality/lot08_2_integrated_scope_gate.py",
}
MODIFIED = {"queue_core/tests/test_kiosk_qr_lab_08_2_d.py"}


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-head", required=True)
    args = parser.parse_args()
    assert git("rev-parse", "HEAD") == args.expected_head, "HEAD_MISMATCH"
    assert git("merge-base", "--is-ancestor", BASE, "HEAD") == "", "BASE_NOT_ANCESTOR"
    lines = git("diff", "--name-status", "--no-renames", BASE, "HEAD").splitlines()
    actual = {}
    for line in lines:
        status, path = line.split("\t", 1)
        assert status in ("A", "M"), f"NON_ADDITIVE_CHANGE: {line}"
        assert path not in actual, f"DUPLICATE_PATH: {path}"
        actual[path] = status
    expected = {**{path: "A" for path in ADDED}, **{path: "M" for path in MODIFIED}}
    assert actual == expected, (
        f"SCOPE_MISMATCH added={sorted(set(actual)-set(expected))} "
        f"missing={sorted(set(expected)-set(actual))} "
        f"status_changes={sorted(k for k in set(actual)&set(expected) if actual[k]!=expected[k])}"
    )
    assert not Path("dist/DigitalCrownSetup.exe").exists(), "INSTALLER_FORBIDDEN"
    print(f"LOT08_2_INTEGRATED_SOURCE_SCOPE_PASS={args.expected_head} files={len(actual)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
