"""LOT06 B06: bounded native inventory wire contract (metadata ONLY).

This frame is intentionally NOT a signed device claim or clinical authority.
It contains one AES-GCM-verified unassigned capture, never patient/appointment/
filename or image bytes. All consumers must fail closed on malformed frames.
"""
from __future__ import annotations

import re

from tools.imaging_gateway.unassigned_queue_v15 import UnassignedCapture

# Fixed 86-byte ASCII frame: I1 | item id (10d) | size (8d) |
# SHA-256 digest (64 lowercase hex) | MIME code | category code.
# N0 means an *integrity-verified* empty queue; E2 means refusal/error.
FRAME_BYTES = 86
EMPTY = b"N0"
DENIED = b"E2"
_MIME_TO_CODE = {"image/png": "P", "image/jpeg": "J",
                 "image/webp": "W", "application/pdf": "D"}
_CODE_TO_MIME = {value: key for key, value in _MIME_TO_CODE.items()}
_CATEGORY_TO_CODE = {"PHOTO": "P", "RADIOGRAPH": "R"}
_CODE_TO_CATEGORY = {value: key for key, value in _CATEGORY_TO_CODE.items()}
_FRAME = re.compile(rb"^I1[0-9]{10}[0-9]{8}[a-f0-9]{64}[PJWD][PR]$")


class NativeInventoryDenied(ValueError):
    """Non-PHI error; never interpret a refused read as an empty queue."""


def encode_inventory(capture: UnassignedCapture | None) -> bytes:
    if capture is None:
        return EMPTY
    if (not isinstance(capture, UnassignedCapture)
            or type(capture.id) is not int or not 1 <= capture.id <= 9_999_999_999
            or type(capture.size) is not int or not 1 <= capture.size <= 50 * 1024 * 1024
            or not isinstance(capture.digest, str)
            or not re.fullmatch(r"[a-f0-9]{64}", capture.digest)
            or capture.mime not in _MIME_TO_CODE
            or capture.category not in _CATEGORY_TO_CODE):
        raise NativeInventoryDenied("NATIVE_UNASSIGNED_METADATA_DENIED")
    result = (f"I1{capture.id:010d}{capture.size:08d}{capture.digest}"
              f"{_MIME_TO_CODE[capture.mime]}{_CATEGORY_TO_CODE[capture.category]}").encode("ascii")
    if len(result) != FRAME_BYTES:
        raise NativeInventoryDenied("NATIVE_UNASSIGNED_FRAME_LENGTH_DENIED")
    return result


def decode_inventory(frame: bytes) -> UnassignedCapture | None:
    if not isinstance(frame, bytes):
        raise NativeInventoryDenied("NATIVE_INVENTORY_TYPE_DENIED")
    if frame == EMPTY:
        return None
    if frame == DENIED or len(frame) != FRAME_BYTES or not _FRAME.fullmatch(frame):
        raise NativeInventoryDenied("NATIVE_INVENTORY_FRAME_DENIED")
    try:
        result = UnassignedCapture(
            id=int(frame[2:12]),
            size=int(frame[12:20]),
            digest=frame[20:84].decode("ascii"),
            mime=_CODE_TO_MIME[chr(frame[84])],
            category=_CODE_TO_CATEGORY[chr(frame[85])],
        )
        if encode_inventory(result) != frame:
            raise NativeInventoryDenied("NATIVE_INVENTORY_NONCANONICAL")
        return result
    except (ValueError, KeyError) as exc:
        raise NativeInventoryDenied("NATIVE_INVENTORY_FRAME_DENIED") from exc
