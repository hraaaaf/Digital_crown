"""Research LAB-only guard: image bytes must match the expert-paired trace.

Never infer that filenames, patient IDs or good-looking coordinates establish
an image-to-landmark match. This does not constitute patient care validation.
"""
from __future__ import annotations
import hashlib
import re
from pathlib import Path
from typing import Any, Mapping


def verified_aariz_display_image_pair(angles_data: Mapping[str, Any], image_file: Path) -> bool:
    if not isinstance(angles_data, dict):
        return False
    if angles_data.get("odf_lab_image_landmark_alignment") != "VERIFIED_AARIZ_EXPERT_PAIR":
        return False
    fields = (
        "odf_lab_display_png_sha256",
        "odf_lab_source_image_sha256",
        "odf_lab_source_senior_sha256",
        "odf_lab_source_junior_sha256",
    )
    if not all(
        isinstance(angles_data.get(key), str)
        and re.fullmatch("[0-9a-f]{64}", angles_data[key])
        for key in fields
    ):
        return False
    if not isinstance(angles_data.get("odf_lab_dataset_image_id"), str):
        return False
    if "/cephalograms/" not in ("/" + angles_data["odf_lab_dataset_image_id"].lower()):
        return False
    try:
        if not image_file.is_file() or image_file.stat().st_size > 30_000_000:
            return False
        digest=hashlib.sha256(image_file.read_bytes()).hexdigest()
    except OSError:
        return False
    return digest==angles_data["odf_lab_display_png_sha256"]


def build_verified_aariz_research_plate(
    angles_data: Mapping[str, Any], image_file: Path,
) -> dict[str, str] | None:
    """Generate a LAB-only annotated film from the *same persisted evidence*.

    The image and the clinical measurements are both linked to a SHA256-checked
    matching Aariz image, not to a synthetic landmark overlay or a client photo.
    Annotated research imagery is never automatically a diagnostic document.
    """
    if not verified_aariz_display_image_pair(angles_data, image_file):
        return None
    from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY
    from PIL import Image, ImageDraw, ImageFont
    from io import BytesIO
    from base64 import b64encode
    from math import isfinite

    graph = angles_data.get(EVIDENCE_GRAPH_KEY)
    points = graph.get("landmarks") if isinstance(graph, dict) else None
    if not isinstance(points, list):
        return None
    selected = {}
    for entry in points:
        if not isinstance(entry, dict):
            return None
        key, x, y = entry.get("landmark_id"), entry.get("x"), entry.get("y")
        if (
            not isinstance(key, str) or not key or key in selected
            or isinstance(x, bool) or isinstance(y, bool)
            or not isinstance(x, (int, float)) or not isinstance(y, (int, float))
            or not isfinite(x) or not isfinite(y)
        ):
            return None
        selected[key] = (float(x), float(y))
    mandatory = {"S", "N", "A", "B", "Po", "Or", "Go", "Me",
                 "U1_incisal", "L1_incisal", "U1_apex", "L1_apex"}
    if len(selected) < 19 or not mandatory.issubset(selected):
        return None
    try:
        with Image.open(image_file) as im:
            if im.size != (1935, 2400):
                return None
            image = im.convert("RGB")
    except (OSError, ValueError):
        return None
    if any(not (0 <= x < image.width and 0 <= y < image.height)
           for x, y in selected.values()):
        return None

    draw = ImageDraw.Draw(image)
    # Professional readable markers, without altering the clinical image
    # geometry or printing fabricated contour traces.
    names = ("S", "N", "A", "B", "Po", "Or", "Go", "Me", "Gn",
             "U1_incisal", "L1_incisal", "U1_apex", "L1_apex")
    for name in names:
        if name not in selected:
            continue
        x, y = selected[name]
        draw.ellipse((x - 7, y - 7, x + 7, y + 7),
                     outline=(245, 197, 87), width=4)
        draw.text((x + 13, y - 11), name, fill=(245, 197, 87), stroke_width=2,
                  stroke_fill=(24, 30, 41))
    buf = BytesIO()
    image.save(buf, "JPEG", quality=84, optimize=True, subsampling=0)
    if buf.tell() > 5_000_000:
        return None
    return {
        "data_uri": "data:image/jpeg;base64," + b64encode(buf.getvalue()).decode("ascii"),
        "mime_type": "image/jpeg",
        "image_b64": b64encode(buf.getvalue()).decode("ascii"),
        "caption": (
            "Téléradiographie de profil — données de recherche Aariz, "
            "repères anatomiques annotés par experts. "
            "Aariz Cephalometric Dataset (CC BY 4.0). "
            "Illustration scientifique, sans validation diagnostique clinique."
        ),
        "source_url": "https://doi.org/10.1038/s41597-025-05542-3",
    }
