"""LOT05.7-C / SQLCipher encrypted OFFLINE copy + restore of FAKE data only.

RUN ONLY with LOT05C_SQLCIPHER_SYNTHETIC_ONLY=1. No Cabinet runtime imports,
source upload, operator path, migration API, network or clinical records.
Never use these helpers with a live cabinet source.
"""
from __future__ import annotations

from contextlib import contextmanager, closing
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest


class Refused(ValueError):
    pass


FLAG = "LOT05C_SQLCIPHER_SYNTHETIC_ONLY"
TABLES = ("patients", "appointments", "acts", "payments", "media_refs")
EXPECTED = (20, 40, 4, 4, 2)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def logical_evidence(db):
    if db.execute("PRAGMA integrity_check").fetchone() != ("ok",):
        raise Refused("INTEGRITY_FAILURE")
    if db.execute("PRAGMA foreign_key_check").fetchall():
        raise Refused("FOREIGN_KEY_FAILURE")
    if db.execute("SELECT value FROM fake_marker WHERE key='dataset'").fetchone() != ("ONLY_FAKE_05_7_C",):
        raise Refused("FAKE_MARKER_REQUIRED")
    rows = {
        name: db.execute(f"SELECT * FROM {name} ORDER BY 1, 2").fetchall()
        for name in TABLES
    }
    counts = tuple(len(rows[name]) for name in TABLES)
    payload = json.dumps(rows, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest(), counts


def _open_db(path, key, dbapi):
    if type(key) is not str or len(key) != 64 or any(c not in "0123456789abcdef" for c in key):
        raise Refused("SYNTHETIC_KEY_REQUIRED")
    db = dbapi.connect(str(path))
    try:
        db.execute(f"PRAGMA key = '{key}'")
        db.execute("PRAGMA foreign_keys = ON")
        return db
    except BaseException:
        db.close()
        raise


@contextmanager
def connect(path, key, dbapi):
    db = _open_db(path, key, dbapi)
    try:
        yield db
    finally:
        db.close()


def fabricate(path, key, dbapi):
    db = _open_db(path, key, dbapi)
    try:
        db.execute("PRAGMA journal_mode=WAL")
        db.executescript("""
CREATE TABLE fake_marker (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE patients (tenant INTEGER NOT NULL, legacy TEXT NOT NULL,
 fake_name TEXT NOT NULL, PRIMARY KEY (tenant,legacy));
CREATE TABLE appointments (tenant INTEGER NOT NULL, legacy TEXT NOT NULL,
 patient_legacy TEXT NOT NULL, PRIMARY KEY (tenant,legacy),
 FOREIGN KEY (tenant,patient_legacy) REFERENCES patients(tenant,legacy));
CREATE TABLE acts (tenant INTEGER NOT NULL, legacy TEXT NOT NULL,
 patient_legacy TEXT NOT NULL, PRIMARY KEY (tenant,legacy),
 FOREIGN KEY (tenant,patient_legacy) REFERENCES patients(tenant,legacy));
CREATE TABLE payments (tenant INTEGER NOT NULL, legacy TEXT NOT NULL,
 act_legacy TEXT NOT NULL, amount_cents INTEGER NOT NULL CHECK(amount_cents>0),
 PRIMARY KEY (tenant,legacy),
 FOREIGN KEY (tenant,act_legacy) REFERENCES acts(tenant,legacy));
CREATE TABLE media_refs (tenant INTEGER NOT NULL, legacy TEXT NOT NULL,
 patient_legacy TEXT NOT NULL, digest TEXT NOT NULL,
 PRIMARY KEY (tenant,legacy),
 FOREIGN KEY (tenant,patient_legacy) REFERENCES patients(tenant,legacy));
""")
        db.execute("INSERT INTO fake_marker VALUES ('dataset','ONLY_FAKE_05_7_C')")
        db.executemany("INSERT INTO patients VALUES (?,?,?)",
                       [(777, f"FAKE-P-{i:02}", f"FAKE_NAME_{i:02}") for i in range(20)])
        db.executemany("INSERT INTO appointments VALUES (?,?,?)",
                       [(777, f"FAKE-A-{i:02}", f"FAKE-P-{i//2:02}") for i in range(40)])
        db.executemany("INSERT INTO acts VALUES (?,?,?)",
                       [(777, f"FAKE-ACT-{i}", f"FAKE-P-{i:02}") for i in range(4)])
        db.executemany("INSERT INTO payments VALUES (?,?,?,?)",
                       [(777, f"FAKE-PAY-{i}", f"FAKE-ACT-{i}", 12000 + i) for i in range(4)])
        db.executemany("INSERT INTO media_refs VALUES (?,?,?,?)",
                       [(777, f"FAKE-MEDIA-{i}", f"FAKE-P-{i:02}",
                         hashlib.sha256(f"FAKE-BYTES-{i}".encode()).hexdigest()) for i in range(2)])
        db.commit()
        baseline = logical_evidence(db)
        if baseline[1] != EXPECTED:
            raise Refused("WRONG_FAKE_COUNTS")
        # Demonstrably leave WAL mode before making a byte-for-byte copy.
        db.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
        if db.execute("PRAGMA journal_mode=DELETE").fetchone() != ("delete",):
            raise Refused("OFFLINE_COPY_MODE_REQUIRED")
        return baseline
    finally:
        db.close()


def offline_snapshot(root, key, dbapi, baseline):
    if os.environ.get(FLAG) != "1" or not root.name.startswith("lot05c_fake_sqlcipher_"):
        raise Refused("SYNTHETIC_ONLY")
    src = root / "source.db"
    dest = root / "snapshot.db"
    if dest.exists() or not src.is_file() or src.is_symlink():
        raise Refused("SNAPSHOT_PATH_REFUSED")
    if (root / "source.db-wal").exists() or (root / "source.db-shm").exists():
        raise Refused("ACTIVE_WAL_COPY_REFUSED")
    with connect(src, key, dbapi) as db:
        if logical_evidence(db) != baseline:
            raise Refused("SOURCE_CHANGED")
    if (root / "source.db-wal").exists() or (root / "source.db-shm").exists():
        raise Refused("ACTIVE_WAL_COPY_REFUSED")
    shutil.copyfile(src, dest)
    with connect(dest, key, dbapi) as db:
        if logical_evidence(db) != baseline:
            dest.unlink(missing_ok=True)
            raise Refused("SNAPSHOT_PARITY_FAILURE")
    return sha(dest)


def restore(root, key, dbapi, baseline, expected_sha):
    if os.environ.get(FLAG) != "1" or not root.name.startswith("lot05c_fake_sqlcipher_"):
        raise Refused("SYNTHETIC_ONLY")
    src = root / "snapshot.db"
    dest = root / "restored.db"
    if dest.exists() or not src.is_file() or src.is_symlink():
        raise Refused("RESTORE_DESTINATION_REFUSED")
    if type(expected_sha) is not str or len(expected_sha) != 64 or sha(src) != expected_sha:
        raise Refused("SNAPSHOT_DIGEST_FAILURE")
    with connect(src, key, dbapi) as db:
        if logical_evidence(db) != baseline:
            raise Refused("SNAPSHOT_CONTENT_FAILURE")
    shutil.copyfile(src, dest)
    try:
        with connect(dest, key, dbapi) as db:
            if logical_evidence(db) != baseline:
                raise Refused("RESTORE_PARITY_FAILURE")
    except BaseException:
        dest.unlink(missing_ok=True)
        raise


class EncryptedOfflineRecovery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get(FLAG) != "1":
            raise Refused("SYNTHETIC_ONLY_RUN_DISABLED")
        from sqlcipher3 import dbapi2
        cls.dbapi = dbapi2

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="lot05c_fake_sqlcipher_")
        self.root = Path(self.tmp.name)
        self.key = secrets.token_hex(32)  # Ephemeral fictional fixture key; not a Cabinet secret.
        self.before = fabricate(self.root / "source.db", self.key, self.dbapi)

    def tearDown(self):
        self.tmp.cleanup()

    def snapshot(self):
        return offline_snapshot(self.root, self.key, self.dbapi, self.before)

    def test_01_database_is_really_encrypted_on_disk(self):
        header = (self.root / "source.db").read_bytes()[:16]
        self.assertNotEqual(header, b"SQLite format 3\x00")
        with closing(sqlite3.connect(self.root / "source.db")) as plain:
            with self.assertRaises(sqlite3.DatabaseError):
                plain.execute("SELECT * FROM patients").fetchone()

    def test_02_offline_snapshot_restore_all_fake_relations(self):
        digest = self.snapshot()
        restore(self.root, self.key, self.dbapi, self.before, digest)
        with connect(self.root / "restored.db", self.key, self.dbapi) as db:
            self.assertEqual(logical_evidence(db), self.before)

    def test_03_incorrect_encryption_key_refused(self):
        self.snapshot()
        with connect(self.root / "snapshot.db", secrets.token_hex(32), self.dbapi) as db:
            with self.assertRaises(self.dbapi.DatabaseError):
                db.execute("SELECT COUNT(*) FROM patients").fetchone()

    def test_04_tampered_encrypted_bytes_refused_before_restore(self):
        digest = self.snapshot()
        path = self.root / "snapshot.db"
        with path.open("r+b") as f:
            f.seek(127)
            b = f.read(1)
            f.seek(127)
            f.write(bytes([b[0] ^ 1]))
        with self.assertRaisesRegex(Refused, "SNAPSHOT_DIGEST_FAILURE"):
            restore(self.root, self.key, self.dbapi, self.before, digest)
        self.assertFalse((self.root / "restored.db").exists())

    def test_05_incorrect_expected_digest_refused(self):
        self.snapshot()
        with self.assertRaisesRegex(Refused, "SNAPSHOT_DIGEST_FAILURE"):
            restore(self.root, self.key, self.dbapi, self.before, "b" * 64)

    def test_06_restore_target_never_overwritten(self):
        digest = self.snapshot()
        path = self.root / "restored.db"
        path.write_bytes(b"FAKE_OCCUPIED")
        with self.assertRaisesRegex(Refused, "RESTORE_DESTINATION_REFUSED"):
            restore(self.root, self.key, self.dbapi, self.before, digest)
        self.assertEqual(path.read_bytes(), b"FAKE_OCCUPIED")

    def test_07_source_change_not_in_earlier_snapshot(self):
        digest = self.snapshot()
        with connect(self.root / "source.db", self.key, self.dbapi) as db:
            db.execute("UPDATE patients SET fake_name='FAKE_AFTER' WHERE legacy='FAKE-P-00'")
            db.commit()
            self.assertNotEqual(logical_evidence(db), self.before)
        restore(self.root, self.key, self.dbapi, self.before, digest)
        with connect(self.root / "restored.db", self.key, self.dbapi) as db:
            self.assertEqual(logical_evidence(db), self.before)

    def test_08_cross_tenant_fk_protection(self):
        with connect(self.root / "source.db", self.key, self.dbapi) as db:
            with self.assertRaises(self.dbapi.IntegrityError):
                db.execute("INSERT INTO appointments VALUES (778,'FAKE-CROSS','FAKE-P-00')")
            db.rollback()
            self.assertEqual(logical_evidence(db), self.before)

    def test_09_payment_fk_protection(self):
        with connect(self.root / "source.db", self.key, self.dbapi) as db:
            with self.assertRaises(self.dbapi.IntegrityError):
                db.execute("INSERT INTO payments VALUES (777,'FAKE-ORPHAN','MISSING-ACT',1234)")
            db.rollback()
            self.assertEqual(logical_evidence(db), self.before)

    def test_10_transactional_rollback_of_partial_write(self):
        with connect(self.root / "source.db", self.key, self.dbapi) as db:
            try:
                db.execute("INSERT INTO patients VALUES (777,'FAKE-P-EXTRA','FAKE_EXTRA')")
                raise Refused("INJECTED_ABORT")
            except Refused:
                db.rollback()
            self.assertEqual(logical_evidence(db), self.before)

    def test_11_fresh_process_can_open_restored_encrypted_clone(self):
        digest = self.snapshot()
        restore(self.root, self.key, self.dbapi, self.before, digest)
        code = ("import os,sys; from sqlcipher3 import dbapi2; "
                "c=dbapi2.connect(sys.argv[1]); "
                "c.execute(\"PRAGMA key = '\"+os.environ['LOT05C_EPHEMERAL_KEY']+\"'\"); "
                "assert c.execute('SELECT COUNT(*) FROM appointments').fetchone()[0]==40; "
                "assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'; c.close()")
        env = dict(os.environ, LOT05C_EPHEMERAL_KEY=self.key)
        process = subprocess.run(
            [sys.executable, "-c", code, str(self.root / "restored.db")],
            env=env, capture_output=True, text=True, timeout=30
        )
        self.assertEqual(process.returncode, 0, "Fresh fake SQLCipher subprocess failed")

    def test_12_no_file_material_after_wrong_source(self):
        with connect(self.root / "source.db", self.key, self.dbapi) as db:
            db.execute("UPDATE payments SET amount_cents=99999 WHERE legacy='FAKE-PAY-0'")
            db.commit()
        with self.assertRaisesRegex(Refused, "SOURCE_CHANGED"):
            self.snapshot()
        self.assertFalse((self.root / "snapshot.db").exists())


if __name__ == "__main__":
    unittest.main()
