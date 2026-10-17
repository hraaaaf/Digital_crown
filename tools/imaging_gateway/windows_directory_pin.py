"""Short-lived native Windows directory pins for synthetic scan transactions.

Windows CreateFileW without FILE_SHARE_DELETE rejects directory rename/junction
replacement while each directory handle is held. This protects the live scan
against common rename-based races, NOT arbitrary file reparse-point attacks,
untrusted admins, or a commercial clinical filesystem ACL policy.
"""
from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path


@contextmanager
def pin_directories(paths):
    if os.name != "nt":
        yield
        return

    import ctypes
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    create = kernel.CreateFileW
    create.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
        ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
    ]
    create.restype = wintypes.HANDLE
    close = kernel.CloseHandle
    close.argtypes = [wintypes.HANDLE]
    close.restype = wintypes.BOOL

    # FILE_READ_ATTRIBUTES; FILE_SHARE_READ | FILE_SHARE_WRITE (no DELETE);
    # OPEN_EXISTING; BACKUP_SEMANTICS | OPEN_REPARSE_POINT.
    access, sharing, existing = 0x80, 0x1 | 0x2, 3
    flags = 0x02000000 | 0x00200000
    invalid = ctypes.c_void_p(-1).value
    opened = []
    try:
        for path in dict.fromkeys(str(Path(p).absolute()) for p in paths):
            handle = create(path, access, sharing, None, existing, flags, None)
            if handle in (None, invalid):
                raise OSError(ctypes.get_last_error(), "IMAGING_PIN_DIRECTORY_FAILED")
            opened.append(handle)
        yield
    finally:
        for handle in reversed(opened):
            close(handle)
