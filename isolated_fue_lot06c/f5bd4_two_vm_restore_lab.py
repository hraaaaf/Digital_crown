"""J4 F5B-D4f: two distinct GitHub-hosted Windows VM jobs, PUBLIC SYNTHETIC ONLY.

VM1 stages a precommitted AES-GCM backup as a GitHub Actions artifact.
VM2 independently downloads the artifact, checks its pinned pre-run digest
and exercises the EXISTING real Windows D4b restore/oracle/negative FUE.

GitHub Actions artifact storage is NOT independent offsite custody.
The public synthetic fixture password is NOT a separated human secret.
Never use for patients, production keys, deployments or clinical approval.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys

import f5bd4_fixed_recovery_windows_fue as existing

_SCHEMA = "dc06-j4-two-vm-public-synthetic-escrow-v1"
_BACKUP = "encrypted_backup.dcm2rec"
_RECEIPT = "custody_receipt.json"
_EXPECTED_CUSTODIAN = "custodian"
_EXPECTED_OPERATOR = "operator"


def _runtime(expected_job: str) -> tuple[str, str]:
    if (os.name != "nt" or os.environ.get("GITHUB_ACTIONS") != "true"
            or os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") != "true"
            or os.environ.get("GITHUB_JOB") != expected_job):
        raise RuntimeError("DC06_J4_TWO_VM_GITHUB_WINDOWS_SYNTHETIC_ONLY")
    source_sha = os.environ.get("GITHUB_SHA", "")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    if (len(source_sha) != 40 or any(c not in "0123456789abcdef" for c in source_sha)
            or not run_id.isdecimal()):
        raise RuntimeError("DC06_J4_SOURCE_OR_RUN_INVALID")
    return source_sha, run_id


def _directory(raw: str, *, must_exist: bool) -> Path:
    if not raw:
        raise RuntimeError("DC06_J4_ESCROW_DIRECTORY_MISSING")
    target = Path(raw).resolve()
    runner_temp = Path(os.environ["RUNNER_TEMP"]).resolve()
    if not target.is_relative_to(runner_temp) or target == runner_temp:
        raise RuntimeError("DC06_J4_ESCROW_OUTSIDE_EPHEMERAL_RUNNER")
    if must_exist:
        if not target.is_dir():
            raise RuntimeError("DC06_J4_ESCROW_NOT_DOWNLOADED")
    else:
        target.mkdir(parents=True, exist_ok=False)
    return target


def stage(target_raw: str) -> None:
    sha, run_id = _runtime(_EXPECTED_CUSTODIAN)
    # The producer does NOT generate a new oracle or a new backup during CI.
    # It stages a fixture committed before the job, pinned in the existing FUE.
    fixture, ciphertext = existing.fixture()
    assert hashlib.sha256(ciphertext).hexdigest() == fixture["envelope_sha256"]
    target = _directory(target_raw, must_exist=False)
    (target / _BACKUP).write_bytes(ciphertext)
    receipt = {
        "schema": _SCHEMA,
        "scope": "PUBLIC_SYNTHETIC_TWO_VM_ONLY_NOT_OFFSITE",
        "source_sha": sha,
        "workflow_run_id": run_id,
        "origin_job": _EXPECTED_CUSTODIAN,
        "fixture_sha256": existing.PINNED_FIXTURE_SHA256,
        "encrypted_backup_sha256": fixture["envelope_sha256"],
        "encrypted_backup_bytes": len(ciphertext),
    }
    (target / _RECEIPT).write_text(
        json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print("DC06_J4_VM1_PRECOMMITTED_ORACLE_PIN_PASS")
    print("DC06_J4_VM1_SYNTHETIC_ENCRYPTED_ESCROW_STAGED_PASS")



def _validate_encrypted_transfer(
    backup: bytes, receipt: dict, oracle: dict, expected_backup: bytes
) -> None:
    """Validate the actual downloaded ciphertext; reject before any disk restore."""
    if (not isinstance(backup, bytes)
            or not 52 <= len(backup) <= 16464
            or len(backup) != receipt["encrypted_backup_bytes"]
            or hashlib.sha256(backup).hexdigest() != receipt["encrypted_backup_sha256"]
            or receipt["encrypted_backup_sha256"] != oracle["envelope_sha256"]
            or backup != expected_backup):
        raise RuntimeError("DC06_J4_BACKUP_PIN_OR_TRANSFER_DENIED")


def operator(escrow_raw: str, verdict_raw: str) -> None:
    sha, run_id = _runtime(_EXPECTED_OPERATOR)
    escrow = _directory(escrow_raw, must_exist=True)
    if {p.name for p in escrow.iterdir()} != {_BACKUP, _RECEIPT}:
        raise RuntimeError("DC06_J4_ARTIFACT_CONTENTS_DENIED")
    receipt = json.loads((escrow / _RECEIPT).read_text(encoding="utf-8"))
    required = {
        "schema", "scope", "source_sha", "workflow_run_id",
        "origin_job", "fixture_sha256", "encrypted_backup_sha256",
        "encrypted_backup_bytes",
    }
    if not isinstance(receipt, dict) or set(receipt) != required:
        raise RuntimeError("DC06_J4_CUSTODY_RECEIPT_INVALID")
    if (receipt["schema"] != _SCHEMA
            or receipt["scope"] != "PUBLIC_SYNTHETIC_TWO_VM_ONLY_NOT_OFFSITE"
            or receipt["source_sha"] != sha
            or receipt["workflow_run_id"] != run_id
            or receipt["origin_job"] != _EXPECTED_CUSTODIAN
            or receipt["fixture_sha256"] != existing.PINNED_FIXTURE_SHA256):
        raise RuntimeError("DC06_J4_CUSTODY_BOUNDARY_MISMATCH")

    # VM2 has its OWN checkout of the oracle committed BEFORE this workflow.
    # The authenticated ciphertext must come from a separate GitHub artifact.
    oracle, expected_backup = existing.fixture()
    backup = (escrow / _BACKUP).read_bytes()
    _validate_encrypted_transfer(backup, receipt, oracle, expected_backup)
    # Regression: run intentionally altered ciphertext through the EXACT SAME
    # admission path. A hash-difference assertion alone was a false positive.
    corrupted = backup[:-1] + bytes((backup[-1] ^ 1,))
    try:
        _validate_encrypted_transfer(corrupted, receipt, oracle, expected_backup)
    except RuntimeError as exc:
        if str(exc) != "DC06_J4_BACKUP_PIN_OR_TRANSFER_DENIED":
            raise
    else:
        raise AssertionError("DC06_J4_ARTIFACT_TAMPER_FALSE_ACCEPT")
    print("DC06_J4_VM2_ARTIFACT_SHA_AND_PRECOMMITTED_ORACLE_PASS")
    print("DC06_J4_VM2_TAMPERED_TRANSFER_PREWRITE_DENIED_PASS")

    # Reuse the actual Windows D4b test, including native NEW private restore,
    # wrong password / tamper / overwrite negatives, and a FRESH Python process
    # checking both active and retained DCM2 media and locator oracles.
    # ONLY the parent process backup source is replaced by the transferred blob.
    original = existing.fixture

    def staged_backup_with_precommitted_oracle():
        f, _ = original()  # pin SHA and load independently committed expectations
        return f, backup

    existing.fixture = staged_backup_with_precommitted_oracle
    try:
        existing.main()
    finally:
        existing.fixture = original

    verdict = {
        "schema": _SCHEMA,
        "source_sha": sha,
        "workflow_run_id": run_id,
        "escrow_origin_job": _EXPECTED_CUSTODIAN,
        "operator_job": _EXPECTED_OPERATOR,
        "backup_sha256": receipt["encrypted_backup_sha256"],
        "oracle_fixture_sha256": existing.PINNED_FIXTURE_SHA256,
        "result": "PASS_TWO_REAL_WINDOWS_JOBS_SYNTHETIC_ARTIFACT_ONLY",
        "independent_human_custodian_attested": False,
        "offsite_escrow_verified": False,
        "full_cabinet_restore_verified": False,
        "clinical_go": False,
    }
    verdict_file = Path(verdict_raw).resolve()
    if (not verdict_file.is_relative_to(Path(os.environ["RUNNER_TEMP"]).resolve())
            or verdict_file.suffix != ".json" or verdict_file.is_file()):
        raise RuntimeError("DC06_J4_VERDICT_PATH_DENIED")
    verdict_file.write_text(json.dumps(verdict, sort_keys=True, indent=2) + "\n",
                            encoding="utf-8")
    print("DC06_J4_VM2_CROSS_RUNNER_NATIVE_RESTORE_ORACLE_PASS")
    print("DC06_J4_TWO_VM_SYNTHETIC_ONLY_NO_CLINICAL_GO_PASS")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "stage":
        stage(sys.argv[2])
    elif len(sys.argv) == 4 and sys.argv[1] == "operator":
        operator(sys.argv[2], sys.argv[3])
    else:
        raise RuntimeError("DC06_J4_TWO_VM_INVALID_MODE")
