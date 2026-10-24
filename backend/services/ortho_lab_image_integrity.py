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
