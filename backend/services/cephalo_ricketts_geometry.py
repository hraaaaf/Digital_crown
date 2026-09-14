"""Versioned geometry for the source-locked R9/R18 Ricketts subset.

Only patient-observed geometry with explicitly versioned conventions is
implemented here. No norms, classification, diagnosis, prognosis or treatment
logic belongs in this module.
"""
from __future__ import annotations

import math
from typing import Optional, Tuple

Point = Tuple[float, float]
_EPS = 1e-12


def _cross(a: Point, b: Point) -> float:
    return a[0] * b[1] - a[1] * b[0]


def _finite_points(*points: Point) -> bool:
    return all(math.isfinite(value) for point in points for value in point)


def _angle_deg(v1: Point, v2: Point) -> Optional[float]:
    len1 = math.hypot(*v1)
    len2 = math.hypot(*v2)
    if not all(math.isfinite(value) for value in (*v1, *v2, len1, len2)):
        return None
    if len1 <= _EPS or len2 <= _EPS:
        return None
    cosine = (v1[0] * v2[0] + v1[1] * v2[1]) / (len1 * len2)
    cosine = max(-1.0, min(1.0, cosine))
    angle = math.degrees(math.acos(cosine))
    return angle if math.isfinite(angle) else None


def ricketts_facial_depth_deg_v1(
    po: Point,
    or_: Point,
    n: Point,
    pog: Point,
) -> Optional[float]:
    """Posterior angle from anatomical Frankfort Po->Or to facial plane Pog->N."""
    if not _finite_points(po, or_, n, pog):
        return None
    return _angle_deg(
        (or_[0] - po[0], or_[1] - po[1]),
        (n[0] - pog[0], n[1] - pog[1]),
    )


def ricketts_constructed_gn_v1(
    n: Point,
    pog: Point,
    go: Point,
    me: Point,
) -> Optional[Point]:
    """Construct clinical Gn as intersection of N-Pog and Go-Me infinite lines."""
    if not _finite_points(n, pog, go, me):
        return None
    facial = (pog[0] - n[0], pog[1] - n[1])
    mandibular = (me[0] - go[0], me[1] - go[1])
    if math.hypot(*facial) <= _EPS or math.hypot(*mandibular) <= _EPS:
        return None
    denominator = _cross(facial, mandibular)
    if not math.isfinite(denominator) or abs(denominator) <= _EPS:
        return None
    delta = (go[0] - n[0], go[1] - n[1])
    t = _cross(delta, mandibular) / denominator
    gn = (n[0] + t * facial[0], n[1] + t * facial[1])
    return gn if _finite_points(gn) else None


def ricketts_facial_axis_deg_v1(
    ba: Point,
    n: Point,
    pt: Point,
    gn_constructed: Point,
) -> Optional[float]:
    """Inferior/non-reflex angle between Ba->N and Pt->constructed-Gn."""
    if not _finite_points(ba, n, pt, gn_constructed):
        return None
    return _angle_deg(
        (n[0] - ba[0], n[1] - ba[1]),
        (gn_constructed[0] - pt[0], gn_constructed[1] - pt[1]),
    )


def ricketts_convexity_signed_distance_px_v1(
    a: Point,
    n: Point,
    pog: Point,
    po: Point,
    or_: Point,
) -> Optional[float]:
    """Signed perpendicular A-to-NPog distance in source pixels."""
    if not _finite_points(a, n, pog, po, or_):
        return None
    facial = (pog[0] - n[0], pog[1] - n[1])
    facial_len_sq = facial[0] ** 2 + facial[1] ** 2
    fh = (or_[0] - po[0], or_[1] - po[1])
    fh_len = math.hypot(*fh)
    if facial_len_sq <= _EPS or fh_len <= _EPS:
        return None
    t = ((a[0] - n[0]) * facial[0] + (a[1] - n[1]) * facial[1]) / facial_len_sq
    projection = (n[0] + t * facial[0], n[1] + t * facial[1])
    residual = (a[0] - projection[0], a[1] - projection[1])
    magnitude = math.hypot(*residual)
    if not math.isfinite(magnitude):
        return None
    if magnitude <= _EPS:
        return 0.0
    anterior_score = residual[0] * (fh[0] / fh_len) + residual[1] * (fh[1] / fh_len)
    if not math.isfinite(anterior_score) or abs(anterior_score) <= _EPS:
        return None
    return math.copysign(magnitude, anterior_score)


def ricketts_e_line_horizontal_signed_distance_px_v1(
    lip: Point,
    prn: Point,
    pog_soft: Point,
    po: Point,
    or_: Point,
) -> Optional[float]:
    """Legacy V1: signed E-line displacement measured parallel to Frankfort.

    Retained only so persisted V1 evidence keeps immutable semantics. New R18
    evidence uses the source-strict perpendicular V2 convention below.
    """
    if not _finite_points(lip, prn, pog_soft, po, or_):
        return None
    fh = (or_[0] - po[0], or_[1] - po[1])
    fh_len = math.hypot(*fh)
    e_line = (pog_soft[0] - prn[0], pog_soft[1] - prn[1])
    if fh_len <= _EPS or math.hypot(*e_line) <= _EPS:
        return None
    anterior = (fh[0] / fh_len, fh[1] / fh_len)
    denominator = _cross(anterior, e_line)
    if not math.isfinite(denominator) or abs(denominator) <= _EPS:
        return None
    displacement = _cross((lip[0] - prn[0], lip[1] - prn[1]), e_line) / denominator
    return displacement if math.isfinite(displacement) else None


def ricketts_e_line_perpendicular_signed_distance_px_v2(
    lip: Point,
    prn: Point,
    pog_soft: Point,
    po: Point,
    or_: Point,
) -> Optional[float]:
    """R18 V2: signed shortest/perpendicular lip distance to Prn-Pog'.

    Magnitude is the perpendicular point-to-line distance. Frankfort Po->Or is
    used only to orient the sign (positive anterior, negative posterior), never
    to change the distance magnitude. V2 is mirror-invariant and matches the
    source-strict cephalometric E-line definition used by the runtime/frontend.
    """
    if not _finite_points(lip, prn, pog_soft, po, or_):
        return None
    e_line = (pog_soft[0] - prn[0], pog_soft[1] - prn[1])
    e_len_sq = e_line[0] ** 2 + e_line[1] ** 2
    fh = (or_[0] - po[0], or_[1] - po[1])
    fh_len = math.hypot(*fh)
    if e_len_sq <= _EPS or fh_len <= _EPS:
        return None
    t = ((lip[0] - prn[0]) * e_line[0] + (lip[1] - prn[1]) * e_line[1]) / e_len_sq
    projection = (prn[0] + t * e_line[0], prn[1] + t * e_line[1])
    residual = (lip[0] - projection[0], lip[1] - projection[1])
    magnitude = math.hypot(*residual)
    if not math.isfinite(magnitude):
        return None
    if magnitude <= _EPS:
        return 0.0
    anterior_score = residual[0] * (fh[0] / fh_len) + residual[1] * (fh[1] / fh_len)
    if not math.isfinite(anterior_score) or abs(anterior_score) <= _EPS:
        return None
    return math.copysign(magnitude, anterior_score)
