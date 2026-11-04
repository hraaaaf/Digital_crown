"""LOT06 B06 — lightweight Windows native pipe transport, LAB inventory only.

Never mounted in backend.main or offered through a patient route. Exposes ONLY
one non-PHI verified-spool metadata record. Does NOT trust a clinical device,
return image bytes, or authorize patient association, upload, or receipt.
"""
from __future__ import annotations

import os
import re

from tools.imaging_gateway.native_inventory_protocol_v15 import (
    FRAME_BYTES, NativeInventoryDenied, UnassignedCapture, decode_inventory,
)

_PIPE = re.compile(r"^\\\\\.\\pipe\\DigitalCrown-LAB-R-[a-f0-9]{32}$")


def read_native_unassigned(pipe_name: str) -> UnassignedCapture | None:
    """Talk to the real restricted Windows SCM pipe as the current OS user.

    Both programmatically enforced LAB environment and actual Windows DACL
    are required. Never let the request/client choose a pipe in production.
    """
    if (os.name != "nt"
            or os.getenv("GITHUB_ACTIONS") != "true"
            or os.getenv("RUNNER_ENVIRONMENT") != "github-hosted"
            or os.getenv("RUNNER_OS") != "Windows"
            or os.getenv("ENVIRONMENT") != "test"
            or os.getenv("DIGITALCROWN_ISOLATED_RUNTIME") != "true"
            or os.getenv("DC06_B06_NATIVE_INVENTORY_LAB") != "1"
            or not isinstance(pipe_name, str)
            or not _PIPE.fullmatch(pipe_name)):
        raise NativeInventoryDenied("NATIVE_INVENTORY_LAB_DISABLED")

    import ctypes
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
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
    kernel.WaitNamedPipeW.argtypes = (wintypes.LPCWSTR, wintypes.DWORD)
    kernel.WaitNamedPipeW.restype = wintypes.BOOL

    if not kernel.WaitNamedPipeW(pipe_name, 1500):
        raise NativeInventoryDenied("NATIVE_INVENTORY_PIPE_UNAVAILABLE")
    # Strictly NO FILE_APPEND_DATA/FILE_CREATE_PIPE_INSTANCE access bit.
    handle = kernel.CreateFileW(
        pipe_name, 0x00100183, 0, None, 3, 0, None,
    )
    if handle is None or handle == ctypes.c_void_p(-1).value:
        raise NativeInventoryDenied("NATIVE_INVENTORY_PEER_DENIED")
    try:
        command = ctypes.create_string_buffer(b"I", 1)
        written = wintypes.DWORD(0)
        if not kernel.WriteFile(handle, command, 1, ctypes.byref(written), None) or written.value != 1:
            raise NativeInventoryDenied("NATIVE_INVENTORY_REQUEST_DENIED")
        data = ctypes.create_string_buffer(FRAME_BYTES)
        count = wintypes.DWORD(0)
        if not kernel.ReadFile(handle, data, FRAME_BYTES, ctypes.byref(count), None):
            raise NativeInventoryDenied("NATIVE_INVENTORY_REPLY_DENIED")
        if count.value not in (2, FRAME_BYTES):
            raise NativeInventoryDenied("NATIVE_INVENTORY_REPLY_LENGTH")
        return decode_inventory(data.raw[:count.value])
    finally:
        kernel.CloseHandle(handle)
