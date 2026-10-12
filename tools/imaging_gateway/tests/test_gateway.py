"""Synthetic fixtures only; no device, patient or server access."""
import os
from pathlib import Path
import tempfile
import unittest

from tools.imaging_gateway import Config, HotFolder, GatewayError


SYNTHETIC = b"\x89PNG\r\n\x1a\nsynthetic-no-real-patient"


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

    def test_deduplicated_after_restart_without_another_blob_or_row(self):
        self.stage()
        self.assertEqual(self.agent.scan_once()["duplicate"], 1)
        restarted = HotFolder(self.config)
        self.assertEqual(restarted.scan_once()["unstable"], 1)
        self.assertEqual(restarted.scan_once()["duplicate"], 1)
        self.assertEqual(len(restarted.items()), 1)
        self.assertEqual(len(list((self.private / "spool").iterdir())), 1)

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
        wrong = HotFolder(Config("cabinet1", "device2", self.watch, self.private, b"k" * 32))
        with self.assertRaises(GatewayError):
            wrong.read_verified(1)

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


if __name__ == "__main__":
    unittest.main()
