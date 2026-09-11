"""Versioned geometry for the source-safe R9 Ricketts subset.

Only patient-observed geometry with locked directional conventions is
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
    """Ricketts facial depth as the posterior angle FH(Po->Or) to Pog->N."""

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


def ricketts_e_line_signed_distance_px_v1(
    lip: Point,
    prn: Point,
    pog_soft: Point,
    po: Point,
    or_: Point,
) -> Optional[float]:
    """Signed perpendicular lip distance to Prn-Pog' in source pixels.

    Magnitude is the shortest point-to-line distance. Sign is positive when the
    perpendicular residual points anteriorly according to anatomical Frankfort
    (Po->Or), negative posteriorly. Frankfort is used only to orient the sign;
    it does not change the perpendicular magnitude. This makes the convention
    invariant under image mirroring and rigid rotation.
    """

    values = (*lip, *prn, *pog_soft, *po, *or_)
    if not all(math.isfinite(value) for value in values):
        return None

    e = (pog_soft[0] - prn[0], pog_soft[1] - prn[1])
    e_len_sq = e[0] * e[0] + e[1] * e[1]
    fh = (or_[0] - po[0], or_[1] - po[1])
    fh_len = math.hypot(*fh)
    if e_len_sq <= _EPS or fh_len <= _EPS:
        return None

    t = ((lip[0] - prn[0]) * e[0] + (lip[1] - prn[1]) * e[1]) / e_len_sq
    projection = (prn[0] + t * e[0], prn[1] + t * e[1])
    residual = (lip[0] - projection[0], lip[1] - projection[1])
    magnitude = math.hypot(*residual)
    if not math.isfinite(magnitude):
        return None
    if magnitude <= _EPS:
        return 0.0

    anterior_score = residual[0] * (fh[0] / fh_len) + residual[1] * (fh[1] / fh_len)
    if not math.isfinite(anterior_score) or abs(anterior_score) <= _EPS:
        return None
    return math.copysign(magnitude, anterior_score)
