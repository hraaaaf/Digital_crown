"""FACAD Tweed Wits geometry candidate — NOT wired to clinical runtime.

Vendor-specific construction from the already accepted FACAD contract:
OLa = midpoint(Is, Ii); OL = OLp -> OLa (OLp explicitly manual);
Wits = signed projection of B -> A onto OL in calibrated millimetres.
This is not the historical Jacobson Wits implementation and has no
normative, diagnostic, PDF or persistence activation.
"""
from __future__ import annotations

import math
from typing import Optional, Tuple

Point = Tuple[float, float]
_EPS = 1e-12


def _finite_point(point: Optional[Point]) -> bool:
    return (
        point is not None
        and isinstance(point, (tuple, list))
        and len(point) == 2
        and all(
            isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
            for v in point
        )
    )


def facad_tweed_wits_bisected_ol_mm_candidate_v1(
    *,
    olp: Optional[Point],
    u1_incisal: Optional[Point],
    l1_incisal: Optional[Point],
    b: Optional[Point],
    a: Optional[Point],
    mm_per_pixel: Optional[float],
) -> Optional[float]:
    """Signed B->A projection onto OLp->midpoint(Is,Ii); fail closed."""
    if not all(_finite_point(p) for p in (olp, u1_incisal, l1_incisal, b, a)):
        return None
    if (
        not isinstance(mm_per_pixel, (int, float))
        or isinstance(mm_per_pixel, bool)
        or not math.isfinite(mm_per_pixel)
        or mm_per_pixel <= 0
    ):
        return None
    assert olp is not None and u1_incisal is not None and l1_incisal is not None
    assert a is not None and b is not None
    ola = ((u1_incisal[0] + l1_incisal[0]) / 2.0,
           (u1_incisal[1] + l1_incisal[1]) / 2.0)
    direction = (ola[0] - olp[0], ola[1] - olp[1])
    length = math.hypot(*direction)
    if not math.isfinite(length) or length <= _EPS:
        return None
    ba = (a[0] - b[0], a[1] - b[1])
    projection_px = (ba[0] * direction[0] + ba[1] * direction[1]) / length
    result = projection_px * mm_per_pixel
    return result if math.isfinite(result) else None
