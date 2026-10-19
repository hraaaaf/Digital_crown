"""LOT05.7-J5: actual Win32 CreateFileW handle / file identity FAKE lab.

No application imports, clinical paths, SCM installation or patient files.
Checking a file through a handle is NOT equivalent to a race-free relative
open under an anchored parent handle. That limitation is intentionally tested.
"""
from __future__ import annotations

import os
from pathlib import Path

FLAG = "LOT05J5_NATIVE_HANDLES_FAKE_ONLY"
CONTENTS = b"J5_FAKE_WIN32_HANDLE_PROOF"
FILE_ATTRIBUTE_REPARSE_POINT = 0x400
FILE_ATTRIBUTE_DIRECTORY = 0x10
FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
FILE_SHARE_READ = 0x1
FILE_SHARE_WRITE = 0x2
FILE_SHARE_DELETE = 0x4
OPEN_EXISTING = 3
GENERIC_READ = 0x80000000


class J5Denied(PermissionError):
    pass


def require_fake_windows(root: Path) -> None:
    if (os.name != "nt" or os.getenv(FLAG) != "1"
            or not isinstance(root, Path) or not root.is_absolute()
            or not root.name.startswith("lot05j5_fake_")
            or root.is_symlink() or root.is_junction()
            or not root.is_dir()):
        raise J5Denied("NATIVE_FAKE_WINDOWS_ROOT_REQUIRED")


def _kernel():
    """Win32 binding declarations stay local; Linux must fail before loading."""
    import ctypes
    from ctypes import wintypes
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = (
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
        wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE)
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.GetFileInformationByHandle.argtypes = (
        wintypes.HANDLE, wintypes.LPVOID)
    kernel.GetFileInformationByHandle.restype = wintypes.BOOL
    kernel.ReadFile.argtypes = (
        wintypes.HANDLE, wintypes.LPVOID, wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID)
    kernel.ReadFile.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel.CloseHandle.restype = wintypes.BOOL
    return ctypes, wintypes, kernel


def inspect_win32_handles(root: Path, *, attack_hook=None) -> bytes:
    """Check opened Win32 file identities and refuse fixture link attacks.

    Input contains exactly root/inputs/payload.fake. Root and inputs and
    payload are opened with FILE_FLAG_OPEN_REPARSE_POINT to inspect the entry
    itself. Race hook executes AFTER first file open, BEFORE second open.
    No clinical writes, service activation, symlink traversal or persistence.
    """
    require_fake_windows(root)
    import contextlib

    ctypes, wintypes, kernel = _kernel()

    class FILETIME(ctypes.Structure):
        _fields_ = [("lo", wintypes.DWORD), ("hi", wintypes.DWORD)]

    class HANDLE_INFO(ctypes.Structure):
        _fields_ = [
            ("attributes", wintypes.DWORD),
            ("created", FILETIME), ("accessed", FILETIME), ("modified", FILETIME),
            ("volume", wintypes.DWORD),
            ("size_hi", wintypes.DWORD), ("size_lo", wintypes.DWORD),
            ("links", wintypes.DWORD),
            ("file_hi", wintypes.DWORD), ("file_lo", wintypes.DWORD)]

    @contextlib.contextmanager
    def opened(path: Path, *, directory: bool):
        flags = FILE_FLAG_OPEN_REPARSE_POINT | (
            FILE_FLAG_BACKUP_SEMANTICS if directory else 0)
        handle = kernel.CreateFileW(str(path), GENERIC_READ,
                                    FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
                                    None, OPEN_EXISTING, flags, None)
        if handle is None or int(handle) == ctypes.c_void_p(-1).value:
            raise J5Denied("WIN32_HANDLE_OPEN_FAILED")
        try:
            info = HANDLE_INFO()
            if not kernel.GetFileInformationByHandle(handle, ctypes.byref(info)):
                raise J5Denied("WIN32_HANDLE_INFO_FAILED")
            if info.attributes & FILE_ATTRIBUTE_REPARSE_POINT:
                raise J5Denied("WIN32_REPARSE_POINT_DENIED")
            if bool(info.attributes & FILE_ATTRIBUTE_DIRECTORY) != directory:
                raise J5Denied("WIN32_UNEXPECTED_HANDLE_TYPE")
            if not directory and info.links != 1:
                raise J5Denied("WIN32_HARDLINK_DENIED")
            yield handle, (info.volume, info.file_hi, info.file_lo)
        finally:
            kernel.CloseHandle(handle)

    folder = root / "inputs"
    file = folder / "payload.fake"
    try:
        with opened(root, directory=True) as (_, root_id):
            with opened(folder, directory=True) as (_, folder_id):
                with opened(file, directory=False) as (first_handle, file_id):
                    if attack_hook is not None:
                        attack_hook()
                    with opened(root, directory=True) as (_, next_root_id):
                        with opened(folder, directory=True) as (_, next_folder_id):
                            with opened(file, directory=False) as (read_handle, next_file_id):
                                if ((root_id, folder_id, file_id) !=
                                        (next_root_id, next_folder_id, next_file_id)):
                                    raise J5Denied("WIN32_OPENED_FILE_ID_CHANGED")
                                buf = ctypes.create_string_buffer(1024)
                                read = wintypes.DWORD(0)
                                if not kernel.ReadFile(read_handle, buf, 1024,
                                                       ctypes.byref(read), None):
                                    raise J5Denied("WIN32_READFILE_FAILED")
                                value = buf.raw[:read.value]
                                if value != CONTENTS:
                                    raise J5Denied("WIN32_FAKE_CONTENT_MISMATCH")
                                return value
    except J5Denied:
        raise
    except (OSError, ValueError) as exc:
        raise J5Denied("WIN32_NATIVE_HANDLE_REJECTED") from exc
