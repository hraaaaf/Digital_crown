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
    """Non-reflex angle between two directed rays, in [0, 180]."""
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
    """Steiner ANB with runtime parity: round(SNA, 1) - round(SNB, 1)."""
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


def _point_line_distance_mm_v1(
    point: Optional[Point], line_a: Optional[Point], line_b: Optional[Point],
    mm_per_pixel: Optional[float],
) -> Optional[float]:
    """Unsigned perpendicular point-to-infinite-line distance in mm."""
    if point is None or line_a is None or line_b is None or mm_per_pixel is None:
        return None
    if not math.isfinite(mm_per_pixel) or mm_per_pixel <= 0:
        return None
    dx=line_b[0]-line_a[0]; dy=line_b[1]-line_a[1]
    den=math.hypot(dx,dy)
    if not math.isfinite(den) or den <= _EPS:
        return None
    num=abs(dy*point[0]-dx*point[1]+line_b[0]*line_a[1]-line_b[1]*line_a[0])
    value=(num/den)*mm_per_pixel
    return value if math.isfinite(value) else None


def steiner_u1_na_mm_v1(u1_facial_surface: Optional[Point], nasion: Optional[Point],
                         point_a: Optional[Point], mm_per_pixel: Optional[float]) -> Optional[float]:
    """Steiner linear U1-to-NA using an explicit facial crown-surface point."""
    return _point_line_distance_mm_v1(u1_facial_surface,nasion,point_a,mm_per_pixel)


def steiner_l1_nb_mm_v1(l1_facial_surface: Optional[Point], nasion: Optional[Point],
                         point_b: Optional[Point], mm_per_pixel: Optional[float]) -> Optional[float]:
    """Steiner linear L1-to-NB using an explicit facial crown-surface point."""
    return _point_line_distance_mm_v1(l1_facial_surface,nasion,point_b,mm_per_pixel)


def steiner_pog_nb_mm_v1(pogonion: Optional[Point], nasion: Optional[Point],
                          point_b: Optional[Point], mm_per_pixel: Optional[float]) -> Optional[float]:
    """Perpendicular Pog-to-NB distance for the Steiner/Holdaway relationship."""
    return _point_line_distance_mm_v1(pogonion,nasion,point_b,mm_per_pixel)


def steiner_l1_gogn_deg_v1(l1_apex: Optional[Point], l1_incisal: Optional[Point],
                            gonion: Optional[Point], gnathion: Optional[Point]) -> Optional[float]:
    """Smallest angle between the lower-incisor axis and Steiner Go-Gn."""
    return _axis_angle_deg(l1_apex,l1_incisal,gonion,gnathion)


def steiner_occlusal_sn_deg_v1(sella: Optional[Point], nasion: Optional[Point],
                                occ_ant: Optional[Point], occ_post: Optional[Point]) -> Optional[float]:
    """Angle between SN and explicit Steiner-1953 occlusal-plane anchors."""
    return _axis_angle_deg(sella,nasion,occ_ant,occ_post)


def steiner_snd_deg_v1(sella: Optional[Point], nasion: Optional[Point],
                        d_steiner_1959: Optional[Point]) -> Optional[float]:
    """SND at N using an explicit Steiner-1959 D identity."""
    return _ray_angle_deg(nasion,sella,nasion,d_steiner_1959)


def steiner_l1_dline_mm_v1(l1_facial_surface: Optional[Point], d_steiner_1959: Optional[Point],
                            gonion: Optional[Point], gnathion: Optional[Point],
                            mm_per_pixel: Optional[float]) -> Optional[float]:
    """Distance from L1 facial crown point to Steiner D-line (D perpendicular to Go-Gn)."""
    if None in (l1_facial_surface,d_steiner_1959,gonion,gnathion) or mm_per_pixel is None:
        return None
    assert l1_facial_surface and d_steiner_1959 and gonion and gnathion
    dx=gnathion[0]-gonion[0]; dy=gnathion[1]-gonion[1]
    den=math.hypot(dx,dy)
    if not math.isfinite(den) or den <= _EPS:
        return None
    # D-line direction is perpendicular to Go-Gn; distance to D-line equals
    # absolute projection of (L1-D) along Go-Gn.
    ux,uy=dx/den,dy/den
    px=l1_facial_surface[0]-d_steiner_1959[0]; py=l1_facial_surface[1]-d_steiner_1959[1]
    if not math.isfinite(mm_per_pixel) or mm_per_pixel <= 0:
        return None
    value=abs(px*ux+py*uy)*mm_per_pixel
    return value if math.isfinite(value) else None


def steiner_l1_dline_deg_v1(l1_apex: Optional[Point], l1_incisal: Optional[Point],
                             gonion: Optional[Point], gnathion: Optional[Point]) -> Optional[float]:
    """Smallest angle between L1 axis and D-line (perpendicular to Go-Gn)."""
    if gonion is None or gnathion is None:
        return None
    dx=gnathion[0]-gonion[0]; dy=gnathion[1]-gonion[1]
    if not all(math.isfinite(v) for v in (dx,dy)) or math.hypot(dx,dy) <= _EPS:
        return None
    d0=(0.0,0.0); d1=(-dy,dx)
    return _axis_angle_deg(l1_apex,l1_incisal,d0,d1)
