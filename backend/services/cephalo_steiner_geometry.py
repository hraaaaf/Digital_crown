"""Versioned Steiner geometry.

Deterministic patient geometry only. No norms, diagnosis, growth projection or treatment.
Linear U1-NA/L1-NB distances are intentionally not implemented in V1 because Steiner's
primary description uses the most mesial point of the crown, while the current landmark
contract exposes incisal-edge points only.
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
    """Directed-ray angle magnitude in [0, 180), preserving ray orientation."""
    if not all((p1, p2, p3, p4)):
        return None
    assert p1 is not None and p2 is not None and p3 is not None and p4 is not None
    v1 = (p2[0] - p1[0], p2[1] - p1[1])
    v2 = (p4[0] - p3[0], p4[1] - p3[1])
    len1 = math.hypot(*v1)
    len2 = math.hypot(*v2)
    if (
        not math.isfinite(len1)
        or not math.isfinite(len2)
        or len1 <= _EPS
        or len2 <= _EPS
    ):
        return None
    a1 = math.degrees(math.atan2(v1[1], v1[0]))
    a2 = math.degrees(math.atan2(v2[1], v2[0]))
    value = abs(a1 - a2) % 180.0
    return value if math.isfinite(value) else None


def _axis_angle_deg(
    p1: Optional[Point],
    p2: Optional[Point],
    p3: Optional[Point],
    p4: Optional[Point],
) -> Optional[float]:
    """Smallest angle between two unoriented axes, in [0, 90]."""
    value = _ray_angle_deg(p1, p2, p3, p4)
    if value is None:
        return None
    acute = min(value, 180.0 - value)
    return acute if math.isfinite(acute) else None


def steiner_sna_deg_v1(
    sella: Optional[Point], nasion: Optional[Point], point_a: Optional[Point]
) -> Optional[float]:
    """Steiner SNA angle at N between N->S and N->A."""
    return _ray_angle_deg(nasion, sella, nasion, point_a)


def steiner_snb_deg_v1(
    sella: Optional[Point], nasion: Optional[Point], point_b: Optional[Point]
) -> Optional[float]:
    """Steiner SNB angle at N between N->S and N->B."""
    return _ray_angle_deg(nasion, sella, nasion, point_b)


def steiner_anb_deg_v1(
    sella: Optional[Point],
    nasion: Optional[Point],
    point_a: Optional[Point],
    point_b: Optional[Point],
) -> Optional[float]:
    """Steiner ANB with legacy-runtime parity: round(SNA, 1) - round(SNB, 1)."""
    sna = steiner_sna_deg_v1(sella, nasion, point_a)
    snb = steiner_snb_deg_v1(sella, nasion, point_b)
    if sna is None or snb is None:
        return None
    value = round(sna, 1) - round(snb, 1)
    return value if math.isfinite(value) else None


def steiner_u1_na_deg_v1(
    u1_apex: Optional[Point],
    u1_incisal: Optional[Point],
    nasion: Optional[Point],
    point_a: Optional[Point],
) -> Optional[float]:
    """Smallest angle between the upper-incisor long axis and N-A."""
    return _axis_angle_deg(u1_apex, u1_incisal, nasion, point_a)


def steiner_l1_nb_deg_v1(
    l1_apex: Optional[Point],
    l1_incisal: Optional[Point],
    nasion: Optional[Point],
    point_b: Optional[Point],
) -> Optional[float]:
    """Smallest angle between the lower-incisor long axis and N-B."""
    return _axis_angle_deg(l1_apex, l1_incisal, nasion, point_b)


def steiner_sn_mp_deg_v1(
    sella: Optional[Point],
    nasion: Optional[Point],
    gonion: Optional[Point],
    gnathion: Optional[Point],
) -> Optional[float]:
    """Smallest angle between Steiner's SN reference and mandibular plane Go-Gn."""
    return _axis_angle_deg(sella, nasion, gonion, gnathion)
