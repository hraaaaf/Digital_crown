"""Deterministic Tweed/Merrifield patient geometry for R6.

Observed geometry only: no norms, classification, diagnosis or treatment logic.
"""
from __future__ import annotations

import math
from typing import Optional, Tuple

Point = Tuple[float, float]
_EPS = 1e-12


def _finite_point(point: Point) -> bool:
    return all(math.isfinite(float(value)) for value in point)


def _ray_angle_deg(p1: Point, p2: Point, p3: Point, p4: Point) -> Optional[float]:
    """Match the legacy runtime ray-angle convention exactly, before rounding."""
    if not all(_finite_point(point) for point in (p1, p2, p3, p4)):
        return None
    v1 = (p2[0] - p1[0], p2[1] - p1[1])
    v2 = (p4[0] - p3[0], p4[1] - p3[1])
    if math.hypot(*v1) <= _EPS or math.hypot(*v2) <= _EPS:
        return None
    a1 = math.degrees(math.atan2(v1[1], v1[0]))
    a2 = math.degrees(math.atan2(v2[1], v2[0]))
    value = abs(a1 - a2) % 180.0
    return value if math.isfinite(value) else None


def _axis_angle_deg(p1: Point, p2: Point, p3: Point, p4: Point) -> Optional[float]:
    """Smallest orientation-invariant angle between two unoriented axes."""
    raw = _ray_angle_deg(p1, p2, p3, p4)
    if raw is None:
        return None
    value = min(raw, 180.0 - raw)
    return value if math.isfinite(value) else None


def tweed_fma_deg_v1(go: Point, me: Point, po: Point, or_: Point) -> Optional[float]:
    """FMA with exact legacy runtime orientation semantics: Go->Me vs Po->Or."""
    return _ray_angle_deg(go, me, po, or_)


def tweed_impa_deg_v1(
    l1_apex: Point, l1_incisal: Point, go: Point, me: Point
) -> Optional[float]:
    """IMPA with exact legacy runtime operation order, before final serialization."""
    raw = _ray_angle_deg(l1_apex, l1_incisal, go, me)
    if raw is None:
        return None
    value = 180.0 - round(raw, 1)
    return value if math.isfinite(value) else None


def tweed_fmia_deg_v1(
    l1_apex: Point, l1_incisal: Point, po: Point, or_: Point
) -> Optional[float]:
    """Direct FMIA: smallest angle between lower-incisor long axis and Frankfort."""
    return _axis_angle_deg(l1_apex, l1_incisal, po, or_)


def _most_protrusive_lip(
    *, po: Point, or_: Point, ls: Point, li: Point
) -> Optional[Point]:
    if not all(_finite_point(point) for point in (po, or_, ls, li)):
        return None
    anterior = (or_[0] - po[0], or_[1] - po[1])
    length = math.hypot(*anterior)
    if length <= _EPS:
        return None
    unit = (anterior[0] / length, anterior[1] / length)
    ls_score = ls[0] * unit[0] + ls[1] * unit[1]
    li_score = li[0] * unit[0] + li[1] * unit[1]
    if not math.isfinite(ls_score) or not math.isfinite(li_score):
        return None
    if math.isclose(ls_score, li_score, rel_tol=0.0, abs_tol=1e-12):
        if math.isclose(ls[0], li[0], rel_tol=0.0, abs_tol=1e-12) and math.isclose(
            ls[1], li[1], rel_tol=0.0, abs_tol=1e-12
        ):
            return ls
        return None
    return ls if ls_score > li_score else li


def merrifield_z_angle_deg_v1(
    po: Point,
    or_: Point,
    pog_soft: Point,
    ls_soft: Point,
    li_soft: Point,
) -> Optional[float]:
    """Merrifield Z-angle: Frankfort vs Pog' -> most protrusive lip."""
    lip = _most_protrusive_lip(po=po, or_=or_, ls=ls_soft, li=li_soft)
    if lip is None:
        return None
    return _axis_angle_deg(po, or_, pog_soft, lip)
