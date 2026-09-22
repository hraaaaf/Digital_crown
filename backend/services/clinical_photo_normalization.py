from __future__ import annotations

from io import BytesIO

from fastapi import HTTPException
from PIL import Image, ImageOps, UnidentifiedImageError

CLINICAL_PHOTO_MAX_BYTES = 12 * 1024 * 1024
CLINICAL_PHOTO_MAX_PIXELS = 50_000_000
CLINICAL_PHOTO_SOURCE_FORMATS = {"JPEG", "PNG", "WEBP"}


def normalize_clinical_photo(raw: bytes) -> bytes:
    """Validate, orient and rewrite a clinical image as metadata-free JPEG."""
    if not raw:
        raise HTTPException(status_code=422, detail="La photo clinique est vide.")
    if len(raw) > CLINICAL_PHOTO_MAX_BYTES:
        raise HTTPException(status_code=413, detail="La photo clinique dépasse la limite de 12 MiB.")

    try:
        with Image.open(BytesIO(raw)) as probe:
            source_format = str(probe.format or "").upper()
            width, height = probe.size
            if source_format not in CLINICAL_PHOTO_SOURCE_FORMATS:
                raise HTTPException(
                    status_code=422,
                    detail="Format de photo non pris en charge. Utilisez JPEG, PNG ou WebP.",
                )
            if width <= 0 or height <= 0 or width * height > CLINICAL_PHOTO_MAX_PIXELS:
                raise HTTPException(
                    status_code=413,
                    detail="La résolution de la photo clinique est trop élevée.",
                )
            probe.verify()

        with Image.open(BytesIO(raw)) as image:
            image = ImageOps.exif_transpose(image)
            image.load()
            if (
                image.width <= 0
                or image.height <= 0
                or image.width * image.height > CLINICAL_PHOTO_MAX_PIXELS
            ):
                raise HTTPException(
                    status_code=413,
                    detail="La résolution de la photo clinique est trop élevée.",
                )

            if image.mode in ("RGBA", "LA") or (
                image.mode == "P" and "transparency" in image.info
            ):
                rgba = image.convert("RGBA")
                normalized_image = Image.new("RGB", rgba.size, "white")
                normalized_image.paste(rgba, mask=rgba.getchannel("A"))
            else:
                normalized_image = image.convert("RGB")

            output = BytesIO()
            normalized_image.save(output, format="JPEG", quality=95, optimize=True)
            normalized = output.getvalue()
            if not normalized:
                raise HTTPException(
                    status_code=422,
                    detail="Impossible de normaliser la photo clinique.",
                )
            return normalized
    except HTTPException:
        raise
    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        Image.DecompressionBombError,
    ) as exc:
        raise HTTPException(
            status_code=422,
            detail="Le fichier sélectionné n'est pas une image clinique valide.",
        ) from exc
