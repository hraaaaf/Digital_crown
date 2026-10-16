"""LOT06-H: Windows CurrentUser DPAPI key custody LAB ONLY.

This isolated module is not connected to the acquisition CLI or clinical ingestion.
Its local revocation flag is rollbackable: NEVER claim cryptographic erasure.
"""
from __future__ import annotations

import base64
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import stat

_ID = re.compile(r"[A-Za-z0-9_-]{1,64}\Z")
_MAX_RECORD = 8192
_SCHEMA = frozenset({"version", "scope", "binding", "sealed"})
_UI_FORBIDDEN = 0x01


class KeyCustodyError(RuntimeError):
    """Error code only: no path, account, DPAPI payload or OS exception text."""


class _DataBlob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD),
                ("pbData", ctypes.POINTER(ctypes.c_ubyte))]


def _input_blob(data: bytes):
    buffer = ctypes.create_string_buffer(data)
    blob = _DataBlob(len(data),
                     ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    return blob, buffer


def _dpapi(data: bytes, entropy: bytes, *, unprotect: bool) -> bytes:
    if os.name != "nt":
        raise KeyCustodyError("WINDOWS_DPAPI_REQUIRED")
    # User profile and logon identity are part of Windows DPAPI CurrentUser.
    try:
        crypt = ctypes.WinDLL("crypt32", use_last_error=True)
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    except (OSError, AttributeError):
        raise KeyCustodyError("DPAPI_API_UNAVAILABLE") from None
    func = crypt.CryptUnprotectData if unprotect else crypt.CryptProtectData
    if unprotect:
        func.argtypes = [
            ctypes.POINTER(_DataBlob), ctypes.POINTER(ctypes.c_wchar_p),
            ctypes.POINTER(_DataBlob), ctypes.c_void_p, ctypes.c_void_p,
            wintypes.DWORD, ctypes.POINTER(_DataBlob),
        ]
    else:
        func.argtypes = [
            ctypes.POINTER(_DataBlob), ctypes.c_wchar_p,
            ctypes.POINTER(_DataBlob), ctypes.c_void_p, ctypes.c_void_p,
            wintypes.DWORD, ctypes.POINTER(_DataBlob),
        ]
    func.restype = wintypes.BOOL
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    source, source_buf = _input_blob(data)
    binding, binding_buf = _input_blob(entropy)
    output = _DataBlob()
    try:
        if not func(ctypes.byref(source), None, ctypes.byref(binding),
                    None, None, _UI_FORBIDDEN, ctypes.byref(output)):
            raise KeyCustodyError(
                "DPAPI_UNPROTECT_FAILED" if unprotect else "DPAPI_PROTECT_FAILED"
            )
        if not output.pbData or not 0 < output.cbData <= _MAX_RECORD:
            raise KeyCustodyError("DPAPI_RESULT_INVALID")
        return ctypes.string_at(output.pbData, output.cbData)
    except (OSError, AttributeError) as exc:
        raise KeyCustodyError("DPAPI_API_UNAVAILABLE") from None
    finally:
        if output.pbData:
            ctypes.memset(output.pbData, 0, output.cbData)
            kernel.LocalFree(ctypes.cast(output.pbData, ctypes.c_void_p))
        # Zero mutable input copies made for the Windows ABI.
        ctypes.memset(source_buf, 0, len(source_buf))
        ctypes.memset(binding_buf, 0, len(binding_buf))


def _binding(cabinet: str, workstation: str) -> bytes:
    if not isinstance(cabinet, str) or not isinstance(workstation, str):
        raise KeyCustodyError("INVALID_DEVICE_SCOPE")
    if not _ID.fullmatch(cabinet) or not _ID.fullmatch(workstation):
        raise KeyCustodyError("INVALID_DEVICE_SCOPE")
    return hashlib.sha256(
        b"DC06H|CURRENT_USER|v1|" +
        cabinet.encode("ascii") + b"|" + workstation.encode("ascii")
    ).digest()


def _revocation_path(path: Path) -> Path:
    return path.with_name(path.name + ".revoked")


def _check_not_revoked(path: Path) -> None:
    marker = _revocation_path(path)
    # A link or any record at this path blocks access; it must never be
    # interpreted as permission or automatically removed on restoration.
    if marker.exists() or marker.is_symlink():
        raise KeyCustodyError("KEY_LOCALLY_REVOKED")


def _read(path: Path) -> bytes:
    if path.is_symlink():
        raise KeyCustodyError("UNSAFE_KEY_RECORD")
    try:
        first = os.stat(path, follow_symlinks=False)
        if not stat.S_ISREG(first.st_mode) or first.st_nlink != 1:
            raise KeyCustodyError("UNSAFE_KEY_RECORD")
        if not 0 < first.st_size <= _MAX_RECORD:
            raise KeyCustodyError("KEY_RECORD_SIZE_INVALID")
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(path, flags)
        try:
            opened = os.fstat(fd)
            signature = (first.st_dev, first.st_ino, first.st_size,
                         first.st_mtime_ns, first.st_ctime_ns)
            def matches(value):
                return (stat.S_ISREG(value.st_mode) and value.st_nlink == 1 and
                        (value.st_dev, value.st_ino, value.st_size,
                         value.st_mtime_ns, value.st_ctime_ns) == signature)
            if not matches(opened):
                raise KeyCustodyError("KEY_RECORD_CHANGED")
            with os.fdopen(fd, "rb", closefd=False) as handle:
                raw = handle.read(_MAX_RECORD + 1)
            after = os.fstat(fd)
        finally:
            os.close(fd)
        final = os.stat(path, follow_symlinks=False)
        if not matches(after) or not matches(final) or len(raw) != first.st_size:
            raise KeyCustodyError("KEY_RECORD_CHANGED")
        return raw
    except FileNotFoundError:
        raise KeyCustodyError("KEY_RECORD_MISSING") from None
    except OSError:
        raise KeyCustodyError("KEY_RECORD_UNREADABLE") from None


def _open_record(raw: bytes, binding: bytes) -> bytes:
    if len(raw) > _MAX_RECORD:
        raise KeyCustodyError("KEY_RECORD_SIZE_INVALID")
    try:
        obj = json.loads(raw.decode("utf-8"))
        if not isinstance(obj, dict) or frozenset(obj) != _SCHEMA:
            raise ValueError()
        if type(obj["version"]) is not int or obj["version"] != 1:
            raise ValueError()
        if obj["scope"] != "CURRENT_USER" or obj["binding"] != binding.hex():
            raise KeyCustodyError("KEY_SCOPE_MISMATCH")
        sealed = base64.b64decode(obj["sealed"], validate=True)
        if not 32 <= len(sealed) <= 4096:
            raise ValueError()
    except (ValueError, UnicodeError, TypeError, KeyError):
        raise KeyCustodyError("KEY_RECORD_INVALID") from None
    key = _dpapi(sealed, binding, unprotect=True)
    if len(key) != 32:
        raise KeyCustodyError("KEY_LENGTH_INVALID")
    return key


def _write_exclusive(path: Path, content: bytes) -> None:
    if path.is_symlink() or not path.parent.is_dir():
        raise KeyCustodyError("KEY_PATH_NOT_READY")
    try:
        # A half-written record left by a crash is rejected by _read.
        # Never overwrite/recycle it silently.
        with path.open("xb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError:
        raise KeyCustodyError("KEY_RECORD_ALREADY_EXISTS") from None
    except (PermissionError, IsADirectoryError, OSError):
        raise KeyCustodyError("KEY_RECORD_WRITE_FAILED") from None


def provision(path: Path, cabinet: str, workstation: str) -> None:
    """Create a random AES-256 key, sealed under the CURRENT Windows user."""
    path = Path(path)
    _check_not_revoked(path)
    binding = _binding(cabinet, workstation)
    if path.exists() or path.is_symlink():
        raise KeyCustodyError("KEY_RECORD_ALREADY_EXISTS")
    key = secrets.token_bytes(32)
    sealed = _dpapi(key, binding, unprotect=False)
    record = {
        "version": 1,
        "scope": "CURRENT_USER",
        "binding": binding.hex(),
        "sealed": base64.b64encode(sealed).decode("ascii"),
    }
    _write_exclusive(path, json.dumps(record, separators=(",", ":")).encode())


def unlock(path: Path, cabinet: str, workstation: str) -> bytes:
    """Memory-only access under the same Windows user/profile and device scope."""
    path = Path(path)
    _check_not_revoked(path)
    key = _open_record(_read(path), _binding(cabinet, workstation))
    _check_not_revoked(path)
    return key


def backup_sealed(source: Path, backup: Path, cabinet: str, workstation: str) -> None:
    """Save only DPAPI ciphertext; does not back up the user's DPAPI master keys."""
    source, backup = Path(source), Path(backup)
    _check_not_revoked(source)
    raw = _read(source)
    _open_record(raw, _binding(cabinet, workstation))
    _write_exclusive(backup, raw)


def restore_same_user(backup: Path, destination: Path,
                      cabinet: str, workstation: str) -> None:
    """No overwrite and no bypass of a local revocation marker."""
    backup, destination = Path(backup), Path(destination)
    _check_not_revoked(destination)
    raw = _read(backup)
    _open_record(raw, _binding(cabinet, workstation))
    _write_exclusive(destination, raw)


def revoke_locally(path: Path, cabinet: str, workstation: str) -> None:
    """Only an app-side tombstone. Not key destruction or reliable remote revocation."""
    path = Path(path)
    unlock(path, cabinet, workstation)
    # Marker keeps restored backups blocked at this same path, but a local
    # administrator can delete/rollback it. No claim of irreversible erasure.
    _write_exclusive(_revocation_path(path), b"DC06H-LOCAL-REVOKED-v1\n")


def rotate_existing_spool(*_args, **_kwargs) -> None:
    """Current DC6A spool has no key_id: changing the key would strand media."""
    raise KeyCustodyError("ROTATION_REQUIRES_VERSIONED_SPOOL_AND_REWRAP")
