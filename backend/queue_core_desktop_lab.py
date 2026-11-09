"""Compatibility entrypoint for the synthetic Queue Core Desktop LAB bridge.

The implementation resides in queue_core.service.desktop_lab_bridge to keep
Queue Core's isolated test dependency graph independent of backend.__init__.
The real backend.main mount imports this module as before; clinic behavior,
test-only guardrails and API remain unchanged.
"""
from queue_core.service.desktop_lab_bridge import (  # noqa: F401
    MOUNT_PATH,
    MARKER,
    FLAG,
    ROOT,
    DesktopQueueLabError,
    resolve_isolated_lab_root,
    attach_queue_core_lab,
)

__all__ = [
    "MOUNT_PATH", "MARKER", "FLAG", "ROOT",
    "DesktopQueueLabError", "resolve_isolated_lab_root",
    "attach_queue_core_lab",
]
