"""Exact Digital Crown COM legacy overjet/overbite projections.

These reproduce the pre-canonical cephalo_engine.py calculations. They are
not normative definitions of clinical overjet/overbite and remain explicitly
screen-orientation dependent for the perpendicular component.
"""
from __future__ import annotations

import math
from typing import Optional

from backend.services.cephalo_constructions import Point, frankfort_axis_v1


def _projected_incisor_separation_px_v1(
    upper_incisal: Point,
    lower_incisal: Point,
    porion: Point,
    orbitale: Point,
    *,
    perpendicular: bool,
) -> Optional[float]:
    values = (*upper_incisal, *lower_incisal, *porion, *orbitale)
    if not all(math.isfinite(value) for value in values):
        return None
    fh = frankfort_axis_v1(porion, orbitale)
    if fh is None:
        return None
    axis = (-fh[1], fh[0]) if perpendicular else fh
    if perpendicular and axis[1] < 0:
        axis = (-axis[0], -axis[1])  # legacy DC: choose positive image-Y normal
    value = (upper_incisal[0] - lower_incisal[0]) * axis[0] + (
        upper_incisal[1] - lower_incisal[1]
    ) * axis[1]
    return value if math.isfinite(value) else None


def com_dc_legacy_overjet_fh_px_v1(
    upper_incisal: Point, lower_incisal: Point, porion: Point, orbitale: Point
) -> Optional[float]:
    """U1i-L1i projected along directed Po->Or, in pixels."""
    return _projected_incisor_separation_px_v1(
        upper_incisal, lower_incisal, porion, orbitale, perpendicular=False
    )


def com_dc_legacy_overbite_screen_positive_y_fh_px_v1(
    upper_incisal: Point, lower_incisal: Point, porion: Point, orbitale: Point
) -> Optional[float]:
    """U1i-L1i projected onto legacy positive-screen-Y normal to Po->Or."""
    return _projected_incisor_separation_px_v1(
        upper_incisal, lower_incisal, porion, orbitale, perpendicular=True
    )


def _legacy_clinical_angle_deg_v1(
    first_start: Point, first_end: Point, second_start: Point, second_end: Point,
) -> Optional[float]:
    """Match the legacy engine's directed-ray angle and one-decimal output."""
    values = (*first_start, *first_end, *second_start, *second_end)
    if not all(math.isfinite(value) for value in values):
        return None
    first = (first_end[0] - first_start[0], first_end[1] - first_start[1])
    second = (second_end[0] - second_start[0], second_end[1] - second_start[1])
    first_len = math.hypot(*first)
    second_len = math.hypot(*second)
    if first_len <= 1e-12 or second_len <= 1e-12:
        return None
    cosine = (first[0] * second[0] + first[1] * second[1]) / (first_len * second_len)
    raw = math.degrees(math.acos(max(-1.0, min(1.0, cosine))))
    return round(raw, 1) if math.isfinite(raw) else None


def com_dc_legacy_fma_po_or_deg_v1(
    go: Point, me: Point, porion: Point, orbitale: Point,
) -> Optional[float]:
    """Legacy COM FMA using the exact legacy ``Po`` point identity."""
    return _legacy_clinical_angle_deg_v1(go, me, porion, orbitale)


def com_dc_legacy_u1_fh_po_or_deg_v1(
    u1_apex: Point, u1_incisal: Point, porion: Point, orbitale: Point,
) -> Optional[float]:
    """Legacy COM U1/FH supplementary directed-ray angle, rounded to 0.1 deg."""
    raw = _legacy_clinical_angle_deg_v1(u1_apex, u1_incisal, porion, orbitale)
    return 180.0 - raw if raw is not None else None


def _legacy_signed_projection_px_v1(
    point: Point, origin: Point, porion: Point, orbitale: Point,
) -> Optional[float]:
    values = (*point, *origin, *porion, *orbitale)
    if not all(math.isfinite(value) for value in values):
        return None
    axis = frankfort_axis_v1(porion, orbitale)
    if axis is None:
        return None
    result = (point[0] - origin[0]) * axis[0] + (point[1] - origin[1]) * axis[1]
    return result if math.isfinite(result) else None


def com_dc_legacy_ab_prime_fh_px_v1(
    a: Point, b: Point, porion: Point, orbitale: Point,
) -> Optional[float]:
    """Legacy CRANIOM A'-B' signed projection along ``Po``→Or, in pixels."""
    return _legacy_signed_projection_px_v1(a, b, porion, orbitale)


def com_dc_legacy_nperp_px_v1(
    point: Point, nasion: Point, porion: Point, orbitale: Point,
) -> Optional[float]:
    """Signed legacy COM distance from N-perp along the exact ``Po``→Or axis."""
    return _legacy_signed_projection_px_v1(point, nasion, porion, orbitale)


def com_dc_legacy_s_nperp_depth_px_v1(
    sella: Point, nasion: Point, porion: Point, orbitale: Point,
) -> Optional[float]:
    """Unsigned legacy COM S-to-N-perp depth magnitude, in pixels."""
    value = com_dc_legacy_nperp_px_v1(sella, nasion, porion, orbitale)
    return abs(value) if value is not None else None
