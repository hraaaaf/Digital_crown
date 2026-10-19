"""LOT05.7-J6: Windows NT relative-to-handle read, disposable FAKE-only lab.

No clinical imports or application installation. The initial absolute root
handle is a TEST trust anchor, not a proven clinical installer/ACL boundary.
NtCreateFile relative to retained directory handles demonstrates a narrower
race property; it is not a complete restore authorization or durability proof.
"""
from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path

FLAG = "LOT05J6_ANCHORED_NT_FAKE_ONLY"
PAYLOAD = b"LOT05J6_ANCHORED_FAKE_ONLY"


class NativeRefused(PermissionError):
    pass


def _environment(root: Path):
    if (os.name != "nt" or os.getenv(FLAG) != "1"
            or not isinstance(root, Path) or not root.is_absolute()
            or not root.name.startswith("lot05j6_fake_")
            or not root.is_dir() or root.is_symlink() or root.is_junction()):
        raise NativeRefused("J6_EPHEMERAL_NT_ROOT_REQUIRED")


def anchored_fake_read(root: Path, *, before_leaf=None) -> bytes:
    """Use a retained parent HANDLE for every child; never reopen child by path."""
    _environment(root)
    import ctypes
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    ntdll = ctypes.WinDLL("ntdll", use_last_error=True)
    root_access = 0x80000000
    share = 1 | 2 | 4
    invalid_handle = ctypes.c_void_p(-1).value
    kernel.CreateFileW.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
        wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    kernel.GetFileInformationByHandle.argtypes = [wintypes.HANDLE, ctypes.c_void_p]
    kernel.GetFileInformationByHandle.restype = wintypes.BOOL
    kernel.ReadFile.argtypes = [
        wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p]
    kernel.ReadFile.restype = wintypes.BOOL

    class FILETIME(ctypes.Structure):
        _fields_ = [("low", wintypes.DWORD), ("high", wintypes.DWORD)]

    class INFO(ctypes.Structure):
        _fields_ = [
            ("attributes", wintypes.DWORD), ("creation", FILETIME),
            ("access", FILETIME), ("write", FILETIME),
            ("volume", wintypes.DWORD), ("size_hi", wintypes.DWORD),
            ("size_lo", wintypes.DWORD), ("links", wintypes.DWORD),
            ("id_hi", wintypes.DWORD), ("id_lo", wintypes.DWORD)]

    class UNICODE_STRING(ctypes.Structure):
        _fields_ = [
            ("Length", wintypes.USHORT), ("MaximumLength", wintypes.USHORT),
            ("Buffer", ctypes.c_wchar_p)]

    class OBJECT_ATTRIBUTES(ctypes.Structure):
        _fields_ = [
            ("Length", wintypes.ULONG), ("RootDirectory", wintypes.HANDLE),
            ("ObjectName", ctypes.POINTER(UNICODE_STRING)),
            ("Attributes", wintypes.ULONG),
            ("SecurityDescriptor", ctypes.c_void_p),
            ("SecurityQualityOfService", ctypes.c_void_p)]

    class IO_STATUS_BLOCK(ctypes.Structure):
        _fields_ = [("Status", ctypes.c_void_p), ("Information", ctypes.c_size_t)]

    ntdll.NtCreateFile.argtypes = [
        ctypes.POINTER(wintypes.HANDLE), wintypes.DWORD,
        ctypes.POINTER(OBJECT_ATTRIBUTES), ctypes.POINTER(IO_STATUS_BLOCK),
        ctypes.c_void_p, wintypes.ULONG, wintypes.ULONG, wintypes.ULONG,
        wintypes.ULONG, ctypes.c_void_p, wintypes.ULONG]
    ntdll.NtCreateFile.restype = wintypes.LONG

    @contextmanager
    def hold(handle):
        native_value = handle.value if hasattr(handle, "value") else handle
        if native_value is None or native_value == invalid_handle:
            raise NativeRefused("J6_NT_HANDLE_OPEN_FAILED")
        try:
            yield handle
        finally:
            kernel.CloseHandle(handle)

    def check(handle, directory: bool):
        info = INFO()
        if not kernel.GetFileInformationByHandle(handle, ctypes.byref(info)):
            raise NativeRefused("J6_NT_HANDLE_INFO_FAILED")
        if info.attributes & 0x400:
            raise NativeRefused("J6_REPARSE_ENTRY_REFUSED")
        if bool(info.attributes & 0x10) != directory:
            raise NativeRefused("J6_HANDLE_TYPE_REFUSED")
        if not directory and info.links != 1:
            raise NativeRefused("J6_HARDLINK_REFUSED")
        return (info.volume, info.id_hi, info.id_lo)

    def child(parent, segment: str, directory: bool):
        if (not segment or segment in (".", "..")
                or any(x in segment for x in "\\/:")
                or "\x00" in segment or len(segment) > 80):
            raise NativeRefused("J6_SINGLE_RELATIVE_COMPONENT_REQUIRED")
        text = ctypes.create_unicode_buffer(segment)
        uni = UNICODE_STRING(len(segment) * 2, (len(segment) + 1) * 2,
                             ctypes.cast(text, ctypes.c_wchar_p))
        attr = OBJECT_ATTRIBUTES(
            ctypes.sizeof(OBJECT_ATTRIBUTES), parent, ctypes.pointer(uni),
            0x40 | 0x1000, None, None)  # case insensitive + OBJ_DONT_REPARSE
        io = IO_STATUS_BLOCK()
        output = wintypes.HANDLE()
        # read attributes and traverse directories; data read only for leaf.
        desired = 0x00100000 | 0x80 | (0x20 if directory else 0x1)
        options = 0x20 | 0x00200000 | (0x1 if directory else 0x40)
        status = ntdll.NtCreateFile(
            ctypes.byref(output), desired, ctypes.byref(attr),
            ctypes.byref(io), None, 0, share, 1, options, None, 0)
        if status != 0:
            raise NativeRefused("J6_NT_RELATIVE_OPEN_REJECTED")
        return output

    first = kernel.CreateFileW(
        str(root), root_access, share, None, 3,
        0x02000000 | 0x00200000, None)
    with hold(first) as root_handle:
        check(root_handle, directory=True)
        with hold(child(root_handle, "inputs", True)) as folder_handle:
            check(folder_handle, directory=True)
            if before_leaf is not None:
                before_leaf()
            with hold(child(folder_handle, "payload.fake", False)) as leaf:
                check(leaf, directory=False)
                buf = ctypes.create_string_buffer(1024)
                count = wintypes.DWORD(0)
                if not kernel.ReadFile(leaf, buf, 1024, ctypes.byref(count), None):
                    raise NativeRefused("J6_NT_HANDLE_READ_FAILED")
                value = buf.raw[:count.value]
                if value != PAYLOAD:
                    raise NativeRefused("J6_NT_FAKE_CONTENT_DENIED")
                return value
