"""Independent subprocess Media Core recovery proof; not a LAB production cutover."""
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys


def test_sqlcipher_real_media_and_synthetic_receipt_survive_process_restart(tmp_path):
    assert "pytest-" in str(tmp_path), "ISOLATED_TEMP_PATH_REQUIRED"
    env = os.environ.copy()
    env.update({
        "DATABASE_URL": "sqlite:///:memory:",
        "ENVIRONMENT": "test",
        "DIGITALCROWN_ISOLATED_RUNTIME": "true",
        "DC06B_SQLCIPHER_PROOF_KEY": secrets.token_hex(32),
        "CABINET_MASTER_KEY_HEX": secrets.token_hex(32),
        "DC_V15_06_TRANSFER_LAB": "1",
        "TELEMETRY_ENABLED": "false",
        "CLOUD_AI_ENABLED": "false",
    })
    steps = [
        ("write", "SQLCIPHER_MEDIA_COMMITTED_BEFORE_PROCESS_EXIT"),
        ("wrong-key", "SQLCIPHER_WRONG_DB_KEY_REJECTED"),
        ("verify", "SQLCIPHER_MEDIA_PROCESS_RESTART_RECEIPT_VERIFIED"),
        ("corrupt", "SQLCIPHER_MEDIA_SYNTHETIC_CIPHERTEXT_CORRUPTED"),
        ("verify-tamper", "SQLCIPHER_MEDIA_TAMPER_REJECTED_AFTER_NEW_PROCESS"),
    ]
    results = []
    for stage, marker in steps:
        # Each phase is an entirely new interpreter and SQLCipher connection,
        # not a fresh SQLAlchemy session on the same engine.
        process = subprocess.run(
            [
                sys.executable, "-m",
                "tools.imaging_gateway.qa_sqlcipher_media_restart_lab",
                stage, str(tmp_path),
            ],
            env=env, cwd=Path(__file__).resolve().parents[2],
            capture_output=True, text=True, timeout=75,
        )
        # Never publish stdout/stderr on failure: they may include test-only
        # filesystem paths or non-redacted DB internals.
        assert process.returncode == 0, f"SQLCIPHER_{stage}_PROCESS_FAILED"
        assert marker in process.stdout, f"SQLCIPHER_{stage}_MARKER_MISSING"
        results.append({"stage": stage, "success": True})
    # No key material, filenames, synthetic patient metadata or PHI in JSON.
    evidence = os.environ.get("DC06B_DURABILITY_EVIDENCE_DIR")
    if evidence:
        target = Path(evidence)
        target.mkdir(parents=True, exist_ok=True)
        report = {
            "type": "LOT06B_INDEPENDENT_SQLCIPHER_MEDIA_CORE_RESTART",
            "exact_mode": "independent_processes_file_backed_sqlcipher_test_only",
            "actual_lab_transfer_used": False,
            "receipt_written_by": "synthetic_test_fixture_not_lab_transfer",
            "actual_media_core_storage_used": True,
            "sqlcipher_encrypted_db_and_aes_gcm_blob": True,
            "db_engine_reopened_in_fresh_process": True,
            "wrong_db_key_denied": True,
            "tampered_media_denied": True,
            "persistent_lab_transfer_remains_disabled": True,
            "power_cut_durability_certified": False,
            "postgresql_and_external_rollback_witness_tested": False,
            "stages": results,
        }
        (target / "sqlcipher-media-restart-proof.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )
    print("LOT06B_SQLCIPHER_MEDIA_CORE_PROCESS_RESTART_PASS")
