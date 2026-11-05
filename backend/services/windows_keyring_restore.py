"""F5B-D2 Windows-only secure restore to a NEW file; never overwrite.

Experimental operator primitive. Parent reparse traversal is rejected before
creation, and ancestor handles remain open without write/delete sharing.
Only the current user and SYSTEM are granted access by the creation DACL.
"""
from __future__ import annotations

import ctypes
import json
import os
from ctypes import wintypes
from pathlib import Path

from backend.services.windows_keyring_handle_probe import (
    _FileInfo,
)


class WindowsRestoreDenied(ValueError):
    pass


class _SecurityAttributes(ctypes.Structure):
    _fields_ = [
        ("length", wintypes.DWORD),
        ("descriptor", ctypes.c_void_p),
        ("inherit", wintypes.BOOL),
    ]


class _TokenUser(ctypes.Structure):
    class _SidAndAttributes(ctypes.Structure):
        _fields_ = [("sid", ctypes.c_void_p), ("attributes", wintypes.DWORD)]
    _fields_ = [("user", _SidAndAttributes)]


def restore_new_private_file(filename: str, raw: bytes) -> None:
    """Write one validated JSON keyring to a private Windows file, exclusively."""
    if os.name != "nt":
        raise WindowsRestoreDenied("WINDOWS_ONLY")
    if not isinstance(raw, bytes) or not 1 <= len(raw) <= 16384:
        raise WindowsRestoreDenied("RESTORE_SIZE_DENIED")
    # Reject malformed or incomplete key registries before touching the filesystem.
    from backend.services.clinical_media_keyring_recovery import (
        KeyringRecoveryDenied, _canonical,
    )
    try:
        parsed = json.loads(raw.decode("utf-8"))
        _canonical(parsed)
    except (UnicodeError, ValueError, KeyringRecoveryDenied) as exc:
        raise WindowsRestoreDenied("RESTORE_KEYRING_INVALID") from exc
    if not isinstance(filename, str):
        raise WindowsRestoreDenied("RESTORE_PATH_DENIED")
    path = Path(filename)
    if (not path.is_absolute() or len(path.drive) != 2
            or path.drive[1] != ":" or path.anchor != path.drive + "\\"
            or len(path.parts) < 2
            or any(p in (".", "..", "") or ":" in p or p.endswith((" ", "."))
                   for p in path.parts[1:])):
        raise WindowsRestoreDenied("RESTORE_PATH_DENIED")

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    adv = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel.CreateFileW.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
        ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
    ]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.GetFileInformationByHandle.argtypes = [wintypes.HANDLE, ctypes.c_void_p]
    kernel.GetFileInformationByHandle.restype = wintypes.BOOL
    kernel.WriteFile.argtypes = [
        wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p,
    ]
    kernel.WriteFile.restype = wintypes.BOOL
    kernel.FlushFileBuffers.argtypes = [wintypes.HANDLE]
    kernel.FlushFileBuffers.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    adv.OpenProcessToken.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)
    ]
    adv.OpenProcessToken.restype = wintypes.BOOL
    adv.GetTokenInformation.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, ctypes.c_void_p,
        wintypes.DWORD, ctypes.POINTER(wintypes.DWORD),
    ]
    adv.GetTokenInformation.restype = wintypes.BOOL
    adv.ConvertSidToStringSidW.argtypes = [
        ctypes.c_void_p, ctypes.POINTER(wintypes.LPWSTR)
    ]
    adv.ConvertSidToStringSidW.restype = wintypes.BOOL
    adv.ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(wintypes.DWORD),
    ]
    adv.ConvertStringSecurityDescriptorToSecurityDescriptorW.restype = wintypes.BOOL

    token = wintypes.HANDLE()
    sid_string = wintypes.LPWSTR()
    descriptor = ctypes.c_void_p()
    opened = []
    try:
        if not adv.OpenProcessToken(kernel.GetCurrentProcess(), 0x0008,
                                    ctypes.byref(token)):
            raise WindowsRestoreDenied("RESTORE_TOKEN_DENIED")
        size = wintypes.DWORD()
        adv.GetTokenInformation(token, 1, None, 0, ctypes.byref(size))
        if not 0 < size.value <= 65536:
            raise WindowsRestoreDenied("RESTORE_TOKEN_DENIED")
        buffer = ctypes.create_string_buffer(size.value)
        if not adv.GetTokenInformation(token, 1, buffer, size,
                                       ctypes.byref(size)):
            raise WindowsRestoreDenied("RESTORE_TOKEN_DENIED")
        sid = ctypes.cast(buffer, ctypes.POINTER(_TokenUser)).contents.user.sid
        if not adv.ConvertSidToStringSidW(sid, ctypes.byref(sid_string)):
            raise WindowsRestoreDenied("RESTORE_SID_DENIED")
        owner_sid = sid_string.value
        sddl = "O:" + owner_sid + "D:P(A;;GA;;;" + owner_sid + ")(A;;GA;;;SY)"
        if not adv.ConvertStringSecurityDescriptorToSecurityDescriptorW(
                sddl, 1, ctypes.byref(descriptor), None):
            raise WindowsRestoreDenied("RESTORE_DACL_DENIED")
        attributes = _SecurityAttributes(
            ctypes.sizeof(_SecurityAttributes), descriptor, False
        )
        for depth in range(1, len(path.parts)):
            parent = str(Path(*path.parts[:depth]))
            handle = kernel.CreateFileW(parent, 0x00000080 | 0x00020000,
                                        0x00000001, None, 3,
                                        0x00200000 | 0x02000000, None)
            if handle is None or handle == ctypes.c_void_p(-1).value:
                raise WindowsRestoreDenied("RESTORE_PARENT_OPEN_DENIED")
            opened.append(handle)
            info = _FileInfo()
            if (not kernel.GetFileInformationByHandle(handle, ctypes.byref(info))
                    or info.attributes & 0x400 or not info.attributes & 0x10):
                raise WindowsRestoreDenied("RESTORE_PARENT_REPARSE_DENIED")
        handle = kernel.CreateFileW(str(path), 0x40000000 | 0x80000000 | 0x00020000,
                                    0, ctypes.byref(attributes), 1,
                                    0x00200000, None)
        if handle is None or handle == ctypes.c_void_p(-1).value:
            raise WindowsRestoreDenied("RESTORE_CREATE_NEW_DENIED")
        opened.append(handle)
        count = wintypes.DWORD()
        raw_buffer = ctypes.create_string_buffer(raw)
        if (not kernel.WriteFile(handle, raw_buffer, len(raw),
                                 ctypes.byref(count), None)
                or count.value != len(raw)
                or not kernel.FlushFileBuffers(handle)):
            raise WindowsRestoreDenied("RESTORE_WRITE_DENIED")
    finally:
        for handle in reversed(opened):
            kernel.CloseHandle(handle)
        if descriptor.value:
            kernel.LocalFree(descriptor)
        if sid_string.value:
            kernel.LocalFree(ctypes.cast(sid_string, ctypes.c_void_p))
        if token.value:
            kernel.CloseHandle(token)
        # Never unlink by pathname after closing the exclusive handle: another
        # actor could have replaced the path. An interrupted private file is
        # quarantined for explicit operator handling, not auto-retried.
