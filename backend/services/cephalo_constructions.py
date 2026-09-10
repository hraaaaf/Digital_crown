"""Versioned, fail-closed cephalometric constructions.

Only deterministic geometry lives here. No norms, diagnostic labels, growth
projection, treatment indication or patient-context inference is allowed.

Source-specific constructions are named explicitly so one analysis cannot
silently reuse a geometrically different convention from another analysis.
"""

from __future__ import annotations

import math
from typing import Optional, Tuple


Point = Tuple[float, float]
_EPS = 1e-12


def _valid_ratio(mm_per_pixel: Optional[float]) -> bool:
    return mm_per_pixel is not None and math.isfinite(mm_per_pixel) and mm_per_pixel > 0


def unit_axis(start: Optional[Point], end: Optional[Point]) -> Optional[Point]:
    """Return the unit vector start->end, or None for missing/degenerate input."""
    if start is None or end is None:
        return None
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = math.hypot(dx, dy)
    if not math.isfinite(length) or length <= _EPS:
        return None
    return (dx / length, dy / length)


def frankfort_axis_v1(po: Optional[Point], orbitale: Optional[Point]) -> Optional[Point]:
    """FH_PO_OR_V1: anatomical Frankfort axis, oriented Po -> Or."""
    return unit_axis(po, orbitale)


def orthogonal_projection_v1(
    line_start: Optional[Point],
    line_end: Optional[Point],
    target: Optional[Point],
) -> Optional[Point]:
    """Project target orthogonally onto an infinite line, fail-closed."""
    if line_start is None or line_end is None or target is None:
        return None
    dx = line_end[0] - line_start[0]
    dy = line_end[1] - line_start[1]
    length_sq = dx * dx + dy * dy
    if not math.isfinite(length_sq) or length_sq <= _EPS:
        return None
    t = (
        (target[0] - line_start[0]) * dx
        + (target[1] - line_start[1]) * dy
    ) / length_sq
    projected = (line_start[0] + t * dx, line_start[1] + t * dy)
    if not all(math.isfinite(v) for v in projected):
        return None
    return projected


def signed_axis_distance_mm_v1(
    target: Optional[Point],
    origin: Optional[Point],
    axis: Optional[Point],
    mm_per_pixel: Optional[float],
) -> Optional[float]:
    """Signed distance from origin to target along a unit axis, in millimetres."""
    if target is None or origin is None or axis is None or not _valid_ratio(mm_per_pixel):
        return None
    assert mm_per_pixel is not None
    value = (
        (target[0] - origin[0]) * axis[0]
        + (target[1] - origin[1]) * axis[1]
    ) * mm_per_pixel
    return value if math.isfinite(value) else None


def craniom_ab_prime_mm_v1(
    a: Optional[Point],
    b: Optional[Point],
    po: Optional[Point],
    orbitale: Optional[Point],
    mm_per_pixel: Optional[float],
) -> Optional[float]:
    """CRANIOM_AB_PRIME_V1.

    A' and B' are the orthogonal projections of A and B on Frankfort.
    Positive means A is anterior to B along the anatomical Po->Or direction.
    Algebraically this is dot(A-B, unit(Po->Or)) * mm_per_pixel.
    """
    axis = frankfort_axis_v1(po, orbitale)
    return signed_axis_distance_mm_v1(a, b, axis, mm_per_pixel)


def nasion_vertical_offset_mm_v1(
    point: Optional[Point],
    nasion: Optional[Point],
    po: Optional[Point],
    orbitale: Optional[Point],
    mm_per_pixel: Optional[float],
) -> Optional[float]:
    """Signed AP distance to the line through N perpendicular to Frankfort.

    Positive is anterior, following the Po->Or Frankfort orientation.
    """
    axis = frankfort_axis_v1(po, orbitale)
    return signed_axis_distance_mm_v1(point, nasion, axis, mm_per_pixel)


def craniom_facial_depth_mm_v1(
    sella: Optional[Point],
    nasion: Optional[Point],
    po: Optional[Point],
    orbitale: Optional[Point],
    mm_per_pixel: Optional[float],
) -> Optional[float]:
    """Magnitude of S-to-Nasion-vertical distance used by the legacy COM flow."""
    offset = nasion_vertical_offset_mm_v1(
        sella, nasion, po, orbitale, mm_per_pixel
    )
    return abs(offset) if offset is not None else None
