"""LOT06 B06 — genuine Win32 media-bytes read, disposable hosted-LAB only.

This is NOT a product/media endpoint or staff-authorized release path.
Windows pipe DACL restricts account; the service re-verifies AES-GCM and
pending capture before every slice. Caller checks final hash/size/MIME.
"""
from __future__ import annotations

import hashlib
import os

from tools.imaging_gateway.media_validation import validated_mime
from tools.imaging_gateway.native_inventory_protocol_v15 import (
    NativeInventoryDenied, UnassignedCapture,
)
from tools.imaging_gateway.native_inventory_windows_v15 import (
    _check_pipe_server_pid, _require_server_pid, read_native_unassigned,
)
from tools.imaging_gateway.native_media_protocol_v15 import (
    DENIED, LAB_MEDIA_MAX, MAX_CHUNK,
    decode_response, encode_request,
)


def read_native_capture_bytes(
    pipe_name: str, capture: UnassignedCapture, *,
    expected_server_pid: int | None = None,
) -> bytes:
    if (os.getenv("DC06_B06_NATIVE_MEDIA_LAB") != "1"
            or not isinstance(capture, UnassignedCapture)
            or capture.mime != "image/png"
            or type(capture.size) is not int
            or not 0 < capture.size <= LAB_MEDIA_MAX):
        raise NativeInventoryDenied("NATIVE_MEDIA_LAB_DISABLED")
    _require_server_pid(expected_server_pid)

    # This call verifies the OS and CI scope, opens native pipe through Win32,
    # and requires identical freshly AES-validated, unassigned inventory.
    if read_native_unassigned(
        pipe_name, expected_server_pid=expected_server_pid,
    ) != capture:
        raise NativeInventoryDenied("NATIVE_MEDIA_INVENTORY_CHANGED")

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
    kernel.WaitNamedPipeW.argtypes = (wintypes.LPCWSTR, wintypes.DWORD)
    kernel.WaitNamedPipeW.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel.CloseHandle.restype = wintypes.BOOL

    def receive_exact(handle, count: int) -> bytes:
        parts = bytearray()
        while len(parts) < count:
            piece = ctypes.create_string_buffer(count - len(parts))
            received = wintypes.DWORD(0)
            if (not kernel.ReadFile(
                    handle, piece, count - len(parts),
                    ctypes.byref(received), None
                ) or received.value == 0):
                raise NativeInventoryDenied("NATIVE_MEDIA_TRUNCATED")
            parts.extend(piece.raw[:received.value])
        return bytes(parts)

    data = bytearray()
    for offset in range(0, capture.size, MAX_CHUNK):
        size = min(MAX_CHUNK, capture.size - offset)
        frame = encode_request(capture, offset, size)
        if not kernel.WaitNamedPipeW(pipe_name, 1500):
            raise NativeInventoryDenied("NATIVE_MEDIA_PIPE_UNAVAILABLE")
        handle = kernel.CreateFileW(pipe_name, 0x00100183, 0, None, 3, 0, None)
        if handle is None or handle == ctypes.c_void_p(-1).value:
            raise NativeInventoryDenied("NATIVE_MEDIA_PEER_DENIED")
        try:
            # Check peer of THIS M handle, never only a previous Q/I probe.
            _check_pipe_server_pid(kernel, handle, expected_server_pid)
            message = ctypes.create_string_buffer(frame, len(frame))
            written = wintypes.DWORD(0)
            if (not kernel.WriteFile(
                    handle, message, len(frame), ctypes.byref(written), None
                ) or written.value != len(frame)):
                raise NativeInventoryDenied("NATIVE_MEDIA_SEND_DENIED")
            header = receive_exact(handle, 5)
            if header == DENIED or header[:1] != b"D" or not header[1:].isdigit():
                raise NativeInventoryDenied("NATIVE_MEDIA_SERVICE_REFUSED")
            if int(header[1:]) != size:
                raise NativeInventoryDenied("NATIVE_MEDIA_LENGTH_MISMATCH")
            payload = receive_exact(handle, size)
            data.extend(decode_response(header + payload, size))
            # The test service retains the byte pipe until receipt of this
            # purely transport-level drain marker. This is NOT a durable ACK.
            drain = ctypes.create_string_buffer(b"K", 1)
            acknowledged = wintypes.DWORD(0)
            if (not kernel.WriteFile(handle, drain, 1,
                    ctypes.byref(acknowledged), None) or acknowledged.value != 1):
                raise NativeInventoryDenied("NATIVE_MEDIA_DRAIN_FAILED")
        finally:
            kernel.CloseHandle(handle)

    # Recheck inventory after all fragments: no stale patient association or
    # capture swap, even when service restarted between requests.
    if (len(data) != capture.size
            or hashlib.sha256(data).hexdigest() != capture.digest
            or not validated_mime(bytes(data), capture.mime)
            or read_native_unassigned(
                pipe_name, expected_server_pid=expected_server_pid,
            ) != capture):
        raise NativeInventoryDenied("NATIVE_MEDIA_FINAL_INTEGRITY_DENIED")
    return bytes(data)
