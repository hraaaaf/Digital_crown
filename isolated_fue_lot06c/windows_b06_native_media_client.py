"""B06 real Windows separate-user binary spool probe; synthetic PNG only.

Never print, persist or upload media. Positive + bad id/hash prove the
service itself refuses forged capture requests (not only the client API).
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import hashlib
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from isolated_fue_lot06c.scm_spool_read_b03 import PNG
from tools.imaging_gateway.native_inventory_protocol_v15 import (
    NativeInventoryDenied, UnassignedCapture,
)
from tools.imaging_gateway.native_inventory_windows_v15 import read_native_unassigned
from tools.imaging_gateway.native_media_protocol_v15 import DENIED, encode_request
from tools.imaging_gateway.native_media_windows_v15 import read_native_capture_bytes


def direct_lab_probe(pipe: str, request: bytes) -> bytes | None:
    """Return exactly the binary reply header, NOT image bytes or log content."""
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.WaitNamedPipeW.argtypes = (wintypes.LPCWSTR, wintypes.DWORD)
    kernel.WaitNamedPipeW.restype = wintypes.BOOL
    kernel.CreateFileW.argtypes = (
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
        wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
    )
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.ReadFile.argtypes = (
        wintypes.HANDLE, wintypes.LPVOID, wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID,
    )
    kernel.ReadFile.restype = wintypes.BOOL
    kernel.WriteFile.argtypes = (
        wintypes.HANDLE, wintypes.LPCVOID, wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID,
    )
    kernel.WriteFile.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel.CloseHandle.restype = wintypes.BOOL
    if not kernel.WaitNamedPipeW(pipe, 1500):
        return None
    handle = kernel.CreateFileW(pipe, 0x00100183, 0, None, 3, 0, None)
    if handle is None or handle == ctypes.c_void_p(-1).value:
        return None
    try:
        message = ctypes.create_string_buffer(request, len(request))
        sent = wintypes.DWORD(0)
        if (not kernel.WriteFile(handle, message, len(request), ctypes.byref(sent), None)
                or sent.value != len(request)):
            return None
        header = ctypes.create_string_buffer(5)
        got = wintypes.DWORD(0)
        if not kernel.ReadFile(handle, header, 5, ctypes.byref(got), None):
            return None
        if got.value != 5:
            return None
        return header.raw
    finally:
        kernel.CloseHandle(handle)


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[1] not in {
        "Valid", "WrongKey", "Tampered", "Unauthorized",
    }:
        return 64
    pipe, mode = argv
    os.environ["DC06_B06_NATIVE_INVENTORY_LAB"] = "1"
    os.environ["DC06_B06_NATIVE_MEDIA_LAB"] = "1"
    expected = UnassignedCapture(
        id=1, digest=hashlib.sha256(PNG).hexdigest(),
        size=len(PNG), mime="image/png", category="PHOTO",
    )
    if mode == "Valid":
        try:
            capture = read_native_unassigned(pipe)
            if capture != expected:
                return 65
            result = read_native_capture_bytes(pipe, capture)
            if result != PNG:
                return 66
            print("DC06_B06_NATIVE_REAL_WINDOWS_BINARY_AES_MEDIA_SHA256_PASS")
            if direct_lab_probe(pipe, encode_request(
                UnassignedCapture(
                    id=2, digest=expected.digest, size=expected.size,
                    mime="image/png", category="PHOTO",
                ), 0, len(PNG),
            )) != DENIED:
                return 67
            if direct_lab_probe(pipe, encode_request(
                UnassignedCapture(
                    id=1, digest="0" * 64, size=expected.size,
                    mime="image/png", category="PHOTO",
                ), 0, len(PNG),
            )) != DENIED:
                return 68
            print("DC06_B06_NATIVE_SERVER_WRONG_ID_AND_DIGEST_DENIED_PASS")
            # Full binary acquisition does not create an ACK or patient link.
            return 0
        except NativeInventoryDenied:
            return 69
    frame = encode_request(expected, 0, len(PNG))
    answer = direct_lab_probe(pipe, frame)
    if mode == "Unauthorized":
        if answer is not None:
            return 70
    elif answer != DENIED:
        # Must reach the AES-GCM verification refusal from service, not ACL.
        return 71
    print("DC06_B06_NATIVE_MEDIA_" + mode.upper() + "_DENIED_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
