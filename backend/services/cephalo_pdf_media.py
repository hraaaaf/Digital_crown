"""Verified local-only imagery for the cephalometric PDF.

Every image originates from a selected, authorized patient/study or a
tenant-scoped encrypted ClinicalAsset. No client paths, URLs or base64 payloads.
Image pixels are decoded and bounded before the PDF renderer receives them.
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import re

from PIL import Image, ImageOps
from sqlalchemy.orm import Session

from backend.core.media_paths import get_imaging_root
from backend.services.clinical_asset_storage import read_clinical_asset_bytes
from backend.services.ortho_media_record import build_ortho_media_record

_RADIO_PREFIX = "api/static/uploads/radios/"
_SAFE_FILENAME = re.compile(r"^[a-zA-Z0-9_-]{1,120}\\.(?:png|jpe?g|webp)$", re.I)
_MAX_IMAGE_BYTES = 10 * 1024 * 1024
_MAX_PIXELS = 25_000_000
_THUMBNAIL_EDGE = 1400


def _verified_jpeg(content: bytes) -> bytes:
    if not isinstance(content, bytes) or not content or len(content) > _MAX_IMAGE_BYTES:
        raise ValueError("Clinical image missing or oversize")
    with Image.open(BytesIO(content)) as original:
        if original.width * original.height > _MAX_PIXELS:
            raise ValueError("Clinical image too large")
        if original.format not in {"JPEG", "PNG", "WEBP"}:
            raise ValueError("Unsupported clinical image")
        normalized = ImageOps.exif_transpose(original)
        normalized.thumbnail((_THUMBNAIL_EDGE, _THUMBNAIL_EDGE))
        output = BytesIO()
        normalized.convert("RGB").save(output, format="JPEG", quality=83)
        return output.getvalue()


def _authorized_study_radio(image_original_path: str | None) -> bytes | None:
    """Only exact persisted URLs for local radios, never caller filesystem paths."""
    if not isinstance(image_original_path, str) or not image_original_path.startswith(_RADIO_PREFIX):
        return None
    name = image_original_path[len(_RADIO_PREFIX):]
    if not _SAFE_FILENAME.fullmatch(name):
        return None
    root = (get_imaging_root() / "radios").resolve()
    candidate = (root / name).resolve()
    if candidate.parent != root or not candidate.is_file() or candidate.stat().st_size > _MAX_IMAGE_BYTES:
        return None
    return _verified_jpeg(candidate.read_bytes())


def load_cephalo_pdf_media(
    db: Session, *, employer_id: int, patient_id: int, image_original_path: str | None,
) -> dict:
    """Read only canonical T0 photos from the patient's own tenant.

    Model hooks are not image sources; unavailable 3-D models and UI-only tracings
    are never invented or represented as certified visual evidence.
    """
    radio = _authorized_study_radio(image_original_path)
    record = build_ortho_media_record(
        db, employer_id=employer_id, patient_id=patient_id, timepoint="T0",
    )
    photographs: list[dict] = []
    unavailable: list[str] = []
    for slot in record["photo_slots"]:
        if slot.get("state") != "FILLED" or not isinstance(slot.get("asset"), dict):
            continue
        asset = slot["asset"]
        if asset.get("mime_type") not in {"image/png", "image/jpeg", "image/webp"}:
            unavailable.append(str(slot.get("slot_id")))
            continue
        try:
            content = read_clinical_asset_bytes(
                db, employer_id=employer_id, patient_id=patient_id,
                asset_id=int(asset["asset_id"]),
            )
            image_bytes = _verified_jpeg(content)
        except (ValueError, OSError, RuntimeError, KeyError, TypeError):
            unavailable.append(str(slot.get("slot_id")))
            continue
        slot_id = str(slot["slot_id"])
        photographs.append({
            "slot_id": slot_id,
            "group": "Extra-buccales" if slot_id.startswith("EXTRA_") else "Intra-buccales",
            "label": slot_id.replace("EXTRA_", "").replace("INTRA_", "").replace("_", " ").title(),
            "jpeg": image_bytes,
        })
    return {"radio_jpeg": radio, "photos": photographs, "media_unavailable": unavailable}
