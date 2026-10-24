"""G5: strictly source-bound clinician-drawn anatomical contour contract.

No curve is inferred from 24 Aariz landmarks. Coordinates are in *the same
displayed radiograph pixel space* as G4 and require an explicit dentist's
manual stroke + separate authenticated approval. This contract does not
constitute R14 diagnostic validation.
"""
from __future__ import annotations

from hashlib import sha256
import json
from math import hypot, isfinite
import re
from typing import Any, Mapping

CONTOUR_CONTRACT = "ODF_ANATOMIC_TRACE_V1"
CONTOUR_LABELS = {
    "cranial_base": "Base du crâne",
    "maxilla": "Maxillaire",
    "mandible": "Mandibule",
    "upper_incisor": "Incisive supérieure",
    "lower_incisor": "Incisive inférieure",
    "soft_tissue_profile": "Profil cutané",
}
# A few landmarks are NOT enough to establish anatomical curves. Real manual
# contours have many successive sampled points — not a 2-point chord.
MIN_POINTS = {
    "cranial_base": 10, "maxilla": 10, "mandible": 16,
    "upper_incisor": 7, "lower_incisor": 7, "soft_tissue_profile": 16,
}
CONTOUR_COLORS = {
    "cranial_base": "#28466A",
    "maxilla": "#345C83",
    "mandible": "#24496E",
    "upper_incisor": "#246D72",
    "lower_incisor": "#246D72",
    "soft_tissue_profile": "#B26B55",
}


class ContourRejected(ValueError):
    """No clinical anatomic trace may print from an invalid contour payload."""


def canonical_digest(data: Any) -> str:
    return sha256(json.dumps(data,sort_keys=True,separators=(",",":"),
                             ensure_ascii=False,allow_nan=False).encode("utf8")).hexdigest()


def normalize_manual_contours(
    contours: object, *, image_size: tuple[int, int],
) -> dict[str, Any]:
    if (
        type(image_size) is not tuple or len(image_size) != 2
        or any(type(d) is not int or not 1 <= d <= 10000 for d in image_size)
        or type(contours) is not list
        or len(contours) != len(CONTOUR_LABELS)
    ):
        raise ContourRejected("G5_SIX_DOCUMENTED_CONTOURS_REQUIRED")
    w, h = image_size
    canonical: dict[str, Any] = {}
    for entry in contours:
        if not isinstance(entry, dict) or set(entry) != {"id","points"}:
            raise ContourRejected("G5_CONTOUR_SCHEMA_INVALID")
        key = entry["id"]
        if type(key) is not str or key not in CONTOUR_LABELS or key in canonical:
            raise ContourRejected("G5_CONTOUR_UNKNOWN_OR_DUPLICATE")
        points = entry["points"]
        if type(points) is not list or not MIN_POINTS[key] <= len(points) <= 600:
            raise ContourRejected("G5_CONTOUR_INSUFFICIENT_REAL_POINTS")
        normal=[]
        length=0.0
        for p in points:
            if type(p) not in (list,tuple) or len(p) != 2:
                raise ContourRejected("G5_CONTOUR_POINT_INVALID")
            x,y=p
            if any(type(a) not in (float,int) or not isfinite(a) for a in (x,y)):
                raise ContourRejected("G5_CONTOUR_NONFINITE_POINT")
            if not (0<=x<w and 0<=y<h):
                raise ContourRejected("G5_CONTOUR_POINT_OUTSIDE_SOURCE_IMAGE")
            px,py=float(x),float(y)
            if normal:
                dist=hypot(px-normal[-1][0],py-normal[-1][1])
                if dist < 0.5:
                    raise ContourRejected("G5_CONTOUR_DUPLICATE_OR_STATIONARY_POINT")
                length+=dist
            normal.append([px,py])
        if length < max(15.0, 2*(len(points)-1)):
            raise ContourRejected("G5_CONTOUR_IS_A_SHORT_CHORD")
        canonical[key]={"id":key,"label":CONTOUR_LABELS[key],
                        "color":CONTOUR_COLORS[key],
                        "points":normal,"length_pixels":round(length,2)}
    if set(canonical)!=set(CONTOUR_LABELS):
        raise ContourRejected("G5_CONTOURS_MISSING_REQUIRED_ANATOMY")
    ordered=[canonical[k] for k in CONTOUR_LABELS]
    return {
        "contract":CONTOUR_CONTRACT,
        "coordinate_space":"image_pixels",
        "image_size":[w,h],
        "contours":ordered,
        "contour_digest":canonical_digest(
            {"contract":CONTOUR_CONTRACT,"size":[w,h],
             "curves":[{"id":v["id"],"points":v["points"]} for v in ordered]}),
    }


def verify_approved_anatomical_trace(
    source: Mapping[str,Any], *,
    patient_id:int, analysis_id:int, revision:int,
    scientific_digest:str, image_sha256:str, image_size:tuple[int,int],
) -> dict[str,Any] | None:
    """Accept only a previously stored, versioned and explicitly signed trace.

    Caller must supply DB-authoritative rows, never client-provided metadata.
    """
    if not isinstance(source,dict) or source.get("state")!="APPROVED":
        return None
    if not (
        source.get("contract")==CONTOUR_CONTRACT
        and source.get("source_mode")=="CLINICIAN_MANUAL"
        and source.get("patient_id")==patient_id
        and source.get("analysis_id")==analysis_id
        and source.get("analysis_revision")==revision
        and source.get("scientific_digest")==scientific_digest
        and source.get("image_sha256")==image_sha256
        and source.get("image_size")==list(image_size)
        and type(source.get("version")) is int and source["version"]>0
        and type(source.get("approved_by")) is int and source["approved_by"]>0
        and isinstance(source.get("approved_at"),str) and source["approved_at"]
        and isinstance(source.get("contour_digest"),str)
        and re.fullmatch("[0-9a-f]{64}",source["contour_digest"])
        and isinstance(source.get("approved_digest"),str)
    ):
        return None
    try:
        data=normalize_manual_contours(
            source.get("contours"),image_size=image_size)
    except (ContourRejected,ValueError,TypeError):
        return None
    if data["contour_digest"]!=source["contour_digest"]:
        return None
    proof=canonical_digest([
        source["patient_id"],source["analysis_id"],
        source["analysis_revision"],source["scientific_digest"],
        source["image_sha256"],source["version"],
        source["contour_digest"],source["approved_by"],
    ])
    if proof!=source["approved_digest"]:
        return None
    return data


def draw_contours(image: Any, validated: Mapping[str,Any], *,
                  background_is_white:bool=False) -> None:
    """Draw only approved polyline samples; never interpolate hidden anatomy."""
    from PIL import ImageDraw
    pen=ImageDraw.Draw(image)
    for contour in validated["contours"]:
        pts=[(round(x),round(y)) for x,y in contour["points"]]
        if background_is_white:
            col=contour["color"]
            width=5
        else:
            # A light keyline keeps authentic drawn anatomy visible on X-rays.
            pen.line(pts,fill=(255,255,255),width=9,joint="curve")
            col=contour["color"]
            width=5
        pen.line(pts,fill=col,width=width,joint="curve")
