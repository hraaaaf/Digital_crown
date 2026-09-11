"""Versioned CRANIOM angular geometry.

Deterministic geometry only. No norms, interpretation, diagnosis or treatment.
"""
from __future__ import annotations

import math
from typing import Optional, Tuple

Point = Tuple[float, float]
_EPS = 1e-12


def _directed_line_angle_deg(start: Optional[Point], end: Optional[Point]) -> Optional[float]:
    if start is None or end is None:
        return None
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = math.hypot(dx, dy)
    if not math.isfinite(length) or length <= _EPS:
        return None
    angle = math.degrees(math.atan2(dy, dx))
    return angle if math.isfinite(angle) else None


def craniom_u1_frankfort_deg_v1(
    u1_apex: Optional[Point],
    u1_incisal: Optional[Point],
    po: Optional[Point],
    orbitale: Optional[Point],
) -> Optional[float]:
    """Upper-incisor long-axis inclination to Frankfort, in degrees.

    The upper-incisor axis is oriented apex -> incisal edge and Frankfort is
    oriented Po -> Or. The clinical obtuse angle matches the existing backend
    `I_Francfort` convention and is kept versioned here so typed evidence cannot
    silently drift from runtime geometry.
    """
    incisor_angle = _directed_line_angle_deg(u1_apex, u1_incisal)
    frankfort_angle = _directed_line_angle_deg(po, orbitale)
    if incisor_angle is None or frankfort_angle is None:
        return None
    raw = abs(incisor_angle - frankfort_angle) % 180.0
    value = 180.0 - raw
    return value if math.isfinite(value) else None
