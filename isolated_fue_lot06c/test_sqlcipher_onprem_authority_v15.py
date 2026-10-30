"""LOT06-C05B-03A: cabinet-target SQLCipher file transaction rehearsal.

This is a stand-alone synthetic FUE. No clinical endpoints or actual approval
authority are enabled. The SQLCipher on-prem lock is BEGIN IMMEDIATE, not
PostgreSQL SELECT FOR UPDATE. All identifiers and records are synthetic.
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys

import pytest
from sqlalchemy import column, select, table
from sqlalchemy.dialects import postgresql, sqlite


TENANT, PATIENT, STAFF = 31, 73, 81
DEVICE = "sqlcipher-device"
CLAIM_COLUMNS = ("tenant", "device", "capture", "digest", "byte_size",
                 "patient", "staff", "approval_version", "asset_id", "reason")
SCHEMA = (
    """CREATE TABLE approvals (
        tenant INTEGER NOT NULL, device TEXT NOT NULL, capture TEXT NOT NULL,
        digest TEXT NOT NULL, byte_size INTEGER NOT NULL, patient INTEGER NOT NULL,
        staff INTEGER NOT NULL, approval_version INTEGER NOT NULL,
        asset_id INTEGER NOT NULL, reason TEXT NOT NULL, approved INTEGER NOT NULL,
        PRIMARY KEY(tenant,device,capture))""",
    """CREATE TABLE receipts (
        tenant INTEGER NOT NULL, device TEXT NOT NULL, capture TEXT NOT NULL,
        receipt_id TEXT NOT NULL UNIQUE, digest TEXT NOT NULL,
        byte_size INTEGER NOT NULL, patient INTEGER NOT NULL, staff INTEGER NOT NULL,
        approval_version INTEGER NOT NULL, asset_id INTEGER NOT NULL UNIQUE,
        reason TEXT NOT NULL, PRIMARY KEY(tenant,device,capture))""",
    """CREATE TABLE audit (
        receipt_id TEXT NOT NULL PRIMARY KEY, event TEXT NOT NULL)""",
    """CREATE TABLE outbox (
        receipt_id TEXT NOT NULL PRIMARY KEY, event TEXT NOT NULL)""",
)


def _guard() -> None:
    if (os.getenv("ENVIRONMENT") != "test"
            or os.getenv("DIGITALCROWN_ISOLATED_RUNTIME") != "true"
            or os.getenv("DC06C05B03A_TEST_SQLCIPHER") != "1"):
        raise RuntimeError("C05B03A_ISOLATED_TARGET_ONLY")


def _open(db_file: Path, key: str):
    _guard()
    from sqlcipher3 import dbapi2 as sqlcipher
    if not (len(key) == 64 and all(c in "0123456789abcdef" for c in key)):
        raise RuntimeError("SQLCIPHER_TEST_KEY_REQUIRED")
    con = sqlcipher.connect(str(db_file), timeout=30, isolation_level=None)
    try:
        con.execute(f"PRAGMA key = '{key}'")
        assert con.execute("PRAGMA cipher_version").fetchone()
        con.execute("PRAGMA busy_timeout=30000")
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA synchronous=FULL")
        con.execute("SELECT name FROM sqlite_master LIMIT 1").fetchone()
    except Exception:
        con.close()
        raise
    return con


def _claim(capture: str, asset_id: int) -> tuple:
    payload = ("synthetic:" + capture).encode()
    return (TENANT, DEVICE, capture, hashlib.sha256(payload).hexdigest(),
            len(payload), PATIENT, STAFF, 2, asset_id, "LAB_WALK_IN")


def _initialize(db_file: Path, key: str, claims: tuple[tuple, ...]) -> None:
    with _open(db_file, key) as con:
        for statement in SCHEMA:
            con.execute(statement)
        for claim in claims:
            con.execute(
                "INSERT INTO approvals VALUES(?,?,?,?,?,?,?,?,?,?,1)", claim
            )


def _issue(db_file: Path, key: str, claim: tuple, fail: str = "") -> str:
    con = _open(db_file, key)  # each caller owns an independent SQLCipher connection
    try:
        # Acquire SQLite's real writer transaction *before* reading approval.
        # SELECT FOR UPDATE on the same backend silently compiles to a plain SELECT.
        con.execute("BEGIN IMMEDIATE")
        approved = con.execute(
            "SELECT tenant,device,capture,digest,byte_size,patient,staff,"
            "approval_version,asset_id,reason,approved FROM approvals "
            "WHERE tenant=? AND device=? AND capture=?",
            claim[:3],
        ).fetchone()
        if approved != (*claim, 1):
            raise ValueError("SQLCIPHER_APPROVAL_BINDING_CONFLICT")
        old = con.execute(
            "SELECT receipt_id,tenant,device,capture,digest,byte_size,patient,"
            "staff,approval_version,asset_id,reason FROM receipts "
            "WHERE tenant=? AND device=? AND capture=?",
            claim[:3],
        ).fetchone()
        if old is not None:
            if old[1:] != claim:
                raise ValueError("SQLCIPHER_RECEIPT_IDENTITY_CONFLICT")
            rid = old[0]
            for tbl, event in (("audit", "CAPTURE_COMMITTED"), ("outbox", "MEDIA_READY")):
                assert con.execute(
                    f"SELECT event FROM {tbl} WHERE receipt_id=?", (rid,)
                ).fetchone() == (event,), "INCOMPLETE_COMMITTED_RECEIPT"
            con.execute("COMMIT")
            return rid
        rid = "SC-TEST-" + secrets.token_hex(16)
        con.execute(
            "INSERT INTO receipts VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (*claim[:3], rid, *claim[3:]),
        )
        if fail == "after_receipt":
            raise RuntimeError("INJECTED_ROLLBACK")
        con.execute("INSERT INTO audit VALUES(?,?)", (rid, "CAPTURE_COMMITTED"))
        if fail == "after_audit":
            raise RuntimeError("INJECTED_ROLLBACK")
        con.execute("INSERT INTO outbox VALUES(?,?)", (rid, "MEDIA_READY"))
        if fail == "after_outbox":
            raise RuntimeError("INJECTED_ROLLBACK")
        con.execute("COMMIT")
        return rid
    except BaseException:
        if con.in_transaction:
            con.execute("ROLLBACK")
        raise
    finally:
        con.close()


def _count(db_file: Path, key: str) -> tuple[int, int, int]:
    con = _open(db_file, key)
    try:
        return tuple(con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                     for t in ("receipts", "audit", "outbox"))
    finally:
        con.close()


def test_sqlcipher_cabinet_lock_is_not_postgres_row_lock():
    _guard()
    stmt = select(column("capture")).select_from(
        table("approvals")
    ).with_for_update()
    assert "FOR UPDATE" in str(stmt.compile(dialect=postgresql.dialect()))
    assert "FOR UPDATE" not in str(stmt.compile(dialect=sqlite.dialect()))
    print("LOT06C05B03A_SQLITE_FOR_UPDATE_NOT_A_LOCK_PASS")


def test_sqlcipher_six_writers_commit_rollback_lost_ack(tmp_path):
    _guard()
    db_file = tmp_path / "onprem-isolated-receipts.db"
    key = secrets.token_hex(32)
    first = _claim("six-concurrent-writers", 501)
    lost = _claim("postcommit-lost-ack", 502)
    _initialize(db_file, key, (first, lost))

    for failpoint in ("after_receipt", "after_audit", "after_outbox"):
        with pytest.raises(RuntimeError, match="INJECTED_ROLLBACK"):
            _issue(db_file, key, first, failpoint)
        assert _count(db_file, key) == (0, 0, 0)

    with ThreadPoolExecutor(max_workers=6) as pool:
        receipts = list(pool.map(lambda _: _issue(db_file, key, first), range(6)))
    assert len(receipts) == 6 and len(set(receipts)) == 1
    assert _count(db_file, key) == (1, 1, 1)
    with pytest.raises(ValueError, match="APPROVAL_BINDING_CONFLICT"):
        _issue(db_file, key, (*first[:3], "0" * 64, *first[4:]))
    with pytest.raises(ValueError, match="APPROVAL_BINDING_CONFLICT"):
        _issue(db_file, key, (*first[:7], 3, *first[8:]))
    assert _count(db_file, key) == (1, 1, 1)

    # An entirely separate OS process completes SQL COMMIT then exits without
    # returning an ACK. The parent opens another connection to recover it.
    env = dict(os.environ, DC06C05B03A_FILE=str(db_file),
               DC06C05B03A_KEY=key)
    child = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--postcommit-child"],
        env=env, capture_output=True, text=True, timeout=60, check=False,
    )
    assert child.returncode == 75, f"POSTCOMMIT_WORKER_EXIT_{child.returncode}"
    assert key not in child.stdout + child.stderr
    recovered = _issue(db_file, key, lost)
    assert recovered.startswith("SC-TEST-")
    assert all(_issue(db_file, key, lost) == recovered for _ in range(3))
    assert _count(db_file, key) == (2, 2, 2)

    # Actual encrypted file, wrong key failure, no plaintext fallback.
    assert db_file.read_bytes()[:16] != b"SQLite format 3\x00"
    with pytest.raises(Exception):
        wrong = _open(db_file, "f" * 64 if key != "f" * 64 else "e" * 64)
        try:
            wrong.execute("SELECT COUNT(*) FROM receipts").fetchone()
        finally:
            wrong.close()

    evidence = Path(os.environ.get("DC06C05B03A_EVIDENCE_DIR", str(tmp_path)))
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "lot06c05b03a-sqlcipher-target-fue.json").write_text(
        json.dumps({
            "kind": "LOT06_C05B03A_REAL_SQLCIPHER_FILE_TEST_NOT_CLINICAL",
            "encrypted_sqlcipher_file_and_wrong_key_refusal": True,
            "six_concurrent_independent_sqlcipher_connections": True,
            "begin_immediate_serializes_writers": True,
            "sql_receipt_audit_outbox_atomic_rollback": True,
            "postcommit_os_process_exit_before_ack_replayed": True,
            "postgres_for_update_not_supported_by_sqlite": True,
            "approval_and_version_conflicts_fail_closed": True,
            "actual_clinical_asset_joined": False,
            "production_schema_migration_applied": False,
            "real_staff_device_identity_certified": False,
            "physical_power_loss_tested": False,
            "product_ready": False,
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("LOT06C05B03A_SQLCIPHER_FILE_CONCURRENT_RECEIPT_ACK_RECOVERY_PASS")


if __name__ == "__main__" and sys.argv[1:] == ["--postcommit-child"]:
    _guard()
    _issue(Path(os.environ["DC06C05B03A_FILE"]),
           os.environ["DC06C05B03A_KEY"],
           _claim("postcommit-lost-ack", 502))
    os._exit(75)
