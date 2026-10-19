"""LOT05.7-J deterministic FAKE-only fail-closed restoration regressions."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.core.paths import AppPaths
from backend.services.guided_restore import GuidedRestoreService
from backend.services.guided_restore_worker import GuidedRestoreWorker
from backend.services.legacy_migration_safe_restore_lab_v15 import (
    FakeRecoveryDenied, clone_current_into_new_fake_dir,
    publish_fake_snapshot, read_fake_current,
)


class SafeFakeRecoveryLab(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="lot05j_fake_")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.inputs = self.root / "inputs"
        self.inputs.mkdir()
        (self.inputs / "media-fake").mkdir()
        (self.inputs / "license_fake.bin").write_bytes(b"FAKE-VAULT-NO-SECRETS")
        (self.inputs / "media-fake" / "scan.fake").write_bytes(b"FAKE-SCAN")
        (self.inputs / "media-fake" / "invoice.fake").write_bytes(b"FAKE-INVOICE")
        self.db = self.inputs / "clinical.db"
        self.cn = sqlite3.connect(str(self.db))
        self.addCleanup(self.cn.close)
        self.assertEqual(self.cn.execute("PRAGMA journal_mode=WAL").fetchone()[0].lower(), "wal")
        self.cn.execute("PRAGMA wal_autocheckpoint=0")
        self.cn.execute("CREATE TABLE truth (v TEXT NOT NULL)")
        self.cn.execute("INSERT INTO truth VALUES ('committed-v1')")
        self.cn.commit()
        self.assertTrue(Path(str(self.db) + "-wal").is_file())

    def publish(self, **kwargs):
        return publish_fake_snapshot(
            self.root, self.cn, request_owner=7, expected_owner=7, **kwargs)

    def current(self):
        return read_fake_current(self.root, request_owner=7, expected_owner=7)

    def _value(self, db):
        with sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True) as conn:
            return conn.execute("SELECT v FROM truth").fetchone()[0]

    def test_01_real_sqlite_wal_commit_is_captured_and_cloned(self):
        self.publish()
        directory, _ = self.current()
        self.assertEqual(self._value(directory / "snapshot.db"), "committed-v1")
        destination = clone_current_into_new_fake_dir(
            self.root, self.root / "isolated-recovery", request_owner=7, expected_owner=7)
        self.assertEqual(self._value(destination / "snapshot.db"), "committed-v1")
        self.assertTrue(Path(str(self.db) + "-wal").exists())

    def test_02_no_missing_wrong_or_coercible_owner_can_publish(self):
        for value in (None, 0, -1, True, False, "7", 7.0, 8):
            with self.subTest(value=value):
                with self.assertRaises(FakeRecoveryDenied):
                    publish_fake_snapshot(self.root, self.cn, request_owner=value, expected_owner=7)
                self.assertFalse((self.root / "CURRENT.json").exists())

    def test_03_expected_owner_must_be_explicit_not_forced(self):
        for value in (None, True, "7", 8):
            with self.subTest(value=value), self.assertRaises(FakeRecoveryDenied):
                publish_fake_snapshot(self.root, self.cn, request_owner=7, expected_owner=value)

    def test_04_all_staging_crashes_leave_current_unpublished(self):
        for phase in ("after_db", "after_media", "before_publish", "after_generation"):
            with self.subTest(phase=phase):
                with self.assertRaisesRegex(FakeRecoveryDenied, "INJECTED"):
                    self.publish(fail_at=phase)
                self.assertFalse((self.root / "CURRENT.json").exists())
                self.assertFalse(list((self.root / "generations").glob(".stage-*")))

    def test_05_second_generation_failure_keeps_previous_generation(self):
        self.publish()
        old_dir, old_ptr = self.current()
        self.cn.execute("UPDATE truth SET v='committed-v2'")
        self.cn.commit()
        with self.assertRaises(FakeRecoveryDenied):
            self.publish(fail_at="after_generation")
        self.assertEqual(self.current()[1], old_ptr)
        self.assertEqual(self._value(old_dir / "snapshot.db"), "committed-v1")

    def test_06_successful_next_generation_has_verified_new_pointer(self):
        first = self.publish()
        self.cn.execute("UPDATE truth SET v='committed-v2'")
        self.cn.commit()
        second = self.publish()
        self.assertNotEqual(first["generation"], second["generation"])
        self.assertEqual(self._value(self.current()[0] / "snapshot.db"), "committed-v2")
        self.assertEqual(self._value(self.root / "generations" / first["generation"] / "snapshot.db"),
                         "committed-v1")

    def test_07_tampered_snapshot_refused_before_clone(self):
        self.publish()
        directory, _ = self.current()
        (directory / "snapshot.db").write_bytes(b"CORRUPT")
        with self.assertRaises(FakeRecoveryDenied):
            self.current()
        with self.assertRaises(FakeRecoveryDenied):
            clone_current_into_new_fake_dir(
                self.root, self.root / "isolated-recovery", request_owner=7, expected_owner=7)
        self.assertFalse((self.root / "isolated-recovery").exists())

    def test_08_modified_fake_media_or_vault_refused(self):
        for name in ("media-fake/scan.fake", "license_fake.bin"):
            with self.subTest(name=name):
                self.publish()
                directory, _ = self.current()
                path = directory / name
                original = path.read_bytes()
                path.write_bytes(b"TAMPERED")
                with self.assertRaises(FakeRecoveryDenied):
                    self.current()
                path.write_bytes(original)

    def test_09_incomplete_new_bundle_does_not_replace_old_pointer(self):
        self.publish()
        before = self.current()[1]
        (self.inputs / "license_fake.bin").unlink()
        with self.assertRaises((FakeRecoveryDenied, FileNotFoundError)):
            self.publish()
        self.assertEqual(self.current()[1], before)

    def test_10_forged_pointer_or_incomplete_generation_is_denied(self):
        self.publish()
        p = self.root / "CURRENT.json"
        saved = p.read_bytes()
        p.write_text('{"version":1,"owner":7,"generation":"../../escape","manifest":{}}')
        with self.assertRaises(FakeRecoveryDenied):
            self.current()
        p.write_bytes(saved)
        self.assertTrue(self.current()[0].is_dir())

    def test_11_cloning_must_not_replace_existing_destination(self):
        self.publish()
        destination = self.root / "isolated-recovery"
        destination.mkdir()
        marker = destination / "NEVER_REPLACE.txt"
        marker.write_text("untouched")
        with self.assertRaises(FakeRecoveryDenied):
            clone_current_into_new_fake_dir(
                self.root, destination, request_owner=7, expected_owner=7)
        self.assertEqual(marker.read_text(), "untouched")

    def test_12_root_link_denied_cross_platform_without_privileged_symlink(self):
        original = Path.is_symlink
        with patch.object(Path, "is_symlink", lambda path: path == self.root or original(path)):
            with self.assertRaisesRegex(FakeRecoveryDenied, "SYNTHETIC_ROOT_REQUIRED"):
                self.publish()

    def test_13_actual_owner_helper_denies_missing_bool_str_cross_tenant(self):
        job = {"restore_id": "f" * 32, "owner_employer_id": 7}
        GuidedRestoreService._assert_owner(job, 7)
        for identity in (None, False, True, 0, -1, "7", 7.0, 8):
            with self.subTest(identity=identity), self.assertRaises(PermissionError):
                GuidedRestoreService._assert_owner(job, identity)
        with self.assertRaises(PermissionError):
            GuidedRestoreService._assert_owner({"owner_employer_id": "7"}, 7)

    def test_14_true_detached_worker_denies_before_job_or_file_activity(self):
        marker = self.root / "clinical_vault.db"
        marker.write_bytes(b"FAKE-ACTIVE-KEEP")
        with self.assertRaisesRegex(RuntimeError, "worker non attesté"):
            GuidedRestoreWorker.run("nonexistent", parent_pid=999)
        self.assertEqual(marker.read_bytes(), b"FAKE-ACTIVE-KEEP")
        self.assertFalse((self.root / "guided-restore").exists())

    def test_15_true_request_apply_refuses_even_if_runtime_claims_supported(self):
        # All inputs and job files are fake; no process can be launched.
        with patch.object(AppPaths, "get_user_data_dir", return_value=self.root):
            job_id = "a" * 32
            job_dir = GuidedRestoreService.job_dir(job_id)
            job_dir.mkdir(parents=True, exist_ok=True)
            source = job_dir / "source.upload"
            encrypted = job_dir / "database.enc"
            source.write_bytes(b"FAKE-ARCHIVE")
            encrypted.write_bytes(b"FAKE-ENCRYPTED-BACKUP")
            checksum = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
            job = {"restore_id": job_id, "owner_employer_id": 7, "status": "prepared",
                   "compatible": True, "restore_media": False,
                   "source_sha256": checksum(source), "database_sha256": checksum(encrypted)}
            GuidedRestoreService._write_job(job)
            with patch.object(GuidedRestoreService, "runtime_apply_supported", return_value=True), \
                 patch.object(GuidedRestoreService, "_launch_detached_worker",
                              side_effect=AssertionError("WORKER_MUST_NOT_LAUNCH")):
                with self.assertRaisesRegex(RuntimeError, "autorité worker non attestée"):
                    GuidedRestoreService.request_apply(job_id, "RESTAURER", owner_employer_id=7)
            self.assertEqual(GuidedRestoreService.get_job(job_id)["status"], "prepared")
            self.assertFalse((job_dir / "rescue").exists())


    def test_16_injected_partial_clone_copy_failure_leaves_no_destination(self):
        import backend.services.legacy_migration_safe_restore_lab_v15 as lab
        self.publish()
        target = self.root / "isolated-recovery"

        def fail_after_partial_copy(_src, dst):
            dst.mkdir()
            (dst / "INCOMPLETE").write_bytes(b"PARTIAL-NEVER-ACCEPT")
            raise OSError("INJECTED_COPY_INTERRUPTION")

        with patch.object(lab.shutil, "copytree", side_effect=fail_after_partial_copy):
            with self.assertRaisesRegex(OSError, "INJECTED_COPY_INTERRUPTION"):
                clone_current_into_new_fake_dir(
                    self.root, target, request_owner=7, expected_owner=7)
        self.assertFalse(target.exists())
        self.assertTrue(self.current()[0].is_dir())


if __name__ == "__main__":
    unittest.main(verbosity=2)
