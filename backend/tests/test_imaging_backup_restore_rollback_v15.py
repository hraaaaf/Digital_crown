"""Isolated cold backup/restore + synthetic external witness FUE.

Real SQLCipher bytes and existing AES-GCM Media Core storage, separate Python
processes for every DB state transition. NO clinical LAB persistent enablement.
The trusted HMAC witness is stored outside restored snapshots but on the same
test runner; this does NOT replace independently secured production custody.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys


def test_file_sqlcipher_backup_restore_and_stale_rollback_detection(tmp_path):
    root = tmp_path / "ledger"
    root.mkdir()
    snapshots = tmp_path / "cold-backups"
    snapshots.mkdir()
    env = os.environ.copy()
    env.update({
        "ENVIRONMENT": "test",
        "DIGITALCROWN_ISOLATED_RUNTIME": "true",
        "DC06B_TEST_SQLCIPHER_KEY": secrets.token_hex(32),
        "DC06B_TEST_MEDIA_KEY": secrets.token_hex(32),
        "DC06B_TEST_WITNESS_KEY": secrets.token_hex(32),
    })
    steps = []

    def spawn(module: str, phase: str, marker: str, extra_env=None):
        # New OS interpreter every time, with all DB connections closed
        # before the next cold backup or restore action.
        args = [
            sys.executable, "-m", module,
            "--root", str(root), "--phase", phase,
        ]
        actual_env = dict(env, **(extra_env or {}))
        output = subprocess.run(
            args, env=actual_env, capture_output=True, text=True, timeout=40,
            check=False,
        )
        assert output.returncode == 0, (
            f"FUE {phase} failed (exit {output.returncode}), "
            f"stderr type={output.stderr[-180:]}"
        )
        assert marker in output.stdout, f"FUE {phase} marker absent"
        for secret in (env["DC06B_TEST_SQLCIPHER_KEY"],
                       env["DC06B_TEST_MEDIA_KEY"],
                       env["DC06B_TEST_WITNESS_KEY"]):
            assert secret not in output.stdout + output.stderr
        steps.append({"phase": phase, "pass": True})

    dr = "tools.imaging_gateway.qa_durable_receipt_restart_lab"
    backup = "tools.imaging_gateway.qa_backup_restore_witness_lab"

    def save(label: str):
        target = snapshots / label
        target.mkdir()
        # Cold backup ONLY, with all worker processes shut down.
        shutil.copy2(root / "isolated-ledger.db", target / "isolated-ledger.db")
        shutil.copytree(root / "media", target / "media")
        assert (target / "isolated-ledger.db").read_bytes()[:16] != b"SQLite format 3\x00"
        assert all(x.read_bytes().startswith(b"DCM1")
                   for x in (target / "media").rglob("*.dcm"))
        assert not (target / "independent-test-witness.json").exists()
        steps.append({"phase": "cold-backup-" + label, "pass": True})

    def restore(label: str):
        target = snapshots / label
        db = root / "isolated-ledger.db"
        db.unlink(missing_ok=True)
        shutil.rmtree(root / "media", ignore_errors=True)
        shutil.copy2(target / "isolated-ledger.db", db)
        shutil.copytree(target / "media", root / "media")
        # The independent authenticated witness remains under root.parent,
        # never copied, rolled back, rewritten or re-seeded by this operation.
        steps.append({"phase": "cold-restore-" + label, "pass": True})

    # First SQLCipher+AES-GCM receipt uses the existing DR04 worker.
    spawn(dr, "write", "FILE_SQLCIPHER_AND_AESGCM_RECEIPT_COMMITTED")
    spawn(backup, "checkpoint-one", "BACKUP_V1_INDEPENDENT_WITNESS_COMMITTED")
    spawn(backup, "verify-one", "RESTORED_BACKUP_V1_VALID_WITH_MATCHING_WITNESS")
    save("v1")

    # A second committed image+receipt raises the independent witness epoch.
    spawn(backup, "advance-two", "BACKUP_V2_NEW_SQL_RECEIPT_AND_WITNESS_COMMITTED")
    spawn(backup, "verify-two", "RESTORED_BACKUP_V2_VALID_WITH_INDEPENDENT_WITNESS")
    save("v2")

    # Force stale restore. A perfectly decryptable older SQLCipher backup is
    # explicitly rejected by the out-of-backup, higher-epoch HMAC witness.
    restore("v1")
    spawn(backup, "expect-rollback", "STALE_ENCRYPTED_BACKUP_BLOCKED_BY_EXTERNAL_WITNESS")

    # Restore latest valid offline backup, keep witness intact, validate all
    # ciphertext, SHA, tenant/patient and 2 receipt/audit/outbox records.
    restore("v2")
    spawn(backup, "verify-two", "RESTORED_BACKUP_V2_VALID_WITH_INDEPENDENT_WITNESS")
    spawn(backup, "expect-wrong-witness-key", "WRONG_WITNESS_KEY_REJECTED",
          {"DC06B_TEST_WITNESS_KEY": secrets.token_hex(32)})
    spawn(backup, "tamper-witness", "SYNTHETIC_WITNESS_TAMPERED")
    spawn(backup, "expect-tamper", "TAMPERED_HMAC_WITNESS_REJECTED")

    evidence_dir = Path(os.environ.get(
        "DC06B_BACKUP_EVIDENCE_DIR", str(tmp_path / "evidence")
    ))
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "lot06b-backup-restore-antirollback-fue.json").write_text(
        json.dumps({
            "kind": "LOT06B_TEST_ONLY_BACKUP_RESTORE_ROLLBACK_FUE",
            "scope": "offline_SQLCipher_synthetic_ledger_plus_AESGCM_not_real_LAB_HTTP",
            "previous_dr04_restart_gate_retained": True,
            "sqlcipher_offline_encrypted_backup": True,
            "media_core_aesgcm_offline_backup": True,
            "two_generations_of_sql_receipts": True,
            "fresh_process_per_phase": True,
            "restore_matching_latest_epoch_verified": True,
            "stale_backup_restore_refused": True,
            "hmac_witness_held_outside_restored_snapshot": True,
            "witness_wrong_key_rejected": True,
            "witness_tamper_rejected": True,
            "real_external_trusted_monotonic_custody_tested": False,
            "witness_and_backup_same_host": True,
            "restore_both_backup_and_witness_attack_tested": False,
            "physical_power_cut_tested": False,
            "directory_fsync_tested": False,
            "real_clinical_LAB_endpoint_tested_on_disk": False,
            "production_backup_policy_or_key_custody_tested": False,
            "product_ready": False,
            "steps": steps,
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )
    print("LOT06B_BACKUP_RESTORE_ROLLBACK_WITNESS_PASS")
