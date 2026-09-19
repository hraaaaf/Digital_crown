from __future__ import annotations

import ctypes
import os
from ctypes import wintypes

_DPAPI_ENTROPY = b"Digital Crown Patient Companion remote keys v1"
_CRYPTPROTECT_UI_FORBIDDEN = 0x1


class OsKeyProtectionUnavailable(RuntimeError):
    pass


class _DATA_BLOB(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_ubyte)),
    ]


def _blob(value: bytes) -> tuple[_DATA_BLOB, ctypes.Array]:
    buffer = (ctypes.c_ubyte * len(value)).from_buffer_copy(value)
    return (
        _DATA_BLOB(
            cbData=len(value),
            pbData=ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)),
        ),
        buffer,
    )


def _windows_crypto():
    if os.name != "nt":
        raise OsKeyProtectionUnavailable(
            "Patient Companion remote cabinet keys require an OS-bound key protector; "
            "v1 supports Windows DPAPI only."
        )
    crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    crypt32.CryptProtectData.argtypes = [
        ctypes.POINTER(_DATA_BLOB),
        wintypes.LPCWSTR,
        ctypes.POINTER(_DATA_BLOB),
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(_DATA_BLOB),
    ]
    crypt32.CryptProtectData.restype = wintypes.BOOL

    crypt32.CryptUnprotectData.argtypes = [
        ctypes.POINTER(_DATA_BLOB),
        ctypes.c_void_p,
        ctypes.POINTER(_DATA_BLOB),
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(_DATA_BLOB),
    ]
    crypt32.CryptUnprotectData.restype = wintypes.BOOL

    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p
    return crypt32, kernel32


def _raise_last_error(operation: str) -> None:
    code = ctypes.get_last_error()
    raise OSError(code, f"{operation} failed with Windows error {code}")


def protect_os_bound(plaintext: bytes) -> bytes:
    if not plaintext:
        raise ValueError("cannot protect empty key material")
    crypt32, kernel32 = _windows_crypto()
    source, source_buffer = _blob(plaintext)
    entropy, entropy_buffer = _blob(_DPAPI_ENTROPY)
    output = _DATA_BLOB()

    ok = crypt32.CryptProtectData(
        ctypes.byref(source),
        None,
        ctypes.byref(entropy),
        None,
        None,
        _CRYPTPROTECT_UI_FORBIDDEN,
        ctypes.byref(output),
    )
    # Keep buffers alive until the OS call returns.
    _ = source_buffer, entropy_buffer
    if not ok:
        _raise_last_error("CryptProtectData")
    try:
        return ctypes.string_at(output.pbData, output.cbData)
    finally:
        kernel32.LocalFree(ctypes.cast(output.pbData, ctypes.c_void_p))


def unprotect_os_bound(ciphertext: bytes) -> bytes:
    if not ciphertext:
        raise ValueError("cannot unprotect empty key material")
    crypt32, kernel32 = _windows_crypto()
    source, source_buffer = _blob(ciphertext)
    entropy, entropy_buffer = _blob(_DPAPI_ENTROPY)
    output = _DATA_BLOB()

    ok = crypt32.CryptUnprotectData(
        ctypes.byref(source),
        None,
        ctypes.byref(entropy),
        None,
        None,
        _CRYPTPROTECT_UI_FORBIDDEN,
        ctypes.byref(output),
    )
    _ = source_buffer, entropy_buffer
    if not ok:
        _raise_last_error("CryptUnprotectData")
    try:
        return ctypes.string_at(output.pbData, output.cbData)
    finally:
        kernel32.LocalFree(ctypes.cast(output.pbData, ctypes.c_void_p))
