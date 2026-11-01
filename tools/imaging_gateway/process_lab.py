"""LAB-only supervised child entry point (not a second installed application).

Only callable with explicit TEST-isolated, TEMP-marked fixture. The backend
supervises its lifetime and can terminate/reap this process even if a scan is
stuck in an OS read. Never processes patient identities or sends media.
"""
from __future__ import annotations

import os
import signal
import sys
import threading

from tools.imaging_gateway.bridge_background_lab import make_lab_collector


def _arm_parent_death_on_linux() -> bool:
    if not sys.platform.startswith("linux"):
        return True
    try:
        import ctypes
        expected = int(os.environ["DC_V15_06_BRIDGE_LAB_PARENT_PID"])
        libc = ctypes.CDLL(None, use_errno=True)
        libc.prctl.argtypes = [ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong,
                              ctypes.c_ulong, ctypes.c_ulong]
        libc.prctl.restype = ctypes.c_int
        if libc.prctl(1, signal.SIGKILL, 0, 0, 0) != 0:
            return False
        return os.getppid() == expected
    except (ValueError, KeyError, OSError, AttributeError):
        return False


def main() -> int:
    # Parent controls ALL filesystem mutations: GO arrives only after OS
    # lifetime supervision and singleton LAB lock are established.
    try:
        if sys.stdin.buffer.readline() != b"GO\n":
            return 3
    except (OSError, ValueError):
        return 3
    if not _arm_parent_death_on_linux():
        return 3
    try:
        collector = make_lab_collector()
        if collector is None:
            return 2
    except Exception:
        return 2  # No fixture path, exception or key in child output.

    stopped = threading.Event()

    def await_parent():
        try:
            # EOF also stops the worker when the parent process disappears.
            # Unbuffered fd read: a daemon blocked in BufferedReader.readline
            # can trigger a fatal interpreter-shutdown lock on child exit.
            # Parent STOP or EOF both wake the control thread.
            os.read(sys.stdin.fileno(), 1)
        finally:
            stopped.set()

    threading.Thread(target=await_parent, daemon=True, name="dc-lab-control").start()
    try:
        sys.stdout.buffer.write(b"READY\n")
        sys.stdout.buffer.flush()
    except (BrokenPipeError, OSError):
        return 3
    consecutive_errors = 0
    while not stopped.is_set():
        try:
            # Deliberately uncooperative TEST-only scan: stdin EOF sets stop
            # in another thread but CANNOT interrupt this blocked main loop.
            # Enables actual OS parent-death kill proof in synthetic CI.
            if os.environ.get("DC_V15_06_BRIDGE_LAB_BLOCK_SCAN") == "1":
                from pathlib import Path
                marker = Path(os.environ["DC_V15_06_BRIDGE_LAB_ROOT"]) / ".bridge-synthetic-scan-blocked"
                with marker.open("xb") as proof:
                    proof.write(b"BLOCKED\n")
                    proof.flush()
                    os.fsync(proof.fileno())
                threading.Event().wait(90)
                # No real scan or patient data, even if 90s expires.
                return 5
            # Only an already isolated, opt-in TEST fixture can set this
            # synthetic failure injection. Never enabled on normal startup.
            if os.environ.get("DC_V15_06_BRIDGE_LAB_FORCE_SCAN_ERRORS") == "1":
                raise RuntimeError("SYNTHETIC_LAB_SCAN_FAILURE")
            collector.scan_once()
            consecutive_errors = 0
        except Exception:
            # Never silently spin after permanent SQLite/filesystem failures.
            # Supervisor sees nonzero exit and emits non-PHI error/status.
            consecutive_errors += 1
            if consecutive_errors >= 3:
                return 4
        stopped.wait(0.25)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
