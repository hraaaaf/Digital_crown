"""Read-only SOURCE preflight, never an installable or clinical certificate.

This tool does not build, install, read patient data, activate, migrate, inspect
secrets or validate a live package. The canonical master certification remains
the sole route to CODE_CERTIFIED and later INSTALLABLE_CERTIFIED.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys

# Lexical markers check presence of known guards, NOT their runtime correctness.
RULES = (
    ("release_policy", "docs/CABINET_CERTIFIED_RELEASE_POLICY.md",
     ("CODE_CERTIFIED", "INSTALLABLE_CERTIFIED", "GitHub/Sigstore", "BASIC / GOLD / ELITE")),
    ("master_certificate", ".github/workflows/cabinet-release-certification.yml",
     ("workflow_dispatch:", "refs/heads/master", "CERTIFIED_SHA", "MASTER_SHA")),
    ("pyinstaller_certificate", "DigitalCrown.spec",
     ("verify_installable_release_directory(_CERTIFIED_RELEASE_ROOT)",)),
    ("frozen_preboot", "run.py",
     ("\n_verify_frozen_release_certification()\n"
      "_select_cabinet_env_profile()\n"
      "_first_boot_bootstrap()",)),
    ("inno_seven_manifests", "installer/DigitalCrown.iss",
     ("release-certification.json", ".digitalcrown-release-sha", "release-content.sha256",
      "installable-certification.json", "runtime-assets-certification.json",
      "runtime-assets-content.sha256", "github-attestation-verification.json",
      "CloseApplications=no", "RestartApplications=no", "PrivilegesRequired=lowest")),
    ("test_only_queue_bridge", "queue_core/service/desktop_lab_bridge.py",
     ('environment != "test" or variables.get(FLAG) != "1"',
      '".queue-fue-marker"', '"auth.sqlite"', '"queue.sqlite"',
      "QUEUE_LAB_CLINICAL_DB_COLLISION")),
    ("opt_in_main_mount", "backend/main.py",
     ('os.environ.get("DIGITALCROWN_QUEUE_CORE_LAB_ENABLE") == "1"',
      "environment=str(app_settings.ENVIRONMENT).lower()",
      "_QUEUE_CORE_LAB_MOUNTED")),
    ("dev_only_react_route", "frontend/src/App.tsx",
     ('import.meta.env.DEV && import.meta.env.VITE_QUEUE_CORE_LAB_PREVIEW === "true"',
      'path="/queue-core-lab"')),
    ("risk_proof_policy", "docs/quality/REALITY_PROOF_GATE.md",
     ("RPG-P", "FUE-G", "GREEN is not CONVERGED")),
    ("clinical_waiting_room_still_legacy", "frontend/src/pages/WaitingRoomPage.tsx",
     ("/appointments/",)),
)


class PreflightError(ValueError):
    pass


def inspect_sources(root: Path) -> list[dict]:
    """Inspect only named source files; never touch cabinet profile paths."""
    result = []
    for gate, relative, required in RULES:
        path = root / relative
        if path.is_file() and not path.is_symlink():
            content = path.read_text(encoding="utf-8")
            missing = [v for v in required if v not in content]
            if gate == "clinical_waiting_room_still_legacy" and "queue-core-lab" in content:
                missing.append("CLINICAL_SCREEN_MUST_NOT_USE_LAB")
        else:
            missing = list(required)
        result.append({
            "gate": gate, "source": relative,
            "source_status": "PRESENT" if not missing else "MISSING",
            "missing_markers": missing,
        })
    return result


def build_report(root: Path, expected_sha: str, actual_sha: str, branch: str) -> dict:
    if re.fullmatch(r"[0-9a-f]{40}", expected_sha) is None:
        raise PreflightError("EXPECTED_SHA_40_HEX_REQUIRED")
    if expected_sha != actual_sha:
        raise PreflightError("EXACT_SOURCE_SHA_MISMATCH")
    rules = inspect_sources(root)
    ok = all(x["source_status"] == "PRESENT" for x in rules)
    return {
        "marker": "V15_08_2_B_INSTALLABLE_SOURCE_ONLY_NO_GO",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_sha": actual_sha, "branch": branch,
        "source_checks": rules,
        "source_status": "PRESENT" if ok else "MISSING",
        # No certificate can be inferred from a PR's sources or green CI.
        "exact_master_code_certified_artifact": "NOT_VERIFIED",
        "github_sigstore_code_attestation": "NOT_VERIFIED",
        "scientific_runtime_asset_bundle": "NOT_VERIFIED",
        "installable_certification": "NOT_RUN",
        "actual_native_package": "NOT_BUILT",
        "physical_restore_and_rollback": "NOT_RUN",
        "clinical_appointment_migration": "NOT_AUTHORIZED",
        "clinical_go": False,
        "installable_ready": False,
        "verdict": "SOURCE_GATE_PRESENT_NO_INSTALLABLE_GO" if ok else "SOURCE_GATE_MISSING_STOP",
    }


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True,
        check=True, text=True, timeout=15,
    ).stdout.strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", action="store_true",
                        help="Write machine-readable evidence to standard output only.")
    args = parser.parse_args(argv)
    root = args.repo_root.resolve()
    try:
        report = build_report(
            root, args.expected_sha, git(root, "rev-parse", "HEAD"),
            git(root, "branch", "--show-current"),
        )
    except (PreflightError, OSError, subprocess.SubprocessError) as exc:
        print("SOURCE_PREFLIGHT_STOP " + str(exc), file=sys.stderr)
        return 2
    # There is deliberately NO output-path argument and NO file write.
    # Only stdout may receive evidence; clinical filesystem stays untouched.
    if args.json:
        print(json.dumps(report, sort_keys=True, indent=2))
    else:
        print(report["verdict"], "sha=" + report["source_sha"],
              "checks=" + str(len(report["source_checks"])),
              "installable_ready=false")
    return 0 if report["source_status"] == "PRESENT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
