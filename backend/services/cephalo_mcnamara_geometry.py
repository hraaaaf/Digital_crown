"""Source-specific McNamara linear geometry.

Only patient-observed deterministic geometry lives here. No norms, diagnosis,
growth projection or treatment logic is allowed.
"""
from __future__ import annotations

import math
from typing import Optional, Tuple

Point = Tuple[float, float]
_EPS = 1e-12


def _finite_point(point: Optional[Point]) -> bool:
    return (
        point is not None
        and len(point) == 2
        and math.isfinite(point[0])
        and math.isfinite(point[1])
    )


def _valid_ratio(mm_per_pixel: Optional[float]) -> bool:
    return (
        mm_per_pixel is not None
        and math.isfinite(mm_per_pixel)
        and mm_per_pixel > 0
    )


def mcnamara_linear_distance_px_v1(
    start: Optional[Point], end: Optional[Point]
) -> Optional[float]:
    """Return a source-image Euclidean segment length, fail-closed if degenerate."""
    if not _finite_point(start) or not _finite_point(end):
        return None
    assert start is not None and end is not None
    value = math.hypot(end[0] - start[0], end[1] - start[1])
    if not math.isfinite(value) or value <= _EPS:
        return None
    return value


def mcnamara_linear_distance_mm_v1(
    start: Optional[Point],
    end: Optional[Point],
    mm_per_pixel: Optional[float],
) -> Optional[float]:
    """Convert one McNamara linear segment to millimetres using verified calibration."""
    if not _valid_ratio(mm_per_pixel):
        return None
    distance_px = mcnamara_linear_distance_px_v1(start, end)
    if distance_px is None:
        return None
    assert mm_per_pixel is not None
    value = distance_px * mm_per_pixel
    return value if math.isfinite(value) else None


def mcnamara_co_a_mm_v1(
    co: Optional[Point], a: Optional[Point], mm_per_pixel: Optional[float]
) -> Optional[float]:
    return mcnamara_linear_distance_mm_v1(co, a, mm_per_pixel)


def mcnamara_co_gn_mm_v1(
    co: Optional[Point], gn: Optional[Point], mm_per_pixel: Optional[float]
) -> Optional[float]:
    return mcnamara_linear_distance_mm_v1(co, gn, mm_per_pixel)


def mcnamara_ans_me_mm_v1(
    ans: Optional[Point], me: Optional[Point], mm_per_pixel: Optional[float]
) -> Optional[float]:
    return mcnamara_linear_distance_mm_v1(ans, me, mm_per_pixel)
