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


def build_g5_anatomical_two_views(
    angles_data: Mapping[str, Any], image_file: Path,
    approved_source: Mapping[str, Any], *,
    patient_id: int, analysis_id: int, revision: int,
    scientific_digest: str,
) -> dict[str, Any] | None:
    """G5: one approved hand-drawn contour set -> X-ray overlay + white tracing.

    This never creates an anatomy curve from ceph landmark coordinates.
    Both images use the identical pixels/approved manual strokes; the G4
    geometric reference planes remain available but visually secondary.
    """
    if not verified_aariz_display_image_pair(angles_data, image_file):
        return None
    from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY
    from backend.services.ortho_ceph_tracing import trace_geometry_from_evidence, draw_trace_overlay
    from backend.services.ortho_anatomical_trace import (
        draw_contours, verify_approved_anatomical_trace, CONTOUR_CONTRACT,
    )
    from PIL import Image, ImageDraw
    from io import BytesIO
    from base64 import b64encode

    graph=angles_data.get(EVIDENCE_GRAPH_KEY)
    landmarks=graph.get("landmarks") if isinstance(graph,dict) else None
    if not isinstance(landmarks,list):
        return None
    try:
        with Image.open(image_file) as source:
            if source.size!=(1935,2400):
                return None
            radio=source.convert("RGB")
    except (OSError,ValueError):
        return None
    image_sha=hashlib.sha256(image_file.read_bytes()).hexdigest()
    approved=verify_approved_anatomical_trace(
        approved_source,patient_id=patient_id,analysis_id=analysis_id,
        revision=revision,scientific_digest=scientific_digest,
        image_sha256=image_sha,image_size=radio.size,
    )
    geometry=trace_geometry_from_evidence(landmarks,radio.size)
    if approved is None or geometry is None:
        return None

    overlay=radio.copy()
    draw_trace_overlay(overlay,geometry)
    draw_contours(overlay,approved)

    clean=Image.new("RGB",radio.size,"white")
    # Thin geometry, intentionally subordinate to continuous anatomy contours.
    thin=ImageDraw.Draw(clean)
    for item in geometry["segments"]:
        a,b=item["from_xy"],item["to_xy"]
        thin.line([tuple(a),tuple(b)],fill="#BBC4CF",width=2)
    draw_contours(clean,approved,background_is_white=True)

    def encode(image):
        mem=BytesIO()
        image.save(mem,"JPEG",quality=86,optimize=True,subsampling=0)
        if mem.tell()>5_000_000:
            raise ValueError("G5_IMAGE_TOO_LARGE")
        raw=b64encode(mem.getvalue()).decode("ascii")
        return raw, "data:image/jpeg;base64,"+raw
    try:
        overlay_b64,overlay_uri=encode(overlay)
        clean_b64,clean_uri=encode(clean)
    except (ValueError,OSError):
        return None
    return {
        "kind":"G5_MANUAL_ANATOMICAL_TRACE",
        "contract_version":CONTOUR_CONTRACT,
        "image_b64":overlay_b64,"data_uri":overlay_uri,
        "anatomical_only_b64":clean_b64,
        "anatomical_only_data_uri":clean_uri,
        "contour_digest":approved["contour_digest"],
        "image_sha256":image_sha,
        "geometry_sha256":geometry["geometry_sha256"],
        "contours":[x["label"] for x in approved["contours"]],
        "contour_count":len(approved["contours"]),
        "landmark_count":geometry["landmark_count"],
        "segment_count":geometry["segment_count"],
        "segments":[s["label"] for s in geometry["segments"]],
        "legend":[{"name":s["label"],"color":s["color"],
                   "description":s["description"]}
                  for s in geometry["segments"]],
        "caption":(
            ("COURBES SYNTHÉTIQUES DE RECETTE TECHNIQUE — NON EXPERTISÉES. "
             if __import__("os").environ.get("ODF_G5_E2E_SYNTHETIC_STROKES") == "1"
             else "")
            + "Tracé manuel enregistré par l'utilisateur authentifié du laboratoire, "
            + "superposé à la téléradiographie appariée Aariz (CC BY 4.0). "
            + "Ces courbes sont des annotations saisies, jamais des contours "
            + "déduits des 24 repères. "
            + "Document de recherche sans validation diagnostique R14."
        ),
        "source_url":"https://doi.org/10.1038/s41597-025-05542-3",
    }
