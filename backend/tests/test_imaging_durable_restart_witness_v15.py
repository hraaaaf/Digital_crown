"""LOT06-B DR-04 — independent on-disk SQLCipher restart witness, TEST ONLY.

This does NOT execute or enable the real /lab/transfer endpoint: that endpoint
must remain guarded to SQLite :memory:. Here a deliberately minimal synthetic
receipt schema exercises real SQLCipher persistence across OS processes and
the existing C2 AES-GCM media encryption/fsync implementation. No PHI, API
credentials, deployment, PostgreSQL, external witness or power-cut claims.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest

from backend.services import clinical_asset_storage as media

TENANT = 19
PATIENT = 73
DEVICE = "dr04-synthetic-device"
CAPTURE = "dr04-synthetic-capture"
RECEIPT = "LAB-RESTART-WITNESS-001"
ASSET = 501
BLOB_NAME = "synthetic-image.aesgcm"
SCHEMA = """
CREATE TABLE IF NOT EXISTS dr04_receipts (
    tenant INTEGER NOT NULL,
    device TEXT NOT NULL,
    capture TEXT NOT NULL,
    receipt_id TEXT NOT NULL UNIQUE,
    asset_id INTEGER NOT NULL UNIQUE,
    patient_id INTEGER NOT NULL,
    digest TEXT NOT NULL,
    bytes_count INTEGER NOT NULL,
    PRIMARY KEY (tenant, device, capture)
);
CREATE TABLE IF NOT EXISTS dr04_audit (
    receipt_id TEXT PRIMARY KEY,
    event TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS dr04_outbox (
    receipt_id TEXT PRIMARY KEY,
    event TEXT NOT NULL
);
"""


def _synthetic_png() -> bytes:
    from io import BytesIO
    from PIL import Image
    output = BytesIO()
    Image.new("RGB", (4, 4), color=(20, 60, 110)).save(output, format="PNG")
    return output.getvalue()


def _open(root: Path, *, incorrect_key: bool = False):
    try:
        from sqlcipher3 import dbapi2 as sqlcipher
    except ImportError as exc:
        raise AssertionError("SQLCIPHER_DRIVER_REQUIRED_NO_PLAINTEXT_FALLBACK") from exc
    key_hex = os.environ.get("DC06B_DR_SQLCIPHER_KEY_HEX", "")
    if len(key_hex) != 64 or any(c not in "0123456789abcdefABCDEF" for c in key_hex):
        raise AssertionError("SYNTHETIC_SQLCIPHER_KEY_MISSING")
    if incorrect_key:
        key_hex = "fe" * 32
    conn = sqlcipher.connect(str(root / "synthetic-receipts.sqlcipher"))
    try:
        conn.execute(f'PRAGMA key = "x' + "'" + key_hex + "'" + '"')
        cipher = conn.execute("PRAGMA cipher_version").fetchone()
        if cipher is None or not cipher[0]:
            raise AssertionError("NOT_ACTUALLY_SQLCIPHER")
        # DELETE mode + FULL sync avoids mistaking an unflushed WAL sidecar
        # for the complete database at the process boundary.
        conn.execute("PRAGMA journal_mode=DELETE")
        conn.execute("PRAGMA synchronous=FULL")
        conn.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()
        return conn
    except Exception:
        conn.close()
        raise


def _initialize(conn):
    conn.executescript(SCHEMA)
    conn.commit()


def _verify(root: Path) -> dict:
    conn = _open(root)
    try:
        receipts = conn.execute(
            "SELECT tenant,device,capture,receipt_id,asset_id,patient_id,"
            "digest,bytes_count FROM dr04_receipts"
        ).fetchall()
        if len(receipts) != 1:
            raise AssertionError("RECEIPT_NOT_DURABLE_OR_DUPLICATED")
        tenant, device, capture, receipt, asset, patient, digest, count = receipts[0]
        if (tenant,device,capture,receipt,asset,patient) != (
            TENANT,DEVICE,CAPTURE,RECEIPT,ASSET,PATIENT
        ):
            raise AssertionError("RECEIPT_IDENTITY_MISMATCH")
        if conn.execute("SELECT event FROM dr04_audit WHERE receipt_id=?",
                        (RECEIPT,)).fetchone() != ("LAB_ACQUISITION_COMMITTED",):
            raise AssertionError("AUDIT_NOT_DURABLE")
        if conn.execute("SELECT event FROM dr04_outbox WHERE receipt_id=?",
                        (RECEIPT,)).fetchone() != ("LAB_MEDIA_READY",):
            raise AssertionError("OUTBOX_NOT_DURABLE")
        decrypted = media._read_verified_path(
            root / BLOB_NAME, employer_id=TENANT,
            digest=digest, byte_size=count
        )
        if decrypted != _synthetic_png() or hashlib.sha256(decrypted).hexdigest() != digest:
            raise AssertionError("MEDIA_DIGEST_MISMATCH")
        try:
            media._read_verified_path(
                root / BLOB_NAME, employer_id=TENANT+1, digest=digest, byte_size=count
            )
        except media.ClinicalAssetIntegrityError:
            pass
        else:
            raise AssertionError("WRONG_TENANT_MEDIA_DECRYPTED")
        return {"receipt_id":receipt,"sha256":digest,"patient_id":patient}
    finally:
        conn.close()


def _child(mode: str, root: Path) -> int:
    root.mkdir(parents=True, exist_ok=True)
    try:
        if mode == "wrong-key":
            try:
                conn = _open(root, incorrect_key=True)
            except Exception:
                print("WRONG_KEY_FAIL_CLOSED")
                return 0
            else:
                conn.close()
                raise AssertionError("WRONG_SQLCIPHER_KEY_ACCEPTED")

        if mode in ("verify", "replay"):
            if mode == "verify":
                result = _verify(root)
            else:
                result = _verify(root)
                conn = _open(root)
                try:
                    # Replay same exact receipt may read, never insert.
                    assert conn.execute("SELECT count(*) FROM dr04_receipts").fetchone()[0] == 1
                finally:
                    conn.close()
            print("RESTART_RECEIPT_VERIFIED " + result["receipt_id"])
            return 0

        if mode not in ("write", "crash-before-commit", "orphan"):
            raise AssertionError("UNKNOWN_TEST_ONLY_MODE")
        png = _synthetic_png()
        digest = hashlib.sha256(png).hexdigest()
        encrypted = media._encrypt_payload(png, TENANT, digest)
        if png in encrypted:
            raise AssertionError("PLAINTEXT_MEDIA_LEAK")
        conn = _open(root)
        try:
            _initialize(conn)
            media._atomic_write(root / BLOB_NAME, encrypted)
            if mode == "orphan":
                # Ciphertext was fsynced, ledger not started: safe unlinked
                # encrypted blob, NOT a committed clinical receipt.
                print("ORPHAN_MEDIA_NO_SQL_RECEIPT")
                os._exit(71)
            row = (TENANT,DEVICE,CAPTURE,RECEIPT,ASSET,PATIENT,digest,len(png))
            conn.execute("INSERT INTO dr04_receipts VALUES (?,?,?,?,?,?,?,?)", row)
            conn.execute("INSERT INTO dr04_audit VALUES (?,?)",
                         (RECEIPT,"LAB_ACQUISITION_COMMITTED"))
            conn.execute("INSERT INTO dr04_outbox VALUES (?,?)",
                         (RECEIPT,"LAB_MEDIA_READY"))
            if mode == "crash-before-commit":
                # End the *actual child process* before SQL commit, not a mock
                # exception. The OS remains running, not a power-cut test.
                os._exit(72)
            conn.commit()
            print("SQLCIPHER_RECEIPT_COMMITTED")
            return 0
        finally:
            conn.close()
    except Exception as exc:
        # No secret key, patient free-text, or images printed in test output.
        print("DR04_FAIL_CLOSED " + type(exc).__name__)
        return 73


def _run(mode: str, root: Path, env: dict[str,str]) -> subprocess.CompletedProcess[str]:
    child_env = env.copy()
    # Running an absolute test file sets sys.path[0] to backend/tests, not the
    # repository root. Mirror the same import boundary as python -m pytest.
    repo_root = str(Path(__file__).resolve().parents[2])
    child_env["PYTHONPATH"] = repo_root + os.pathsep + child_env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--dr04-child", mode, str(root)],
        cwd=repo_root, env=child_env, check=False,
        capture_output=True, text=True, timeout=40
    )


def _test_env() -> dict[str,str]:
    env = os.environ.copy()
    env.update({
        "ENVIRONMENT":"test",
        "DIGITALCROWN_ISOLATED_RUNTIME":"true",
        "DC06B_DR_SQLCIPHER_KEY_HEX":"a1"*32,
        "CABINET_MASTER_KEY_HEX":"b2"*32,
        "SQLCIPHER_KEY_HEX":"a1"*32,
        "SECRET_KEY":"dr04-restart-secret-nonprod-32-chars",
    })
    return env


def test_dr04_real_sqlcipher_and_aesgcm_receipt_survive_process_restart(tmp_path):
    root = tmp_path / "durable-witness"
    env = _test_env()
    writer = _run("write", root, env)
    assert writer.returncode == 0, writer.stdout[-500:] + writer.stderr[-400:]
    db_path = root / "synthetic-receipts.sqlcipher"
    blob = root / BLOB_NAME
    assert db_path.is_file() and blob.is_file()
    assert not db_path.read_bytes().startswith(b"SQLite format 3")
    assert _synthetic_png() not in db_path.read_bytes()
    assert _synthetic_png() not in blob.read_bytes()
    verifier = _run("verify", root, env)  # separate PID, fresh connections & HKDF
    assert verifier.returncode == 0, verifier.stdout[-500:] + verifier.stderr[-400:]
    assert "RESTART_RECEIPT_VERIFIED" in verifier.stdout
    replay = _run("replay", root, env)
    assert replay.returncode == 0, replay.stdout[-500:] + replay.stderr[-400:]
    wrong_key = _run("wrong-key", root, env)
    assert wrong_key.returncode == 0 and "WRONG_KEY_FAIL_CLOSED" in wrong_key.stdout
    ciphertext = blob.read_bytes()
    try:
        corrupted = bytearray(ciphertext)
        corrupted[-1] ^= 1
        blob.write_bytes(corrupted)
        assert _run("verify", root, env).returncode != 0
    finally:
        blob.write_bytes(ciphertext)
    assert _run("verify", root, env).returncode == 0
    # Independent ordinary SQLite driver must also fail on encrypted DB.
    with pytest.raises(sqlite3.DatabaseError):
        plain = sqlite3.connect(str(db_path))
        try:
            plain.execute("SELECT name FROM sqlite_master").fetchall()
        finally:
            plain.close()

    evidence_root = Path(os.environ.get("DC06B_DR_EVIDENCE_DIR", str(tmp_path)))
    evidence_root.mkdir(parents=True, exist_ok=True)
    evidence = {
        "kind":"LOT06B_DR04_STANDALONE_PERSISTENT_STORAGE_WITNESS",
        "scope":"independent synthetic SQLCipher receipt + actual C2 AES-GCM media",
        "actual_lab_transfer_endpoint_tested":False,
        "durable_sqlcipher_file_reopened_new_process":True,
        "aesgcm_verified_after_new_process":True,
        "receipt_audit_outbox_verified_after_restart":True,
        "wrong_sqlcipher_key_denied":True,
        "tampered_ciphertext_denied":True,
        "sql_receipt_idempotent_after_restart":True,
        "plaintext_sqlite_rejected":True,
        "power_cut_or_os_crash_tested":False,
        "postgresql_tested":False,
        "independent_antirollback_witness_tested":False,
        "manufacturer_hardware_tested":False,
        "clinical_product_certified":False,
    }
    (evidence_root / "dr04-sqlcipher-restart-witness.json").write_text(
        json.dumps(evidence,sort_keys=True,indent=2)+"\n",encoding="utf-8"
    )
    print("LOT06B_DR04_SQLCIPHER_PROCESS_RESTART_WITNESS_PASS")


@pytest.mark.parametrize("mode,expected", [
    ("orphan",71),("crash-before-commit",72),
])
def test_dr04_interrupted_persistent_write_has_no_committed_receipt(tmp_path,mode,expected):
    root = tmp_path / mode
    env = _test_env()
    writer = _run(mode, root, env)
    assert writer.returncode == expected, writer.stdout[-400:] + writer.stderr[-400:]
    # Process really ended; reopen SQLCipher on disk independently.
    # Test runner's own key must be explicit and never fall back to plaintext.
    monkey = os.environ.get("DC06B_DR_SQLCIPHER_KEY_HEX")
    try:
        os.environ["DC06B_DR_SQLCIPHER_KEY_HEX"] = env["DC06B_DR_SQLCIPHER_KEY_HEX"]
        conn = _open(root)
        try:
            assert conn.execute("SELECT count(*) FROM dr04_receipts").fetchone()[0] == 0
            assert conn.execute("SELECT count(*) FROM dr04_audit").fetchone()[0] == 0
            assert conn.execute("SELECT count(*) FROM dr04_outbox").fetchone()[0] == 0
        finally:
            conn.close()
    finally:
        if monkey is None:
            os.environ.pop("DC06B_DR_SQLCIPHER_KEY_HEX",None)
        else:
            os.environ["DC06B_DR_SQLCIPHER_KEY_HEX"] = monkey
    assert (root / BLOB_NAME).is_file()  # encrypted orphan: HOLD / no auto-delete
    assert not (root / BLOB_NAME).read_bytes().startswith(b"\x89PNG")
    assert _run("verify",root,env).returncode != 0
    print("LOT06B_DR04_NO_PARTIAL_RECEIPT_AFTER_CHILD_EXIT_PASS " + mode)


def test_production_lab_guard_still_rejects_file_backed_sqlite(tmp_path,monkeypatch):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from backend.services import imaging_acquisition_transfer_lab_v15 as lab
    monkeypatch.setenv("ENVIRONMENT","test")
    monkeypatch.setenv("DIGITALCROWN_ISOLATED_RUNTIME","true")
    monkeypatch.setenv("DC_V15_06_TRANSFER_LAB","1")
    engine = create_engine("sqlite:///" + str(tmp_path / "not-a-lab-storage.db"))
    try:
        with Session(engine) as session:
            with pytest.raises(lab.TransferLabRejected, match="ISOLATED_TRANSFER_DISABLED"):
                lab.guard(session)
    finally:
        engine.dispose()


if __name__ == "__main__":
    if len(sys.argv) != 4 or sys.argv[1] != "--dr04-child":
        raise SystemExit(90)
    raise SystemExit(_child(sys.argv[2], Path(sys.argv[3])))
