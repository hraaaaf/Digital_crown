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
        with patch("tools.imaging_gateway.gateway.os.replace",
                   side_effect=OSError(errno.ENOSPC, "synthetic disk full")):
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
