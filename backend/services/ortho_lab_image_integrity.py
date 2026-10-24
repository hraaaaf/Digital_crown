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
) -> dict[str, Any] | None:
    """G4: a REAL cephalometric geometric trace overlay on one source-locked film.

    Source anatomy silhouettes are not invented from the isolated landmarks.
    A mandatory line, landmark, image, or hash failure suppresses the image.
    """
    if not verified_aariz_display_image_pair(angles_data, image_file):
        return None
    from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY
    from backend.services.ortho_ceph_tracing import (
        TRACE_CONTRACT, trace_geometry_from_evidence, draw_trace_overlay,
    )
    from PIL import Image
    from io import BytesIO
    from base64 import b64encode

    graph = angles_data.get(EVIDENCE_GRAPH_KEY)
    points = graph.get("landmarks") if isinstance(graph, dict) else None
    if not isinstance(points, list):
        return None
    try:
        with Image.open(image_file) as im:
            if im.size != (1935, 2400):
                return None
            image = im.convert("RGB")
    except (OSError, ValueError):
        return None
    geometry = trace_geometry_from_evidence(points, image.size)
    if geometry is None:
        return None
    draw_trace_overlay(image, geometry)
    buf = BytesIO()
    image.save(buf, "JPEG", quality=87, optimize=True, subsampling=0)
    if buf.tell() > 5_000_000:
        return None
    b64 = b64encode(buf.getvalue()).decode("ascii")
    # A fixed set of named constructions is disclosed to the reader and
    # checked again by the exact-head G4 PDF CI.
    return {
        "contract_version": TRACE_CONTRACT,
        "kind": "GEOMETRIC_CEPHALOMETRIC_TRACING",
        "data_uri": "data:image/jpeg;base64," + b64,
        "mime_type": "image/jpeg",
        "image_b64": b64,
        "geometry_sha256": geometry["geometry_sha256"],
        "source_image_sha256": angles_data["odf_lab_display_png_sha256"],
        "segment_count": geometry["segment_count"],
        "landmark_count": geometry["landmark_count"],
        "segments": [item["label"] for item in geometry["segments"]],
        "legend": [
            {"name":item["label"], "color":item["color"],
             "description":item["description"]}
            for item in geometry["segments"]
        ],
        "caption": (
            "Tracé céphalométrique superposé à la téléradiographie : "
            "repères d'experts et plans/axes géométriques SN, Francfort, "
            "NA, NB, mandibulaire et incisifs. "
            "Aariz Cephalometric Dataset (CC BY 4.0). "
            "Contours anatomiques non tracés — document de recherche, "
            "sans validation diagnostique clinique."
        ),
        "source_url": "https://doi.org/10.1038/s41597-025-05542-3",
    }
