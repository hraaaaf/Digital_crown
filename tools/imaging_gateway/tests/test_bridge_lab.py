"""LAB-only background worker contract: no hardware or patient access."""
import asyncio
from contextlib import closing
import ast
import base64
import hashlib
import json
import os
import sqlite3
import threading
import time
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

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
        module = "tools.imaging_gateway.bridge_background_lab"
        imports = [alias.name for node in ast.walk(tree)
                   if isinstance(node, ast.ImportFrom) and node.module == module
                   for alias in node.names]
        self.assertCountEqual(imports, ["start_if_enabled", "stop_bridge_lab"])
        # Start must be guarded by an explicit opt-in, and shutdown must
        # require an existing handle. Both imports are intentionally present.
        start_guards = [node for node in ast.walk(tree)
                        if isinstance(node, ast.If)
                        and "DC_V15_06_BRIDGE_LAB" in ast.unparse(node.test)
                        and any(isinstance(stmt, ast.ImportFrom) and stmt.module == module
                                and any(a.name == "start_if_enabled" for a in stmt.names)
                                for stmt in node.body)]
        stop_guards = [node for node in ast.walk(tree)
                       if isinstance(node, ast.If)
                       and "imaging_bridge_lab_handle is not None" in ast.unparse(node.test)
                       and any(isinstance(stmt, ast.ImportFrom) and stmt.module == module
                               and any(a.name == "stop_bridge_lab" for a in stmt.names)
                               for stmt in node.body)]
        self.assertEqual(len(start_guards), 1)
        self.assertEqual(len(stop_guards), 1)

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

    def test_symlinked_fixture_rejected_even_inside_temp(self):
        alias = self.root.with_name(self.root.name + "-link")
        try:
            alias.symlink_to(self.root, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("fixture symlinks unavailable on this runner")
        self.addCleanup(alias.unlink)
        with self.assertRaisesRegex(BridgeLabConfigurationError, "UNSAFE_FIXTURE_ROOT"):
            make_lab_collector({
                **self.env, "DC_V15_06_BRIDGE_LAB_ROOT": str(alias),
            })

    @unittest.skipUnless(os.name == "nt", "NTFS junction regression only on Windows")
    def test_windows_junction_incoming_rejected(self):
        with tempfile.TemporaryDirectory(prefix="dc-outside-fixture-") as outside:
            incoming = self.root / "incoming"
            incoming.rmdir()
            result = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(incoming), outside],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, "NTFS junction creation must run")
            try:
                with self.assertRaisesRegex(BridgeLabConfigurationError, "UNSAFE_FIXTURE_FOLDERS"):
                    make_lab_collector(self.env)
            finally:
                os.rmdir(incoming)  # Removes junction itself, never its target.

    @unittest.skipUnless(os.name == "nt", "NTFS junction regression only on Windows")
    def test_windows_junction_private_rejected(self):
        with tempfile.TemporaryDirectory(prefix="dc-spool-outside-") as outside:
            private = self.root / "private"
            result = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(private), outside],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, "NTFS junction creation must run")
            try:
                with self.assertRaisesRegex(BridgeLabConfigurationError, "UNSAFE_FIXTURE_FOLDERS"):
                    make_lab_collector(self.env)
            finally:
                os.rmdir(private)  # Remove the junction, not the external folder.

    def test_single_owner_refuses_second_backend_before_spawn(self):
        from tools.imaging_gateway.owner_lock_lab import LabOwnerLock
        first = LabOwnerLock.acquire(self.root)
        try:
            with patch("tools.imaging_gateway.bridge_background_lab.subprocess.Popen",
                       side_effect=AssertionError("a second worker must not spawn")):
                with self.assertRaisesRegex(BridgeLabConfigurationError, "OWNER_ALREADY_ACTIVE"):
                    start_if_enabled(self.env, trusted_environment="test")
        finally:
            first.close()
        next_owner = LabOwnerLock.acquire(self.root)
        next_owner.close()

    def test_single_owner_blocks_a_separate_python_process(self):
        from tools.imaging_gateway.owner_lock_lab import LabOwnerLock
        script = (
            "import sys; from pathlib import Path; "
            "from tools.imaging_gateway.owner_lock_lab import LabOwnerLock,LabOwnerLockError; "
            "p=Path(sys.argv[1]); "
            "lock=LabOwnerLock.acquire(p); lock.close()"
        )
        def contender():
            return subprocess.run(
                [sys.executable, "-c", script, str(self.root)],
                cwd=Path(__file__).resolve().parents[3],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=8, check=False,
            )
        first = LabOwnerLock.acquire(self.root)
        try:
            self.assertNotEqual(contender().returncode, 0,
                                "a second OS process must not own the LAB")
        finally:
            first.close()
        self.assertEqual(contender().returncode, 0,
                         "OS lock must be reusable after release")

    def test_invalid_ready_ack_kills_child_and_releases_owner(self):
        """A live but untrusted child ACK must never activate a LAB Bridge."""
        from tools.imaging_gateway.owner_lock_lab import LabOwnerLock
        real_popen = subprocess.Popen
        children = []

        def wrong_ack_child(*args, **kwargs):
            # The child sends an invalid ACK and remains alive unless killed.
            child = real_popen([
                sys.executable, "-c",
                "import sys,time; "
                "sys.stdin.buffer.readline(); "
                "sys.stdout.buffer.write(b'WRONG\\n'); "
                "sys.stdout.buffer.flush(); time.sleep(15)"
            ], **kwargs)
            children.append(child)
            return child

        try:
            with patch("tools.imaging_gateway.bridge_background_lab.subprocess.Popen",
                       side_effect=wrong_ack_child):
                with self.assertRaisesRegex(BridgeLabConfigurationError,
                                            "IMAGING_LAB_SUPERVISION_START_FAILED"):
                    start_if_enabled(self.env, trusted_environment="test")
            self.assertEqual(len(children), 1)
            self.assertIsNotNone(children[0].poll(), "child must be killed and reaped")
            with LabOwnerLock.acquire(self.root):
                pass
        finally:
            for child in children:
                if child.poll() is None:
                    child.kill()
                    child.wait(timeout=3)

    def test_failed_start_releases_owner_lock(self):
        from tools.imaging_gateway.owner_lock_lab import LabOwnerLock
        with patch("tools.imaging_gateway.bridge_background_lab.subprocess.Popen",
                   side_effect=OSError("synthetic spawn refused")):
            with self.assertRaisesRegex(BridgeLabConfigurationError, "SUPERVISION_START_FAILED"):
                start_if_enabled(self.env, trusted_environment="test")
        with LabOwnerLock.acquire(self.root) as owner:
            self.assertIsNotNone(owner)

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
            self.assertIsNotNone(handle.process)
            self.assertNotEqual(handle.process.pid, os.getpid())
            db_path = root / "private" / "acquisitions.sqlite3"
            try:
                async def was_staged():
                    while True:
                        with closing(sqlite3.connect(db_path)) as db:
                            row = db.execute("SELECT state FROM items").fetchone()
                        if row is not None:
                            self.assertEqual(row[0], "PENDING_CONFIRMATION")
                            return
                        await asyncio.sleep(0.05)
                await asyncio.wait_for(was_staged(), timeout=8)
            finally:
                completed = await stop_bridge_lab(handle)
            self.assertTrue(completed, "child did not stop gracefully")
            self.assertIsNotNone(handle.process.poll(), "child not reaped")
            self.assertTrue(handle.task.done())
            from tools.imaging_gateway.owner_lock_lab import LabOwnerLock
            reopened = LabOwnerLock.acquire(root)
            reopened.close()
            self.assertEqual(photo.read_bytes(), PNG)
            with closing(sqlite3.connect(db_path)) as db:
                self.assertEqual(db.execute("SELECT COUNT(*) FROM items").fetchone()[0], 1)
            # sqlite3.Connection.__exit__ commits, but does NOT close the
            # handle. Windows refuses fixture cleanup if even a read handle
            # remains open. Explicitly prove the final read connection closed.
            with self.assertRaises(sqlite3.ProgrammingError):
                db.execute("SELECT 1")

    async def test_repeated_scan_failures_exit_worker_and_are_reported(self):
        with tempfile.TemporaryDirectory(prefix="dc-lab-errors-") as tmp:
            root = Path(tmp)
            (root / ".digitalcrown-imaging-lab-only").write_text(
                "DIGITALCROWN_IMAGING_LAB_ONLY_V1\n", encoding="utf-8")
            (root / "incoming").mkdir()
            env = {
                "DC_V15_06_BRIDGE_LAB": "1",
                "ENVIRONMENT": "test",
                "DIGITALCROWN_ISOLATED_RUNTIME": "true",
                "DC_V15_06_BRIDGE_LAB_ROOT": str(root),
                "DC_V15_06_BRIDGE_LAB_KEY_HEX": (b"k" * 32).hex(),
                "DC_V15_06_BRIDGE_LAB_FORCE_SCAN_ERRORS": "1",
            }
            with self.assertLogs("tools.imaging_gateway.bridge_background_lab",
                                 level="ERROR") as logs:
                handle = start_if_enabled(env, trusted_environment="test")
                try:
                    await asyncio.wait_for(handle.task, timeout=4)
                    self.assertEqual(handle.process.poll(), 4)
                finally:
                    self.assertFalse(await stop_bridge_lab(handle))
            self.assertTrue(any("exited unexpectedly" in msg for msg in logs.output))
            self.assertTrue(all("SCAN_FAILURE" not in msg for msg in logs.output))
            from tools.imaging_gateway.owner_lock_lab import LabOwnerLock
            subsequent = LabOwnerLock.acquire(root)
            subsequent.close()

    @unittest.skipUnless(os.name == "nt" or sys.platform.startswith("linux"),
                         "Native process death checks are Windows/Linux only")
    async def test_abrupt_parent_death_stops_real_child_and_releases_singleton(self):
        """Prove OS kill of a *blocked* child that cannot obey stdin EOF.

        Kill ONLY the disposable test harness parent. A static fixture marker
        proves the child entered a 90s noninterruptible-by-EOF scan wait.
        Windows waits on the original child process handle; Linux tracks
        the original PID and process starttime. No clinic/backend/device.
        """
        from tools.imaging_gateway.owner_lock_lab import LabOwnerLock
        import signal
        with tempfile.TemporaryDirectory(prefix="dc-abrupt-lab-parent-") as tmp:
            root = Path(tmp)
            (root / ".digitalcrown-imaging-lab-only").write_text(
                "DIGITALCROWN_IMAGING_LAB_ONLY_V1\n", encoding="utf-8")
            (root / "incoming").mkdir()
            pidfile = root / "synthetic-child-pid.txt"
            blocked_marker = root / ".bridge-synthetic-scan-blocked"
            # No real image, patient, SDK, credentials or clinic backend.
            harness_source = """
import asyncio, os, sys
from pathlib import Path
from tools.imaging_gateway.bridge_background_lab import start_if_enabled
async def main():
    env = dict(
        DC_V15_06_BRIDGE_LAB="1",
        ENVIRONMENT="test",
        DIGITALCROWN_ISOLATED_RUNTIME="true",
        DC_V15_06_BRIDGE_LAB_ROOT=sys.argv[1],
        DC_V15_06_BRIDGE_LAB_KEY_HEX=(b"k" * 32).hex(),
        DC_V15_06_BRIDGE_LAB_BLOCK_SCAN="1",
    )
    handle = start_if_enabled(env, trusted_environment="test")
    evidence = Path(sys.argv[2])
    partial = evidence.with_suffix(".writing")
    partial.write_text(str(handle.process.pid), encoding="ascii")
    os.replace(partial, evidence)
    await asyncio.sleep(60)
asyncio.run(main())
"""
            minimal_env = {
                key: value for key, value in os.environ.items()
                if key.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "PATHEXT",
                                   "TMP", "TEMP", "TMPDIR", "HOME",
                                   "USERPROFILE", "SYSTEMDRIVE"}
            }
            parent = subprocess.Popen(
                [sys.executable, "-c", harness_source, str(root), str(pidfile)],
                cwd=Path(__file__).resolve().parents[3],
                env=minimal_env, stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            child_handle = None
            child_pid = None
            before_starttime = None
            try:
                deadline = time.monotonic() + 12
                while time.monotonic() < deadline and not pidfile.exists():
                    if parent.poll() is not None:
                        self.fail("isolated synthetic parent exited before READY")
                    await asyncio.sleep(0.05)
                self.assertTrue(pidfile.exists(), "real child PID never reported")
                child_pid = int(pidfile.read_text(encoding="ascii"))
                self.assertGreater(child_pid, 0)
                self.assertIsNone(parent.poll())
                deadline = time.monotonic() + 8
                while time.monotonic() < deadline and not blocked_marker.exists():
                    if parent.poll() is not None:
                        self.fail("LAB parent died before child was blocked")
                    await asyncio.sleep(0.05)
                self.assertTrue(blocked_marker.exists(), "child never entered blocked scan")
                self.assertEqual(blocked_marker.read_bytes(), b"BLOCKED\n")
                self.assertIsNone(parent.poll())

                if os.name == "nt":
                    import ctypes
                    from ctypes import wintypes
                    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
                    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
                    kernel.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
                    kernel.TerminateProcess.restype = wintypes.BOOL
                    kernel.OpenProcess.restype = wintypes.HANDLE
                    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
                    kernel.WaitForSingleObject.restype = wintypes.DWORD
                    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
                    kernel.CloseHandle.restype = wintypes.BOOL
                    child_handle = kernel.OpenProcess(0x00100001, False, child_pid)
                    self.assertTrue(child_handle, "cannot open synthetic child for wait")
                    self.assertEqual(kernel.WaitForSingleObject(child_handle, 0), 0x102,
                                     "child must be living before parent death")
                else:
                    # Require the original child was running BEFORE the parent
                    # was killed; otherwise a preexisting child failure would
                    # be incorrectly counted as a PDEATHSIG success.
                    before_stat = Path(f"/proc/{child_pid}/stat").read_text().split()
                    self.assertNotIn(before_stat[2], ("Z", "X"),
                                     "child already dead before parent crash")
                    before_starttime = before_stat[21]

                # Force-kill only the freshly launched test harness parent.
                # This executes no cleanup handler and simulates backend crash.
                parent.kill()
                await asyncio.wait_for(asyncio.to_thread(parent.wait, timeout=4), timeout=5)

                if os.name == "nt":
                    self.assertEqual(kernel.WaitForSingleObject(child_handle, 8000), 0,
                                     "Windows Job close did not kill real LAB child")
                else:
                    # A vanished /proc entry is success; a reused PID is not
                    # evidence the original child remained alive.
                    deadline = time.monotonic() + 8
                    still_running = True
                    while time.monotonic() < deadline:
                        try:
                            fields = Path(f"/proc/{child_pid}/stat").read_text().split()
                            still_running = (
                                fields[2] not in ("Z", "X")
                                and fields[21] == before_starttime
                            )
                        except FileNotFoundError:
                            still_running = False
                        if not still_running:
                            break
                        await asyncio.sleep(0.05)
                    self.assertFalse(still_running, "Linux child survived parent SIGKILL")

                # The backend lock must not be stale after the killed parent.
                with LabOwnerLock.acquire(root):
                    pass
            finally:
                if parent.poll() is None:
                    parent.kill()
                    parent.wait(timeout=4)
                if child_handle:
                    # If an OS kill regression occurs, don't leak a LAB process
                    # blocked for 90s into later CI jobs. Handle is PID-reuse-safe.
                    if kernel.WaitForSingleObject(child_handle, 0) == 0x102:
                        kernel.TerminateProcess(child_handle, 5)
                        kernel.WaitForSingleObject(child_handle, 3000)
                    kernel.CloseHandle(child_handle)
                elif (sys.platform.startswith("linux") and child_pid is not None
                      and before_starttime is not None):
                    try:
                        state = Path(f"/proc/{child_pid}/stat").read_text().split()
                        if state[21] == before_starttime and state[2] not in ("Z", "X"):
                            os.kill(child_pid, signal.SIGKILL)
                    except (FileNotFoundError, ProcessLookupError):
                        pass

    @unittest.skipUnless(os.name == "nt", "Windows Job Object only")
    async def test_windows_job_close_terminates_uncooperative_child(self):
        from tools.imaging_gateway.windows_job_lab import WindowsLabJob
        child = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(15)"],
            stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        job = None
        try:
            job = WindowsLabJob.assign(child)
            self.assertIsNotNone(job)
            self.assertIsNone(child.poll(), "child must still be alive before job close")
            closed_at = time.monotonic()
            job.close()
            job = None
            await asyncio.wait_for(asyncio.to_thread(child.wait, timeout=3), timeout=4)
            elapsed = time.monotonic() - closed_at
            self.assertIsNotNone(child.returncode)
            # Windows can assign exit code 0 to a job-terminated process:
            # the kill proof is that a live 15s sleeper exits within 4s.
            self.assertLess(elapsed, 4.0, "job close did not end living child promptly")
        finally:
            if job is not None:
                job.close()
            if child.poll() is None:
                child.kill()
                child.wait(timeout=3)
            if child.stdin is not None:
                child.stdin.close()

    async def test_supervised_child_force_kills_and_reaps_stuck_process(self):
        from tools.imaging_gateway.bridge_background_lab import BridgeLabHandle
        child = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(15)"],
            stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        stop = asyncio.Event()
        monitor = asyncio.create_task(stop.wait())
        handle = BridgeLabHandle(stop, monitor, child)
        try:
            with self.assertLogs("tools.imaging_gateway.bridge_background_lab", level="ERROR"):
                completed = await asyncio.wait_for(
                    stop_bridge_lab(handle, timeout=0.12), timeout=4)
            self.assertFalse(completed, "forced kill must not claim graceful exit")
            self.assertIsNotNone(child.poll(), "uninterruptible child was not reaped")
            self.assertTrue(monitor.done())
        finally:
            if child.poll() is None:
                child.kill()
                child.wait(timeout=3)

    async def test_blocking_scan_reports_bounded_shutdown_without_false_success(self):
        started = threading.Event()
        release = threading.Event()

        class HeldCollector:
            def scan_once(self):
                started.set()
                release.wait(timeout=1.0)
                return {"staged": 0}

        from tools.imaging_gateway.bridge_background_lab import BridgeLabHandle
        stop = asyncio.Event()
        task = asyncio.create_task(poll_lab_collector(HeldCollector(), stop, interval=0.01))
        handle = BridgeLabHandle(stop, task)
        try:
            self.assertTrue(await asyncio.to_thread(started.wait, 0.5))
            with self.assertLogs("tools.imaging_gateway.bridge_background_lab", level="ERROR"):
                result = await asyncio.wait_for(stop_bridge_lab(handle, timeout=0.02), timeout=0.8)
            self.assertFalse(result)
            self.assertTrue(task.done())
        finally:
            release.set()

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
