"""Synthetic fixtures only; no device, patient or server access."""
import base64
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest

from tools.imaging_gateway import Config, HotFolder, GatewayError


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
        file.write_bytes(SYNTHETIC + b"-changed")
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

    def test_ready_mode_does_not_quarantine_marker_as_media(self):
        self.enable_ready_mode()
        self.ready_marker()
        result = self.agent.scan_once()
        self.assertEqual(result, dict(staged=0, quarantine=0, duplicate=0, unstable=0, rejected=0))
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


if __name__ == "__main__":
    unittest.main()
