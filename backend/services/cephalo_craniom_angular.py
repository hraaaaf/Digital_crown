"""Versioned CRANIOM angular geometry.

Deterministic geometry only. No norms, interpretation, diagnosis or treatment.
"""
from __future__ import annotations

import math
from typing import Optional, Tuple

Point = Tuple[float, float]
_EPS = 1e-12


def _ray_angle_deg(
    p1: Optional[Point],
    p2: Optional[Point],
    p3: Optional[Point],
    p4: Optional[Point],
) -> Optional[float]:
    if not all((p1, p2, p3, p4)):
        return None
    assert p1 is not None and p2 is not None and p3 is not None and p4 is not None
    v1 = (p2[0] - p1[0], p2[1] - p1[1])
    v2 = (p4[0] - p3[0], p4[1] - p3[1])
    len1 = math.hypot(*v1)
    len2 = math.hypot(*v2)
    if (
        not all(math.isfinite(value) for value in (*v1, *v2, len1, len2))
        or len1 <= _EPS
        or len2 <= _EPS
    ):
        return None
    cosine = (v1[0] * v2[0] + v1[1] * v2[1]) / (len1 * len2)
    cosine = max(-1.0, min(1.0, cosine))
    value = math.degrees(math.acos(cosine))
    return value if math.isfinite(value) else None


def _clinical_obtuse_angle_deg_v1(
    axis_start: Optional[Point],
    axis_end: Optional[Point],
    reference_start: Optional[Point],
    reference_end: Optional[Point],
) -> Optional[float]:
    raw = _ray_angle_deg(axis_start, axis_end, reference_start, reference_end)
    if raw is None:
        return None
    value = 180.0 - raw
    return value if math.isfinite(value) else None


def _clinical_interincisal_angle_deg_v1(
    u1_apex: Optional[Point],
    u1_incisal: Optional[Point],
    l1_apex: Optional[Point],
    l1_incisal: Optional[Point],
) -> Optional[float]:
    """Posterior/obtuse angle between maxillary and mandibular incisor long axes."""
    raw = _ray_angle_deg(u1_apex, u1_incisal, l1_apex, l1_incisal)
    if raw is None:
        return None
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

    This preserves the certified convention: use the larger of the two
    supplementary line angles. It carries geometry only, never a norm or clinical
    classification.
    """
    return _clinical_interincisal_angle_deg_v1(
        u1_apex, u1_incisal, l1_apex, l1_incisal
    )
