"""Native Windows private-keyring read security probe (not activated in product).

Read from a single checked handle. Keep every ancestor directory handle open
without FILE_SHARE_WRITE or FILE_SHARE_DELETE while traversing a local drive.
Verify security descriptor owner and protected DACL from the opened file handle.
"""
from __future__ import annotations

import ctypes
import os
from ctypes import wintypes
from pathlib import Path


class WindowsKeyringHandleDenied(Exception):
    pass


class _FileTime(ctypes.Structure):
    _fields_ = [("low", wintypes.DWORD), ("high", wintypes.DWORD)]


class _FileInfo(ctypes.Structure):
    _fields_ = [
        ("attributes", wintypes.DWORD), ("created", _FileTime),
        ("accessed", _FileTime), ("written", _FileTime),
        ("volume_serial", wintypes.DWORD), ("size_high", wintypes.DWORD),
        ("size_low", wintypes.DWORD), ("links", wintypes.DWORD),
        ("index_high", wintypes.DWORD), ("index_low", wintypes.DWORD),
    ]


class _Acl(ctypes.Structure):
    _fields_ = [
        ("revision", ctypes.c_ubyte), ("unused", ctypes.c_ubyte),
        ("size", wintypes.WORD), ("ace_count", wintypes.WORD),
        ("unused2", wintypes.WORD),
    ]


class _AceHeader(ctypes.Structure):
    _fields_ = [
        ("ace_type", ctypes.c_ubyte), ("ace_flags", ctypes.c_ubyte),
        ("ace_size", wintypes.WORD),
    ]


class _SidAndAttributes(ctypes.Structure):
    _fields_ = [("sid", ctypes.c_void_p), ("attributes", wintypes.DWORD)]


class _TokenUser(ctypes.Structure):
    _fields_ = [("user", _SidAndAttributes)]


def _require_private_acl(handle: int) -> None:
    """Validate owner, protected DACL and all explicit ALLOW ACEs on THIS handle."""
    adv = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    adv.GetSecurityInfo.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD,
        ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    adv.GetSecurityInfo.restype = wintypes.DWORD
    adv.GetSecurityDescriptorControl.argtypes = [
        ctypes.c_void_p, ctypes.POINTER(ctypes.c_ushort),
        ctypes.POINTER(wintypes.DWORD),
    ]
    adv.GetSecurityDescriptorControl.restype = wintypes.BOOL
    adv.GetAce.argtypes = [ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(ctypes.c_void_p)]
    adv.GetAce.restype = wintypes.BOOL
    adv.EqualSid.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    adv.EqualSid.restype = wintypes.BOOL
    adv.OpenProcessToken.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)
    ]
    adv.OpenProcessToken.restype = wintypes.BOOL
    adv.GetTokenInformation.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, ctypes.c_void_p,
        wintypes.DWORD, ctypes.POINTER(wintypes.DWORD),
    ]
    adv.GetTokenInformation.restype = wintypes.BOOL
    adv.ConvertStringSidToSidW.argtypes = [
        wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_void_p)
    ]
    adv.ConvertStringSidToSidW.restype = wintypes.BOOL
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p

    owner = ctypes.c_void_p()
    dacl = ctypes.c_void_p()
    descriptor = ctypes.c_void_p()
    result = adv.GetSecurityInfo(handle, 1, 0x01 | 0x04,
                                 ctypes.byref(owner), None, ctypes.byref(dacl),
                                 None, ctypes.byref(descriptor))
    if result != 0 or not descriptor.value:
        raise WindowsKeyringHandleDenied("KEYRING_SECURITY_DESCRIPTOR_DENIED")
    token = wintypes.HANDLE()
    system_sid = ctypes.c_void_p()
    try:
        control = ctypes.c_ushort()
        revision = wintypes.DWORD()
        if not adv.GetSecurityDescriptorControl(descriptor, ctypes.byref(control),
                                                ctypes.byref(revision)):
            raise WindowsKeyringHandleDenied("KEYRING_DACL_CONTROL_DENIED")
        if not control.value & 0x1000 or not dacl.value or not owner.value:
            raise WindowsKeyringHandleDenied("KEYRING_ACL_NOT_PRIVATE")
        if not adv.OpenProcessToken(kernel.GetCurrentProcess(), 0x0008,
                                    ctypes.byref(token)):
            raise WindowsKeyringHandleDenied("KEYRING_TOKEN_UNAVAILABLE")
        needed = wintypes.DWORD()
        adv.GetTokenInformation(token, 1, None, 0, ctypes.byref(needed))
        if not 0 < needed.value <= 65536:
            raise WindowsKeyringHandleDenied("KEYRING_TOKEN_UNAVAILABLE")
        token_buffer = ctypes.create_string_buffer(needed.value)
        if not adv.GetTokenInformation(token, 1, token_buffer, needed,
                                       ctypes.byref(needed)):
            raise WindowsKeyringHandleDenied("KEYRING_TOKEN_UNAVAILABLE")
        current_sid = ctypes.cast(token_buffer, ctypes.POINTER(_TokenUser)).contents.user.sid
        if not current_sid or not adv.ConvertStringSidToSidW(
                "S-1-5-18", ctypes.byref(system_sid)):
            raise WindowsKeyringHandleDenied("KEYRING_TOKEN_UNAVAILABLE")

        def expected(sid: int) -> bool:
            return bool(adv.EqualSid(sid, current_sid) or adv.EqualSid(sid, system_sid))

        if not expected(owner):
            raise WindowsKeyringHandleDenied("KEYRING_OWNER_DENIED")
        acl = ctypes.cast(dacl, ctypes.POINTER(_Acl)).contents
        if not 0 < acl.ace_count <= 64 or acl.size < ctypes.sizeof(_Acl):
            raise WindowsKeyringHandleDenied("KEYRING_DACL_INVALID")
        has_current_allow = False
        for index in range(acl.ace_count):
            ace = ctypes.c_void_p()
            if not adv.GetAce(dacl, index, ctypes.byref(ace)) or not ace.value:
                raise WindowsKeyringHandleDenied("KEYRING_DACL_INVALID")
            header = ctypes.cast(ace, ctypes.POINTER(_AceHeader)).contents
            if header.ace_flags & 0x10 or header.ace_size < 8:
                raise WindowsKeyringHandleDenied("KEYRING_INHERITED_ACE_DENIED")
            if header.ace_type not in (0, 1):
                raise WindowsKeyringHandleDenied("KEYRING_ACE_TYPE_DENIED")
            if header.ace_type == 0:
                ace_sid = ctypes.c_void_p(ace.value + 8)
                if not expected(ace_sid):
                    raise WindowsKeyringHandleDenied("KEYRING_BROAD_ACL_DENIED")
                if adv.EqualSid(ace_sid, current_sid):
                    has_current_allow = True
        if not has_current_allow:
            raise WindowsKeyringHandleDenied("KEYRING_CURRENT_USER_NOT_GRANTED")
    finally:
        if system_sid.value:
            kernel.LocalFree(system_sid)
        if token.value:
            kernel.CloseHandle(token)
        kernel.LocalFree(descriptor)


def read_no_reparse_file(path: str, *, max_bytes: int = 16384) -> bytes:
    """Windows local-drive, handle-bound, ACL-checked bounded read; no product use."""
    if os.name != "nt":
        raise WindowsKeyringHandleDenied("WINDOWS_ONLY")
    candidate = Path(path)
    if (not candidate.is_absolute() or len(candidate.drive) != 2
            or candidate.drive[1] != ":" or candidate.anchor != candidate.drive + "\\"):
        raise WindowsKeyringHandleDenied("KEYRING_PATH_UNSUPPORTED")
    parts = candidate.parts
    if len(parts) < 2 or any(
        part in ("", "..") or ":" in part or part.endswith((" ", "."))
        for part in parts[1:]
    ):
        raise WindowsKeyringHandleDenied("KEYRING_PATH_UNSUPPORTED")
    if not isinstance(max_bytes, int) or not 0 < max_bytes <= 16384:
        raise WindowsKeyringHandleDenied("KEYRING_BOUNDS_DENIED")

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
        ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
    ]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.GetFileInformationByHandle.argtypes = [wintypes.HANDLE, ctypes.c_void_p]
    kernel.GetFileInformationByHandle.restype = wintypes.BOOL
    kernel.ReadFile.argtypes = [
        wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p,
    ]
    kernel.ReadFile.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    opened = []
    try:
        # Retain all parent handles with READ-only sharing: each ancestor cannot
        # be renamed, deleted, or opened for reparse mutation while the read runs.
        for depth in range(1, len(parts) + 1):
            is_file = depth == len(parts)
            current_path = str(Path(*parts[:depth]))
            flags = 0x00200000 | (0 if is_file else 0x02000000)
            access = (0x80000000 if is_file else 0x00000080) | 0x00020000
            handle = kernel.CreateFileW(current_path, access, 0x00000001,
                                        None, 3, flags, None)
            if handle is None or handle == ctypes.c_void_p(-1).value:
                raise WindowsKeyringHandleDenied("KEYRING_OPEN_DENIED")
            opened.append(handle)
            info = _FileInfo()
            if not kernel.GetFileInformationByHandle(handle, ctypes.byref(info)):
                raise WindowsKeyringHandleDenied("KEYRING_HANDLE_INFO_DENIED")
            if info.attributes & 0x400:
                raise WindowsKeyringHandleDenied("KEYRING_REPARSE_DENIED")
            is_directory = bool(info.attributes & 0x10)
            if is_directory == is_file:
                raise WindowsKeyringHandleDenied("KEYRING_FILE_TYPE_DENIED")
            if is_file:
                size = (info.size_high << 32) | info.size_low
                if size > max_bytes:
                    raise WindowsKeyringHandleDenied("KEYRING_FILE_TOO_LARGE")
                _require_private_acl(handle)
                buffer = ctypes.create_string_buffer(max_bytes + 1)
                received = wintypes.DWORD()
                if not kernel.ReadFile(handle, buffer, max_bytes + 1,
                                       ctypes.byref(received), None):
                    raise WindowsKeyringHandleDenied("KEYRING_READ_DENIED")
                if received.value > max_bytes:
                    raise WindowsKeyringHandleDenied("KEYRING_FILE_TOO_LARGE")
                return buffer.raw[:received.value]
        raise WindowsKeyringHandleDenied("KEYRING_FILE_TYPE_DENIED")
    finally:
        for handle in reversed(opened):
            kernel.CloseHandle(handle)
