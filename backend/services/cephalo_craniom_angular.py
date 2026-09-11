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


def _clinical_obtuse_angle_deg_v1(
    axis_start: Optional[Point],
    axis_end: Optional[Point],
    reference_start: Optional[Point],
    reference_end: Optional[Point],
) -> Optional[float]:
    axis_angle = _directed_line_angle_deg(axis_start, axis_end)
    reference_angle = _directed_line_angle_deg(reference_start, reference_end)
    if axis_angle is None or reference_angle is None:
        return None
    raw = abs(axis_angle - reference_angle) % 180.0
    value = 180.0 - raw
    return value if math.isfinite(value) else None


def _clinical_interincisal_angle_deg_v1(
    u1_apex: Optional[Point],
    u1_incisal: Optional[Point],
    l1_apex: Optional[Point],
    l1_incisal: Optional[Point],
) -> Optional[float]:
    """Posterior/obtuse angle between maxillary and mandibular incisor long axes."""
    upper = _directed_line_angle_deg(u1_apex, u1_incisal)
    lower = _directed_line_angle_deg(l1_apex, l1_incisal)
    if upper is None or lower is None:
        return None
    raw = abs(upper - lower) % 180.0
    value = max(raw, 180.0 - raw)
    return value if math.isfinite(value) else None


def craniom_u1_frankfort_deg_v1(
    u1_apex: Optional[Point],
    u1_incisal: Optional[Point],
    po: Optional[Point],
    orbitale: Optional[Point],
) -> Optional[float]:
    """Upper-incisor long-axis inclination to Frankfort, in degrees."""
    return _clinical_obtuse_angle_deg_v1(u1_apex, u1_incisal, po, orbitale)


def craniom_l1_downs_deg_v1(
    l1_apex: Optional[Point],
    l1_incisal: Optional[Point],
    gonion: Optional[Point],
    menton: Optional[Point],
) -> Optional[float]:
    """Lower-incisor inclination to Downs mandibular plane Go->Me, in degrees.

    The construction is explicitly versioned as the clinical obtuse angle between
    the lower-incisor apex->incisal long axis and the Downs mandibular plane,
    represented by Go->Me in the certified runtime. It intentionally carries no
    normative interpretation.
    """
    return _clinical_obtuse_angle_deg_v1(l1_apex, l1_incisal, gonion, menton)


def craniom_interincisal_deg_v1(
    u1_apex: Optional[Point],
    u1_incisal: Optional[Point],
    l1_apex: Optional[Point],
    l1_incisal: Optional[Point],
) -> Optional[float]:
    """Interincisal angle between U1 and L1 long axes, in degrees.

    This preserves the existing runtime convention: use the larger of the two
    supplementary line angles. It carries geometry only, never a norm or clinical
    classification.
    """
    return _clinical_interincisal_angle_deg_v1(
        u1_apex, u1_incisal, l1_apex, l1_incisal
    )
