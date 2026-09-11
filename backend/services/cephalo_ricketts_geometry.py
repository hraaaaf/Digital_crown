"""Versioned geometry for the source-safe R9 Ricketts subset.

Only patient-observed geometry with a locked directional convention is
implemented here. No norms, classification, diagnosis, prognosis or treatment
logic belongs in this module.
"""
from __future__ import annotations

import math
from typing import Optional, Tuple

Point = Tuple[float, float]
_EPS = 1e-12


def ricketts_facial_depth_deg_v1(
    po: Point,
    or_: Point,
    n: Point,
    pog: Point,
) -> Optional[float]:
    """Ricketts facial depth as the posterior angle FH(Po->Or) to Pog->N.

    The directed axes preserve clinically meaningful values on both sides of
    90 degrees while remaining invariant under image mirroring. This is not the
    legacy Downs acute-axis helper and must not be silently aliased to it.
    """

    fh = (or_[0] - po[0], or_[1] - po[1])
    facial_posterior = (n[0] - pog[0], n[1] - pog[1])
    fh_len = math.hypot(*fh)
    facial_len = math.hypot(*facial_posterior)
    values = (*po, *or_, *n, *pog, fh_len, facial_len)
    if not all(math.isfinite(value) for value in values):
        return None
    if fh_len <= _EPS or facial_len <= _EPS:
        return None

    cosine = (
        fh[0] * facial_posterior[0] + fh[1] * facial_posterior[1]
    ) / (fh_len * facial_len)
    cosine = max(-1.0, min(1.0, cosine))
    angle = math.degrees(math.acos(cosine))
    return angle if math.isfinite(angle) else None
