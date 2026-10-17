"""Native Windows, LAB-only encrypted spool write on a verified folder HANDLE.

A producer may rename a *path* between check and open. This writer instead
creates the temporary ciphertext using NtCreateFile(RootDirectory=spool_handle),
then renames that *same file handle* with FileRenameInfo relative to the same
verified directory handle. No arbitrary absolute path is used for writes.

No SQLite or installer ACL guarantee is supplied by this module.
"""
from __future__ import annotations

import os
from pathlib import Path

from tools.imaging_gateway.windows_scoped_read_lab import _win_api, _open_root, _identity_from_handle


def write_ciphertext(root_path: Path, name: str, data: bytes, expected_root) -> None:
    if os.name != "nt":
        raise RuntimeError("WINDOWS_ONLY")
    if not name or name in (".", "..") or any(char in name for char in ("/", "\\", ":")):
        raise OSError("IMAGING_INVALID_SPOOL_LEAF")
    if not name.endswith(".dc6") or len(name) > 80:
        raise OSError("IMAGING_INVALID_SPOOL_FILENAME")
    import ctypes
    import msvcrt
    import secrets
    from ctypes import wintypes

    (ct, wt, kernel, ntdll, FileInfo, UnicodeString, ObjectAttributes,
     IoStatusBlock, parent) = _open_root(root_path)
    fd = None
    file_handle = None
    published = False
    try:
        if _identity_from_handle(kernel, ct, parent, FileInfo) != expected_root:
            raise OSError("IMAGING_SPOOL_ROOT_ID_CHANGED")
        temp_name = ".partial-" + secrets.token_hex(16)
        leaf_buffer = ct.create_unicode_buffer(temp_name)
        leaf_string = UnicodeString(
            Length=len(temp_name) * 2,
            MaximumLength=(len(temp_name) + 1) * 2,
            Buffer=ct.cast(leaf_buffer, wt.LPWSTR),
        )
        obj = ObjectAttributes(
            Length=ct.sizeof(ObjectAttributes),
            RootDirectory=parent,
            ObjectName=ct.pointer(leaf_string),
            Attributes=0x40 | 0x1000,  # case insensitive, no reparse traversal
            SecurityDescriptor=None, SecurityQualityOfService=None,
        )
        io = IoStatusBlock()
        child = wt.HANDLE()
        # WRITE + DELETE rights, FILE_CREATE (never open existing), no reparse.
        status = ntdll.NtCreateFile(
            ct.byref(child), 0x00130116, ct.byref(obj), ct.byref(io),
            None, 0x80, 0x1 | 0x2, 2,
            0x40 | 0x00200000 | 0x20, None, 0,
        )
        if status < 0:
            raise OSError("IMAGING_SPOOL_NATIVE_CREATE_FAILED")
        file_handle = child
        fd = msvcrt.open_osfhandle(int(child.value), os.O_BINARY | os.O_WRONLY)
        file_handle = None  # CRT fd owns handle
        with os.fdopen(fd, "wb", closefd=False) as writer:
            writer.write(data)
            writer.flush()
            os.fsync(writer.fileno())

        # Rename by source handle and *destination root handle*, not by
        # re-resolving either the temp directory or the target's full path.
        class RenameInfo(ct.Structure):
            _fields_ = [
                ("ReplaceIfExists", wt.BOOL),
                ("RootDirectory", wt.HANDLE),
                ("FileNameLength", wt.DWORD),
                ("FileName", wt.WCHAR * len(name)),
            ]

        file_info = RenameInfo()
        file_info.ReplaceIfExists = 0  # collision fails closed
        file_info.RootDirectory = parent
        file_info.FileNameLength = len(name) * ct.sizeof(wt.WCHAR)
        file_info.FileName = name
        kernel.SetFileInformationByHandle.argtypes = [
            wt.HANDLE, ct.c_int, ct.c_void_p, wt.DWORD,
        ]
        kernel.SetFileInformationByHandle.restype = wt.BOOL
        file_os_handle = wt.HANDLE(msvcrt.get_osfhandle(fd))
        if not kernel.SetFileInformationByHandle(
            file_os_handle, 3, ct.byref(file_info), ct.sizeof(file_info)
        ):
            raise OSError(ct.get_last_error(), "IMAGING_SPOOL_ATOMIC_RENAME_FAILED")
        published = True
    finally:
        if fd is not None:
            if not published:
                class DispositionInfo(ct.Structure):
                    _fields_ = [("DeleteFile", wt.BOOL)]
                delete_info = DispositionInfo(1)
                kernel.SetFileInformationByHandle(
                    wt.HANDLE(msvcrt.get_osfhandle(fd)), 4,
                    ct.byref(delete_info), ct.sizeof(delete_info),
                )
            os.close(fd)
        if file_handle is not None:
            kernel.CloseHandle(file_handle)
        kernel.CloseHandle(parent)
