"""Windows native no-follow keyring handle probe.

This is a test-only security primitive. Product Windows keyring remains denied until
handle-bound ACL and owner verification are implemented and certified.
"""
from __future__ import annotations

import ctypes
import os
from ctypes import wintypes
from pathlib import Path


class WindowsKeyringHandleDenied(Exception):
    pass


def read_no_reparse_file(path: str, *, max_bytes: int = 16384) -> bytes:
    """Read from one Windows file handle; reject reparse points, directories, and oversize."""
    if os.name != "nt":
        raise WindowsKeyringHandleDenied("WINDOWS_ONLY")
    candidate = Path(path)
    if not candidate.is_absolute():
        raise WindowsKeyringHandleDenied("KEYRING_PATH_NOT_ABSOLUTE")
    # This primitive alone does NOT authorize product keyring use.
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create = kernel32.CreateFileW
    create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                       ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    create.restype = wintypes.HANDLE
    get_info = kernel32.GetFileInformationByHandle
    get_info.argtypes = [wintypes.HANDLE, ctypes.c_void_p]
    get_info.restype = wintypes.BOOL
    read = kernel32.ReadFile
    read.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD,
                     ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p]
    read.restype = wintypes.BOOL
    close = kernel32.CloseHandle
    close.argtypes = [wintypes.HANDLE]
    close.restype = wintypes.BOOL

    class FileTime(ctypes.Structure):
        _fields_ = [("low", wintypes.DWORD), ("high", wintypes.DWORD)]

    class FileInfo(ctypes.Structure):
        _fields_ = [
            ("attributes", wintypes.DWORD), ("created", FileTime),
            ("accessed", FileTime), ("written", FileTime),
            ("volume_serial", wintypes.DWORD), ("size_high", wintypes.DWORD),
            ("size_low", wintypes.DWORD), ("links", wintypes.DWORD),
            ("index_high", wintypes.DWORD), ("index_low", wintypes.DWORD),
        ]

    # FILE_FLAG_OPEN_REPARSE_POINT ensures final reparse point itself is opened.
    # Parent reparse points are not safely blocked by this flag; product remains disabled.
    handle = create(str(candidate), 0x80000000, 0x00000001, None, 3,
                    0x00200000 | 0x02000000, None)
    invalid = ctypes.c_void_p(-1).value
    if handle is None or handle == invalid:
        raise WindowsKeyringHandleDenied("KEYRING_OPEN_DENIED")
    try:
        info = FileInfo()
        if not get_info(handle, ctypes.byref(info)):
            raise WindowsKeyringHandleDenied("KEYRING_HANDLE_INFO_DENIED")
        if info.attributes & 0x400:
            raise WindowsKeyringHandleDenied("KEYRING_REPARSE_DENIED")
        if info.attributes & 0x10:
            raise WindowsKeyringHandleDenied("KEYRING_DIRECTORY_DENIED")
        size = (info.size_high << 32) | info.size_low
        if size > max_bytes:
            raise WindowsKeyringHandleDenied("KEYRING_FILE_TOO_LARGE")
        buffer = ctypes.create_string_buffer(max_bytes + 1)
        count = wintypes.DWORD()
        if not read(handle, buffer, max_bytes + 1, ctypes.byref(count), None):
            raise WindowsKeyringHandleDenied("KEYRING_READ_DENIED")
        if count.value > max_bytes:
            raise WindowsKeyringHandleDenied("KEYRING_FILE_TOO_LARGE")
        return buffer.raw[:count.value]
    finally:
        close(handle)
