"""B-02 disposable LAB snapshots only: positive and hostile recovery oracles."""
import hashlib
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from tools.imaging_gateway import Config, HotFolder
from tools.imaging_gateway.owner_lock_lab import LabOwnerLock
from tools.imaging_gateway.p2_backup_lab import (
    B02SnapshotError, snapshot_quiescent_lab, verify_snapshot,
)
from tools.imaging_gateway.tests.test_gateway import SYNTHETIC


class B02QuiescentBackupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="dc-b02-lab-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "fixture"
        self.root.mkdir()
        (self.root / ".digitalcrown-imaging-lab-only").write_text(
            "DIGITALCROWN_IMAGING_LAB_ONLY_V1\n", encoding="utf-8")
        self.watch = self.root / "incoming"
        self.watch.mkdir()
        self.private = self.root / "private"
        self.key = b"Q" * 32
        self.collector = HotFolder(Config(
            "lab_cabinet", "lab_station", self.watch, self.private, self.key))
        (self.watch / "fixture.png").write_bytes(SYNTHETIC)
        self.assertEqual(self.collector.scan_once()["unstable"], 1)
        self.assertEqual(self.collector.scan_once()["staged"], 1)
        self.item = self.collector.items()[0]
        self.destination = self.root / "snapshots" / "verified_backup"

    def test_quiescent_snapshot_restores_complete_state(self):
        snapshot = snapshot_quiescent_lab(self.root, self.destination, self.key)
        self.assertEqual(snapshot, self.destination)
        self.assertTrue(verify_snapshot(snapshot, self.key))
        self.assertFalse((snapshot / "key.bin").exists())
        self.assertNotIn(self.key.hex().encode(), (snapshot / "manifest.json").read_bytes())
        recovered = self.root / "recovered"
        shutil.copytree(snapshot, recovered)
        restarted = HotFolder(Config(
            "lab_cabinet", "lab_station", self.watch, recovered, self.key))
        self.assertEqual(restarted.items(), [self.item])
        self.assertEqual(restarted.read_verified(self.item["id"]), SYNTHETIC)

    def test_active_bridge_owner_refuses_backup_without_publishing(self):
        with LabOwnerLock.acquire(self.root):
            with self.assertRaisesRegex(B02SnapshotError, "B02_ACTIVE_BRIDGE"):
                snapshot_quiescent_lab(self.root, self.destination, self.key)
        self.assertFalse(self.destination.exists())
        self.assertTrue(verify_snapshot(
            snapshot_quiescent_lab(self.root, self.destination, self.key),
            self.key))

    def test_interrupted_copy_never_publishes_incomplete_archive(self):
        with patch("tools.imaging_gateway.p2_backup_lab.shutil.copytree",
                   side_effect=OSError("synthetic-copy-interrupted")):
            with self.assertRaises(OSError):
                snapshot_quiescent_lab(self.root, self.destination, self.key)
        self.assertFalse(self.destination.exists())
        self.assertEqual(list((self.root / "snapshots").iterdir()), [])
        self.assertEqual(self.collector.read_verified(self.item["id"]), SYNTHETIC)

    def test_noncooperative_spool_mutation_during_copy_is_detected(self):
        original_copy = shutil.copytree
        blob = next((self.private / "spool").glob("*.dc6"))
        previous = blob.read_bytes()

        def mutate_after_copy(src, dst, *args, **kwargs):
            result = original_copy(src, dst, *args, **kwargs)
            altered = bytearray(previous)
            altered[-1] ^= 1
            blob.write_bytes(altered)
            return result

        with patch("tools.imaging_gateway.p2_backup_lab.shutil.copytree",
                   side_effect=mutate_after_copy):
            with self.assertRaisesRegex(B02SnapshotError, "B02_SOURCE_CHANGED"):
                snapshot_quiescent_lab(self.root, self.destination, self.key)
        self.assertFalse(self.destination.exists())
        self.assertEqual(list((self.root / "snapshots").iterdir()), [])

    def test_direct_ledger_write_during_copy_is_detected(self):
        """Non-cooperating SQLite writes must not yield a published archive."""
        original_copy = shutil.copytree

        def mutate_ledger_after_copy(src, dst, *args, **kwargs):
            result = original_copy(src, dst, *args, **kwargs)
            self.collector.record_transport_failure(self.item["id"], 123)
            return result

        with patch("tools.imaging_gateway.p2_backup_lab.shutil.copytree",
                   side_effect=mutate_ledger_after_copy):
            with self.assertRaisesRegex(B02SnapshotError, "B02_LEDGER_CHANGED"):
                snapshot_quiescent_lab(self.root, self.destination, self.key)
        self.assertFalse(self.destination.exists())
        self.assertEqual(list((self.root / "snapshots").iterdir()), [])

    def test_manifest_tamper_or_wrong_key_fails_verification(self):
        archive = snapshot_quiescent_lab(self.root, self.destination, self.key)
        with self.assertRaisesRegex(B02SnapshotError, "B02_MANIFEST_AUTH"):
            verify_snapshot(archive, b"Z" * 32)
        content = (archive / "manifest.json").read_bytes()
        (archive / "manifest.json").write_bytes(content + b" ")
        with self.assertRaisesRegex(B02SnapshotError, "B02_MANIFEST_AUTH"):
            verify_snapshot(archive, self.key)

    def test_incomplete_private_source_or_outside_destination_rejected(self):
        with self.assertRaisesRegex(B02SnapshotError, "B02_DESTINATION"):
            snapshot_quiescent_lab(
                self.root, self.root.parent / "elsewhere", self.key)
        (self.private / ".acquisitions-initialized-v1").unlink()
        with self.assertRaisesRegex(B02SnapshotError, "B02_SOURCE_INCOMPLETE"):
            snapshot_quiescent_lab(self.root, self.destination, self.key)
        self.assertFalse(self.destination.exists())


if __name__ == "__main__":
    unittest.main()
