"""LOT06 DR-S1: encrypted media and SQLCipher receipt survive a real process exit.

ISOLATED TEST PROBE ONLY. Uses the existing Media Core AES-GCM/storage helpers,
but a deliberately separate synthetic SQLCipher receipt schema, NOT the
production LAB SQLite :memory: ledger (whose guard must remain unchanged).
A clean process restart is NOT a power-loss/fsync-directory/backup-restore proof.
Never points at a real cabinet database, device or patient.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys

from PIL import Image
from io import BytesIO


def _png(rgb: tuple[int, int, int]) -> bytes:
    b = BytesIO()
    Image.new("RGB", (6, 6), rgb).save(b, format="PNG")
    return b.getvalue()


def _target(media_root: Path, storage_key: str) -> Path:
    return media_root.joinpath(*PurePosixPath(storage_key).parts)


def _sqlcipher(db_path: Path, password: str):
    # Driver import MUST fail (not silently skip or use plaintext sqlite3).
    from sqlcipher3 import dbapi2 as sqlcipher

    connection = sqlcipher.connect(str(db_path))
    try:
        if "'" in password or not password.startswith("LAB_DR_S1_"):
            raise AssertionError("UNSAFE_SYNTHETIC_SQLCIPHER_KEY")
        connection.execute(f"PRAGMA key = '{password}'")
        cipher = connection.execute("PRAGMA cipher_version").fetchone()
        if not cipher or not cipher[0]:
            raise AssertionError("SQLCIPHER_DRIVER_NOT_ACTIVE")
        connection.execute("SELECT count(*) FROM sqlite_master").fetchone()
        return connection
    except BaseException:
        connection.close()
        raise


def _worker(mode: str, db_path: Path, media_root: Path) -> dict:
    from backend.services.clinical_asset_storage import (
        ClinicalAssetIntegrityError, _atomic_write, _encrypt_payload,
        _read_verified_path, _storage_key, _prepare_parent_directory,
        _resolve_storage_path,
    )

    if os.environ.get("ENVIRONMENT") != "test" or os.environ.get(
        "DIGITALCROWN_ISOLATED_RUNTIME"
    ) != "true":
        raise AssertionError("DURABILITY_TEST_RUNTIME_REQUIRED")

    # Identity deliberately synthetic, never used to authorize a real tenant.
    tenant, patient = 11, 42
    device, capture = "dr-s1-fake-device", "dr-s1-fake-capture"
    png = _png((35, 100, 160))
    digest = hashlib.sha256(png).hexdigest()
    key = _storage_key(tenant, digest)
    target = _target(media_root, key)
    secret = os.environ["DC_DR_S1_SQLCIPHER_KEY"]

    if mode == "wrong_sql_key":
        from sqlcipher3 import dbapi2 as sqlcipher
        bad = sqlcipher.connect(str(db_path))
        try:
            bad.execute("PRAGMA key = 'LAB_DR_S1_WRONG_KEY'")
            try:
                bad.execute("SELECT count(*) FROM probe_receipts").fetchone()
            except sqlcipher.DatabaseError:
                return {"wrong_sql_key_rejected": True}
            raise AssertionError("WRONG_SQLCIPHER_KEY_ACCEPTED")
        finally:
            bad.close()

    conn = _sqlcipher(db_path, secret)
    try:
        if mode == "seed":
            conn.execute("PRAGMA journal_mode = DELETE")
            conn.execute("PRAGMA synchronous = FULL")
            conn.execute("""CREATE TABLE probe_receipts (
                tenant INTEGER NOT NULL, device TEXT NOT NULL,
                capture TEXT NOT NULL, receipt_id TEXT NOT NULL UNIQUE,
                patient INTEGER NOT NULL, digest TEXT NOT NULL,
                byte_size INTEGER NOT NULL, storage_key TEXT NOT NULL,
                PRIMARY KEY (tenant, device, capture))""")
            conn.execute("""CREATE TABLE probe_audit (
                receipt_id TEXT PRIMARY KEY, event TEXT NOT NULL)""")
            conn.execute("""CREATE TABLE probe_outbox (
                receipt_id TEXT PRIMARY KEY, event TEXT NOT NULL)""")
            root, path = _resolve_storage_path(key, tenant, media_root)
            _prepare_parent_directory(root, path)
            _atomic_write(path, _encrypt_payload(png, tenant, digest))
            assert _read_verified_path(path, employer_id=tenant,
                                       digest=digest, byte_size=len(png)) == png
            receipt = "DR-S1-SYNTHETIC-RECEIPT"
            conn.execute(
                "INSERT INTO probe_receipts VALUES (?,?,?,?,?,?,?,?)",
                (tenant, device, capture, receipt, patient, digest, len(png), key)
            )
            conn.execute("INSERT INTO probe_audit VALUES (?,?)",
                         (receipt, "SYNTHETIC_MEDIA_COMMITTED"))
            conn.execute("INSERT INTO probe_outbox VALUES (?,?)",
                         (receipt, "SYNTHETIC_MEDIA_READY"))
            conn.commit()
            assert target.is_file() and target.read_bytes().startswith(b"DCM1")
            return {"seeded": True, "receipt_id": receipt}

        if mode in {"verify", "wrong_media_key", "wrong_tenant", "verify_corrupt"}:
            row = conn.execute(
                "SELECT receipt_id,patient,digest,byte_size,storage_key "
                "FROM probe_receipts WHERE tenant=? AND device=? AND capture=?",
                (tenant,device,capture)
            ).fetchone()
            assert row is not None
            rid, owner, stored_digest, size, stored_key = row
            assert owner == patient and stored_digest == digest
            assert stored_key == key and size == len(png)
            assert conn.execute(
                "SELECT count(*) FROM probe_receipts"
            ).fetchone()[0] == 1
            assert conn.execute(
                "SELECT count(*) FROM probe_audit WHERE receipt_id=?",
                (rid,)
            ).fetchone()[0] == 1
            assert conn.execute(
                "SELECT count(*) FROM probe_outbox WHERE receipt_id=?",
                (rid,)
            ).fetchone()[0] == 1

            if mode in {"wrong_media_key", "wrong_tenant", "verify_corrupt"}:
                scope = tenant + 1 if mode == "wrong_tenant" else tenant
                try:
                    _read_verified_path(
                        target, employer_id=scope,
                        digest=digest, byte_size=len(png)
                    )
                except ClinicalAssetIntegrityError:
                    return {"integrity_rejected": True}
                raise AssertionError("INTEGRITY_BYPASS")

            assert _read_verified_path(
                target, employer_id=tenant,
                digest=digest, byte_size=len(png)
            ) == png
            # Lookup and a read-only replay cannot create a second receipt.
            assert conn.execute(
                "SELECT receipt_id FROM probe_receipts WHERE "
                "tenant=? AND device=? AND capture=?",
                (tenant, device, capture)
            ).fetchone()[0] == rid
            return {"recovered": True, "receipt_id": rid, "digest": digest}

        if mode == "precommit_rollback":
            # An independent second, encrypted orphan is safe after SQL rollback,
            # but garbage collection decisions are OUT OF SCOPE here.
            other = _png((170, 44, 20))
            other_digest = hashlib.sha256(other).hexdigest()
            other_key = _storage_key(tenant, other_digest)
            root, path = _resolve_storage_path(other_key, tenant, media_root)
            _prepare_parent_directory(root, path)
            _atomic_write(path, _encrypt_payload(other, tenant, other_digest))
            conn.execute(
                "INSERT INTO probe_receipts VALUES (?,?,?,?,?,?,?,?)",
                (tenant, device, "NOT_COMMITTED", "DR-S1-ROLLBACK",
                 patient, other_digest, len(other), other_key)
            )
            conn.rollback()
            assert path.exists()
            return {"encrypted_orphan_after_rollback": True}

        if mode == "verify_rollback":
            assert conn.execute(
                "SELECT count(*) FROM probe_receipts"
            ).fetchone()[0] == 1
            assert conn.execute(
                "SELECT count(*) FROM probe_receipts WHERE capture='NOT_COMMITTED'"
            ).fetchone()[0] == 0
            assert len(list(media_root.rglob("*.dcm"))) == 2
            assert all(p.read_bytes().startswith(b"DCM1")
                       for p in media_root.rglob("*.dcm"))
            return {"no_false_receipt_after_reopen": True}

        if mode == "tamper":
            content = bytearray(target.read_bytes())
            content[-1] ^= 1
            target.write_bytes(content)
            return {"tampered": True}

        raise AssertionError("UNKNOWN_PROBE_MODE")
    finally:
        conn.close()


def _run(mode: str, db_path: Path, root: Path, env: dict) -> dict:
    proc = subprocess.run(
        [sys.executable, "-m", "backend.tests.test_imaging_sqlcipher_restart_v15",
         "--worker", mode, str(db_path), str(root)],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        capture_output=True, text=True, timeout=40, check=False,
    )
    # Fail without exposing env secrets or patient data in exception text.
    assert proc.returncode == 0, (
        "DR_S1_" + mode.upper() + "_PROCESS_EXIT_" + str(proc.returncode)
        + " " + proc.stderr[-300:]
    )
    return json.loads(proc.stdout.strip().splitlines()[-1])


def test_sqlcipher_and_aesgcm_receipt_survive_independent_process_restart(
    tmp_path, monkeypatch
):
    """DR-S1: clean exit/reopen, not power cut or the LAB production ledger."""
    env = os.environ.copy()
    env.update({
        "ENVIRONMENT": "test",
        "DIGITALCROWN_ISOLATED_RUNTIME": "true",
        "DC_DR_S1_SQLCIPHER_KEY": "LAB_DR_S1_" + os.urandom(24).hex(),
        "CABINET_MASTER_KEY_HEX": os.urandom(32).hex(),
        # Keep any unrelated package initialization away from cabinet data.
        "MEDIA_ROOT": str(tmp_path / "synthetic-media"),
        "DATABASE_URL": "sqlite:///:memory:",
    })
    db_path = tmp_path / "probe-encrypted.db"
    media_root = tmp_path / "synthetic-media"

    seeded = _run("seed", db_path, media_root, env)
    assert seeded["seeded"]
    assert db_path.is_file()
    assert db_path.read_bytes()[:16] != b"SQLite format 3\x00"
    assert not db_path.read_bytes().startswith(b"\x89PNG")
    assert b"\x89PNG" not in db_path.read_bytes()
    assert len(list(media_root.rglob("*.dcm"))) == 1
    assert b"\x89PNG" not in next(media_root.rglob("*.dcm")).read_bytes()

    # Each invocation below starts a NEW Python process + SQLCipher connection.
    recovered = _run("verify", db_path, media_root, env)
    assert recovered["recovered"]
    assert recovered["receipt_id"] == seeded["receipt_id"]
    assert _run("wrong_sql_key", db_path, media_root, env)["wrong_sql_key_rejected"]
    wrong_media = dict(env, CABINET_MASTER_KEY_HEX=os.urandom(32).hex())
    assert _run("wrong_media_key", db_path, media_root, wrong_media)["integrity_rejected"]
    assert _run("wrong_tenant", db_path, media_root, env)["integrity_rejected"]
    assert _run("precommit_rollback", db_path, media_root, env)["encrypted_orphan_after_rollback"]
    assert _run("verify_rollback", db_path, media_root, env)["no_false_receipt_after_reopen"]
    assert _run("tamper", db_path, media_root, env)["tampered"]
    assert _run("verify_corrupt", db_path, media_root, env)["integrity_rejected"]

    # No patient content or keys in CI artifact.
    evidence = {
        "kind": "LOT06_DR_S1_SYNTHETIC_SQLCIPHER_RESTART_ONLY",
        "separate_python_processes": True,
        "file_backed_sqlcipher": True,
        "aesgcm_media_from_existing_c2_helpers": True,
        "ciphertext_only_disk": True,
        "synthetic_receipt_and_audit_survived_clean_restart": True,
        "one_receipt_on_relookup": True,
        "wrong_database_key_blocked": True,
        "wrong_media_key_and_tenant_blocked": True,
        "rollback_no_false_receipt": True,
        "corrupt_blob_blocked": True,
        "production_lab_ledger_tested": False,
        "power_loss_fsync_directory_tested": False,
        "real_postgresql_and_antirollback_tested": False,
        "clinical_go_live": False,
    }
    output = os.getenv("DC06_DR_S1_EVIDENCE_DIR")
    if output:
        directory = Path(output)
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "lot06-dr-s1-restart-proof.json").write_text(
            json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
        )
    print("LOT06_DR_S1_SQLCIPHER_RESTART_SYNTHETIC_PASS")


if __name__ == "__main__":
    if len(sys.argv) != 5 or sys.argv[1] != "--worker":
        raise SystemExit(2)
    result = _worker(sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4]))
    print(json.dumps(result))
