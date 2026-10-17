"""LOT06 prototype: background hot-folder polling in the *existing* cabinet backend.

Disabled by default. Restricted to explicit isolated TEST fixtures in OS temp.
No patient lookup, clinical asset, transport, SDK, upload or server receipt.
Do not treat this laboratory worker as a supported Windows service/installer.
"""
from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass
import logging
import os
import subprocess
import sys
import stat
from pathlib import Path
import tempfile
from typing import Mapping

from tools.imaging_gateway.gateway import _is_unsafe_path_component
from tools.imaging_gateway.windows_job_lab import WindowsLabJob
from tools.imaging_gateway.owner_lock_lab import LabOwnerLock, LabOwnerLockError

logger = logging.getLogger(__name__)
_MARKER = ".digitalcrown-imaging-lab-only"
_MARKER_VALUE = "DIGITALCROWN_IMAGING_LAB_ONLY_V1\n"


class BridgeLabConfigurationError(RuntimeError):
    """Fail closed without exposing local paths or configured secrets."""


@dataclass(frozen=True)
class BridgeLabHandle:
    stop: asyncio.Event
    task: asyncio.Task
    process: subprocess.Popen | None = None
    job: WindowsLabJob | None = None
    owner: LabOwnerLock | None = None


def lab_requested(environ: Mapping[str, str] | None = None) -> bool:
    env = os.environ if environ is None else environ
    return env.get("DC_V15_06_BRIDGE_LAB", "") == "1"


def make_lab_collector(environ: Mapping[str, str] | None = None, *, acquire_owner: bool = False):
    """Make a synthetic collector only in an explicitly marked temp fixture.

    No ordinary clinical folder is ever discovered or watched automatically.
    """
    env = os.environ if environ is None else environ
    if not lab_requested(env):
        return None
    if (env.get("ENVIRONMENT", "").lower() != "test" or
            env.get("DIGITALCROWN_ISOLATED_RUNTIME", "").lower() not in {"true", "1"}):
        raise BridgeLabConfigurationError("IMAGING_BRIDGE_TEST_ISOLATION_REQUIRED")
    raw = env.get("DC_V15_06_BRIDGE_LAB_ROOT", "")
    if not raw or not Path(raw).is_absolute():
        raise BridgeLabConfigurationError("IMAGING_BRIDGE_FIXTURE_ROOT_REQUIRED")
    configured = Path(raw)
    try:
        root = configured.resolve(strict=True)
        temp = Path(tempfile.gettempdir()).resolve(strict=True)
        # Compare filesystem identity, not lexical paths: Windows TEMP and
        # resolved paths can use different case, short names or drive spelling.
        # A syntactically nested string alone is never enough for confinement.
        if not root.is_dir() or not any(p.samefile(temp) for p in root.parents):
            raise BridgeLabConfigurationError("IMAGING_BRIDGE_UNSAFE_FIXTURE_ROOT")
        # Also reject symlinks/junctions in the *supplied* path between the
        # fixture and the actual TEMP root. Path.resolve alone would follow
        # a reparse point even if its target happened to be inside TEMP.
        reached_temp = False
        for component in (configured, *configured.parents):
            if component.samefile(temp):
                reached_temp = True
                break
            info = component.lstat()
            if (stat.S_ISLNK(info.st_mode) or
                    (os.name == "nt" and
                     bool(getattr(info, "st_file_attributes", 0) &
                          stat.FILE_ATTRIBUTE_REPARSE_POINT))):
                raise BridgeLabConfigurationError("IMAGING_BRIDGE_UNSAFE_FIXTURE_ROOT")
        if not reached_temp:
            raise BridgeLabConfigurationError("IMAGING_BRIDGE_UNSAFE_FIXTURE_ROOT")
        if (_is_unsafe_path_component(root / _MARKER) or
                (root / _MARKER).read_text(encoding="utf-8") != _MARKER_VALUE):
            raise BridgeLabConfigurationError("IMAGING_BRIDGE_FIXTURE_MARKER_REQUIRED")
        incoming = root / "incoming"
        private = root / "private"
        # A Windows NTFS junction is *not* necessarily Path.is_symlink().
        # Constrain both nested roots by reparse attributes and real parent.
        if (not incoming.is_dir() or _is_unsafe_path_component(incoming) or
                _is_unsafe_path_component(private) or
                (private.exists() and not private.is_dir()) or
                not incoming.resolve(strict=True).parent.samefile(root) or
                (private.exists() and
                 not private.resolve(strict=True).parent.samefile(root))):
            raise BridgeLabConfigurationError("IMAGING_BRIDGE_UNSAFE_FIXTURE_FOLDERS")
    except (OSError, ValueError, UnicodeError):
        raise BridgeLabConfigurationError("IMAGING_BRIDGE_FIXTURE_INVALID") from None

    key_hex = env.get("DC_V15_06_BRIDGE_LAB_KEY_HEX", "")
    if len(key_hex) != 64:
        raise BridgeLabConfigurationError("IMAGING_BRIDGE_TEST_KEY_REQUIRED")
    try:
        key = bytes.fromhex(key_hex)
    except ValueError:
        raise BridgeLabConfigurationError("IMAGING_BRIDGE_TEST_KEY_INVALID") from None

    # OS-owned parent lock must precede even SQLite bootstrap to avoid
    # concurrent initializations by two FastAPI workers on one fixture.
    owner = None
    try:
        if acquire_owner:
            owner = LabOwnerLock.acquire(root)
        from tools.imaging_gateway import Config, HotFolder
        collector = HotFolder(Config("lab_cabinet", "lab_station", incoming,
                                     private, key, require_ready_manifest=True))
        return (collector, owner) if acquire_owner else collector
    except BaseException:
        if owner is not None:
            owner.close()
        raise


async def poll_lab_collector(collector, stop: asyncio.Event, *, interval: float = 0.25) -> None:
    """Poll off the API event loop; never attach patient or send media anywhere."""
    if not 0.01 <= interval <= 60.0:
        raise ValueError("invalid isolated poll interval")
    while not stop.is_set():
        try:
            await asyncio.to_thread(collector.scan_once)
        except Exception:
            # Driver/filesystem exceptions can contain patient filenames/paths.
            # Do not log exception objects or tracebacks in this prototype.
            logger.warning("Imaging LAB poll failed; acquisition not confirmed")
        try:
            await asyncio.wait_for(stop.wait(), timeout=interval)
        except asyncio.TimeoutError:
            pass


def start_if_enabled(
    environ: Mapping[str, str] | None = None, *, trusted_environment: str | None = None
) -> BridgeLabHandle | None:
    """Require the backend settings and process environment to agree on TEST."""
    env = os.environ if environ is None else environ
    if lab_requested(env) and str(trusted_environment).lower() != "test":
        raise BridgeLabConfigurationError("IMAGING_BRIDGE_BACKEND_TEST_REQUIRED")
    if not lab_requested(env):
        return None
    try:
        collector, owner = make_lab_collector(env, acquire_owner=True)
    except LabOwnerLockError as error:
        raise BridgeLabConfigurationError(str(error)) from None
    # Start a supervised internal process. The old to_thread helper remains
    # exclusively for isolated unit fixtures; backend runtime never uses it.
    # Explicitly pass only LAB vars and minimal OS loader/temp variables:
    # never inherit backend patient/cloud/auth credentials into this child.
    child_env = {key: value for key, value in os.environ.items()
                 if key.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "PATHEXT",
                                     "TMP", "TEMP", "TMPDIR", "HOME",
                                     "USERPROFILE", "SYSTEMDRIVE"}}
    for name in ("DC_V15_06_BRIDGE_LAB", "DC_V15_06_BRIDGE_LAB_ROOT",
                 "DC_V15_06_BRIDGE_LAB_KEY_HEX", "ENVIRONMENT",
                 "DIGITALCROWN_ISOLATED_RUNTIME"):
        child_env[name] = env[name]
    if env.get("DC_V15_06_BRIDGE_LAB_FORCE_SCAN_ERRORS") == "1":
        child_env["DC_V15_06_BRIDGE_LAB_FORCE_SCAN_ERRORS"] = "1"
    child_env["DC_V15_06_BRIDGE_LAB_PARENT_PID"] = str(os.getpid())
    launch_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    proc = None
    job = None
    try:
        proc = subprocess.Popen(
            [sys.executable, "-m", "tools.imaging_gateway.process_lab"],
            cwd=Path(__file__).resolve().parents[2],
            env=child_env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, creationflags=launch_flags,
            close_fds=True,
        )
        # No scan is allowed before successful Job assignment AND a READY
        # handshake from the correctly isolated child process.
        job = WindowsLabJob.assign(proc)
        if proc.stdin is None or proc.stdout is None:
            raise BridgeLabConfigurationError("IMAGING_LAB_CONTROL_CHANNEL_MISSING")
        proc.stdin.write(b"GO\n")
        proc.stdin.flush()

        # Bounded, synchronous setup: this is a LAB opt-in at API startup.
        # Kill + close the pipe on timeout to unblock the daemon reader.
        import queue
        import threading
        ready_messages = queue.Queue(maxsize=1)
        def read_ack():
            try:
                ready_messages.put(proc.stdout.readline())
            except (OSError, ValueError):
                ready_messages.put(b"")
        threading.Thread(target=read_ack, daemon=True, name="dc-lab-ready").start()
        try:
            ready = ready_messages.get(timeout=3)
        except queue.Empty:
            raise BridgeLabConfigurationError("IMAGING_LAB_READY_TIMEOUT") from None
        if ready != b"READY\n" or proc.poll() is not None:
            raise BridgeLabConfigurationError("IMAGING_LAB_READY_REJECTED")
        proc.stdout.close()
    except BaseException:
        try:
            if proc is not None:
                if proc.poll() is None:
                    proc.kill()
                proc.wait(timeout=3)
        finally:
            if job is not None:
                job.close()
            if proc is not None and proc.stdin is not None:
                with contextlib.suppress(OSError, ValueError):
                    proc.stdin.close()
            if proc is not None and proc.stdout is not None and not proc.stdout.closed:
                proc.stdout.close()
            owner.close()
        raise BridgeLabConfigurationError("IMAGING_LAB_SUPERVISION_START_FAILED") from None
    stop = asyncio.Event()

    async def monitor():
        while not stop.is_set():
            if proc.poll() is not None:
                # No PHI/filenames/paths, but operational error visible to
                # application operators. Child uses distinct failure codes.
                logger.error("Imaging LAB worker exited unexpectedly; acquisitions stopped")
                return
            await asyncio.sleep(0.05)

    return BridgeLabHandle(stop=stop, task=asyncio.create_task(monitor()),
                           process=proc, job=job, owner=owner)


async def stop_bridge_lab(handle: BridgeLabHandle, *, timeout: float = 2.0) -> bool:
    """Bound asynchronous shutdown; report, never hide, uninterruptible scans.

    asyncio.to_thread cannot forcefully stop a filesystem operation stuck in
    the OS. On timeout return False after cancelling the asyncio task; the
    underlying scan thread may remain. This is NOT clinical-grade process
    supervision: hardware must eventually run in a supervised child process.
    """
    if not 0.01 <= timeout <= 30.0:
        raise ValueError("invalid LAB shutdown deadline")
    handle.stop.set()
    if handle.process is not None:
        # The real backend uses a separate LAB process; a blocked OS scan
        # cannot prevent the parent from killing/reaping the child.
        proc = handle.process
        clean = proc.poll() is None
        try:
            if proc.stdin is not None and not proc.stdin.closed:
                try:
                    proc.stdin.write(b"STOP\\n".replace(b"\\n", bytes([10])))
                    proc.stdin.flush()
                except (OSError, ValueError):
                    clean = False
            try:
                await asyncio.to_thread(proc.wait, timeout=timeout)
            except subprocess.TimeoutExpired:
                clean = False
                proc.kill()
                await asyncio.to_thread(proc.wait, timeout=2)
        finally:
            if proc.poll() is None:
                proc.kill()
                await asyncio.to_thread(proc.wait, timeout=2)
            if handle.job is not None:
                handle.job.close()
            if proc.stdin is not None:
                with contextlib.suppress(OSError, ValueError):
                    proc.stdin.close()
            if handle.owner is not None:
                handle.owner.close()
            if not handle.task.done():
                handle.task.cancel()
            with contextlib.suppress(asyncio.CancelledError, BridgeLabConfigurationError):
                await handle.task
        if proc.returncode != 0:
            clean = False
        if not clean:
            logger.error("Imaging LAB child terminated or failed; no acquisition confirmed")
        return clean
    # Compatibility-only helper used by low-level unit fixtures, never the
    # active backend path. It cannot kill a blocked thread.
    try:
        await asyncio.wait_for(asyncio.shield(handle.task), timeout=timeout)
        return True
    except asyncio.TimeoutError:
        logger.error("Imaging LAB stop timeout: underlying scan thread NOT confirmed stopped")
        handle.task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await handle.task
        return False
