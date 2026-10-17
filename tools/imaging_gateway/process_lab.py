"""LAB-only supervised child entry point (not a second installed application).

Only callable with explicit TEST-isolated, TEMP-marked fixture. The backend
supervises its lifetime and can terminate/reap this process even if a scan is
stuck in an OS read. Never processes patient identities or sends media.
"""
from __future__ import annotations

import sys
import threading

from tools.imaging_gateway.bridge_background_lab import make_lab_collector


def main() -> int:
    try:
        collector = make_lab_collector()
        if collector is None:
            return 2  # No silent startup without explicit isolated LAB flag.
    except Exception:
        return 2  # Do not leak configured paths or key values to stderr.

    # Child must not read any capture until the parent has assigned its
    # Windows KILL_ON_JOB_CLOSE lifetime guard.
    try:
        if sys.stdin.buffer.readline() != b"GO\n":
            return 3
    except (OSError, ValueError):
        return 3

    stopped = threading.Event()

    def await_parent():
        try:
            # EOF also stops the worker when the parent process disappears.
            sys.stdin.buffer.readline()
        finally:
            stopped.set()

    threading.Thread(target=await_parent, daemon=True, name="dc-lab-control").start()
    while not stopped.is_set():
        try:
            collector.scan_once()
        except Exception:
            # Untrusted exception text can contain fixture paths.
            pass
        stopped.wait(0.25)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
