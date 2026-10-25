"""ODF G4 — source-bound 2D cephalometric construction geometry.

This is a geometric PLAN/AXIS tracing on actual expert-marked radiograph
pixels. It is NOT a fabricated soft-tissue or bony silhouette. Such contour
curves would require independent line/curve annotations on the exact image.
All segments are reconstructed from the same persisted evidence graph used
by the cephalometric measurements, not from client narrative.
"""
from __future__ import annotations

from hashlib import sha256
import json
from math import hypot, isfinite
from typing import Any, Mapping

# (display label, first point, second point, meaning, color).
# Anatomical line conventions are explicit; non-existent lines are never drawn.
TRACE_SEGMENTS = (
    ("SN", "S", "N", "Base crânienne antérieure", "#44C5FF"),
    ("FH", "Po", "Or", "Plan de Francfort", "#4FDEBA"),
    ("NA", "N", "A", "Ligne NA", "#D899FF"),
    ("NB", "N", "B", "Ligne NB", "#D899FF"),
    ("Go–Me", "Go", "Me", "Plan mandibulaire", "#FFAD56"),
    ("Go–Gn", "Go", "Gn", "Plan mandibulaire (Gn)", "#FFAD56"),
    ("ANS–PNS", "ANS", "PNS", "Plan palatin", "#70DDCE"),
    ("U1", "U1_apex", "U1_incisal", "Axe incisive supérieure", "#FFE071"),
    ("L1", "L1_apex", "L1_incisal", "Axe incisive inférieure", "#FFE071"),
)
REQUIRED_SEGMENTS = frozenset(("SN", "FH", "NA", "NB", "Go–Me", "U1", "L1"))
MIN_LANDMARKS = frozenset((
    "S", "N", "A", "B", "Po", "Or", "Go", "Me",
    "U1_apex", "U1_incisal", "L1_apex", "L1_incisal",
))
TRACE_CONTRACT = "ODF_CEPHALOMETRIC_GEOMETRY_V1"


def trace_geometry_from_evidence(
    landmarks: object, image_size: tuple[int, int]
) -> dict[str, Any] | None:
    """Return only study-image coordinates; never interpolate an anatomy contour.

    Returns None if a necessary landmark is absent, malformed, duplicate,
    outside the image, or any mandatory two-point plan is degenerate.
    """
    if (
        not isinstance(landmarks, list)
        or not (isinstance(image_size, tuple) and len(image_size) == 2)
        or not all(type(d) is int and 0 < d <= 10000 for d in image_size)
    ):
        return None
    w, h = image_size
    points: dict[str, tuple[float, float]] = {}
    for raw in landmarks:
        if not isinstance(raw, Mapping):
            return None
        name, x, y = raw.get("landmark_id"), raw.get("x"), raw.get("y")
        if (
            not isinstance(name, str) or not name or name in points
            or type(x) not in (float, int) or type(y) not in (float, int)
            or not isfinite(x) or not isfinite(y)
            or not (0 <= x < w and 0 <= y < h)
        ):
            return None
        points[name] = (float(x), float(y))
    if not MIN_LANDMARKS.issubset(points):
        return None
    segments = []
    for label, a, b, title, color in TRACE_SEGMENTS:
        if a not in points or b not in points:
            continue
        x1, y1 = points[a]
        x2, y2 = points[b]
        if hypot(x2-x1, y2-y1) < 2.0:
            if label in REQUIRED_SEGMENTS:
                return None
            continue
        segments.append({
            "label":label, "from":a, "to":b,
            "from_xy":[x1,y1], "to_xy":[x2,y2],
            "description":title, "color":color,
        })
    if not REQUIRED_SEGMENTS.issubset({s["label"] for s in segments}):
        return None

    canonical = {
        "contract":TRACE_CONTRACT,
        "image_size":[w,h],
        "landmarks":{k:list(points[k]) for k in sorted(points)},
        "segments":segments,
    }
    canonical["geometry_sha256"] = sha256(
        json.dumps(canonical, sort_keys=True, ensure_ascii=False,
                   separators=(",", ":")).encode("utf8")
    ).hexdigest()
    canonical["landmark_count"] = len(points)
    canonical["segment_count"] = len(segments)
    return canonical


def draw_trace_overlay(image: Any, geometry: Mapping[str, Any]) -> None:
    """Mutate a separate RGB PIL copy; pixel geometry never rescaled or shifted."""
    from PIL import ImageDraw
    draw = ImageDraw.Draw(image, "RGBA")
    p = geometry["landmarks"]
    # Shadow keylines improve visibility across X-ray light and dark areas.
    for segment in geometry["segments"]:
        start, end = [tuple(v) for v in (segment["from_xy"], segment["to_xy"])]
        draw.line([start, end], fill=(5, 14, 29, 210), width=12)
        hexa = segment["color"].lstrip("#")
        rgb = tuple(int(hexa[i:i+2],16) for i in (0,2,4))
        draw.line([start, end], fill=(*rgb, 240), width=6)
    labels = set()
    for segment in geometry["segments"]:
        labels.add(segment["from"])
        labels.add(segment["to"])
    for name in sorted(labels):
        x,y = p[name]
        draw.ellipse((x-7,y-7,x+7,y+7), fill=(253,250,235,250),
                     outline=(7,21,32,255), width=3)
        # Distinct text backing avoids illegible labels on dental structures.
        bx=max(0,min(image.width-160,x+11))
        by=max(0,min(image.height-32,y-14))
        draw.rectangle((bx-2,by-2,bx+max(36,10*len(name))+5,by+23),
                       fill=(12,22,38,211))
        draw.text((bx+3,by+2), name, fill=(255,255,255,255),
                  stroke_width=1, stroke_fill=(11,22,34,255))
