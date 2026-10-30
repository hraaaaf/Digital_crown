"""LOT06 C05B-03D: SQLCipher WAL sync-policy and uncertain-ACK FUE (TEST ONLY).

No VFS xSync instrumentation, OS crash, unplug, real power failure, hardware
barrier certification, cabinet migration or production clinical receipt API.
Application-process termination must never be mislabeled a power-loss test.
SQLite reference: https://www.sqlite.org/pragma.html#pragma_synchronous
"""
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import pytest
from sqlcipher3 import dbapi2 as sqlcipher

MODES = {"NORMAL": 1, "FULL": 2}
CLINICAL_DURABILITY_CERTIFIED = False
CAPTURE = "synthetic-capture"
TENANT = 31
DEVICE = "synthetic-device"
MEDIA = b"DC06D-SYNTHETIC-ONLY-NO-PATIENT-DATA"


def _guard():
    if (os.environ.get("ENVIRONMENT") != "test"
            or os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") != "true"
            or os.environ.get("DC06C05B03D_TEST_ONLY") != "1"):
        raise RuntimeError("C05B03D_ISOLATED_RUNTIME_REQUIRED")


def _key(env):
    key = os.environ.get(env, "")
    if len(key) != 64 or any(c not in "0123456789abcdef" for c in key):
        raise RuntimeError("C05B03D_SYNTHETIC_KEY_REQUIRED")
    return key


def _connect(root: Path, mode: str):
    _guard()
    if mode not in MODES:
        raise ValueError("INVALID_SYNC_MODE")
    db = sqlcipher.connect(str(root / "synthetic-receipt.db"),
                           timeout=10, isolation_level=None)
    try:
        db.execute(f"PRAGMA key = '{_key('DC06C05B03D_SQLCIPHER_KEY')}'")
        if not db.execute("PRAGMA cipher_version").fetchone():
            raise RuntimeError("SQLCIPHER_DRIVER_MISSING")
        db.execute("PRAGMA journal_mode=WAL")
        db.execute(f"PRAGMA synchronous={mode}")
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA wal_autocheckpoint=0")
        assert db.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
        assert db.execute("PRAGMA synchronous").fetchone()[0] == MODES[mode]
        return db
    except BaseException:
        db.close()
        raise


def _require_full_before_commit(db):
    """LAB proposal: never call a receipt power-safe just by inspecting an ACK.

    Strict mode checks the *same connection* which will later COMMIT.
    It proves configuration, not that the physical storage honors xSync.
    """
    if db.execute("PRAGMA journal_mode").fetchone()[0].lower() != "wal":
        raise RuntimeError("RECEIPT_JOURNAL_POLICY_NOT_WAL")
    if db.execute("PRAGMA synchronous").fetchone()[0] != 2:
        raise RuntimeError("RECEIPT_SYNC_POLICY_NOT_FULL")
    return True


def _setup(root: Path, monkeypatch):
    _guard()
    root.mkdir()
    monkeypatch.setenv("DC06C05B03D_SQLCIPHER_KEY", secrets.token_hex(32))
    monkeypatch.setenv("DC06C05B03D_MEDIA_KEY", secrets.token_hex(32))
    db = _connect(root, "NORMAL")
    try:
        db.execute("BEGIN IMMEDIATE")
        db.execute("""CREATE TABLE approvals (
            tenant INTEGER NOT NULL, device TEXT NOT NULL, capture TEXT NOT NULL,
            digest TEXT NOT NULL, byte_size INTEGER NOT NULL, version INTEGER NOT NULL,
            approved INTEGER NOT NULL, PRIMARY KEY(tenant,device,capture))""")
        db.execute("""CREATE TABLE receipts (
            tenant INTEGER NOT NULL, device TEXT NOT NULL, capture TEXT NOT NULL,
            receipt_id TEXT NOT NULL UNIQUE, digest TEXT NOT NULL,
            byte_size INTEGER NOT NULL, version INTEGER NOT NULL,
            PRIMARY KEY(tenant,device,capture))""")
        db.execute("CREATE TABLE audit (receipt_id TEXT PRIMARY KEY, event TEXT NOT NULL)")
        db.execute("CREATE TABLE outbox (receipt_id TEXT PRIMARY KEY, event TEXT NOT NULL)")
        db.execute(
            "INSERT INTO approvals VALUES(?,?,?,?,?,?,1)",
            (TENANT, DEVICE, CAPTURE, hashlib.sha256(MEDIA).hexdigest(), len(MEDIA), 1),
        )
        db.commit()
    finally:
        db.close()

    # Synthetic Media Core *analogue*: AES-GCM + file fsync + POSIX dir barrier.
    # C05B-03C separately tests real ClinicalAsset/Media Core and authorization.
    iv = secrets.token_bytes(12)
    encrypted = b"D3D1" + iv + AESGCM(bytes.fromhex(_key("DC06C05B03D_MEDIA_KEY"))).encrypt(
        iv, MEDIA, None,
    )
    path = root / "test-media.bin"
    with path.open("xb") as f:
        f.write(encrypted)
        f.flush()
        os.fsync(f.fileno())
    if os.name == "posix":
        fd = os.open(root, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    return (TENANT, DEVICE, CAPTURE, hashlib.sha256(MEDIA).hexdigest(), len(MEDIA), 1)


def _verify_media(root: Path, claim):
    path = root / "test-media.bin"
    try:
        content = path.read_bytes()
        if content[:4] != b"D3D1":
            raise ValueError("MEDIA_INTEGRITY_BLOCKED")
        clear = AESGCM(bytes.fromhex(_key("DC06C05B03D_MEDIA_KEY"))).decrypt(
            content[4:16], content[16:], None,
        )
        if (hashlib.sha256(clear).hexdigest() != claim[3]
                or len(clear) != claim[4]):
            raise ValueError("MEDIA_INTEGRITY_BLOCKED")
    except (OSError, InvalidTag) as exc:
        raise ValueError("MEDIA_INTEGRITY_BLOCKED") from exc


def _counts(root: Path, mode: str):
    db = _connect(root, mode)
    try:
        return tuple(db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                     for table in ("receipts", "audit", "outbox"))
    finally:
        db.close()


def _issue(root: Path, mode: str, claim, *, strict_full=False, fail_at=None):
    """SQLCipher single-transaction authority + receipt; ACK only after COMMIT.

    No global SQL/filesystem atomicity. Files were independently encrypted/fsynced.
    """
    _guard()
    if fail_at not in (None, "after_receipt", "after_audit", "after_outbox",
                       "process_exit_before_commit", "process_exit_after_commit"):
        raise ValueError("INVALID_FAILPOINT")
    db = _connect(root, mode)
    try:
        if strict_full:
            _require_full_before_commit(db)
        db.execute("BEGIN IMMEDIATE")
        approved = db.execute(
            """SELECT tenant,device,capture,digest,byte_size,version FROM approvals
               WHERE tenant=? AND device=? AND capture=? AND approved=1""",
            claim[:3],
        ).fetchone()
        if approved != claim:
            raise ValueError("APPROVAL_IDENTITY_VERSION_CONFLICT")
        _verify_media(root, claim)

        existing = db.execute(
            """SELECT tenant,device,capture,receipt_id,digest,byte_size,version
               FROM receipts WHERE tenant=? AND device=? AND capture=?""",
            claim[:3],
        ).fetchone()
        if existing is not None:
            if (*existing[:3], *existing[4:]) != claim:
                raise ValueError("RECEIPT_IDENTITY_CONFLICT")
            rid = existing[3]
            for table, label in (("audit", "RECEIPT_COMMITTED"),
                                 ("outbox", "MEDIA_READY")):
                if db.execute(
                    f"SELECT event FROM {table} WHERE receipt_id=?", (rid,)
                ).fetchone() != (label,):
                    raise ValueError("RECEIPT_PROVENANCE_INCOMPLETE")
            db.commit()
            return rid  # no fresh clinical authorization; LAB-only ACK replay

        rid = "DUR-LAB-" + secrets.token_hex(16)
        db.execute("INSERT INTO receipts VALUES(?,?,?,?,?,?,?)",
                   (*claim[:3], rid, *claim[3:]))
        if fail_at == "after_receipt":
            raise RuntimeError("INJECTED_PRECOMMIT_ROLLBACK")
        db.execute("INSERT INTO audit VALUES(?,?)", (rid, "RECEIPT_COMMITTED"))
        if fail_at == "after_audit":
            raise RuntimeError("INJECTED_PRECOMMIT_ROLLBACK")
        db.execute("INSERT INTO outbox VALUES(?,?)", (rid, "MEDIA_READY"))
        if fail_at == "after_outbox":
            raise RuntimeError("INJECTED_PRECOMMIT_ROLLBACK")
        if fail_at == "process_exit_before_commit":
            os._exit(75)  # process only; power/OS remain up
        db.commit()
        if fail_at == "process_exit_after_commit":
            os._exit(76)  # ACK deliberately lost; power/OS remain up
        return rid
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()


def _recovery_decision(root, mode, claim):
    """Uncertain commit is never blindly ACKed or marked power-loss durable."""
    db = _connect(root, mode)
    try:
        row = db.execute(
            """SELECT tenant,device,capture,receipt_id,digest,byte_size,version
               FROM receipts WHERE tenant=? AND device=? AND capture=?""",
            claim[:3],
        ).fetchone()
    finally:
        db.close()
    if row is None:
        return "NO_RECEIPT_REAUTHORIZE_AND_RETRY_SAME_IDENTITY"
    if (*row[:3], *row[4:]) != claim:
        raise ValueError("RECEIPT_IDENTITY_CONFLICT")
    # Verification + idempotent replay also checks audit/outbox and ciphertext.
    assert _issue(root, mode, claim) == row[3]
    return "RECOVERED_PROCESS_CRASH_ACK_NOT_POWERLOSS_CERTIFICATION"


def _child(root, mode, when):
    env = dict(os.environ, DC06C05B03D_ROOT=str(root),
               DC06C05B03D_MODE=mode, DC06C05B03D_FAIL=when)
    return subprocess.run(
        [sys.executable, "-m",
         "isolated_fue_lot06c.test_sqlcipher_wal_durability_contract_v15",
         "--child"],
        env=env, capture_output=True, text=True, timeout=35, check=False,
    )


def test_c05b03d_01_actual_sqlcipher_policy_and_cabinet_parity(tmp_path, monkeypatch):
    _guard()
    runtime = (Path(__file__).resolve().parents[1] / "backend" / "database.py"
               ).read_text(encoding="utf-8")
    assert 'cursor.execute("PRAGMA journal_mode=WAL")' in runtime
    assert 'cursor.execute("PRAGMA synchronous=NORMAL")' in runtime
    root = tmp_path / "policy"
    _setup(root, monkeypatch)
    normal, full = _connect(root, "NORMAL"), _connect(root, "FULL")
    try:
        assert normal.execute("PRAGMA synchronous").fetchone() == (1,)
        assert full.execute("PRAGMA synchronous").fetchone() == (2,)
        with pytest.raises(RuntimeError, match="RECEIPT_SYNC_POLICY_NOT_FULL"):
            _require_full_before_commit(normal)
        assert _require_full_before_commit(full) is True
        # A FULL connection does not upgrade another existing NORMAL writer.
        assert normal.execute("PRAGMA synchronous").fetchone() == (1,)
    finally:
        normal.close()
        full.close()
    print("LOT06C05B03D_WAL_SYNC_POLICY_PER_CONNECTION_PASS")


def test_c05b03d_02_sql_triplet_rollback_and_strict_full_gate(tmp_path, monkeypatch):
    _guard()
    for mode in MODES:
        root = tmp_path / mode
        claim = _setup(root, monkeypatch)
        if mode == "NORMAL":
            with pytest.raises(RuntimeError, match="RECEIPT_SYNC_POLICY_NOT_FULL"):
                _issue(root, mode, claim, strict_full=True)
            assert _counts(root, mode) == (0, 0, 0)
        for at in ("after_receipt", "after_audit", "after_outbox"):
            with pytest.raises(RuntimeError, match="INJECTED_PRECOMMIT_ROLLBACK"):
                _issue(root, mode, claim, strict_full=(mode == "FULL"), fail_at=at)
            assert _counts(root, mode) == (0, 0, 0)
    print("LOT06C05B03D_TRIPLET_ROLLBACK_POLICY_PASS")


def test_c05b03d_03_os_process_pre_postcommit_matrix(tmp_path, monkeypatch):
    _guard()
    for mode in MODES:
        root = tmp_path / mode
        claim = _setup(root, monkeypatch)
        for at in ("after_receipt", "after_audit", "after_outbox"):
            with pytest.raises(RuntimeError, match="INJECTED_PRECOMMIT_ROLLBACK"):
                _issue(root, mode, claim, fail_at=at)
            assert _counts(root, mode) == (0, 0, 0)
        before = _child(root, mode, "process_exit_before_commit")
        assert before.returncode == 75, f"PRECOMMIT_CHILD_{before.returncode}"
        assert _counts(root, mode) == (0, 0, 0)
        assert _recovery_decision(root, mode, claim) == (
            "NO_RECEIPT_REAUTHORIZE_AND_RETRY_SAME_IDENTITY"
        )
        after = _child(root, mode, "process_exit_after_commit")
        assert after.returncode == 76, f"POSTCOMMIT_CHILD_{after.returncode}"
        assert _counts(root, mode) == (1, 1, 1)
        assert _recovery_decision(root, mode, claim) == (
            "RECOVERED_PROCESS_CRASH_ACK_NOT_POWERLOSS_CERTIFICATION"
        )
        receipt = _issue(root, mode, claim)
        assert all(_issue(root, mode, claim) == receipt for _ in range(3))
        assert _counts(root, mode) == (1, 1, 1)
    print("LOT06C05B03D_PROCESS_EXIT_ONLY_ACK_MATRIX_PASS")


def test_c05b03d_04_corruption_and_identity_fail_closed(tmp_path, monkeypatch):
    _guard()
    root = tmp_path / "negative"
    claim = _setup(root, monkeypatch)
    issued = _issue(root, "FULL", claim, strict_full=True)
    assert issued.startswith("DUR-LAB-")
    for wrong in ((99, *claim[1:]), (*claim[:3], "0" * 64, *claim[4:]),
                  (*claim[:5], 2)):
        with pytest.raises(ValueError, match="APPROVAL_IDENTITY_VERSION_CONFLICT"):
            _issue(root, "FULL", wrong, strict_full=True)
    media = root / "test-media.bin"
    blob = media.read_bytes()
    media.write_bytes(blob[:-1] + bytes([blob[-1] ^ 1]))
    with pytest.raises(ValueError, match="MEDIA_INTEGRITY_BLOCKED"):
        _recovery_decision(root, "FULL", claim)
    media.write_bytes(blob)
    media.unlink()
    with pytest.raises(ValueError, match="MEDIA_INTEGRITY_BLOCKED"):
        _recovery_decision(root, "FULL", claim)
    assert _counts(root, "FULL") == (1, 1, 1)

    evidence = Path(os.environ.get("DC06C05B03D_EVIDENCE_DIR", str(tmp_path)))
    evidence.mkdir(parents=True, exist_ok=True)
    report = {
        "kind": "LOT06_C05B03D_SQLCIPHER_SYNC_DURABILITY_LAB_ONLY",
        "actual_sqlcipher_wal_normal_and_full_config_observed": True,
        "cabinet_wal_normal_source_pinned": True,
        "full_requires_same_writer_connection": True,
        "normal_refused_for_strict_policy": True,
        "normal_full_sql_triplet_rollback_verified": True,
        "normal_full_precommit_os_process_exit_verified": True,
        "normal_full_postcommit_os_process_exit_ack_recovered": True,
        "identity_and_media_corruption_block_receipt_recovery": True,
        "uncertain_commit_no_receipt_never_acknowledged": True,
        "sqlite_primary_documentation_wal_sync_semantics": "https://www.sqlite.org/pragma.html",
        "test_only_synthetic_aesgcm_media_not_clinical_asset": True,
        "observed_os_process_exit_not_power_failure": True,
        "actual_power_loss_tested": False,
        "os_kernel_crash_tested": False,
        "vfs_xsync_invocations_instrumented": False,
        "physical_media_flush_guaranteed": False,
        "windows_ntfs_certified": False,
        "clinical_staff_device_authenticated": False,
        "production_schema_migrated": False,
        "sql_and_filesystem_globally_atomic": False,
        "per_commit_powerloss_durability_certified": False,
        "production_durable_receipt_enabled": False,
        "product_ready": False,
    }
    (evidence / "lot06c05b03d-wal-sync-uncertain-ack-fue.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print("LOT06C05B03D_NO_FALSE_DURABLE_ACK_PASS")


if __name__ == "__main__" and sys.argv[1:] == ["--child"]:
    _guard()
    root = Path(os.environ["DC06C05B03D_ROOT"])
    claim = (TENANT, DEVICE, CAPTURE, hashlib.sha256(MEDIA).hexdigest(),
             len(MEDIA), 1)
    _issue(root, os.environ["DC06C05B03D_MODE"], claim,
           fail_at=os.environ["DC06C05B03D_FAIL"])
    os._exit(88)
