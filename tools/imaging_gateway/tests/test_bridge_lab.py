"""LAB-only background worker contract: no hardware or patient access."""
import asyncio
import ast
import base64
import hashlib
import json
import os
import sqlite3
from pathlib import Path
import tempfile
import unittest

from tools.imaging_gateway.bridge_background_lab import (
    BridgeLabConfigurationError, lab_requested, make_lab_collector,
    poll_lab_collector, start_if_enabled, stop_bridge_lab,
)

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91Jpz"
    "AAAAFklEQVR4nGPkEpFjYGBgYmBgYGBgAAAC5gBAXKUgWwAAAABJRU5ErkJggg=="
)


def mark_complete(photo: Path, content: bytes) -> None:
    marker = photo.with_name(photo.name + ".ready")
    marker.write_text(json.dumps({
        "version": 1, "size": len(content), "sha256": hashlib.sha256(content).hexdigest()
    }), encoding="utf-8")


class BridgeLabConfigTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / ".digitalcrown-imaging-lab-only").write_text(
            "DIGITALCROWN_IMAGING_LAB_ONLY_V1\n", encoding="utf-8")
        (self.root / "incoming").mkdir()
        self.env = {
            "DC_V15_06_BRIDGE_LAB": "1",
            "ENVIRONMENT": "test",
            "DIGITALCROWN_ISOLATED_RUNTIME": "true",
            "DC_V15_06_BRIDGE_LAB_ROOT": str(self.root),
            "DC_V15_06_BRIDGE_LAB_KEY_HEX": (b"k" * 32).hex(),
        }

    def test_default_runtime_does_not_import_optional_lab_tooling(self):
        # Small CI runners do not ship the entire clinical backend dependencies.
        # Check the actual lifespan source: optional module must be guarded by
        # a positive LAB switch, not imported during ordinary cabinet startup.
        source = (Path(__file__).resolve().parents[3] / "backend" / "main.py").read_text(
            encoding="utf-8")
        tree = ast.parse(source)
        imports = [(n, p) for p in ast.walk(tree)
                   if isinstance(p, ast.If) for n in p.body
                   if isinstance(n, ast.ImportFrom)
                   and n.module == "tools.imaging_gateway.bridge_background_lab"]
        self.assertEqual(len(imports), 1)
        for _, conditional in imports:
            self.assertIn("DC_V15_06_BRIDGE_LAB", ast.unparse(conditional.test))

    def test_disabled_by_default_has_no_collector(self):
        self.assertFalse(lab_requested({}))
        self.assertIsNone(make_lab_collector({}))
        self.assertFalse((self.root / "private").exists())

    def test_rejects_production_even_if_switch_was_set(self):
        with self.assertRaisesRegex(BridgeLabConfigurationError, "TEST_ISOLATION_REQUIRED"):
            make_lab_collector({**self.env, "ENVIRONMENT": "cabinet"})
        self.assertFalse((self.root / "private").exists())

    def test_rejects_mismatched_backend_environment(self):
        with self.assertRaisesRegex(BridgeLabConfigurationError, "BACKEND_TEST_REQUIRED"):
            start_if_enabled(self.env, trusted_environment="cabinet")
        self.assertFalse((self.root / "private").exists())

    def test_rejects_nonisolated_test(self):
        with self.assertRaises(BridgeLabConfigurationError):
            make_lab_collector({**self.env, "DIGITALCROWN_ISOLATED_RUNTIME": "false"})

    @unittest.skipUnless(os.name == "nt", "Windows case-insensitive temp path proof")
    def test_windows_temp_directory_case_alias_is_accepted(self):
        alias = self.root.with_name(self.root.name.swapcase())
        self.assertTrue(alias.exists(), "fixture must be on case-insensitive Windows volume")
        collector = make_lab_collector({
            **self.env, "DC_V15_06_BRIDGE_LAB_ROOT": str(alias),
        })
        self.assertEqual(collector.items(), [])

    def test_rejects_missing_marker(self):
        (self.root / ".digitalcrown-imaging-lab-only").unlink()
        with self.assertRaises(BridgeLabConfigurationError):
            make_lab_collector(self.env)

    def test_rejects_non_temp_and_relative_roots(self):
        for root in ("relative/path", str(Path(self.tmp.name).parent)):
            with self.subTest(root=root), self.assertRaises(BridgeLabConfigurationError):
                make_lab_collector({**self.env, "DC_V15_06_BRIDGE_LAB_ROOT": root})

    def test_rejects_missing_or_malformed_key(self):
        for key in ("", "z" * 64):
            with self.subTest(key=key[:3]), self.assertRaises(BridgeLabConfigurationError):
                make_lab_collector({**self.env, "DC_V15_06_BRIDGE_LAB_KEY_HEX": key})

    def test_real_synthetic_collector_stages_without_patient_binding(self):
        collector = make_lab_collector(self.env)
        photo = self.root / "incoming" / "fake_photo.png"
        photo.write_bytes(PNG)
        mark_complete(photo, PNG)
        self.assertEqual(collector.scan_once()["unstable"], 1)
        self.assertEqual(collector.scan_once()["staged"], 1)
        items = collector.items()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["state"], "PENDING_CONFIRMATION")
        self.assertNotIn("patient_id", items[0])
        self.assertEqual(photo.read_bytes(), PNG)
        self.assertNotIn(PNG, next((self.root / "private" / "spool").iterdir()).read_bytes())

    def test_unfinished_photo_is_never_staged(self):
        collector = make_lab_collector(self.env)
        photo = self.root / "incoming" / "fake_photo.png"
        photo.write_bytes(PNG)
        collector.scan_once()
        self.assertEqual(collector.scan_once()["staged"], 0)
        self.assertEqual(collector.items(), [])
        # Even with a completion claim, a corrupt hash must never be accepted.
        mark_complete(photo, PNG + b"mismatch")
        self.assertEqual(collector.scan_once()["staged"], 0)
        self.assertEqual(collector.items(), [])
        mark_complete(photo, PNG)
        self.assertEqual(collector.scan_once()["staged"], 1)
        self.assertEqual(len(collector.items()), 1)

    def test_invalid_media_is_quarantined_not_confirmed(self):
        collector = make_lab_collector(self.env)
        photo = self.root / "incoming" / "fake_photo.png"
        invalid = b"invalid synthetic data"
        photo.write_bytes(invalid)
        mark_complete(photo, invalid)
        collector.scan_once()
        self.assertEqual(collector.scan_once()["quarantine"], 1)
        self.assertEqual(collector.items()[0]["state"], "QUARANTINED")


class BridgeLabRuntimeTests(unittest.IsolatedAsyncioTestCase):
    async def test_background_worker_runs_and_stops_without_separate_process(self):
        class Collector:
            ticks = 0
            def scan_once(self):
                self.ticks += 1
                return {"staged": 0}
        collector = Collector()
        stop = asyncio.Event()
        task = asyncio.create_task(poll_lab_collector(collector, stop, interval=0.01))
        await asyncio.wait_for(self._until(lambda: collector.ticks >= 2), timeout=3)
        stop.set()
        await asyncio.wait_for(task, timeout=3)
        last = collector.ticks
        await asyncio.sleep(0.04)
        self.assertEqual(collector.ticks, last)

    async def test_real_lab_background_stages_without_patient_or_server(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".digitalcrown-imaging-lab-only").write_text(
                "DIGITALCROWN_IMAGING_LAB_ONLY_V1\n", encoding="utf-8")
            incoming = root / "incoming"
            incoming.mkdir()
            photo = incoming / "fictitious.png"
            photo.write_bytes(PNG)
            mark_complete(photo, PNG)
            env = {
                "DC_V15_06_BRIDGE_LAB": "1",
                "ENVIRONMENT": "test",
                "DIGITALCROWN_ISOLATED_RUNTIME": "true",
                "DC_V15_06_BRIDGE_LAB_ROOT": str(root),
                "DC_V15_06_BRIDGE_LAB_KEY_HEX": (b"k" * 32).hex(),
            }
            handle = start_if_enabled(env, trusted_environment="test")
            self.assertIsNotNone(handle)
            db_path = root / "private" / "acquisitions.sqlite3"
            try:
                async def was_staged():
                    while True:
                        with sqlite3.connect(db_path) as db:
                            row = db.execute("SELECT state FROM items").fetchone()
                        if row is not None:
                            self.assertEqual(row[0], "PENDING_CONFIRMATION")
                            return
                        await asyncio.sleep(0.05)
                await asyncio.wait_for(was_staged(), timeout=8)
            finally:
                await stop_bridge_lab(handle)
            self.assertTrue(handle.task.done())
            self.assertEqual(photo.read_bytes(), PNG)
            with sqlite3.connect(db_path) as db:
                self.assertEqual(db.execute("SELECT COUNT(*) FROM items").fetchone()[0], 1)

    async def test_start_is_silent_when_not_requested(self):
        self.assertIsNone(start_if_enabled({}))

    async def test_failure_is_private_and_retry_does_not_create_confirmation(self):
        class BadCollector:
            ticks = 0
            def scan_once(self):
                self.ticks += 1
                raise RuntimeError("PATIENT_PERSONAL_SECRET_FILENAME")
        collector = BadCollector()
        stop = asyncio.Event()
        with self.assertLogs("tools.imaging_gateway.bridge_background_lab", level="WARNING") as logs:
            task = asyncio.create_task(poll_lab_collector(collector, stop, interval=0.01))
            await asyncio.wait_for(self._until(lambda: collector.ticks >= 2), timeout=3)
            stop.set()
            await task
        self.assertNotIn("PATIENT_PERSONAL_SECRET_FILENAME", " ".join(logs.output))
        self.assertTrue(all("not confirmed" in line for line in logs.output))

    @staticmethod
    async def _until(predicate):
        while not predicate():
            await asyncio.sleep(0.01)


if __name__ == "__main__":
    unittest.main()
