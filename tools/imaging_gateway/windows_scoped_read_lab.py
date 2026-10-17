"""LAB-only Windows single-file reads anchored to a verified directory handle.

Use NT relative opens (RootDirectory) rather than reopening a full path after
checking it. The leaf must be a single name, opened without following reparse
points. Store operations are separate and NOT certified race-free by this file.
"""
from __future__ import annotations
import os
from pathlib import Path


def _win_api():
    import ctypes
    from ctypes import wintypes

    class FileInfo(ctypes.Structure):
        _fields_ = [
            ("attributes", wintypes.DWORD),
            ("created", wintypes.FILETIME),
            ("accessed", wintypes.FILETIME),
            ("written", wintypes.FILETIME),
            ("volume", wintypes.DWORD),
            ("size_high", wintypes.DWORD),
            ("size_low", wintypes.DWORD),
            ("links", wintypes.DWORD),
            ("index_high", wintypes.DWORD),
            ("index_low", wintypes.DWORD),
        ]

    class UnicodeString(ctypes.Structure):
        _fields_ = [
            ("Length", wintypes.USHORT),
            ("MaximumLength", wintypes.USHORT),
            ("Buffer", wintypes.LPWSTR),
        ]

    class ObjectAttributes(ctypes.Structure):
        _fields_ = [
            ("Length", wintypes.ULONG),
            ("RootDirectory", wintypes.HANDLE),
            ("ObjectName", ctypes.POINTER(UnicodeString)),
            ("Attributes", wintypes.ULONG),
            ("SecurityDescriptor", ctypes.c_void_p),
            ("SecurityQualityOfService", ctypes.c_void_p),
        ]

    class IoStatusBlock(ctypes.Structure):
        _fields_ = [
            ("Status", ctypes.c_void_p),
            ("Information", ctypes.c_size_t),
        ]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    ntdll = ctypes.WinDLL("ntdll", use_last_error=True)
    kernel.CreateFileW.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
        wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
    ]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    kernel.GetFileInformationByHandle.argtypes = [
        wintypes.HANDLE, ctypes.POINTER(FileInfo),
    ]
    kernel.GetFileInformationByHandle.restype = wintypes.BOOL
    ntdll.NtCreateFile.argtypes = [
        ctypes.POINTER(wintypes.HANDLE), wintypes.DWORD,
        ctypes.POINTER(ObjectAttributes), ctypes.POINTER(IoStatusBlock),
        ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD,
        wintypes.DWORD, ctypes.c_void_p, wintypes.ULONG,
    ]
    ntdll.NtCreateFile.restype = ctypes.c_long
    return ctypes, wintypes, kernel, ntdll, FileInfo, UnicodeString, ObjectAttributes, IoStatusBlock


def _identity_from_handle(kernel, ctypes, handle, FileInfo):
    info = FileInfo()
    if not kernel.GetFileInformationByHandle(handle, ctypes.byref(info)):
        raise OSError(ctypes.get_last_error(), "IMAGING_WINDOWS_FILE_ID_FAILED")
    if info.attributes & 0x400:
        raise OSError("IMAGING_WINDOWS_REPARSE_ROOT_REJECTED")
    return (info.volume, (info.index_high << 32) | info.index_low)


def _open_root(path, *, write=False):
    ctypes, wintypes, kernel, ntdll, info, uni, attrs, ios = _win_api()
    handle = kernel.CreateFileW(
        str(Path(path).absolute()), (0x001000A3 if write else 0x001000A1), 0x1 | 0x2 | 0x4,
        None, 3, 0x02000000 | 0x00200000, None,
    )
    if handle in (None, ctypes.c_void_p(-1).value):
        raise OSError(ctypes.get_last_error(), "IMAGING_WINDOWS_ROOT_OPEN_FAILED")
    return ctypes, wintypes, kernel, ntdll, info, uni, attrs, ios, handle


def directory_identity(path):
    """Win32 volume/file ID, not path spelling or case or lexical ancestry."""
    if os.name != "nt":
        return None
    ctypes, wintypes, kernel, ntdll, info, uni, attrs, ios, root = _open_root(path)
    try:
        return _identity_from_handle(kernel, ctypes, root, info)
    finally:
        kernel.CloseHandle(root)


def open_relative_read(root_path, leaf, expected_root):
    """Return an fd for a single regular child of the original watch directory.

    Caller owns fd and must check fstat before/after reading. If the named
    root is swapped, native volume/file ID disagrees BEFORE any content read.
    NT RootDirectory anchors the child open to that exact verified handle.
    """
    if os.name != "nt":
        raise RuntimeError("WINDOWS_ONLY")
    if not leaf or leaf in (".", "..") or any(ch in leaf for ch in ("/", "\\", ":")):
        raise OSError("IMAGING_INVALID_RELATIVE_LEAF")
    import msvcrt
    ctypes, wintypes, kernel, ntdll, info, uni, attrs, ios, parent = _open_root(root_path)
    try:
        if _identity_from_handle(kernel, ctypes, parent, info) != expected_root:
            raise OSError("IMAGING_WINDOWS_WATCH_ID_CHANGED")
        name_buffer = ctypes.create_unicode_buffer(leaf)
        name = uni(
            Length=len(leaf) * 2, MaximumLength=(len(leaf) + 1) * 2,
            Buffer=ctypes.cast(name_buffer, wintypes.LPWSTR),
        )
        obj = attrs(
            Length=ctypes.sizeof(attrs), RootDirectory=parent,
            ObjectName=ctypes.pointer(name),
            Attributes=0x40 | 0x1000,  # OBJ_CASE_INSENSITIVE | OBJ_DONT_REPARSE
            SecurityDescriptor=None, SecurityQualityOfService=None,
        )
        status = ios()
        child = wintypes.HANDLE()
        # FILE_GENERIC_READ, FILE_SHARE_{READ,WRITE,DELETE}, FILE_OPEN;
        # NON_DIRECTORY | OPEN_REPARSE_POINT | SYNCHRONOUS_IO_NONALERT.
        ntstatus = ntdll.NtCreateFile(
            ctypes.byref(child), 0x00120089, ctypes.byref(obj),
            ctypes.byref(status), None, 0, 7, 1,
            0x40 | 0x00200000 | 0x20, None, 0,
        )
        if ntstatus < 0:
            raise OSError("IMAGING_WINDOWS_RELATIVE_OPEN_DENIED")
        owned = False
        try:
            # Fail closed for a symlink, junction, mount point or other reparse.
            _identity_from_handle(kernel, ctypes, child, info)
            fd = msvcrt.open_osfhandle(int(child.value), os.O_RDONLY | os.O_BINARY)
            owned = True  # Ownership transferred to the CRT fd.
            return fd
        finally:
            if not owned:
                kernel.CloseHandle(child)
    finally:
        kernel.CloseHandle(parent)
