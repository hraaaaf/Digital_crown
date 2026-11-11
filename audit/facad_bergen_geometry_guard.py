"""Experimental Bergen Short geometry guards (not a FACAD clinical implementation).

Only the undefined-geometry boundary is asserted here. Unsigned angles are
mathematical primitives; FACAD-specific branches, signs, aliases and norms
remain unverified. None denotes non-computable, never an angle of zero.
"""

from __future__ import annotations

import math
from typing import Sequence

Point = tuple[float, float]
_ZERO_VECTOR_EPS = 1e-12


def _point(p: Sequence[float] | None) -> Point | None:
    if p is None or not isinstance(p, (tuple, list)) or len(p) != 2:
        return None
    x, y = p
    if isinstance(x, bool) or isinstance(y, bool):
        return None
    try:
        xx, yy = float(x), float(y)
    except (TypeError, ValueError, OverflowError):
        return None
    return (xx, yy) if math.isfinite(xx) and math.isfinite(yy) else None


def _vector(start: Sequence[float] | None, end: Sequence[float] | None) -> Point | None:
    a, b = _point(start), _point(end)
    if a is None or b is None:
        return None
    x, y = b[0] - a[0], b[1] - a[1]
    if not math.isfinite(x) or not math.isfinite(y):
        return None
    length = math.hypot(x, y)
    return (x, y) if math.isfinite(length) and length > _ZERO_VECTOR_EPS else None


def _unsigned_angle(u: Point | None, v: Point | None) -> float | None:
    if u is None or v is None:
        return None
    det = u[0] * v[1] - u[1] * v[0]
    dot = u[0] * v[0] + u[1] * v[1]
    if not math.isfinite(det) or not math.isfinite(dot):
        return None
    result = math.degrees(math.atan2(abs(det), dot))
    return result if math.isfinite(result) else None


def angle3p_unsigned_deg(a: Sequence[float] | None, vertex: Sequence[float] | None,
                         c: Sequence[float] | None) -> float | None:
    """Unsigned angle at vertex; None when either ray is undefined."""
    return _unsigned_angle(_vector(vertex, a), _vector(vertex, c))


def angle4p_unsigned_deg(a: Sequence[float] | None, b: Sequence[float] | None,
                         c: Sequence[float] | None, d: Sequence[float] | None) -> float | None:
    """Unsigned angle between AB and CD; no FACAD branch or sign asserted."""
    return _unsigned_angle(_vector(a, b), _vector(c, d))


def point_line_distance_px(p: Sequence[float] | None, a: Sequence[float] | None,
                           b: Sequence[float] | None) -> float | None:
    """Unsigned distance to infinite line AB; None for a degenerate line."""
    point, origin, direction = _point(p), _point(a), _vector(a, b)
    if point is None or origin is None or direction is None:
        return None
    length = math.hypot(*direction)
    numerator = abs(direction[0] * (point[1] - origin[1]) - direction[1] * (point[0] - origin[0]))
    result = numerator / length
    return result if math.isfinite(result) else None
