"""Test-only durability evidence: SQLCipher file and Media Core encrypted media.

Runs separate Python OS processes; intentionally DOES NOT invoke the guarded
in-memory LOT06-B HTTP service or claim power-cut/production crash safety.
"""
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.services.imaging_acquisition_transfer_lab_v15 import (
    TransferLabRejected,
    guard,
)


def test_persistent_lab_service_remains_disabled_even_in_test(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DIGITALCROWN_ISOLATED_RUNTIME", "true")
    monkeypatch.setenv("DC_V15_06_TRANSFER_LAB", "1")
    engine = create_engine(f"sqlite:///{tmp_path / 'forbidden-lab.db'}")
    try:
        with Session(engine) as session:
            with pytest.raises(TransferLabRejected, match="ISOLATED_TRANSFER_DISABLED"):
                guard(session)
    finally:
        engine.dispose()


def test_synthetic_sqlcipher_encrypted_receipt_survives_real_process_restart(
    tmp_path, monkeypatch
):
    root = tmp_path / "durability"
    root.mkdir()
    env = os.environ.copy()
    env.update({
        "ENVIRONMENT": "test",
        "DIGITALCROWN_ISOLATED_RUNTIME": "true",
        "DC06B_TEST_SQLCIPHER_KEY": secrets.token_hex(32),
        "DC06B_TEST_MEDIA_KEY": secrets.token_hex(32),
    })
    phases = (
        ("write", 0, "FILE_SQLCIPHER_AND_AESGCM_RECEIPT_COMMITTED"),
        ("verify", 0, "RESTARTED_PROCESS_VERIFIED_RECEIPT_AND_MEDIA"),
        ("replay", 0, "RESTART_REPLAY_SAME_RECEIPT"),
        ("interrupt-pre-sql", 74, ""),
        ("verify-pre-sql", 0, "PRE_SQL_PROCESS_CRASH_NO_AUTHORITATIVE_RECEIPT"),
        ("interrupt", 73, ""),
        ("verify-interrupted", 0,
         "UNCOMMITTED_RECEIPT_ROLLED_BACK_ENCRYPTED_ORPHAN_QUARANTINED"),
        ("wrong-key", 0, "WRONG_SQLCIPHER_KEY_BLOCKED"),
        ("tamper", 0, "SYNTHETIC_MEDIA_CORRUPTED"),
        ("verify-tampered", 0, "TAMPER_INTEGRITY_BLOCKED"),
    )
    results = []
    for phase, code, expected in phases:
        # Every phase launches the script in a NEW operating system process,
        # discarding DB connections and decryptor memory between each run.
        done = subprocess.run(
            [
                sys.executable, "-m",
                "tools.imaging_gateway.qa_durable_receipt_restart_lab",
                "--root", str(root), "--phase", phase,
            ],
            env=env, text=True, capture_output=True, timeout=35, check=False,
        )
        assert done.returncode == code, (
            f"Durability phase {phase} exit {done.returncode}; "
            f"stdout={done.stdout[-500:]} stderr={done.stderr[-200:]}"
        )
        assert expected in done.stdout, f"Missing phase marker: {phase}"
        for private in (
            env["DC06B_TEST_SQLCIPHER_KEY"], env["DC06B_TEST_MEDIA_KEY"]
        ):
            assert private not in done.stdout + done.stderr
        results.append({"phase": phase, "exit_status": done.returncode, "pass": True})

    db = root / "isolated-ledger.db"
    assert db.exists()
    assert db.read_bytes()[:16] != b"SQLite format 3\x00"
    blobs = list((root / "media").rglob("*.dcm"))
    assert len(blobs) == 3
    assert all(blob.read_bytes().startswith(b"DCM1") for blob in blobs)

    evidence_path = Path(os.environ.get(
        "DC06B_DURABILITY_EVIDENCE_DIR", str(tmp_path)
    ))
    evidence_path.mkdir(parents=True, exist_ok=True)
    (evidence_path / "lot06b-sqlcipher-restart-fue.json").write_text(
        json.dumps({
            "kind": "LOT06B_SYNTHETIC_RESTART_REHEARSAL",
            "exact_scope": "separate_test_ledger_not_guarded_fastapi_lab",
            "file_sqlcipher_encrypted": True,
            "media_core_aesgcm_envelope": True,
            "independent_os_process_per_phase": True,
            "synthetic_receipt_and_audit_after_restart": True,
            "simulated_lost_ack_replay_no_duplicate": True,
            "aborted_transaction_uncommitted_and_encrypted_orphan": True,
            "crash_before_sql_has_no_authoritative_receipt": True,
            "crash_after_receipt_audit_outbox_before_commit_is_atomic": True,
            "wrong_sqlcipher_key_rejected": True,
            "tampered_ciphertext_rejected": True,
            "actual_power_cut_tested": False,
            "directory_fsync_tested": False,
            "postgresql_restart_tested": False,
            "external_anti_rollback_witness_tested": False,
            "product_ready": False,
            "phases": results,
        }, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("LOT06B_SQLCIPHER_FILE_RESTART_REHEARSAL_PASS")

def test_actual_clinical_asset_model_sqlcipher_restart_and_tamper(tmp_path):
    """Converged #1141 proof: real ClinicalAsset and public storage helpers."""
    root = tmp_path / "core-model"
    root.mkdir()
    env = os.environ.copy()
    env.update({
        "ENVIRONMENT": "test",
        "DIGITALCROWN_ISOLATED_RUNTIME": "true",
        "DC06B_TEST_SQLCIPHER_KEY": secrets.token_hex(32),
        "DC06B_TEST_MEDIA_KEY": secrets.token_hex(32),
        "DATABASE_URL": "sqlite:///:memory:",
        "TELEMETRY_ENABLED": "false",
        "CLOUD_AI_ENABLED": "false",
    })
    phases = (
        ("core-write", "ACTUAL_CLINICAL_ASSET_MODEL_SQLCIPHER_COMMITTED"),
        ("core-verify", "ACTUAL_CLINICAL_ASSET_MODEL_VERIFIED_AFTER_PROCESS_RESTART"),
        ("core-tamper", "CLINICAL_ASSET_CIPHERTEXT_TAMPERED"),
        ("core-verify-tampered", "ACTUAL_CLINICAL_ASSET_RECEIPT_TAMPER_REJECTED"),
    )
    results = []
    for phase, marker in phases:
        done = subprocess.run(
            [
                sys.executable, "-m",
                "tools.imaging_gateway.qa_durable_receipt_restart_lab",
                "--root", str(root), "--phase", phase,
            ],
            env=env, text=True, capture_output=True, timeout=75, check=False,
        )
        # Do not leak environment variables or private filenames to CI failure output.
        assert done.returncode == 0, f"CLINICAL_ASSET_{phase}_FAILED"
        assert marker in done.stdout, f"CLINICAL_ASSET_{phase}_MARKER_MISSING"
        assert env["DC06B_TEST_SQLCIPHER_KEY"] not in done.stdout + done.stderr
        assert env["DC06B_TEST_MEDIA_KEY"] not in done.stdout + done.stderr
        results.append({"phase": phase, "pass": True})
    assert (root / "clinical-asset-lab.db").read_bytes()[:16] != b"SQLite format 3\x00"
    evidence_path = Path(os.environ.get(
        "DC06B_DURABILITY_EVIDENCE_DIR", str(tmp_path)
    ))
    evidence_path.mkdir(parents=True, exist_ok=True)
    (evidence_path / "lot06b-actual-clinical-asset-restart-fue.json").write_text(
        json.dumps({
            "kind": "LOT06B_ACTUAL_CLINICAL_ASSET_MODEL_RESTART_TEST",
            "product_ready": False,
            "production_lab_transfer_used": False,
            "receipt_origin": "synthetic_fixture_not_lab_transfer",
            "actual_clinical_asset_model_used": True,
            "actual_store_and_read_helpers_used": True,
            "isolation_patient_and_tenant_negative_tests": True,
            "encrypted_restart_in_new_os_process_verified": True,
            "tampered_ciphertext_rejected_after_process_restart": True,
            "power_cut_or_directory_fsync_tested": False,
            "phases": results,
        }, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("LOT06B_ACTUAL_CLINICAL_ASSET_RESTART_CONVERGENCE_PASS")
