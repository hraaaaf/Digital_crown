"""C05B-03E FUE for external cold-recovery witness, LAB ONLY.

No real outage/NTFS/VFS xSync testing here. Positive software test is NO clinical
release; negative tests prove that missing/contradictory evidence is rejected.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from tools.imaging_gateway.qa_physical_power_witness_lab import (
    EvidenceRejected, _open_db, prepare, recover, main, PRIVATE, MANIFEST,
)


@pytest.fixture(autouse=True)
def _isolated(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DIGITALCROWN_ISOLATED_RUNTIME", "true")
    monkeypatch.setenv("DC06C05B03E_TEST_ONLY", "1")


def _root(tmp_path, name="trial"):
    return tmp_path / ("lot06c05b03e-" + name)


def _make(tmp_path, mode, name="trial"):
    root = _root(tmp_path, name)
    witness, conn = prepare(root, mode)
    try:
        assert conn.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
        assert conn.execute("PRAGMA synchronous").fetchone()[0] == (2 if mode == "FULL" else 1)
    finally:
        conn.close()
    exported = tmp_path / ("witness-" + mode + "-" + name + ".json")
    shutil.copyfile(root / MANIFEST, exported)
    assert exported.is_file()
    return root, witness, exported


def _rejected(code, action):
    with pytest.raises(EvidenceRejected) as exc:
        action()
    assert exc.value.code == code


def test_c05b03e_01_guard_path_and_local_witness_fail_closed(tmp_path, monkeypatch):
    root = _root(tmp_path)
    monkeypatch.delenv("DC06C05B03E_TEST_ONLY")
    _rejected("ISOLATED_LAB_ONLY", lambda: prepare(root, "FULL"))
    assert not root.exists()
    monkeypatch.setenv("DC06C05B03E_TEST_ONLY", "1")

    _rejected("ISOLATED_ROOT_NAME_REQUIRED", lambda: prepare(tmp_path / "clinic", "FULL"))
    _rejected("INVALID_POLICY", lambda: prepare(root, "OFF"))
    assert not root.exists()

    if os.name == "posix":
        link = _root(tmp_path, "symlink")
        link.symlink_to(tmp_path, target_is_directory=True)
        _rejected("INVALID_ISOLATED_ROOT", lambda: prepare(link, "FULL"))

    root, _, ext = _make(tmp_path, "FULL")
    _rejected("EXTERNAL_WITNESS_REQUIRED", lambda: recover(root, root / MANIFEST))
    _rejected("LAB_ROOT_NOT_EMPTY", lambda: prepare(root, "FULL"))
    result = recover(root, ext)
    assert result["clinical_durable_receipt_certified"] is False
    print("LOT06C05B03E_ISOLATION_AND_EXTERNAL_WITNESS_GATE_PASS")


def test_c05b03e_02_normal_full_actual_sqlcipher_cold_recovery_no_false_power_event(tmp_path):
    assert os.name == "posix"  # Linux CI fixture; NTFS is not emulated
    runtime = (Path(__file__).resolve().parents[1] / "backend" / "database.py"
               ).read_text(encoding="utf-8")
    assert 'cursor.execute("PRAGMA journal_mode=WAL")' in runtime
    assert 'cursor.execute("PRAGMA synchronous=NORMAL")' in runtime

    for mode in ("NORMAL", "FULL"):
        root, witness, ext = _make(tmp_path, mode, name=mode)
        assert witness["writer_policy_declared"] == mode
        assert witness["operator_power_interruption_observed"] is False
        assert witness["independent_external_witness_verified"] is False
        assert witness["clinical_receipt_durable_certified"] is False
        for secret in json.loads((root / PRIVATE).read_text()).values():
            assert secret not in json.dumps(witness)
        check = recover(root, ext)
        assert check["status"] == "RECOVERY_OBSERVED_EVENT_UNVERIFIED"
        assert check["sqlcipher_integrity"] == "PASS"
        assert check["receipt_audit_outbox"] == "PASS"
        assert check["encrypted_media_integrity"] == "PASS"
        for flag in ("independent_witness_storage_verified", "physical_power_loss_verified",
                     "vfs_xsync_or_drive_flush_verified", "windows_ntfs_verified",
                     "clinical_durable_receipt_certified", "product_ready"):
            assert check[flag] is False
    print("LOT06C05B03E_NORMAL_FULL_COLD_REOPEN_NO_FALSE_CERTIFICATION_PASS")


def test_c05b03e_03_sql_triplet_and_witness_tampering_denied(tmp_path):
    root, witness, ext = _make(tmp_path, "FULL")
    corrupted = tmp_path / "tampered-witness.json"
    forged = dict(witness, media_digest="f" * 64,
                  operator_power_interruption_observed=True,
                  independent_external_witness_verified=True)
    corrupted.write_text(json.dumps(forged), encoding="utf-8")
    _rejected("RECEIPT_AUDIT_OUTBOX_NOT_RECOVERED", lambda: recover(root, corrupted))
    bad_format = tmp_path / "invalid-witness.json"
    bad_format.write_text('{"schema": "SPOOF"}', encoding="utf-8")
    _rejected("EXTERNAL_WITNESS_INVALID", lambda: recover(root, bad_format))

    private = json.loads((root / PRIVATE).read_text())
    con = _open_db(root, private["db_key"], "FULL")
    try:
        con.execute("DELETE FROM outbox")
    finally:
        con.close()
    _rejected("RECEIPT_AUDIT_OUTBOX_NOT_RECOVERED", lambda: recover(root, ext))
    print("LOT06C05B03E_WITNESS_SQL_TRIPLET_NEGATIVE_PASS")


def test_c05b03e_04_media_corruption_missing_and_claims_never_self_certified(tmp_path):
    root, witness, ext = _make(tmp_path, "NORMAL")
    blobpath = root / "encrypted-test-media.bin"
    orig = blobpath.read_bytes()
    blobpath.write_bytes(orig[:-1] + bytes([orig[-1] ^ 1]))
    _rejected("MEDIA_INTEGRITY_FAILED", lambda: recover(root, ext))
    blobpath.unlink()
    _rejected("MEDIA_INTEGRITY_FAILED", lambda: recover(root, ext))
    blobpath.write_bytes(orig)

    # Unverifiable operator claims in a witness are ignored for certification.
    external_claim = dict(witness,
                          operator_power_interruption_observed=True,
                          independent_external_witness_verified=True,
                          clinical_receipt_durable_certified=True)
    ext.write_text(json.dumps(external_claim), encoding="utf-8")
    result = recover(root, ext)
    assert result["physical_power_loss_verified"] is False
    assert result["independent_witness_storage_verified"] is False
    assert result["clinical_durable_receipt_certified"] is False
    print("LOT06C05B03E_MEDIA_AND_UNTRUSTED_ATTESTATION_NEGATIVE_PASS")


def test_c05b03e_05_cli_cold_process_and_json_lab_evidence(tmp_path):
    root = _root(tmp_path, "real-cli")
    env = dict(os.environ)
    call = subprocess.run(
        [sys.executable, "-m", "tools.imaging_gateway.qa_physical_power_witness_lab",
         "prepare", "--root", str(root), "--mode", "FULL"],
        capture_output=True, text=True, timeout=50, check=False, env=env)
    assert call.returncode == 0, (call.stderr or "")[-250:]
    prepared = json.loads(call.stdout)
    assert prepared["status"] == "ARMED_TEST_ONLY_NO_PHYSICAL_EVENT"
    assert prepared["pre_event_witness"]["clinical_receipt_durable_certified"] is False
    ext = tmp_path / "cli-witness-external-location.json"
    shutil.copyfile(root / MANIFEST, ext)
    cold = subprocess.run(
        [sys.executable, "-m", "tools.imaging_gateway.qa_physical_power_witness_lab",
         "recover", "--root", str(root), "--witness", str(ext)],
        capture_output=True, text=True, timeout=50, check=False, env=env)
    assert cold.returncode == 0, (cold.stderr or "")[-250:]
    assert json.loads(cold.stdout)["status"] == "RECOVERY_OBSERVED_EVENT_UNVERIFIED"
    refusal = subprocess.run(
        [sys.executable, "-m", "tools.imaging_gateway.qa_physical_power_witness_lab",
         "recover", "--root", str(root)],
        capture_output=True, text=True, timeout=50, check=False, env=env)
    assert refusal.returncode == 2
    assert json.loads(refusal.stdout)["status"] == "NO_GO"

    evidence = Path(os.environ.get("DC06C05B03E_EVIDENCE_DIR", str(tmp_path)))
    evidence.mkdir(exist_ok=True, parents=True)
    report = {
        "kind": "LOT06_C05B03E_PHYSICAL_EVENT_PROTOCOL_TEST_ONLY",
        "isolated_root_and_no_real_patient_data": True,
        "external_pre_event_manifest_required": True,
        "sqlcipher_wal_normal_and_full_reopened_in_new_process": True,
        "sqlcipher_receipt_audit_outbox_identity_verified": True,
        "real_synthetic_aesgcm_media_corruption_and_missing_denied": True,
        "falsified_operator_power_claim_cannot_self_certify": True,
        "non_posix_not_covered_by_ci": True,
        "actual_physical_power_cut_tested": False,
        "external_power_witness_independently_verified": False,
        "os_kernel_crash_tested": False,
        "hardware_sync_guarantees_verified": False,
        "windows_ntfs_certified": False,
        "real_clinical_asset_used": False,
        "real_staff_device_authentication": False,
        "production_durable_receipt_enabled": False,
        "human_clinical_approval_recorded": False,
        "product_ready": False,
    }
    (evidence / "lot06c05b03e-physical-witness-protocol-fue.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("LOT06C05B03E_CLI_COLD_REOPEN_NEGATIVE_FUE_PASS")
