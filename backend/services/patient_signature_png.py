from __future__ import annotations

import base64
import binascii
import io

from fastapi import HTTPException
from PIL import Image, UnidentifiedImageError

DEFAULT_MAX_BYTES = 2 * 1024 * 1024
DEFAULT_MAX_PIXELS = 8_000_000
DEFAULT_MIN_INK_PIXELS = 24
PNG_DATA_URL_PREFIX = "data:image/png;base64,"


def validate_patient_signature_png(
    signature_base64: str,
    *,
    max_bytes: int = DEFAULT_MAX_BYTES,
    max_pixels: int = DEFAULT_MAX_PIXELS,
    min_ink_pixels: int = DEFAULT_MIN_INK_PIXELS,
) -> bytes:
    """Validate and normalize a patient-drawn PNG signature.

    This is an image-validation primitive only. It makes no legal-signature claim.
    """
    if not isinstance(signature_base64, str) or not signature_base64.startswith(PNG_DATA_URL_PREFIX):
        raise HTTPException(status_code=422, detail="Signature PNG invalide")

    encoded = signature_base64[len(PNG_DATA_URL_PREFIX):].strip()
    if not encoded:
        raise HTTPException(status_code=422, detail="Signature vide")

    encoded_limit = ((max_bytes + 2) // 3) * 4 + 32
    if len(encoded) > encoded_limit:
        raise HTTPException(status_code=413, detail="Signature trop volumineuse")

    try:
        raw = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=422, detail="Signature invalide")

    if not raw:
        raise HTTPException(status_code=422, detail="Signature vide")
    if len(raw) > max_bytes:
        raise HTTPException(status_code=413, detail="Signature trop volumineuse")

    try:
        with Image.open(io.BytesIO(raw)) as probe:
            if probe.format != "PNG":
                raise HTTPException(status_code=422, detail="Signature PNG invalide")
            width, height = probe.size
            if width < 32 or height < 32:
                raise HTTPException(status_code=422, detail="Dimensions de signature invalides")
            if width * height > max_pixels:
                raise HTTPException(status_code=413, detail="Signature trop grande")
            probe.load()
            rgba = probe.convert("RGBA")
    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(status_code=422, detail="Image de signature invalide")

    ink_pixels = 0
    for red, green, blue, alpha in rgba.getdata():
        if alpha >= 16 and (red < 245 or green < 245 or blue < 245):
            ink_pixels += 1
            if ink_pixels >= min_ink_pixels:
                break
    if ink_pixels < min_ink_pixels:
        raise HTTPException(status_code=422, detail="Signature vide")

    output = io.BytesIO()
    rgba.save(output, format="PNG", optimize=True)
    normalized = output.getvalue()
    if len(normalized) > max_bytes:
        raise HTTPException(status_code=413, detail="Signature trop volumineuse")
    return normalized
