"""LOT06 B06 — bounded binary capture transfer wire, disposable Windows LAB.

Request: ASCII M + id (10d) + SHA256 (64hex) + offset (8d) + count (4d).
Reply: binary D + count (4d) + raw bytes, or exactly E0000 denial.
No patient, patient selector, filename, upload, ACK or media in logs.
"""
from __future__ import annotations

import re

from tools.imaging_gateway.native_inventory_protocol_v15 import (
    NativeInventoryDenied, UnassignedCapture,
)

MAX_CHUNK = 2048
# This experimental fixture is deliberately bounded to small synthetic images.
# It does NOT advertise support for 50-MiB clinical scans.
LAB_MEDIA_MAX = 16384
REQUEST_BYTES = 87
REPLY_HEADER_BYTES = 5
DENIED = b"E0000"
_REQ = re.compile(rb"^M[0-9]{10}[a-f0-9]{64}[0-9]{8}[0-9]{4}$")


def encode_request(capture: UnassignedCapture, offset: int, count: int) -> bytes:
    if (not isinstance(capture, UnassignedCapture)
            or type(capture.id) is not int or not 1 <= capture.id <= 9_999_999_999
            or not isinstance(capture.digest, str)
            or re.fullmatch(r"[a-f0-9]{64}", capture.digest) is None
            or type(capture.size) is not int or not 0 < capture.size <= LAB_MEDIA_MAX
            or capture.mime != "image/png"
            or capture.category not in ("PHOTO", "RADIOGRAPH")
            or type(offset) is not int or offset < 0 or offset >= capture.size
            or type(count) is not int or not 1 <= count <= MAX_CHUNK
            or offset + count > capture.size):
        raise NativeInventoryDenied("NATIVE_MEDIA_REQUEST_DENIED")
    frame = f"M{capture.id:010d}{capture.digest}{offset:08d}{count:04d}".encode("ascii")
    if len(frame) != REQUEST_BYTES:
        raise NativeInventoryDenied("NATIVE_MEDIA_REQUEST_SIZE_DENIED")
    return frame


def decode_request(frame: bytes) -> tuple[int, str, int, int]:
    if not isinstance(frame, bytes) or len(frame) != REQUEST_BYTES or not _REQ.fullmatch(frame):
        raise NativeInventoryDenied("NATIVE_MEDIA_REQUEST_FRAME_DENIED")
    item = int(frame[1:11])
    digest = frame[11:75].decode("ascii")
    offset, count = int(frame[75:83]), int(frame[83:87])
    if (not 1 <= item <= 9_999_999_999 or not 0 <= offset < LAB_MEDIA_MAX
            or not 1 <= count <= MAX_CHUNK or offset + count > LAB_MEDIA_MAX):
        raise NativeInventoryDenied("NATIVE_MEDIA_REQUEST_RANGE_DENIED")
    return item, digest, offset, count


def encode_response(data: bytes) -> bytes:
    if not isinstance(data, bytes) or not 1 <= len(data) <= MAX_CHUNK:
        raise NativeInventoryDenied("NATIVE_MEDIA_RESPONSE_RANGE_DENIED")
    return b"D" + f"{len(data):04d}".encode("ascii") + data


def decode_response(frame: bytes, expected_count: int) -> bytes:
    if (not isinstance(frame, bytes) or type(expected_count) is not int
            or not 1 <= expected_count <= MAX_CHUNK or frame == DENIED
            or len(frame) != expected_count + REPLY_HEADER_BYTES
            or frame[:1] != b"D" or not frame[1:5].isdigit()
            or int(frame[1:5]) != expected_count):
        raise NativeInventoryDenied("NATIVE_MEDIA_RESPONSE_DENIED")
    return frame[REPLY_HEADER_BYTES:]
