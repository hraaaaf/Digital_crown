"""Synthetic fixtures only; no device, patient or server access."""
import base64
import errno
import json
import sqlite3
from unittest.mock import patch
import hashlib
import zlib
import os
import subprocess
import shutil
import sys
from pathlib import Path
import tempfile
import unittest

from tools.imaging_gateway import Config, HotFolder, GatewayError
from tools.imaging_gateway.media_validation import valid_png


SYNTHETIC = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91Jpz"
    "AAAAFklEQVR4nGPkEpFjYGBgYmBgYGBgAAAC5gBAXKUgWwAAAABJRU5ErkJggg=="
)


class GatewayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        parent = Path(self.temp.name)
        self.watch, self.private = parent / "watch", parent / "private"
        self.watch.mkdir()
        self.config = Config("cabinet1", "device1", self.watch, self.private, b"k" * 32)
        self.agent = HotFolder(self.config)

    def stage(self, name="fixture.png", data=SYNTHETIC):
        (self.watch / name).write_bytes(data)
        self.assertEqual(self.agent.scan_once()["unstable"], 1)
        return self.agent.scan_once()

    def test_synthetic_queued_encrypted_and_not_patient_attached(self):
        self.assertEqual(self.stage()["staged"], 1)
        item = self.agent.items()[0]
        self.assertEqual(item["state"], "PENDING_CONFIRMATION")
        self.assertEqual(self.agent.read_verified(item["id"]), SYNTHETIC)
        self.assertNotIn(SYNTHETIC, next((self.private / "spool").iterdir()).read_bytes())
        self.assertEqual(self.agent.audit(item["id"]), ["PENDING_CONFIRMATION"])
        self.assertNotIn("patient_id", item)
        self.assertNotIn("appointment_id", item)

    def test_same_bytes_from_two_distinct_capture_files_stay_separate(self):
        (self.watch / "capture-1.png").write_bytes(SYNTHETIC)
        (self.watch / "capture-2.png").write_bytes(SYNTHETIC)
        self.assertEqual(self.agent.scan_once()["unstable"], 2)
        self.assertEqual(self.agent.scan_once()["staged"], 2)
        self.assertEqual(len(self.agent.items()), 2)
        self.assertNotEqual(self.agent.items()[0]["id"], self.agent.items()[1]["id"])
        self.assertTrue(all(x["state"] == "PENDING_CONFIRMATION" for x in self.agent.items()))

    def test_deduplicated_after_restart_without_another_blob_or_row(self):
        self.stage()
        self.assertEqual(self.agent.scan_once()["duplicate"], 1)
        restarted = HotFolder(self.config)
        self.assertEqual(restarted.scan_once()["unstable"], 1)
        self.assertEqual(restarted.scan_once()["duplicate"], 1)
        self.assertEqual(len(restarted.items()), 1)
        self.assertEqual(len(list((self.private / "spool").iterdir())), 1)

    def test_recapture_same_filename_and_bytes_is_not_dropped(self):
        self.stage()
        path = self.watch / "fixture.png"
        previous = path.stat()
        path.write_bytes(SYNTHETIC)
        os.utime(path, ns=(previous.st_atime_ns, previous.st_mtime_ns + 2_000_000_000))
        self.assertEqual(self.agent.scan_once()["unstable"], 1)
        self.assertEqual(self.agent.scan_once()["staged"], 1)
        self.assertEqual(len(self.agent.items()), 2)

    def test_corrupt_png_magic_and_truncated_png_are_quarantined(self):
        self.assertTrue(valid_png(SYNTHETIC))
        broken = b"\\x89PNG\\r\\n\\x1a\\n".decode("unicode_escape").encode("latin1") + b"invalid"
        self.assertFalse(valid_png(broken))
        self.assertFalse(valid_png(SYNTHETIC[:-9]))
        self.assertEqual(self.stage("fake.png", broken)["quarantine"], 1)
        self.assertEqual(self.agent.items()[0]["state"], "QUARANTINED")

    def test_png_oversized_dimensions_rejected_before_decompression(self):
        crafted = bytearray(SYNTHETIC)
        # IHDR width at byte 16. Recompute CRC to avoid merely testing CRC.
        crafted[16:20] = (1_000_000).to_bytes(4, "big")
        crafted[29:33] = zlib.crc32(b"IHDR" + crafted[16:29]).to_bytes(4, "big")
        self.assertFalse(valid_png(bytes(crafted)))
        self.assertEqual(self.stage("oversized.png", bytes(crafted))["quarantine"], 1)

    def test_unvalidated_jpeg_webp_pdf_are_not_accepted_by_magic_header(self):
        for extension, data in (
            ("jpg", bytes.fromhex("ffd8ff") + b"fakejpeg"),
            ("pdf", b"%PDF-1.7\\nnot-a-pdf"),
            ("webp", b"RIFF" + bytes.fromhex("04000000") + b"WEBPfake"),
        ):
            with self.subTest(extension=extension):
                with tempfile.TemporaryDirectory() as root:
                    watch, private = Path(root)/"watch", Path(root)/"private"
                    watch.mkdir()
                    worker = HotFolder(Config("strict", "station", watch, private, b"k"*32))
                    (watch / ("fake." + extension)).write_bytes(data)
                    worker.scan_once()
                    self.assertEqual(worker.scan_once()["quarantine"], 1)
                    self.assertEqual(worker.items()[0]["state"], "QUARANTINED")

    def test_wrong_extension_quarantined(self):
        self.assertEqual(self.stage("fixture.jpg")["quarantine"], 1)
        self.assertEqual(self.agent.items()[0]["state"], "QUARANTINED")

    def test_dicom_unknown_quarantined(self):
        self.assertEqual(self.stage("fixture.dcm", b"NOT_REAL_DICOM")["quarantine"], 1)
        with self.assertRaises(GatewayError):
            self.agent.record_transport_failure(1, 123)

    def test_changed_source_needs_another_stable_scan(self):
        file = self.watch / "fixture.png"
        file.write_bytes(SYNTHETIC)
        self.assertEqual(self.agent.scan_once()["unstable"], 1)
        # A structural validator correctly rejects trailing garbage; use a
        # valid PNG with a CRC-protected ancillary chunk instead.
        text_data = b"Comment" + bytes([0]) + b"SyntheticChange"
        chunk_type = b"tEXt"
        text_chunk = (len(text_data).to_bytes(4, "big") + chunk_type +
                      text_data + zlib.crc32(chunk_type + text_data).to_bytes(4, "big"))
        file.write_bytes(SYNTHETIC[:-12] + text_chunk + SYNTHETIC[-12:])
        self.assertEqual(self.agent.scan_once()["unstable"], 1)
        self.assertEqual(self.agent.scan_once()["staged"], 1)

    def test_abrupt_process_exit_replays_without_duplicate(self):
        (self.watch / "fixture.png").write_bytes(SYNTHETIC)
        script = (
            "import os,sys; from pathlib import Path; "
            "from tools.imaging_gateway import Config, HotFolder; "
            "a=HotFolder(Config('cabinet1','device1',Path(sys.argv[1]),"
            "Path(sys.argv[2]),b'k'*32)); a.scan_once(); a.scan_once(); os._exit(17)"
        )
        # A separate interpreter writes and exits without Python cleanup.
        result = subprocess.run(
            [sys.executable, "-c", script, str(self.watch), str(self.private)],
            cwd=Path(__file__).resolve().parents[3],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 17, result.stderr)
        recovered = HotFolder(self.config)
        self.assertEqual(recovered.scan_once()["unstable"], 1)
        self.assertEqual(recovered.scan_once()["duplicate"], 1)
        self.assertEqual(len(recovered.items()), 1)
        self.assertEqual(recovered.read_verified(1), SYNTHETIC)

    def test_retry_is_durable_bounded_and_does_not_confirm_server(self):
        self.stage()
        self.agent.record_transport_failure(1, 100)
        restarted = HotFolder(self.config)
        self.assertEqual(restarted.items()[0]["state"], "RETRY_PENDING")
        for i in range(6):
            restarted.record_transport_failure(1, 101 + i)
        self.assertEqual(restarted.items()[0]["state"], "BLOCKED")
        self.assertEqual(restarted.items()[0]["retries"], 7)
        with self.assertRaises(GatewayError):
            restarted.record_transport_failure(1, 300)

    def test_ciphertext_corruption_fails_closed(self):
        self.stage()
        spool = next((self.private / "spool").iterdir())
        spool.write_bytes(b"tampered")
        with self.assertRaises(GatewayError):
            self.agent.scan_once()

    def test_sqlite_precommit_boundary_abort_rolls_back(self):
        live_guard = self.agent._sqlite_guard
        calls = 0

        def fail_before_commit():
            nonlocal calls
            calls += 1
            if calls == 4:
                raise GatewayError("SYNTHETIC_GUARD_PRECOMMIT_DENIAL")
            return live_guard()

        with patch.object(self.agent, "_sqlite_guard", side_effect=fail_before_commit):
            with self.assertRaisesRegex(GatewayError, "PRECOMMIT_DENIAL"):
                with self.agent._db() as db:
                    db.execute("INSERT INTO audit(item_id,event,at) VALUES(0,?,1)",
                               ("SYNTHETIC_ROLLBACK",))
        self.assertEqual(calls, 4)
        self.assertEqual(self.agent.audit(0), [], "failed guard must not commit data")

    def test_successful_commit_has_no_fallible_postcommit_guard(self):
        with patch.object(self.agent, "_sqlite_guard",
                          wraps=self.agent._sqlite_guard) as watched:
            with self.agent._db() as db:
                db.execute("INSERT INTO audit(item_id,event,at) VALUES(0,?,1)",
                           ("SYNTHETIC_COMMIT",))
            self.assertEqual(watched.call_count, 4,
                             "must not raise after a durable SQLite commit")
        self.assertEqual(self.agent.audit(0), ["SYNTHETIC_COMMIT"])

    def test_sqlite_wal_full_sync_and_no_external_attachments(self):
        with self.agent._db() as db:
            self.assertEqual(db.execute("PRAGMA journal_mode").fetchone()[0].lower(), "wal")
            self.assertEqual(db.execute("PRAGMA synchronous").fetchone()[0], 2)
            self.assertEqual(db.execute("PRAGMA trusted_schema").fetchone()[0], 0)
            self.assertEqual(db.execute("PRAGMA temp_store").fetchone()[0], 2)
            self.assertEqual(len(db.execute("PRAGMA database_list").fetchall()), 1)

    def test_sqlite_wal_committed_row_recovers_after_abrupt_writer_exit(self):
        """Real separate Python process terminates without closing SQLite."""
        script = (
            "import os,sqlite3,sys;"
            "db=sqlite3.connect(sys.argv[1]);"
            "assert db.execute('PRAGMA journal_mode=WAL').fetchone()[0]=='wal';"
            "db.execute('INSERT INTO audit(item_id,event,at) VALUES(0,?,1)',"
            "('SYNTHETIC_WAL_CRASH_RECOVERY',));"
            "db.commit();os._exit(23)"
        )
        child = subprocess.run(
            [sys.executable, "-c", script, str(self.agent.db_file)],
            capture_output=True, timeout=6, check=False,
        )
        self.assertEqual(child.returncode, 23)
        self.assertIn("SYNTHETIC_WAL_CRASH_RECOVERY", self.agent.audit(0))
        self.assertEqual(self.agent.items(), [])
        # Reopening the same isolated CABINET/STATION is allowed; no
        # reconstructed patient attachment or duplicate image is created.
        restarted = HotFolder(self.config)
        self.assertEqual(restarted.audit(0), ["SYNTHETIC_WAL_CRASH_RECOVERY"])
        self.assertEqual(restarted.items(), [])

    def test_sqlite_hardlinked_database_is_refused_before_sql(self):
        outside = self.private.parent / "linked-acquisitions.sqlite3"
        os.link(self.agent.db_file, outside)
        try:
            with patch("tools.imaging_gateway.gateway.sqlite3.connect",
                       side_effect=AssertionError("untrusted db must never open")):
                with self.assertRaisesRegex(GatewayError, "SQLite LAB boundary rejected"):
                    self.agent.items()
        finally:
            outside.unlink()
        self.assertEqual(self.agent.items(), [])

    def test_sqlite_missing_database_cannot_be_silently_recreated(self):
        """After bootstrap, a missing SQLite file must never create blank state."""
        path = self.agent.db_file
        moved = self.private / "acquisitions.sqlite3-held"
        path.rename(moved)
        try:
            with self.assertRaisesRegex(GatewayError, "database identity changed"):
                self.agent.items()
            self.assertFalse(path.exists(), "missing DB must not be recreated")
        finally:
            moved.rename(path)
        self.assertEqual(self.agent.items(), [])

    def test_sqlite_existing_database_uses_no_create_uri(self):
        """Verify the actual sqlite3 connector uses mode=rw after bootstrap."""
        real_connect = sqlite3.connect
        observed = []
        def recorded_connect(*args, **kwargs):
            observed.append((str(args[0]), kwargs))
            return real_connect(*args, **kwargs)
        with patch("tools.imaging_gateway.gateway.sqlite3.connect",
                   side_effect=recorded_connect):
            self.assertEqual(self.agent.items(), [])
        self.assertEqual(len(observed), 1)
        self.assertTrue(observed[0][0].endswith("?mode=rw"))
        self.assertIs(observed[0][1].get("uri"), True)

    def test_sqlite_replaced_database_identity_is_refused(self):
        path = self.agent.db_file
        old = self.private / "acquisitions.sqlite3-original"
        path.rename(old)
        try:
            shutil.copyfile(old, path)
            with patch("tools.imaging_gateway.gateway.sqlite3.connect",
                       side_effect=AssertionError("replaced db must never open")):
                with self.assertRaisesRegex(GatewayError, "database identity changed"):
                    self.agent.items()
        finally:
            path.unlink()
            old.rename(path)
        self.assertEqual(self.agent.items(), [])

    def test_sqlite_wal_shm_journal_sidecars_symlinks_fail_closed(self):
        for suffix in ("-wal", "-shm", "-journal"):
            with self.subTest(suffix=suffix):
                sidecar = Path(str(self.agent.db_file) + suffix)
                outside = self.private.parent / ("outside" + suffix)
                outside.write_bytes(b"not-sqlite-or-patient-data")
                self.assertFalse(sidecar.exists(), "fixture must not replace existing sidecar")
                try:
                    sidecar.symlink_to(outside)
                except (NotImplementedError, OSError):
                    outside.unlink()
                    self.skipTest("file symlinks unavailable to this test account")
                try:
                    with patch("tools.imaging_gateway.gateway.sqlite3.connect",
                               side_effect=AssertionError("sidecar attack must not open db")):
                        with self.assertRaisesRegex(GatewayError, "SQLite LAB boundary rejected"):
                            self.agent.items()
                    self.assertEqual(outside.read_bytes(), b"not-sqlite-or-patient-data")
                finally:
                    sidecar.unlink()
                    outside.unlink()
        self.assertEqual(self.agent.items(), [])

    def test_sqlite_private_dir_replaced_rejected_before_connect(self):
        root = self.private
        previous = root.with_name("private-swap-saved")
        root.rename(previous)
        try:
            root.mkdir()
            with patch("tools.imaging_gateway.gateway.sqlite3.connect",
                       side_effect=AssertionError("swapped root must not open db")):
                with self.assertRaisesRegex(GatewayError, "root replaced or unsafe"):
                    self.agent.items()
            self.assertEqual(list(root.iterdir()), [])
        finally:
            root.rmdir()
            previous.rename(root)
        self.assertEqual(self.agent.items(), [])

    def test_cross_workstation_spool_read_fails(self):
        self.stage()
        with self.assertRaises(GatewayError):
            HotFolder(Config("cabinet1", "device2", self.watch, self.private, b"k" * 32))

    def test_configuration_and_symlink_rejection(self):
        with self.assertRaises(GatewayError):
            Config("cabinet1", "device1", self.watch, self.watch / "state", b"k" * 32)
        with self.assertRaises(GatewayError):
            Config("cabinet1", "device1", self.watch, self.private, b"short")
        if hasattr(os, "symlink"):
            outside = self.watch.parent / "outside.png"
            outside.write_bytes(SYNTHETIC)
            try:
                (self.watch / "link.png").symlink_to(outside)
            except OSError:
                return
            self.assertEqual(self.agent.scan_once()["rejected"], 1)
            self.assertEqual(self.agent.items(), [])

    @unittest.skipUnless(os.name == "nt", "Windows handle-anchored spool test")
    def test_windows_spool_write_rename_is_anchored_and_collision_safe(self):
        from tools.imaging_gateway.windows_scoped_spool_lab import write_ciphertext
        name = "a" * 64 + ".dc6"
        root = self.agent.spool
        identity = self.agent._windows_spool_identity
        write_ciphertext(root, name, b"ciphertext-fixture-only", identity)
        self.assertEqual((root / name).read_bytes(), b"ciphertext-fixture-only")
        with self.assertRaises(OSError):
            write_ciphertext(root, name, b"overwrite-must-fail", identity)
        self.assertEqual((root / name).read_bytes(), b"ciphertext-fixture-only")
        self.assertEqual(
            sorted(x.name for x in root.iterdir()), [name],
            "temp files must be cleaned after denied collision",
        )

    @unittest.skipUnless(os.name == "nt", "Windows handle-anchored spool test")
    def test_windows_spool_writer_rejects_replaced_directory_before_write(self):
        from tools.imaging_gateway.windows_scoped_spool_lab import write_ciphertext
        root = self.agent.spool
        previous = root.with_name("original-spool")
        root.rename(previous)
        try:
            root.mkdir()
            with self.assertRaises(OSError):
                write_ciphertext(
                    root, "b" * 64 + ".dc6", b"not-clinical-media",
                    self.agent._windows_spool_identity,
                )
            self.assertEqual(list(root.iterdir()), [])
            self.assertEqual(list(previous.iterdir()), [])
        finally:
            if root.exists():
                root.rmdir()
            previous.rename(root)

    @unittest.skipUnless(os.name == "nt", "NT-relative watch identity regression")
    def test_windows_nt_relative_open_rejects_swapped_root_before_read(self):
        from tools.imaging_gateway.windows_scoped_read_lab import open_relative_read
        original = self.watch.with_name("saved-watch")
        self.watch.rename(original)
        try:
            self.watch.mkdir()
            (self.watch / "malicious.png").write_bytes(SYNTHETIC)
            with self.assertRaises(OSError):
                open_relative_read(
                    self.watch, "malicious.png", self.agent._windows_watch_identity
                )
            # A replaced root must refuse *both* acquisition and ledger
            # access, not merely refuse reading the fake image.
            with self.assertRaisesRegex(GatewayError, "root replaced or unsafe"):
                self.agent.items()
        finally:
            if self.watch.exists():
                shutil.rmtree(self.watch)
            original.rename(self.watch)
        self.assertEqual(self.agent.items(), [])

    def test_root_replaced_during_capture_read_is_never_committed(self):
        file = self.watch / "fixture.png"
        file.write_bytes(SYNTHETIC)
        self.assertEqual(self.agent.scan_once()["unstable"], 1)
        moved = self.watch.with_name("watch-moved-during-capture")
        actual_read = self.agent._read

        def move_after_read(path, initial):
            content = actual_read(path, initial)
            self.watch.rename(moved)
            self.watch.mkdir()
            (self.watch / "fixture.png").write_bytes(SYNTHETIC)
            return content

        try:
            with patch.object(self.agent, "_read", side_effect=move_after_read):
                with self.assertRaisesRegex(GatewayError, "root replaced or unsafe"):
                    self.agent.scan_once()
            with self.assertRaisesRegex(GatewayError, "root replaced or unsafe"):
                self.agent.items()
        finally:
            if moved.exists():
                shutil.rmtree(self.watch)
                moved.rename(self.watch)
        self.assertEqual(self.agent.items(), [])

    def test_watch_directory_replaced_after_initialization_fails_closed(self):
        original = self.watch.parent / "watch-moved"
        self.watch.rename(original)
        try:
            try:
                self.watch.symlink_to(original, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("directory symlink creation unsupported")
            with self.assertRaisesRegex(GatewayError, "root replaced or unsafe"):
                self.agent.scan_once()
        finally:
            if self.watch.is_symlink():
                self.watch.unlink()
            original.rename(self.watch)

    def test_original_is_unchanged(self):
        self.stage()
        self.assertEqual((self.watch / "fixture.png").read_bytes(), SYNTHETIC)

    # LOT06-C: optional producer completion handshake (not an auth receipt).
    def enable_ready_mode(self):
        self.agent = HotFolder(Config(
            "cabinet1", "device1", self.watch, self.private, b"k" * 32,
            require_ready_manifest=True,
        ))

    def ready_marker(self, filename="fixture.png", payload=SYNTHETIC,
                     *, sha=None, size=None, extra=None):
        obj = {
            "version": 1,
            "sha256": sha if sha is not None else hashlib.sha256(payload).hexdigest(),
            "size": len(payload) if size is None else size,
        }
        if extra:
            obj.update(extra)
        marker = self.watch / (filename + ".ready")
        marker.write_text(json.dumps(obj), encoding="utf-8")
        return marker

    def test_ready_mode_requires_explicit_completion_marker(self):
        self.enable_ready_mode()
        (self.watch / "fixture.png").write_bytes(SYNTHETIC)
        self.assertEqual(self.agent.scan_once()["unstable"], 1)
        self.assertEqual(self.agent.scan_once()["unstable"], 1)
        self.assertEqual(self.agent.items(), [])
        marker = self.ready_marker()
        self.assertEqual(self.agent.scan_once()["staged"], 1)
        self.assertEqual(self.agent.scan_once()["duplicate"], 1)
        self.assertEqual(len(self.agent.items()), 1)
        self.assertEqual(self.agent.read_verified(1), SYNTHETIC)
        self.assertTrue(marker.exists())
        self.assertEqual((self.watch / "fixture.png").read_bytes(), SYNTHETIC)

    def test_ready_mode_duplicate_avoids_source_reads_and_spool_decrypt(self):
        self.enable_ready_mode()
        (self.watch / "fixture.png").write_bytes(SYNTHETIC)
        self.ready_marker()
        self.agent.scan_once()
        self.assertEqual(self.agent.scan_once()["staged"], 1)
        # The first capture was hashed and encrypted; subsequent polls should
        # use the SQLite receipt rather than rereading bytes + decrypting.
        with patch.object(self.agent, "_read", side_effect=AssertionError("repeat source read")), \
             patch.object(self.agent, "_decrypt", side_effect=AssertionError("repeat decrypt")):
            for _ in range(12):
                self.assertEqual(self.agent.scan_once()["duplicate"], 1)
        restarted = HotFolder(self.agent.config)
        self.assertEqual(restarted.scan_once()["unstable"], 1)
        with patch.object(restarted, "_read", side_effect=AssertionError("replay re-read")), \
             patch.object(restarted, "_decrypt", side_effect=AssertionError("replay decrypt")):
            self.assertEqual(restarted.scan_once()["duplicate"], 1)
        self.assertEqual(len(restarted.items()), 1)
        self.assertEqual(restarted.read_verified(1), SYNTHETIC)

    def test_ready_mode_does_not_quarantine_marker_as_media(self):
        self.enable_ready_mode()
        self.ready_marker()
        result = self.agent.scan_once()
        self.assertEqual(result, dict(staged=0, quarantine=0, duplicate=0, unstable=0, rejected=0, deferred=0))
        self.assertEqual(self.agent.items(), [])

    def test_incomplete_file_with_future_digest_never_staged(self):
        self.enable_ready_mode()
        (self.watch / "fixture.png").write_bytes(SYNTHETIC[:16])
        self.ready_marker()
        self.agent.scan_once()
        self.assertEqual(self.agent.scan_once()["unstable"], 1)
        self.assertEqual(self.agent.items(), [])
        (self.watch / "fixture.png").write_bytes(SYNTHETIC)
        self.assertEqual(self.agent.scan_once()["unstable"], 1)
        self.assertEqual(self.agent.scan_once()["staged"], 1)

    def test_incorrect_ready_sha_or_size_never_staged(self):
        self.enable_ready_mode()
        (self.watch / "fixture.png").write_bytes(SYNTHETIC)
        marker = self.ready_marker(sha="0" * 64)
        self.agent.scan_once()
        self.assertEqual(self.agent.scan_once()["unstable"], 1)
        self.assertEqual(self.agent.items(), [])
        self.ready_marker(size=len(SYNTHETIC) + 1)
        self.assertEqual(self.agent.scan_once()["unstable"], 1)
        self.assertEqual(self.agent.items(), [])
        self.ready_marker()
        self.assertEqual(self.agent.scan_once()["staged"], 1)
        self.assertTrue(marker.exists())

    def test_malformed_ready_json_and_unknown_fields_rejected(self):
        self.enable_ready_mode()
        (self.watch / "fixture.png").write_bytes(SYNTHETIC)
        marker = self.ready_marker()
        marker.write_text("{bad-json", encoding="utf-8")
        self.agent.scan_once()
        self.assertEqual(self.agent.scan_once()["unstable"], 1)
        self.ready_marker(extra={"patient_id": 111})
        self.assertEqual(self.agent.scan_once()["unstable"], 1)
        self.assertEqual(self.agent.items(), [])
        self.ready_marker()
        self.assertEqual(self.agent.scan_once()["staged"], 1)

    def test_manifest_replacement_during_capture_read_fails_closed(self):
        self.enable_ready_mode()
        (self.watch / "fixture.png").write_bytes(SYNTHETIC)
        marker = self.ready_marker()
        self.agent.scan_once()
        original_read = self.agent._read

        def replace_ready(path, initial):
            result = original_read(path, initial)
            marker.write_text(json.dumps({
                "version": 1, "sha256": "0" * 64, "size": len(result),
            }), encoding="utf-8")
            return result

        self.agent._read = replace_ready
        self.assertEqual(self.agent.scan_once()["unstable"], 1)
        self.assertEqual(self.agent.items(), [])
        self.agent._read = original_read
        self.ready_marker()
        self.assertEqual(self.agent.scan_once()["staged"], 1)

    def test_ready_marker_symlink_fails_closed(self):
        self.enable_ready_mode()
        (self.watch / "fixture.png").write_bytes(SYNTHETIC)
        valid = self.ready_marker("safe.png")
        link = self.watch / "fixture.png.ready"
        try:
            link.symlink_to(valid)
        except (OSError, NotImplementedError):
            self.skipTest("symlink unavailable on this Windows host")
        self.agent.scan_once()
        self.assertEqual(self.agent.scan_once()["unstable"], 1)
        self.assertEqual(self.agent.items(), [])

    def test_ready_mode_restart_and_replay_stays_local(self):
        self.enable_ready_mode()
        (self.watch / "fixture.png").write_bytes(SYNTHETIC)
        self.ready_marker()
        self.agent.scan_once()
        self.assertEqual(self.agent.scan_once()["staged"], 1)
        restarted = HotFolder(Config(
            "cabinet1", "device1", self.watch, self.private, b"k" * 32,
            require_ready_manifest=True,
        ))
        self.assertEqual(restarted.scan_once()["unstable"], 1)
        self.assertEqual(restarted.scan_once()["duplicate"], 1)
        self.assertEqual(len(restarted.items()), 1)
        self.assertEqual(restarted.items()[0]["state"], "PENDING_CONFIRMATION")

    def test_ready_mode_rejects_oversized_or_hardlinked_manifest(self):
        self.enable_ready_mode()
        (self.watch / "fixture.png").write_bytes(SYNTHETIC)
        marker = self.ready_marker()
        marker.write_bytes(b"X" * 300)
        self.agent.scan_once()
        self.assertEqual(self.agent.scan_once()["unstable"], 1)
        marker.unlink()
        outside = self.watch.parent / "outside-ready"
        self.ready_marker().replace(outside)
        try:
            os.link(outside, marker)
        except OSError:
            self.skipTest("hard links unavailable")
        self.assertEqual(self.agent.scan_once()["unstable"], 1)
        self.assertEqual(self.agent.items(), [])

    def test_untrusted_spool_size_rejected_before_read(self):
        self.stage()
        blob = next((self.private / "spool").glob("*.dc6"))
        with blob.open("wb") as output:
            output.truncate(self.config.max_bytes + 33)
        with self.assertRaises(GatewayError):
            self.agent.read_verified(1)

    # LOT06-D: no silent loss on quota, disk-full or an interrupted spool commit.
    def limited_agent(self, **policy):
        opts = dict(
            require_ready_manifest=False,
            max_spool_bytes=2 * 1024 ** 3,
            max_queue_items=1000,
            min_free_bytes=0,
        )
        opts.update(policy)
        return HotFolder(Config(
            "cabinet1", "device1", self.watch, self.private, b"k" * 32, **opts
        ))

    def test_spool_byte_cap_defers_without_deleting_original(self):
        limit = len(SYNTHETIC) + 32
        self.agent = self.limited_agent(max_spool_bytes=limit)
        self.assertEqual(self.stage("one.png")["staged"], 1)
        (self.watch / "two.png").write_bytes(SYNTHETIC)
        self.agent.scan_once()
        outcome = self.agent.scan_once()
        self.assertEqual(outcome["deferred"], 1)
        self.assertEqual(outcome["duplicate"], 1)
        self.assertEqual((self.watch / "two.png").read_bytes(), SYNTHETIC)
        self.assertEqual(len(self.agent.items()), 1)
        health = self.agent.storage_health()
        self.assertEqual(health["state"], "BACKPRESSURE")
        self.assertEqual(health["last_capacity_issue"], "SPOOL_BYTE_LIMIT")

    def test_queue_item_cap_defers_and_replays_existing_capture(self):
        self.agent = self.limited_agent(max_queue_items=1)
        self.stage("first.png")
        (self.watch / "second.png").write_bytes(SYNTHETIC)
        self.agent.scan_once()
        outcome = self.agent.scan_once()
        self.assertEqual(outcome["duplicate"], 1)
        self.assertEqual(outcome["deferred"], 1)
        self.assertEqual(len(self.agent.items()), 1)
        self.assertEqual(self.agent.storage_health()["last_capacity_issue"], "QUEUE_ITEM_LIMIT")

    def test_low_free_space_defers_then_recovers_with_original_intact(self):
        self.agent = self.limited_agent(min_free_bytes=64)
        source = self.watch / "fixture.png"
        source.write_bytes(SYNTHETIC)
        self.agent.scan_once()
        with patch("tools.imaging_gateway.gateway.shutil.disk_usage") as disk:
            disk.return_value.free = 0
            outcome = self.agent.scan_once()
            self.assertEqual(outcome["deferred"], 1)
        self.assertEqual(len(self.agent.items()), 0)
        self.assertEqual(source.read_bytes(), SYNTHETIC)
        self.assertEqual(self.agent.scan_once()["staged"], 1)

    def test_enospc_during_encrypted_write_preserves_source_and_no_row(self):
        self.agent = self.limited_agent()
        source = self.watch / "fixture.png"
        source.write_bytes(SYNTHETIC)
        self.agent.scan_once()
        # Test the actual platform-specific final-publish operation:
        # Windows uses an NT root-relative handle/rename, not os.replace.
        publish = ("tools.imaging_gateway.gateway.write_ciphertext"
                   if os.name == "nt" else "tools.imaging_gateway.gateway.os.replace")
        with patch(publish, side_effect=OSError(errno.ENOSPC, "synthetic disk full")):
            result = self.agent.scan_once()
        self.assertEqual(result["deferred"], 1)
        self.assertEqual(self.agent.storage_health()["last_capacity_issue"], "DISK_FULL")
        self.assertEqual(len(self.agent.items()), 0)
        self.assertEqual(list((self.private / "spool").iterdir()), [])
        self.assertEqual(source.read_bytes(), SYNTHETIC)
        self.assertEqual(self.agent.scan_once()["staged"], 1)

    def test_interrupted_after_ciphertext_rename_orphan_reused_at_quota(self):
        exact_bytes = len(SYNTHETIC) + 32
        self.agent = self.limited_agent(max_spool_bytes=exact_bytes)
        source = self.watch / "fixture.png"
        source.write_bytes(SYNTHETIC)
        self.agent.scan_once()
        real_store = self.agent._store

        def fail_after_rename(*args):
            real_store(*args)
            raise OSError(errno.ENOSPC, "synthetic disk full after rename")

        with patch.object(self.agent, "_store", side_effect=fail_after_rename):
            self.assertEqual(self.agent.scan_once()["deferred"], 1)
        self.assertEqual(len(self.agent.items()), 0)
        health = self.agent.storage_health()
        self.assertEqual(health["orphan_files"], 1)
        self.assertEqual(health["orphan_bytes"], exact_bytes)
        restarted = self.limited_agent(max_spool_bytes=exact_bytes)
        self.assertEqual(restarted.scan_once()["unstable"], 1)
        self.assertEqual(restarted.scan_once()["staged"], 1)
        self.assertEqual(restarted.read_verified(1), SYNTHETIC)
        self.assertEqual(restarted.storage_health()["orphan_files"], 0)
        self.assertEqual(len(list((self.private / "spool").iterdir())), 1)

    def test_untracked_partial_spool_counts_against_quota_no_auto_delete(self):
        self.agent = self.limited_agent(max_spool_bytes=len(SYNTHETIC) + 32)
        partial = self.private / "spool" / ".partial-interrupted"
        partial.write_bytes(b"X" * 64)
        self.assertEqual(self.stage()["deferred"], 1)
        h = self.agent.storage_health()
        self.assertEqual(h["orphan_files"], 1)
        self.assertEqual(h["orphan_bytes"], 64)
        self.assertTrue(partial.exists())
        partial.unlink()  # explicit operator cleanup, not agent deletion
        self.assertEqual(self.agent.scan_once()["staged"], 1)

    def test_new_capture_recovers_on_restart_after_increasing_budget(self):
        self.agent = self.limited_agent(max_queue_items=1)
        self.stage("first.png")
        (self.watch / "second.png").write_bytes(SYNTHETIC)
        self.agent.scan_once()
        self.assertEqual(self.agent.scan_once()["deferred"], 1)
        restarted = self.limited_agent(max_queue_items=2)
        self.assertEqual(restarted.scan_once()["unstable"], 2)
        self.assertEqual(restarted.scan_once()["staged"], 1)
        self.assertEqual(len(restarted.items()), 2)
        self.assertTrue(all(item["state"] == "PENDING_CONFIRMATION" for item in restarted.items()))

    def test_health_exposes_only_aggregate_counters_no_phi(self):
        self.agent = self.limited_agent()
        self.stage("secret_patient_name.png")
        health = self.agent.storage_health()
        exported = json.dumps(health)
        self.assertEqual(health["queued_items"], 1)
        self.assertIn("PENDING_CONFIRMATION", health["states"])
        self.assertNotIn("secret_patient_name", exported)
        self.assertNotIn("filename", exported)
        self.assertNotIn("patient_id", exported)
        self.assertNotIn(self.agent.items()[0]["digest"], exported)

    def test_invalid_capacity_configuration_rejected(self):
        for overrides in [
            {"max_spool_bytes": 0},
            {"max_spool_bytes": -1},
            {"max_queue_items": 0},
            {"max_queue_items": True},
            {"min_free_bytes": -1},
            {"min_free_bytes": False},
        ]:
            with self.subTest(overrides=overrides), self.assertRaises(GatewayError):
                self.limited_agent(**overrides)

    def test_unexpected_storage_error_propagates_without_false_success(self):
        self.agent = self.limited_agent()
        (self.watch / "fixture.png").write_bytes(SYNTHETIC)
        self.agent.scan_once()
        with patch.object(self.agent, "_store", side_effect=OSError(errno.EACCES, "denied")):
            with self.assertRaises(PermissionError):
                self.agent.scan_once()
        self.assertEqual(len(self.agent.items()), 0)
        self.assertEqual((self.watch / "fixture.png").read_bytes(), SYNTHETIC)

    def test_spool_symlink_entry_fails_closed(self):
        self.agent = self.limited_agent()
        external = self.private / "untrusted"
        external.write_bytes(b"X")
        link = self.private / "spool" / "untrusted.dc6"
        try:
            link.symlink_to(external)
        except (OSError, NotImplementedError):
            self.skipTest("symlink unavailable in this synthetic environment")
        (self.watch / "fixture.png").write_bytes(SYNTHETIC)
        self.agent.scan_once()
        with self.assertRaises(GatewayError):
            self.agent.scan_once()
        self.assertEqual(len(self.agent.items()), 0)
        self.assertTrue(link.is_symlink())

    def test_spool_iterator_closed_when_unsafe_entry_is_rejected(self):
        self.agent = self.limited_agent()
        self.stage()
        original = next((self.private / "spool").glob("*.dc6"))
        alias = self.private / "spool" / "unsafe-alias.dc6"
        try:
            os.link(original, alias)
        except (OSError, NotImplementedError):
            self.skipTest("hardlinks unavailable")
        if original.stat().st_nlink <= 1:
            self.skipTest("filesystem cannot report link count")

        real_scandir = os.scandir
        observed = []

        class TrackedScandir:
            def __init__(self, path):
                self.inner = real_scandir(path)
                self.closed = False
                observed.append(self)

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                self.closed = True
                self.inner.close()

            def __iter__(self):
                return iter(self.inner)

        with patch("tools.imaging_gateway.gateway.os.scandir", side_effect=TrackedScandir):
            with self.assertRaisesRegex(GatewayError, "unsafe spool entry"):
                self.agent.storage_health()
        self.assertTrue(observed, "scandir must have been called")
        self.assertTrue(all(item.closed for item in observed), "scandir must close on failure")

    def test_spool_hardlink_entry_rejected_where_link_count_reported(self):
        self.agent = self.limited_agent()
        self.stage()
        original = next((self.private / "spool").glob("*.dc6"))
        alias = self.private / "spool" / "alias.dc6"
        try:
            os.link(original, alias)
        except (OSError, NotImplementedError):
            self.skipTest("hardlinks unavailable")
        if original.stat().st_nlink <= 1:
            self.skipTest("this filesystem does not report hardlink count")
        with self.assertRaises(GatewayError):
            self.agent.storage_health()
        self.assertEqual((self.watch / "fixture.png").read_bytes(), SYNTHETIC)


if __name__ == "__main__":
    unittest.main()
