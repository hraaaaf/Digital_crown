"""LOT08.2-G: read-only fail-closed eligibility gate for an isolated Windows rehearsal.

This gate does not install/start, decrypt, copy, download, certify, build or
promote Digital Crown releases. Only an existing INSTALLABLE_CERTIFIED directory
that passes the existing canonical product verifier AND matches the exact
master SHA can be marked ELIGIBLE_FOR_ISOLATED_REHEARSAL_ONLY.

IMPORTANT: eligible != CODE_CERTIFIED issued by this tool != human install GO.
Never substitute an Actions ZIP, CODE_CERTIFIED only, GitHub release title,
source checkout, mocked candidate or synthetic fixture for an actual installable.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any, Callable

# Delay importing the real product verifier until a *complete* candidate is
# present. A missing ZIP/artifact must fail-closed even in a minimal Windows CI
# environment without any clinical/backend optional dependencies installed.
# Do NOT replace this verifier with metadata-only checks for real candidates.
REQUIRED_INSTALLABLE_FILES = (
    "release-certification.json",
    ".digitalcrown-release-sha",
    "release-content.sha256",
    "installable-certification.json",
    "runtime-assets-certification.json",
    "runtime-assets-content.sha256",
    "github-attestation-verification.json",
)

SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
VERDICT_BLOCKED = "BLOCKED_NO_INSTALLABLE_GO"
VERDICT_REHEARSAL = "ELIGIBLE_FOR_ISOLATED_REHEARSAL_ONLY"


class GateRefusal(ValueError):
    pass


def decide(
    candidate_dir: Path | None,
    exact_master_sha: str,
    *,
    _test_verifier: Callable[[Path], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Assess, never activate. Output intentionally has no paths or secret values."""
    if not isinstance(exact_master_sha, str) or not SHA_PATTERN.fullmatch(exact_master_sha):
        raise GateRefusal("EXACT_MASTER_SHA_REQUIRED")

    report: dict[str, Any] = {
        "lot": "08.2-G",
        "source_master_sha": exact_master_sha,
        "candidate_installable_verified": False,
        "candidate_sha_matches_master": False,
        "actual_installer_executed": False,
        "real_windows_installation_tested": False,
        "sqlcipher_clinical_data_accessed": False,
        "clinical_go": False,
        "installable_go": False,
        "verdict": VERDICT_BLOCKED,
    }

    if candidate_dir is None:
        report["reason"] = "NO_INSTALLABLE_CANDIDATE_SUPPLIED"
        return report
    root = Path(candidate_dir)
    if root.is_symlink() or not root.is_dir():
        report["reason"] = "CANDIDATE_DIR_MISSING_OR_SYMLINK"
        return report

    # Refuse incomplete/forged metadata without importing any runtime modules.
    # A complete-looking candidate still MUST pass the canonical full verifier.
    if any((root / name).is_symlink() or not (root / name).is_file()
           for name in REQUIRED_INSTALLABLE_FILES):
        report["reason"] = "REQUIRED_INSTALLABLE_PROOF_FILES_MISSING_OR_UNSAFE"
        return report

    try:
        if _test_verifier is not None:
            # Unit tests ONLY. Not exposed by the CLI, never a real certification.
            payload = _test_verifier(root)
        else:
            from backend.release_certification import verify_installable_release_directory
            payload = verify_installable_release_directory(root)
    except (RuntimeError, OSError, ValueError, ImportError):
        report["reason"] = "CANONICAL_INSTALLABLE_VERIFIER_REFUSED"
        return report

    candidate_sha = payload.get("commit_sha")
    if not isinstance(candidate_sha, str) or not SHA_PATTERN.fullmatch(candidate_sha):
        report["reason"] = "CERTIFIED_SHA_MALFORMED"
        return report
    if candidate_sha != exact_master_sha:
        report["reason"] = "CERTIFIED_SHA_NOT_CURRENT_MASTER"
        return report
    if payload.get("certification_level") != "INSTALLABLE_CERTIFIED":
        report["reason"] = "CANDIDATE_NOT_INSTALLABLE_CERTIFIED"
        return report
    if payload.get("installable") is not True:
        report["reason"] = "INSTALLABLE_FLAG_NOT_TRUE"
        return report

    report["candidate_installable_verified"] = True
    report["candidate_sha_matches_master"] = True
    report["reason"] = "PRODUCT_VERIFIER_AND_SHA_PASSED_HUMAN_GATE_STILL_REQUIRED"
    report["verdict"] = VERDICT_REHEARSAL
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-master-sha", required=True)
    parser.add_argument("--candidate-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    try:
        result = decide(args.candidate_dir, args.expected_master_sha)
    except GateRefusal as exc:
        result = {
            "lot": "08.2-G", "verdict": VERDICT_BLOCKED,
            "reason": str(exc), "clinical_go": False, "installable_go": False,
        }
    print(json.dumps(result, sort_keys=True))
    # Fail closed if an executable caller uses this command as a preflight.
    return 0 if result["verdict"] == VERDICT_REHEARSAL else 3


if __name__ == "__main__":
    raise SystemExit(main())
