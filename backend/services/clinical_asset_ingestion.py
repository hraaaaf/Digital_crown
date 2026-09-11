"""C3 secure ingestion and controlled thumbnail derivation for ClinicalAsset.

The ingestion boundary never trusts filenames, extensions, client MIME types, sizes or hashes.
Supported C3 payloads are intentionally narrow: JPEG, PNG, WebP and PDF. Unsupported media
fails closed until a content parser/validator exists for that format.

Validation and derivative generation happen fully in memory before the first storage write.
The caller owns the outer SQLAlchemy transaction; this service uses a nested transaction so
failed metadata/storage binding is rolled back without committing unrelated caller work.
"""
from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any, Optional
import warnings

import fitz
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy.orm import Session

from backend.models_media_core import ClinicalAsset
from backend.services.clinical_asset_service import create_clinical_asset
from backend.services.clinical_asset_storage import (
    ClinicalAssetStoreResult,
    store_clinical_asset_bytes,
)


MAX_IMPORT_BYTES = 50 * 1024 * 1024
MAX_IMAGE_PIXELS = 80_000_000
MAX_IMAGE_EDGE = 12_000
MAX_PDF_PAGES = 500
MAX_PDF_PAGE_POINTS = 20_000
MAX_PDF_PAGE_AREA = 100_000_000
PDF_PREVIEW_MAX_EDGE = 1_600
THUMBNAIL_MAX_EDGE = 512
THUMBNAIL_JPEG_QUALITY = 82

_ALLOWED_IMAGE_ASSET_TYPES = {"PHOTO", "RADIOGRAPH"}
_ALLOWED_SOURCE_KINDS = {"UPLOAD", "IMPORT", "DEVICE_CAPTURE"}
_SUPPORTED_MIME = {
    "image/jpeg": "JPEG",
    "image/png": "PNG",
    "image/webp": "WEBP",
    "application/pdf": "PDF",
}
_EXTENSION_BY_MIME = {
    "image/jpeg": {".jpg", ".jpeg"},
    "image/png": {".png"},
    "image/webp": {".webp"},
    "application/pdf": {".pdf"},
}


class ClinicalAssetIngestionError(ValueError):
    """Raised when an import payload is unsupported, unsafe or internally inconsistent."""


@dataclass(frozen=True)
class ValidatedClinicalPayload:
    content: bytes
    mime_type: str
    format_name: str
    width: Optional[int] = None
    height: Optional[int] = None
    page_count: Optional[int] = None
    thumbnail_jpeg: Optional[bytes] = None


@dataclass(frozen=True)
class ClinicalAssetIngestionResult:
    asset: ClinicalAsset
    thumbnail_asset: Optional[ClinicalAsset]
    original_store: ClinicalAssetStoreResult
    thumbnail_store: Optional[ClinicalAssetStoreResult]


def _detect_supported_mime(content: bytes) -> str:
    if content.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "image/webp"
    if content.startswith(b"%PDF-"):
        return "application/pdf"
    raise ClinicalAssetIngestionError("unsupported or unrecognized clinical media content")


def _normalize_claimed_mime(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    normalized = value.split(";", 1)[0].strip().lower()
    aliases = {"image/jpg": "image/jpeg", "image/pjpeg": "image/jpeg"}
    return aliases.get(normalized, normalized)


def _validate_filename_extension(filename: Optional[str], detected_mime: str) -> None:
    if not filename:
        return
    name = filename.strip()
    if not name or "\x00" in name or "/" in name or "\\" in name:
        raise ClinicalAssetIngestionError("original filename must be display metadata only")
    suffix = Path(name).suffix.lower()
    if suffix and suffix not in _EXTENSION_BY_MIME[detected_mime]:
        raise ClinicalAssetIngestionError("filename extension does not match validated content")


def _encode_thumbnail(image: Image.Image) -> bytes:
    image = ImageOps.exif_transpose(image)
    if image.mode not in ("RGB", "L"):
        if "A" in image.getbands():
            background = Image.new("RGB", image.size, "white")
            alpha = image.getchannel("A")
            background.paste(image.convert("RGB"), mask=alpha)
            image = background
        else:
            image = image.convert("RGB")
    elif image.mode == "L":
        image = image.convert("RGB")
    else:
        image = image.copy()

    image.thumbnail((THUMBNAIL_MAX_EDGE, THUMBNAIL_MAX_EDGE), Image.Resampling.LANCZOS)
    clean = Image.new("RGB", image.size)
    clean.paste(image)
    output = BytesIO()
    clean.save(
        output,
        format="JPEG",
        quality=THUMBNAIL_JPEG_QUALITY,
        optimize=True,
        progressive=True,
    )
    data = output.getvalue()
    if not data:
        raise ClinicalAssetIngestionError("thumbnail generation produced empty output")
    return data


def _validate_image(content: bytes, detected_mime: str) -> ValidatedClinicalPayload:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(content)) as probe:
                probe.verify()
            with Image.open(BytesIO(content)) as image:
                width, height = image.size
                if width <= 0 or height <= 0:
                    raise ClinicalAssetIngestionError("image dimensions are invalid")
                if width > MAX_IMAGE_EDGE or height > MAX_IMAGE_EDGE or width * height > MAX_IMAGE_PIXELS:
                    raise ClinicalAssetIngestionError("image dimensions exceed C3 safety limits")
                expected = _SUPPORTED_MIME[detected_mime]
                actual = (image.format or "").upper()
                if actual != expected:
                    raise ClinicalAssetIngestionError("image parser format does not match signature")
                image.load()
                thumb = _encode_thumbnail(image)
    except (
        UnidentifiedImageError,
        OSError,
        SyntaxError,
        Image.DecompressionBombWarning,
        Image.DecompressionBombError,
    ) as exc:
        raise ClinicalAssetIngestionError("image content failed parser validation") from exc

    return ValidatedClinicalPayload(
        content=content,
        mime_type=detected_mime,
        format_name=_SUPPORTED_MIME[detected_mime],
        width=width,
        height=height,
        thumbnail_jpeg=thumb,
    )


def _validate_pdf(content: bytes) -> ValidatedClinicalPayload:
    document = None
    try:
        document = fitz.open(stream=content, filetype="pdf")
        if document.needs_pass:
            raise ClinicalAssetIngestionError("encrypted PDF import is not supported in C3")
        page_count = int(document.page_count)
        if page_count < 1 or page_count > MAX_PDF_PAGES:
            raise ClinicalAssetIngestionError("PDF page count exceeds C3 safety limits")
        page = document.load_page(0)
        rect = page.rect
        width_points = float(rect.width)
        height_points = float(rect.height)
        if (
            width_points <= 0
            or height_points <= 0
            or width_points > MAX_PDF_PAGE_POINTS
            or height_points > MAX_PDF_PAGE_POINTS
            or width_points * height_points > MAX_PDF_PAGE_AREA
        ):
            raise ClinicalAssetIngestionError("PDF page dimensions exceed C3 safety limits")
        preview_scale = min(1.5, PDF_PREVIEW_MAX_EDGE / max(width_points, height_points))
        if preview_scale <= 0:
            raise ClinicalAssetIngestionError("PDF preview scale is invalid")
        pixmap = page.get_pixmap(matrix=fitz.Matrix(preview_scale, preview_scale), alpha=False)
        preview = pixmap.tobytes("png")
        with Image.open(BytesIO(preview)) as image:
            thumb = _encode_thumbnail(image)
    except ClinicalAssetIngestionError:
        raise
    except Exception as exc:
        raise ClinicalAssetIngestionError("PDF content failed parser validation") from exc
    finally:
        if document is not None:
            document.close()

    return ValidatedClinicalPayload(
        content=content,
        mime_type="application/pdf",
        format_name="PDF",
        page_count=page_count,
        thumbnail_jpeg=thumb,
    )


def validate_clinical_import_payload(
    content: bytes,
    *,
    claimed_mime_type: Optional[str] = None,
    original_filename: Optional[str] = None,
) -> ValidatedClinicalPayload:
    """Validate bytes by signature + parser, never by client metadata alone."""
    if isinstance(content, (bytearray, memoryview)):
        content = bytes(content)
    if not isinstance(content, bytes) or not content:
        raise ClinicalAssetIngestionError("clinical import content must be non-empty bytes")
    if len(content) > MAX_IMPORT_BYTES:
        raise ClinicalAssetIngestionError("clinical import exceeds C3 size limit")

    detected_mime = _detect_supported_mime(content)
    claimed = _normalize_claimed_mime(claimed_mime_type)
    if claimed is not None and claimed != detected_mime:
        raise ClinicalAssetIngestionError("claimed MIME type does not match validated content")
    _validate_filename_extension(original_filename, detected_mime)

    if detected_mime.startswith("image/"):
        return _validate_image(content, detected_mime)
    return _validate_pdf(content)


def _validate_asset_type(asset_type: str, mime_type: str) -> str:
    asset_type = str(asset_type).upper()
    if mime_type.startswith("image/"):
        if asset_type not in _ALLOWED_IMAGE_ASSET_TYPES:
            raise ClinicalAssetIngestionError("validated image requires PHOTO or RADIOGRAPH asset type")
    elif mime_type == "application/pdf" and asset_type != "DOCUMENT":
        raise ClinicalAssetIngestionError("validated PDF requires DOCUMENT asset type")
    return asset_type


def ingest_clinical_asset_bytes(
    db: Session,
    *,
    employer_id: int,
    patient_id: int,
    asset_type: str,
    source_kind: str,
    content: bytes,
    original_filename: Optional[str] = None,
    claimed_mime_type: Optional[str] = None,
    source_ref: Optional[str] = None,
    timepoint: Optional[str] = None,
    captured_at=None,
    created_by: Optional[int] = None,
    provenance_json: Optional[dict[str, Any]] = None,
    media_root: Optional[Path] = None,
) -> ClinicalAssetIngestionResult:
    """Validate, create, encrypt/store and derive a thumbnail without committing the caller transaction."""
    source_kind = str(source_kind).upper()
    if source_kind not in _ALLOWED_SOURCE_KINDS:
        raise ClinicalAssetIngestionError("C3 ingestion source_kind is not externally ingestible")

    validated = validate_clinical_import_payload(
        content,
        claimed_mime_type=claimed_mime_type,
        original_filename=original_filename,
    )
    asset_type = _validate_asset_type(asset_type, validated.mime_type)

    base_provenance = dict(provenance_json or {})
    base_provenance.update(
        {
            "validated_format": validated.format_name,
            "validation_version": "C3_V1",
        }
    )
    if validated.width is not None:
        base_provenance["width"] = validated.width
        base_provenance["height"] = validated.height
    if validated.page_count is not None:
        base_provenance["page_count"] = validated.page_count

    with db.begin_nested():
        asset = create_clinical_asset(
            db,
            employer_id=employer_id,
            patient_id=patient_id,
            asset_type=asset_type,
            source_kind=source_kind,
            source_ref=source_ref,
            original_filename=original_filename,
            mime_type=validated.mime_type,
            timepoint=timepoint,
            captured_at=captured_at,
            created_by=created_by,
            provenance_json=base_provenance,
        )
        original_store = store_clinical_asset_bytes(
            db,
            employer_id=employer_id,
            patient_id=patient_id,
            asset_id=asset.id,
            content=validated.content,
            media_root=media_root,
        )

        thumbnail_asset = None
        thumbnail_store = None
        if validated.thumbnail_jpeg is not None:
            thumbnail_asset = create_clinical_asset(
                db,
                employer_id=employer_id,
                patient_id=patient_id,
                asset_type="PHOTO",
                source_kind="DERIVED",
                source_ref="C3_THUMBNAIL_V1",
                original_filename=None,
                mime_type="image/jpeg",
                timepoint=timepoint,
                captured_at=captured_at,
                created_by=created_by,
                parent_asset_id=asset.id,
                provenance_json={
                    "derivative_kind": "THUMBNAIL",
                    "generator": "C3_V1",
                    "max_edge": THUMBNAIL_MAX_EDGE,
                },
            )
            thumbnail_store = store_clinical_asset_bytes(
                db,
                employer_id=employer_id,
                patient_id=patient_id,
                asset_id=thumbnail_asset.id,
                content=validated.thumbnail_jpeg,
                media_root=media_root,
            )

    return ClinicalAssetIngestionResult(
        asset=asset,
        thumbnail_asset=thumbnail_asset,
        original_store=original_store,
        thumbnail_store=thumbnail_store,
    )
