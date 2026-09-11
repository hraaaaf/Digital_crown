"""Versioned geometry for the source-safe subset of Downs analysis.

Only patient-observed angles that do not depend on an unresolved signed or
occlusal-plane convention are implemented here. No norms, classification,
diagnosis, prognosis or treatment logic is included.
"""
from __future__ import annotations

import math
from typing import Optional, Tuple

Point = Tuple[float, float]
_EPS = 1e-12


def _axis_angle_deg(p1: Point, p2: Point, p3: Point, p4: Point) -> Optional[float]:
    v1 = (p2[0] - p1[0], p2[1] - p1[1])
    v2 = (p4[0] - p3[0], p4[1] - p3[1])
    l1 = math.hypot(*v1)
    l2 = math.hypot(*v2)
    if not all(math.isfinite(value) for value in (*p1, *p2, *p3, *p4, l1, l2)):
        return None
    if l1 <= _EPS or l2 <= _EPS:
        return None
    cosine = (v1[0] * v2[0] + v1[1] * v2[1]) / (l1 * l2)
    cosine = max(-1.0, min(1.0, cosine))
    angle = math.degrees(math.acos(cosine))
    if angle > 90.0:
        angle = 180.0 - angle
    return angle if math.isfinite(angle) else None


def downs_facial_angle_deg_v1(po: Point, or_: Point, n: Point, pog: Point) -> Optional[float]:
    """Downs facial angle: Frankfort horizontal versus N-Pog facial plane."""
    return _axis_angle_deg(po, or_, n, pog)


def downs_y_axis_deg_v1(s: Point, gn: Point, po: Point, or_: Point) -> Optional[float]:
    """Downs Y-axis: S-Gn versus Frankfort horizontal."""
    return _axis_angle_deg(s, gn, po, or_)
