"""LOT06-E: synthetic adapter capability contract. No device IO or server writes."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re


class AdapterRejected(ValueError):
    pass


class SourceKind(str, Enum):
    HOT_FOLDER = "HOT_FOLDER"
    DICOM = "DICOM"
    TWAIN = "TWAIN"
    VENDOR_SDK = "VENDOR_SDK"


class AdapterStatus(str, Enum):
    UNSUPPORTED = "UNSUPPORTED"
    NEEDS_DRIVER = "NEEDS_DRIVER"
    SIMULATED = "SIMULATED"


@dataclass(frozen=True)
class AdapterCapability:
    kind: SourceKind
    status: AdapterStatus
    supports_live_capture: bool
    supports_patient_link: bool
    certified_hardware: bool


REGISTRY = {
    SourceKind.HOT_FOLDER: AdapterCapability(
        SourceKind.HOT_FOLDER, AdapterStatus.SIMULATED, False, False, False),
    SourceKind.DICOM: AdapterCapability(
        SourceKind.DICOM, AdapterStatus.NEEDS_DRIVER, False, False, False),
    SourceKind.TWAIN: AdapterCapability(
        SourceKind.TWAIN, AdapterStatus.NEEDS_DRIVER, False, False, False),
    SourceKind.VENDOR_SDK: AdapterCapability(
        SourceKind.VENDOR_SDK, AdapterStatus.UNSUPPORTED, False, False, False),
}


@dataclass(frozen=True)
class CaptureProposal:
    kind: SourceKind
    capture_id: str
    sha256: str
    byte_size: int
    category: str
    mime_type: str
    workstation: str


_ID = re.compile(r"^[A-Za-z0-9_-]{8,128}$")
_SCOPE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_HASH = re.compile(r"^[a-f0-9]{64}$")
_MIME = {"image/png", "image/jpeg", "image/webp", "application/pdf"}
_CATEGORY = {"PHOTO_CLINICAL", "RVG", "PANORAMIC", "CEPHALOMETRY", "OTHER"}


def capability(kind: SourceKind) -> AdapterCapability:
    if not isinstance(kind, SourceKind):
        raise AdapterRejected("UNKNOWN_ADAPTER")
    return REGISTRY[kind]


def propose_capture(*, kind: SourceKind, capture_id: str, sha256: str,
                    byte_size: int, category: str, mime_type: str,
                    workstation: str) -> CaptureProposal:
    """Metadata only; no source files or patient identities accepted."""
    adapter = capability(kind)
    if adapter.status != AdapterStatus.SIMULATED:
        raise AdapterRejected("ADAPTER_NOT_ENABLED")
    if not isinstance(capture_id, str) or not _ID.fullmatch(capture_id):
        raise AdapterRejected("INVALID_CAPTURE_ID")
    if not isinstance(workstation, str) or not _SCOPE.fullmatch(workstation):
        raise AdapterRejected("INVALID_WORKSTATION")
    if not isinstance(sha256, str) or not _HASH.fullmatch(sha256):
        raise AdapterRejected("INVALID_SHA")
    if type(byte_size) is not int or not 0 < byte_size <= 50 * 1024 * 1024:
        raise AdapterRejected("INVALID_BYTE_COUNT")
    if category not in _CATEGORY or mime_type not in _MIME:
        raise AdapterRejected("INVALID_MEDIA_CLASS")
    if category != "PHOTO_CLINICAL" and mime_type != "application/pdf":
        raise AdapterRejected("MODALITY_PARSER_MISSING")
    return CaptureProposal(kind, capture_id, sha256, byte_size,
                           category, mime_type, workstation)
