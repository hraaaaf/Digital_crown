"""P2 SQLite recovery smoke on disposable fixtures ONLY.

This exercises stdlib SQLite WAL semantics in CI. It does NOT install a service,
inspect Windows SIDs, validate DACLs, SQLCipher, packaged backend or clinical data.
The native SCM W01-W12 contract remains NOT TESTED until separately authorized.
"""
from contextlib import closing
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest


class P2SyntheticSQLiteWALContract(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="dc-p2-synthetic-")
        self.addCleanup(self.tmp.cleanup)
        self.db_path = Path(self.tmp.name) / "acquisitions.sqlite3"

    def connect(self):
        connection = sqlite3.connect(str(self.db_path), timeout=2)
        self.assertEqual(connection.execute("PRAGMA journal_mode=WAL").fetchone()[0], "wal")
        connection.execute("PRAGMA synchronous=FULL")
        return connection

    def test_dynamic_wal_shm_commit_and_rollback(self):
        db = self.connect()
        reader = None
        try:
            db.execute("CREATE TABLE ledger(id INTEGER PRIMARY KEY, marker TEXT NOT NULL)")
            db.execute("INSERT INTO ledger(marker) VALUES ('committed')")
            db.commit()
            reader = self.connect()
            self.assertEqual(reader.execute("SELECT marker FROM ledger").fetchall(), [("committed",)])
            self.assertTrue(Path(str(self.db_path) + "-wal").exists())
            self.assertTrue(Path(str(self.db_path) + "-shm").exists())
            db.execute("INSERT INTO ledger(marker) VALUES ('rolled-back')")
            db.rollback()
            self.assertEqual(reader.execute("SELECT marker FROM ledger").fetchall(), [("committed",)])
        finally:
            if reader is not None:
                reader.close()
            db.close()
        with closing(self.connect()) as check:
            self.assertEqual(check.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertEqual(check.execute("SELECT marker FROM ledger").fetchall(), [("committed",)])

    def test_writer_contention_then_checkpoint(self):
        first = self.connect()
        second = self.connect()
        try:
            first.execute("CREATE TABLE ledger(marker TEXT NOT NULL)")
            first.commit()
            first.execute("BEGIN IMMEDIATE")
            first.execute("INSERT INTO ledger(marker) VALUES ('first')")
            second.execute("PRAGMA busy_timeout=100")
            with self.assertRaisesRegex(sqlite3.OperationalError, "locked"):
                second.execute("INSERT INTO ledger(marker) VALUES ('blocked')")
            first.commit()
            second.execute("INSERT INTO ledger(marker) VALUES ('second')")
            second.commit()
            self.assertEqual(first.execute("SELECT marker FROM ledger ORDER BY rowid").fetchall(),
                             [("first",), ("second",)])
            outcome = first.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
            self.assertEqual(outcome[0], 0)
            self.assertEqual(first.execute("PRAGMA integrity_check").fetchone()[0], "ok")
        finally:
            second.close()
            first.close()

    def test_online_backup_contains_uncheckpointed_commits_and_restores(self):
        original = self.connect()
        copied = Path(self.tmp.name) / "backup.sqlite3"
        try:
            original.execute("CREATE TABLE ledger(marker TEXT NOT NULL)")
            original.execute("INSERT INTO ledger(marker) VALUES ('included')")
            original.commit()
            self.assertTrue(Path(str(self.db_path) + "-wal").exists())
            target = sqlite3.connect(copied)
            try:
                original.backup(target)
            finally:
                target.close()
            original.execute("INSERT INTO ledger(marker) VALUES ('not-in-snapshot')")
            original.commit()
            with closing(sqlite3.connect(copied)) as restored:
                self.assertEqual(restored.execute("PRAGMA integrity_check").fetchone()[0], "ok")
                self.assertEqual(restored.execute("SELECT marker FROM ledger").fetchall(), [("included",)])
        finally:
            original.close()

    def test_crash_after_commit_recovers_but_uncommitted_write_does_not(self):
        child_script = r"""
import os, sqlite3, sys
db = sqlite3.connect(sys.argv[1], timeout=2)
assert db.execute('PRAGMA journal_mode=WAL').fetchone()[0] == 'wal'
db.execute('PRAGMA synchronous=FULL')
db.execute('CREATE TABLE ledger(marker TEXT NOT NULL)')
db.execute("INSERT INTO ledger VALUES ('committed')")
db.commit()
db.execute("INSERT INTO ledger VALUES ('not-committed')")
os._exit(17)
"""
        result = subprocess.run([sys.executable, "-c", child_script, str(self.db_path)],
                                stdin=subprocess.DEVNULL, capture_output=True,
                                timeout=20, check=False)
        self.assertEqual(result.returncode, 17, result.stderr.decode("utf-8", "replace"))
        with closing(self.connect()) as recovered:
            self.assertEqual(recovered.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertEqual(recovered.execute("SELECT marker FROM ledger").fetchall(), [("committed",)])
            self.assertEqual(recovered.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
