"""Fail-closed gate for the privileged Windows server console (08.2-A).

This gate is required for bootstrap/enrollment/recovery. Remote Desktop, a
service session, a redirected terminal and a non-elevated process are refused.
A CLI is never an authorization boundary for a future network endpoint.
"""

from __future__ import annotations

import ctypes
import os
import sys


class LocalConsoleRequired(PermissionError):
    pass


def require_local_windows_admin_console() -> None:
    if os.name != "nt" or sys.platform != "win32":
        raise LocalConsoleRequired("LOCAL_WINDOWS_CONSOLE_REQUIRED")
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise LocalConsoleRequired("INTERACTIVE_CONSOLE_REQUIRED")
    try:
        shell = ctypes.windll.shell32
        kernel = ctypes.windll.kernel32
        wts = ctypes.windll.wtsapi32
        if not shell.IsUserAnAdmin() or not kernel.GetConsoleWindow():
            raise LocalConsoleRequired("ELEVATED_WINDOWS_CONSOLE_REQUIRED")
        session = ctypes.c_ulong()
        if not kernel.ProcessIdToSessionId(os.getpid(), ctypes.byref(session)):
            raise LocalConsoleRequired("WINDOWS_SESSION_UNAVAILABLE")
        console_session = kernel.WTSGetActiveConsoleSessionId()
        if session.value != console_session or console_session == 0xFFFFFFFF:
            raise LocalConsoleRequired("REMOTE_SESSION_FORBIDDEN")
        # WTSClientProtocolType=16: 0 console, 2 remote desktop.
        ptr = ctypes.c_void_p()
        size = ctypes.c_ulong()
        if not wts.WTSQuerySessionInformationW(
            ctypes.c_void_p(), session.value, 16,
            ctypes.byref(ptr), ctypes.byref(size)
        ):
            raise LocalConsoleRequired("SESSION_PROTOCOL_UNKNOWN")
        try:
            if size.value < ctypes.sizeof(ctypes.c_ushort):
                raise LocalConsoleRequired("SESSION_PROTOCOL_UNKNOWN")
            protocol = ctypes.cast(ptr, ctypes.POINTER(ctypes.c_ushort)).contents.value
            if protocol != 0:
                raise LocalConsoleRequired("REMOTE_SESSION_FORBIDDEN")
        finally:
            wts.WTSFreeMemory(ptr)
    except LocalConsoleRequired:
        raise
    except (OSError, AttributeError, ValueError) as error:
        raise LocalConsoleRequired("LOCAL_CONSOLE_VERIFICATION_FAILED") from error
