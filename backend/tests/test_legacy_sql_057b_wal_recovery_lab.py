"""LOT05.7-B: real SQLite on-disk WAL snapshot/restore; test-only fictitious data.

No cabinet connection, application imports, Alembic, external sources, or
production restore code. Only freshly created TemporaryDirectory file paths.
The demonstrated backup API does NOT certify SQLCipher/PostgreSQL recovery.
"""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest


class Refused(ValueError):
    pass


TENANT = 777
INSTANCE = "FAKE-LOT05-7B"
MARKER = "ONLY_FAKE_LOT05_7B"
FILES = frozenset(("source.db", "snapshot.db", "restored.db", "snapshot.partial.db", "restored.partial.db"))
SCHEMA = frozenset(("marker", "patients", "appointments", "ledger"))


def digest(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def file_for(root, name):
    if (not isinstance(root, Path) or not root.is_dir() or root.is_symlink()
            or not root.name.startswith("lot05_7b_fake_") or name not in FILES):
        raise Refused("ISOLATED_LAB_PATH_REQUIRED")
    path = root / name
    if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
        raise Refused("ISOLATED_LAB_PATH_REQUIRED")
    return path


@contextmanager
def connect(root, name):
    con = sqlite3.connect(file_for(root, name), timeout=5)
    try:
        con.execute("PRAGMA foreign_keys=ON")
        if con.execute("PRAGMA foreign_keys").fetchone() != (1,):
            raise Refused("SQLITE_FK_DISABLED")
        yield con
    finally:
        con.close()


def prepare(root):
    with connect(root, "source.db") as con:
        if con.execute("PRAGMA journal_mode=WAL").fetchone() != ("wal",):
            raise Refused("WAL_REQUIRED")
        con.execute("PRAGMA synchronous=FULL")
        con.executescript("""
CREATE TABLE marker(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE patients(
 tenant INTEGER NOT NULL, instance TEXT NOT NULL, legacy TEXT NOT NULL,
 fake_name TEXT NOT NULL, PRIMARY KEY(tenant,instance,legacy));
CREATE TABLE appointments(
 tenant INTEGER NOT NULL, instance TEXT NOT NULL, legacy TEXT NOT NULL,
 patient_legacy TEXT NOT NULL, starts TEXT NOT NULL,
 PRIMARY KEY(tenant,instance,legacy),
 FOREIGN KEY(tenant,instance,patient_legacy) REFERENCES patients(tenant,instance,legacy));
CREATE TABLE ledger(
 tenant INTEGER NOT NULL,instance TEXT NOT NULL,batch TEXT NOT NULL,
 payload_sha TEXT NOT NULL,PRIMARY KEY(tenant,instance,batch));
""")
        con.execute("INSERT INTO marker VALUES (?,?)", ("type", MARKER))
        con.commit()


def check(con):
    try:
        tables = {v[0] for v in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if tables != SCHEMA or con.execute("SELECT value FROM marker WHERE key='type'").fetchone() != (MARKER,):
            raise Refused("NOT_SYNTHETIC_LAB")
        if con.execute("PRAGMA integrity_check").fetchone() != ("ok",):
            raise Refused("INTEGRITY_FAILED")
        if con.execute("PRAGMA foreign_key_check").fetchall():
            raise Refused("FOREIGN_KEY_FAILED")
    except sqlite3.DatabaseError:
        raise Refused("UNREADABLE_LAB_DB") from None


def fictional_payload(n=100):
    if type(n) is not int or n < 1 or n > 100:
        raise Refused("ONLY_SYNTHETIC_SCOPE")
    people = [(TENANT, INSTANCE, f"FAKE-P-{i:04}", f"FAKE_NAME_{i:04}") for i in range(n)]
    visits = [(TENANT, INSTANCE, f"FAKE-A-{i:04}", f"FAKE-P-{i//2:04}", f"2026-11-{i%28+1:02} 09:00")
              for i in range(n * 2)]
    return people, visits


def apply_fake_batch(con, *, n=100, tenant=TENANT, fault=False):
    check(con)
    if type(tenant) is not int or tenant != TENANT:
        raise Refused("WRONG_SYNTHETIC_TENANT")
    people, visits = fictional_payload(n)
    sha = digest((people, visits))
    try:
        con.execute("BEGIN IMMEDIATE")
        old = con.execute("SELECT payload_sha FROM ledger WHERE tenant=? AND instance=? AND batch=?",
                          (TENANT, INSTANCE, "FAKE-BATCH")).fetchone()
        if old is not None:
            if old[0] != sha:
                raise Refused("REPLAY_PAYLOAD_CHANGED")
            con.rollback()
            return "NOOP_REPLAY"
        con.executemany("INSERT INTO patients VALUES (?,?,?,?)", people)
        if fault:
            raise Refused("INJECTED_PARTIAL_BATCH_FAILURE")
        con.executemany("INSERT INTO appointments VALUES (?,?,?,?,?)", visits)
        con.execute("INSERT INTO ledger VALUES (?,?,?,?)", (TENANT, INSTANCE, "FAKE-BATCH", sha))
        if con.execute("PRAGMA foreign_key_check").fetchall():
            raise Refused("FOREIGN_KEY_FAILED")
        con.commit()
        return "SYNTHETIC_COMMIT"
    except Exception:
        con.rollback()
        raise


def evidence(con):
    check(con)
    tables = {}
    for name in ("patients", "appointments", "ledger"):
        tables[name] = con.execute(f"SELECT * FROM {name} ORDER BY 1,2,3").fetchall()
    orphans = con.execute("""
SELECT COUNT(*) FROM appointments a LEFT JOIN patients p ON
a.tenant=p.tenant AND a.instance=p.instance AND a.patient_legacy=p.legacy
WHERE p.legacy IS NULL""").fetchone()[0]
    counts = (len(tables["patients"]), len(tables["appointments"]), len(tables["ledger"]), orphans)
    return digest(tables), counts


def bytes_sha(root, name):
    h = hashlib.sha256()
    with file_for(root, name).open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def take_backup(root, expected, *, interrupted=False):
    destination = file_for(root, "snapshot.db")
    temp = file_for(root, "snapshot.partial.db")
    if destination.exists() or temp.exists():
        raise Refused("BACKUP_OVERWRITE_FORBIDDEN")
    try:
        with connect(root, "source.db") as src, connect(root, "snapshot.partial.db") as dest:
            if evidence(src) != expected:
                raise Refused("SOURCE_CHANGED")
            src.backup(dest, pages=8)
            if evidence(dest) != expected:
                raise Refused("BACKUP_CONTENT_MISMATCH")
        if interrupted:
            raise Refused("INJECTED_BACKUP_PUBLISH_FAILURE")
        os.replace(temp, destination)
        return bytes_sha(root, "snapshot.db")
    except (sqlite3.DatabaseError, OSError):
        raise Refused("BACKUP_IO_FAILED") from None
    finally:
        if temp.exists():
            temp.unlink()


def restore_backup(root, expected, expected_sha, *, interrupted=False):
    target = file_for(root, "restored.db")
    partial = file_for(root, "restored.partial.db")
    if target.exists() or partial.exists() or not file_for(root, "snapshot.db").is_file():
        raise Refused("RESTORE_DESTINATION_NOT_EMPTY")
    if type(expected_sha) is not str or bytes_sha(root, "snapshot.db") != expected_sha:
        raise Refused("BACKUP_BYTES_CHANGED")
    try:
        with connect(root, "snapshot.db") as src, connect(root, "restored.partial.db") as dst:
            if evidence(src) != expected:
                raise Refused("BACKUP_CONTENT_MISMATCH")
            src.backup(dst, pages=8)
            if evidence(dst) != expected:
                raise Refused("RESTORE_CONTENT_MISMATCH")
        with connect(root, "restored.partial.db") as check_reopen:
            if evidence(check_reopen) != expected:
                raise Refused("RESTORE_REOPEN_FAILED")
        if interrupted:
            raise Refused("INJECTED_RESTORE_PUBLISH_FAILURE")
        if target.exists():
            raise Refused("RESTORE_DESTINATION_NOT_EMPTY")
        # Synthetic single-process publish, NOT a production atomic CAS or fsync.
        os.replace(partial, target)
        with connect(root, "restored.db") as check_reopen:
            if evidence(check_reopen) != expected:
                raise Refused("RESTORE_REOPEN_FAILED")
    except (sqlite3.DatabaseError, OSError):
        raise Refused("RESTORE_IO_FAILED") from None
    finally:
        if partial.exists():
            partial.unlink()


class SyntheticRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="lot05_7b_fake_")
        self.root = Path(self.temp.name)
        prepare(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def seed(self):
        with connect(self.root, "source.db") as con:
            if apply_fake_batch(con) != "SYNTHETIC_COMMIT":
                raise Refused("SEED_FAILED")
            report = evidence(con)
        self.assertEqual(report[1], (100, 200, 1, 0))
        return report

    def test_01_backup_restore_disk_100x200(self):
        report = self.seed()
        sha = take_backup(self.root, report)
        restore_backup(self.root, report, sha)
        with connect(self.root, "restored.db") as con:
            self.assertEqual(evidence(con), report)

    def test_02_restore_snapshot_not_later_commits(self):
        report = self.seed()
        sha = take_backup(self.root, report)
        with connect(self.root, "source.db") as con:
            con.execute("UPDATE patients SET fake_name='FAKE_CHANGED' WHERE legacy='FAKE-P-0000'")
            con.commit()
            self.assertNotEqual(evidence(con), report)
        restore_backup(self.root, report, sha)
        with connect(self.root, "restored.db") as con:
            self.assertEqual(evidence(con), report)

    def test_03_actual_abrupt_subprocess_exit_rollback(self):
        report = self.seed()
        script = ("import os,sqlite3,sys; c=sqlite3.connect(sys.argv[1]); "
                  "c.execute('BEGIN IMMEDIATE'); "
                  "c.execute(\"INSERT INTO patients VALUES (777,'FAKE-LOT05-7B','FAKE-CRASH','FAKE_CRASH')\"); "
                  "os._exit(77)")
        p = subprocess.run([sys.executable, "-c", script, str(file_for(self.root, "source.db"))],
                           capture_output=True, timeout=15)
        self.assertEqual(p.returncode, 77)
        with connect(self.root, "source.db") as con:
            self.assertEqual(evidence(con), report)

    def test_04_exact_replay_does_not_duplicate_rows(self):
        report = self.seed()
        with connect(self.root, "source.db") as con:
            self.assertEqual(apply_fake_batch(con), "NOOP_REPLAY")
            self.assertEqual(evidence(con), report)

    def test_05_changed_replay_fails_without_changes(self):
        report = self.seed()
        with connect(self.root, "source.db") as con:
            with self.assertRaisesRegex(Refused, "REPLAY_PAYLOAD_CHANGED"):
                apply_fake_batch(con, n=99)
            self.assertEqual(evidence(con), report)

    def test_06_failing_mid_batch_is_transactional(self):
        with connect(self.root, "source.db") as con:
            before = evidence(con)
            with self.assertRaisesRegex(Refused, "INJECTED_PARTIAL_BATCH_FAILURE"):
                apply_fake_batch(con, fault=True)
            self.assertEqual(evidence(con), before)

    def test_07_cross_tenant_fk_blocked(self):
        self.seed()
        with connect(self.root, "source.db") as con:
            with self.assertRaises(sqlite3.IntegrityError):
                con.execute("INSERT INTO appointments VALUES (?,?,?,?,?)",
                            (778, INSTANCE, "CROSS", "FAKE-P-0000", "2026-11-01"))
            con.rollback()
            self.assertEqual(evidence(con)[1], (100, 200, 1, 0))

    def test_08_orphan_fk_blocked(self):
        self.seed()
        with connect(self.root, "source.db") as con:
            with self.assertRaises(sqlite3.IntegrityError):
                con.execute("INSERT INTO appointments VALUES (?,?,?,?,?)",
                            (TENANT, INSTANCE, "ORPHAN", "UNKNOWN", "2026-11-01"))
            con.rollback()
            self.assertEqual(evidence(con)[1], (100, 200, 1, 0))

    def test_09_truncated_backup_refused(self):
        report = self.seed()
        sha = take_backup(self.root, report)
        file_for(self.root, "snapshot.db").write_bytes(b"INVALID_DATABASE")
        with self.assertRaisesRegex(Refused, "BACKUP_BYTES_CHANGED"):
            restore_backup(self.root, report, sha)
        self.assertFalse(file_for(self.root, "restored.db").exists())

    def test_10_sqlite_valid_but_tampered_backup_refused(self):
        report = self.seed()
        take_backup(self.root, report)
        with connect(self.root, "snapshot.db") as con:
            con.execute("UPDATE patients SET fake_name='FAKE_TAMPER' WHERE legacy='FAKE-P-0000'")
            con.commit()
        with self.assertRaisesRegex(Refused, "BACKUP_CONTENT_MISMATCH"):
            restore_backup(self.root, report, bytes_sha(self.root, "snapshot.db"))

    def test_11_never_overwrite_restore_target(self):
        report = self.seed()
        sha = take_backup(self.root, report)
        path = file_for(self.root, "restored.db")
        path.write_bytes(b"EXISTING_FAKE_TARGET")
        with self.assertRaisesRegex(Refused, "RESTORE_DESTINATION_NOT_EMPTY"):
            restore_backup(self.root, report, sha)
        self.assertEqual(path.read_bytes(), b"EXISTING_FAKE_TARGET")

    def test_12_disallow_paths_outside_laboratory(self):
        for invalid in ("../clinic.db", "/etc/passwd", "C:\\Users\\real.db", "cabinet.db"):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(Refused, "ISOLATED_LAB_PATH_REQUIRED"):
                    file_for(self.root, invalid)

    def test_13_external_symlink_rejected_where_supported(self):
        with tempfile.TemporaryDirectory(prefix="lot05_7b_other_fake_") as other:
            outside = Path(other) / "other.db"
            outside.write_bytes(b"FAKE_OUTSIDE")
            try:
                file_for(self.root, "snapshot.db").symlink_to(outside)
            except (OSError, NotImplementedError):
                self.skipTest("OS denies symlink creation")
            with self.assertRaisesRegex(Refused, "ISOLATED_LAB_PATH_REQUIRED"):
                file_for(self.root, "snapshot.db")
            self.assertEqual(outside.read_bytes(), b"FAKE_OUTSIDE")

    def test_14_failed_snapshot_publish_cleans_partial(self):
        report = self.seed()
        with self.assertRaisesRegex(Refused, "INJECTED_BACKUP_PUBLISH_FAILURE"):
            take_backup(self.root, report, interrupted=True)
        self.assertFalse(file_for(self.root, "snapshot.db").exists())
        self.assertFalse(file_for(self.root, "snapshot.partial.db").exists())

    def test_15_backup_overwrite_forbidden(self):
        report = self.seed()
        sha = take_backup(self.root, report)
        with self.assertRaisesRegex(Refused, "BACKUP_OVERWRITE_FORBIDDEN"):
            take_backup(self.root, report)
        self.assertEqual(bytes_sha(self.root, "snapshot.db"), sha)

    def test_16_marker_mismatch_refused(self):
        with connect(self.root, "source.db") as con:
            con.execute("UPDATE marker SET value='NOT_SYNTHETIC'")
            con.commit()
            with self.assertRaisesRegex(Refused, "NOT_SYNTHETIC_LAB"):
                check(con)

    def test_17_source_changed_after_expected_digest_refused(self):
        report = self.seed()
        with connect(self.root, "source.db") as con:
            con.execute("UPDATE patients SET fake_name='FAKE_CHANGED' WHERE legacy='FAKE-P-0000'")
            con.commit()
        with self.assertRaisesRegex(Refused, "SOURCE_CHANGED"):
            take_backup(self.root, report)
        self.assertFalse(file_for(self.root, "snapshot.db").exists())

    def test_18_untrusted_tenant_and_scope_refused(self):
        with connect(self.root, "source.db") as con:
            for tenant in (778, True, "777", None):
                with self.subTest(tenant=tenant):
                    with self.assertRaisesRegex(Refused, "WRONG_SYNTHETIC_TENANT"):
                        apply_fake_batch(con, tenant=tenant)
            for n in (0, 101, True, -1):
                with self.subTest(n=n):
                    with self.assertRaisesRegex(Refused, "ONLY_SYNTHETIC_SCOPE"):
                        apply_fake_batch(con, n=n)
            self.assertEqual(evidence(con)[1], (0, 0, 0, 0))

    def test_19_online_backup_of_committed_active_wal(self):
        self.seed()
        with connect(self.root, "source.db") as writer:
            self.assertEqual(writer.execute("PRAGMA journal_mode").fetchone(), ("wal",))
            writer.execute("UPDATE patients SET fake_name='FAKE_WAL_COMMITTED' WHERE legacy='FAKE-P-0000'")
            writer.commit()
            wal = Path(str(file_for(self.root, "source.db")) + "-wal")
            self.assertTrue(wal.exists())
            self.assertGreater(wal.stat().st_size, 0)
            report = evidence(writer)
            sha = take_backup(self.root, report)
            restore_backup(self.root, report, sha)
            with connect(self.root, "restored.db") as recovered:
                self.assertEqual(evidence(recovered), report)

    def test_20_failed_restore_publish_cleans_partial(self):
        report = self.seed()
        sha = take_backup(self.root, report)
        with self.assertRaisesRegex(Refused, "INJECTED_RESTORE_PUBLISH_FAILURE"):
            restore_backup(self.root, report, sha, interrupted=True)
        self.assertFalse(file_for(self.root, "restored.db").exists())
        self.assertFalse(file_for(self.root, "restored.partial.db").exists())

    def test_21_corrupted_cross_tenant_fk_in_backup_refused(self):
        report = self.seed()
        take_backup(self.root, report)
        with connect(self.root, "snapshot.db") as con:
            con.execute("PRAGMA foreign_keys=OFF")
            con.execute("INSERT INTO appointments VALUES (?,?,?,?,?)",
                        (778, INSTANCE, "BAD-FAKE-CROSS", "FAKE-P-0000", "2026-11-01"))
            con.commit()
        with self.assertRaisesRegex(Refused, "FOREIGN_KEY_FAILED"):
            restore_backup(self.root, report, bytes_sha(self.root, "snapshot.db"))

    def test_22_restored_database_readable_from_fresh_process(self):
        report = self.seed()
        sha = take_backup(self.root, report)
        restore_backup(self.root, report, sha)
        script = ("import json,sqlite3,sys; c=sqlite3.connect(sys.argv[1]); "
                  "print(json.dumps([c.execute('SELECT count(*) FROM patients').fetchone()[0],"
                  "c.execute('SELECT count(*) FROM appointments').fetchone()[0],"
                  "c.execute('PRAGMA integrity_check').fetchone()[0],"
                  "c.execute('PRAGMA foreign_key_check').fetchall()]))")
        p = subprocess.run([sys.executable, "-c", script, str(file_for(self.root, "restored.db"))],
                           capture_output=True, text=True, timeout=15)
        self.assertEqual(p.returncode, 0, "Fresh synthetic subprocess read failed")
        self.assertEqual(json.loads(p.stdout), [100, 200, "ok", []])


if __name__ == "__main__":
    unittest.main()
