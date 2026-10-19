"""LOT05.7-J phase 2: native SQLCipher, Windows boundary FAKE-only tests."""
from __future__ import annotations

from contextlib import closing
import os
from pathlib import Path
import secrets
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from backend.services import legacy_migration_sqlcipher_scm_lab_v15 as j2


class NativeSqlcipherRecoveryBoundaryLab(unittest.TestCase):
    def setUp(self):
        self._flag = os.environ.get("LOT05J2_NATIVE_SQLCIPHER_FAKE_ONLY")
        os.environ["LOT05J2_NATIVE_SQLCIPHER_FAKE_ONLY"] = "1"
        self.addCleanup(self._restore_flag)
        self.tmp = tempfile.TemporaryDirectory(prefix="lot05j2_fake_")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.inputs = self.root / "inputs"
        self.inputs.mkdir()
        (self.inputs / "media-fake").mkdir()
        (self.inputs / "media-fake" / "a.fake").write_bytes(b"FAKE-DOC-A")
        (self.inputs / "media-fake" / "b.fake").write_bytes(b"FAKE-DOC-B")
        (self.inputs / "vault-fake.bin").write_bytes(b"FAKE-NON-SECRET-VAULT")
        self.key = secrets.token_hex(32)
        self.db_path = self.inputs / "source.db"
        self.source = j2._sqlcipher_conn(self.db_path, self.key)
        self.addCleanup(self.source.close)
        self.assertEqual(self.source.execute("PRAGMA journal_mode=WAL").fetchone()[0].lower(), "wal")
        self.source.execute("PRAGMA wal_autocheckpoint=0")
        self.source.execute("CREATE TABLE fake_truth (value TEXT NOT NULL)")
        self.source.execute("INSERT INTO fake_truth VALUES ('FAKE-COMMIT-1')")
        self.source.commit()
        self.assertTrue(Path(str(self.db_path) + "-wal").is_file())
        self.assertFalse(self.db_path.read_bytes().startswith(b"SQLite format 3\x00"))

    def _restore_flag(self):
        if self._flag is None:
            os.environ.pop("LOT05J2_NATIVE_SQLCIPHER_FAKE_ONLY", None)
        else:
            os.environ["LOT05J2_NATIVE_SQLCIPHER_FAKE_ONLY"] = self._flag

    def publish(self, **kwargs):
        return j2.fake_publish(self.root, self.source, owner=7, expected_owner=7, key=self.key, **kwargs)

    def current(self):
        return j2.fake_current(self.root, owner=7, key=self.key)

    def truth(self, path):
        with closing(j2._sqlcipher_conn(path, self.key)) as cn:
            return cn.execute("SELECT value FROM fake_truth").fetchone()[0]

    def test_01_wal_commit_is_preserved_by_true_sqlcipher_backup(self):
        self.publish()
        path, _ = self.current()
        self.assertEqual(self.truth(path / "snapshot.db"), "FAKE-COMMIT-1")
        self.assertTrue(Path(str(self.db_path) + "-wal").exists())
        self.assertFalse((path / "snapshot.db-wal").exists())
        self.assertFalse((path / "snapshot.db-shm").exists())

    def test_02_snapshot_remains_native_sqlcipher_encrypted(self):
        self.publish()
        path, _ = self.current()
        self.assertNotEqual((path / "snapshot.db").read_bytes()[:16], b"SQLite format 3\x00")

    def test_03_wrong_encryption_key_denies_snapshot_open(self):
        self.publish()
        with self.assertRaises(j2.J2Denied):
            j2.fake_current(self.root, owner=7, key=secrets.token_hex(32))

    def test_04_ciphertext_corruption_denies_generation(self):
        self.publish()
        directory, _ = self.current()
        path = directory / "snapshot.db"
        content = bytearray(path.read_bytes())
        content[-30] ^= 1
        path.write_bytes(content)
        with self.assertRaises(j2.J2Denied):
            self.current()

    def test_05_missing_or_modified_media_refused(self):
        self.publish()
        directory, _ = self.current()
        path = directory / "media-fake" / "a.fake"
        original = path.read_bytes()
        path.unlink()
        with self.assertRaises(j2.J2Denied):
            self.current()
        path.write_bytes(original + b"TAMPER")
        with self.assertRaises(j2.J2Denied):
            self.current()

    def test_06_unexpected_sidecar_or_file_is_refused(self):
        self.publish()
        directory, _ = self.current()
        (directory / "snapshot.db-wal").write_bytes(b"FAKE-EXTRA")
        with self.assertRaises(j2.J2Denied):
            self.current()

    def test_07_missing_wrong_bool_or_coercible_owner_refused(self):
        for owner in (None, 0, -1, True, False, "7", 7.0, 8):
            with self.subTest(owner=owner), self.assertRaises(j2.J2Denied):
                j2.fake_publish(self.root, self.source, owner=owner, expected_owner=7, key=self.key)
        self.assertFalse((self.root / "CURRENT.json").exists())

    def test_08_flag_off_or_invalid_key_rejected_before_mutation(self):
        os.environ["LOT05J2_NATIVE_SQLCIPHER_FAKE_ONLY"] = "0"
        with self.assertRaises(j2.J2Denied):
            self.publish()
        os.environ["LOT05J2_NATIVE_SQLCIPHER_FAKE_ONLY"] = "1"
        for key in (None, "abc", 4, "g" * 64):
            with self.subTest(key=key), self.assertRaises(j2.J2Denied):
                j2.fake_publish(self.root, self.source, owner=7, expected_owner=7, key=key)
        self.assertFalse((self.root / "CURRENT.json").exists())

    def test_09_failure_injections_do_not_publish_partial_snapshot(self):
        for phase in ("after_snapshot", "after_assets", "before_rename", "after_rename"):
            with self.subTest(phase=phase):
                with self.assertRaisesRegex(j2.J2Denied, "INJECTED"):
                    self.publish(fail_at=phase)
                self.assertFalse((self.root / "CURRENT.json").exists())
                self.assertFalse(list((self.root / "versions").glob(".stage-*")))

    def test_10_previous_generation_survives_failed_new_publish(self):
        first = self.publish()
        self.source.execute("UPDATE fake_truth SET value='FAKE-COMMIT-2'")
        self.source.commit()
        with self.assertRaisesRegex(j2.J2Denied, "INJECTED"):
            self.publish(fail_at="after_rename")
        directory, record = self.current()
        self.assertEqual(record, first)
        self.assertEqual(self.truth(directory / "snapshot.db"), "FAKE-COMMIT-1")

    def test_11_next_successful_generation_retains_old(self):
        first = self.publish()
        self.source.execute("UPDATE fake_truth SET value='FAKE-COMMIT-2'")
        self.source.commit()
        second = self.publish()
        self.assertNotEqual(first["generation"], second["generation"])
        self.assertEqual(self.truth(self.current()[0] / "snapshot.db"), "FAKE-COMMIT-2")
        self.assertEqual(self.truth(self.root / "versions" / first["generation"] / "snapshot.db"),
                         "FAKE-COMMIT-1")

    def test_12_clone_only_to_fresh_offline_directory(self):
        self.publish()
        target = self.root / "offline-recovery"
        out = j2.fake_clone(self.root, target, owner=7, key=self.key)
        self.assertEqual(self.truth(out / "snapshot.db"), "FAKE-COMMIT-1")
        with self.assertRaises(j2.J2Denied):
            j2.fake_clone(self.root, target, owner=7, key=self.key)

    def test_13_partial_clone_failure_cleans_new_destination(self):
        self.publish()
        target = self.root / "offline-recovery"
        def interrupted(_source, dest):
            dest.mkdir()
            (dest / "PARTIAL").write_bytes(b"INCOMPLETE")
            raise OSError("INJECTED_COPY")
        with patch.object(j2.shutil, "copytree", side_effect=interrupted):
            with self.assertRaisesRegex(OSError, "INJECTED_COPY"):
                j2.fake_clone(self.root, target, owner=7, key=self.key)
        self.assertFalse(target.exists())
        self.assertTrue(self.current()[0].is_dir())

    def test_14_windows_real_host_probe_never_authorizes_worker(self):
        data = j2.inspect_windows_boundary()
        self.assertEqual(data["os"], os.name)
        self.assertFalse(data["scm_service_attested"])
        self.assertFalse(data["clinical_apply_allowed"])
        self.assertEqual(data["whoami_observed"], os.name == "nt")

    def test_15_fake_ticket_flags_cannot_bypass_scm_veto(self):
        for flags in ({}, {"service_sid": "S-1-5-80-FAKE", "approved": True},
                      {"jwt_valid": True, "owner": 7}):
            with self.subTest(flags=flags), self.assertRaisesRegex(j2.J2Denied, "SCM_SERVICE_SID_NOT_ATTESTED"):
                j2.require_real_windows_worker_attestation(flags)

    def test_16_pointer_generation_path_traversal_fails(self):
        import json
        self.publish()
        pointer = self.root / "CURRENT.json"
        before = json.loads(pointer.read_text("utf-8"))
        before["generation"] = "../../different-owner"
        pointer.write_text(json.dumps(before))
        with self.assertRaises(j2.J2Denied):
            self.current()

    def test_17_stdlib_sqlite3_connection_refused_as_real_sqlcipher(self):
        with closing(sqlite3.connect(":memory:")) as plain:
            with self.assertRaises(j2.J2Denied):
                j2.fake_publish(self.root, plain, owner=7, expected_owner=7, key=self.key)
        self.assertFalse((self.root / "CURRENT.json").exists())

    def test_18_no_active_clinical_target_created_by_fake_generation(self):
        self.publish()
        self.assertFalse((self.root / "clinical_vault.db").exists())
        self.assertFalse((self.root / "media").exists())
        self.assertFalse((self.root / "license_vault.bin").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
