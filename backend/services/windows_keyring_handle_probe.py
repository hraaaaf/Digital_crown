"""Native Windows private-keyring read security probe (not activated in product).

Read from a single checked file handle. Traverse descendants RELATIVE to an
open verified root and keep the original directory handles until read completes.
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



class _UnicodeString(ctypes.Structure):
    _fields_ = [
        ("length", wintypes.USHORT), ("maximum_length", wintypes.USHORT),
        ("buffer", wintypes.LPWSTR),
    ]


class _ObjectAttributes(ctypes.Structure):
    _fields_ = [
        ("length", wintypes.ULONG), ("root_directory", wintypes.HANDLE),
        ("object_name", ctypes.POINTER(_UnicodeString)),
        ("attributes", wintypes.ULONG), ("security_descriptor", ctypes.c_void_p),
        ("security_quality_of_service", ctypes.c_void_p),
    ]


class _IoStatusBlock(ctypes.Structure):
    _fields_ = [("status", ctypes.c_void_p), ("information", ctypes.c_size_t)]


def _open_relative_component(parent_handle: int, leaf: str, *, directory: bool) -> int:
    """Open exactly ONE child relative to the verified parent handle (never its path).

    FILE_OPEN_REPARSE_POINT + OBJ_DONT_REPARSE disallows following a junction
    or a symbolic link. The caller must check file attributes on this handle.
    """
    if (not isinstance(parent_handle, int) or parent_handle in (0, -1)
            or not isinstance(leaf, str) or not leaf or leaf in (".", "..")
            or any(ch in leaf for ch in ("/", "\\", ":", "\x00"))
            or leaf.endswith((" ", "."))):
        raise WindowsKeyringHandleDenied("KEYRING_PATH_UNSUPPORTED")
    encoded = leaf.encode("utf-16-le")
    if not 0 < len(encoded) <= 32760:
        raise WindowsKeyringHandleDenied("KEYRING_PATH_UNSUPPORTED")
    name_buffer = ctypes.create_unicode_buffer(leaf)
    name = _UnicodeString(len(encoded), len(encoded) + 2,
                          ctypes.cast(name_buffer, wintypes.LPWSTR))
    attrs = _ObjectAttributes(
        ctypes.sizeof(_ObjectAttributes), wintypes.HANDLE(parent_handle),
        ctypes.pointer(name), 0x00000040 | 0x00001000,  # CASE_INSENSITIVE | DONT_REPARSE
        None, None,
    )
    io = _IoStatusBlock()
    handle = wintypes.HANDLE()
    ntdll = ctypes.WinDLL("ntdll", use_last_error=True)
    ntdll.NtCreateFile.argtypes = [
        ctypes.POINTER(wintypes.HANDLE), wintypes.DWORD,
        ctypes.POINTER(_ObjectAttributes), ctypes.POINTER(_IoStatusBlock),
        ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD,
        wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD,
    ]
    ntdll.NtCreateFile.restype = ctypes.c_long
    status = ntdll.NtCreateFile(
        ctypes.byref(handle),
        (0x00000080 | 0x00000020 | 0x00020000 | 0x00100000
         if directory else 0x80000000 | 0x00020000 | 0x00100000),
        ctypes.byref(attrs), ctypes.byref(io), None,
        0x00000080, (0x00000007 if directory else 0x00000001), 1,
        # normal; directories share READ|WRITE|DELETE deliberately so rename races
        # remain possible, while handle-relative lineage stays immutable.
        # Files share READ only. FILE_OPEN never creates a missing component.
        0x00200000 | 0x00000020 | (0x00000001 if directory else 0x00000040),
        None, 0,
    )
    if status != 0 or not handle.value or io.information != 1:
        if handle.value:
            ctypes.WinDLL("kernel32", use_last_error=True).CloseHandle(handle)
        raise WindowsKeyringHandleDenied("KEYRING_OPEN_DENIED")
    return handle.value


def _open_checked_directory_chain(kernel, parts: tuple[str, ...], opened: list[int]) -> int:
    """One volume root path open, then strictly relative one-component opens.

    Keeping verified handles open protects object identity even when their
    names change concurrently; later opens cannot traverse a replacement path.
    Caller owns and closes every handle (including on error).
    """
    if not parts:
        raise WindowsKeyringHandleDenied("KEYRING_PATH_UNSUPPORTED")
    handle = kernel.CreateFileW(parts[0], 0x00000080 | 0x00020000,
                                0x00000007, None, 3,
                                0x00200000 | 0x02000000, None)
    if handle is None or handle == ctypes.c_void_p(-1).value:
        raise WindowsKeyringHandleDenied("KEYRING_OPEN_DENIED")
    opened.append(handle)
    for i in range(len(parts)):
        if i:
            handle = _open_relative_component(opened[-1], parts[i], directory=True)
            opened.append(handle)
        info = _FileInfo()
        if not kernel.GetFileInformationByHandle(handle, ctypes.byref(info)):
            raise WindowsKeyringHandleDenied("KEYRING_HANDLE_INFO_DENIED")
        if info.attributes & 0x400:
            raise WindowsKeyringHandleDenied("KEYRING_REPARSE_DENIED")
        if not info.attributes & 0x10:
            raise WindowsKeyringHandleDenied("KEYRING_FILE_TYPE_DENIED")
    return opened[-1]




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
    from backend.core.platform import get_platform_adapter

    if not get_platform_adapter().is_windows:
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
        _open_checked_directory_chain(kernel, parts[:-1], opened)
        # The file itself is resolved against the previously verified parent
        # HANDLE; do not independently resolve the full path for a last time.
        handle = _open_relative_component(opened[-1], parts[-1], directory=False)
        opened.append(handle)
        info = _FileInfo()
        if not kernel.GetFileInformationByHandle(handle, ctypes.byref(info)):
            raise WindowsKeyringHandleDenied("KEYRING_HANDLE_INFO_DENIED")
        if info.attributes & 0x400:
            raise WindowsKeyringHandleDenied("KEYRING_REPARSE_DENIED")
        if info.attributes & 0x10:
            raise WindowsKeyringHandleDenied("KEYRING_FILE_TYPE_DENIED")
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
    finally:
        for handle in reversed(opened):
            kernel.CloseHandle(handle)
