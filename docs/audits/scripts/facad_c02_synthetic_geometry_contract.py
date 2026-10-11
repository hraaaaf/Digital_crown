#!/usr/bin/env python3
"""FACAD C02 research-only candidate geometry oracles.

NOT a FACAD implementation. No vendor numeric parity, clinical formula or norm
equivalence is asserted. The one vendor-documented control tested here is the
Auto angle-PRESENTATION range selector (3.14 Reference Manual ch.12, p.85;
3.12 release notes p.1). Geometric functions below are independent synthetic
probes deliberately not mapped to proprietary operator semantics.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import unittest


class NotComputable(ValueError):
    """Explicit fail-closed status for absent/degenerate input."""


def require_finite(*values: float) -> None:
    if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in values):
        raise NotComputable("missing, NaN or infinite numeric input")


def vec(a, b):
    require_finite(*a, *b)
    return (b[0] - a[0], b[1] - a[1])


def cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def nonzero(v):
    if math.hypot(*v) <= 1e-12:
        raise NotComputable("zero-length line or undefined angle")
    return v


def distance_mm(a, b, mm_per_pixel):
    require_finite(mm_per_pixel)
    if mm_per_pixel <= 0:
        raise NotComputable("missing or nonpositive image calibration")
    return math.hypot(*vec(a, b)) * mm_per_pixel


def directed_angle_deg(a, b):
    nonzero(a)
    nonzero(b)
    return math.degrees(math.atan2(cross(a, b), dot(a, b)))


def signed_projection_mm(origin, axis_end, point, mm_per_pixel):
    require_finite(mm_per_pixel)
    if mm_per_pixel <= 0:
        raise NotComputable("missing or nonpositive image calibration")
    axis = nonzero(vec(origin, axis_end))
    target = vec(origin, point)
    return dot(target, axis) / math.hypot(*axis) * mm_per_pixel


def intersection(a, b, c, d):
    """Finite 2D infinite-line intersection; returns NOT_COMPUTABLE for parallels."""
    ab, cd, ac = vec(a, b), vec(c, d), vec(a, c)
    nonzero(ab)
    nonzero(cd)
    determinant = cross(ab, cd)
    if abs(determinant) <= 1e-12:
        raise NotComputable("parallel or coincident lines")
    t = cross(ac, cd) / determinant
    return (a[0] + t * ab[0], a[1] + t * ab[1])


def normalized_unsigned_deg(deg):
    """Mathematical candidate normalizer. FACAD endpoint/boundary not certified."""
    require_finite(deg)
    return deg % 360.0


def normalized_signed_deg(deg):
    """Mathematical candidate normalizer; +180 becomes -180 here by choice."""
    require_finite(deg)
    return (deg + 180.0) % 360.0 - 180.0


def facad_documented_auto_presentation(norm_upper, override="auto"):
    """Range SELECTOR documented by FACAD 3.14 reference manual p85.

    'auto' with upper Norm <135 uses signed; no Norm or >=135 unsigned.
    Does NOT resolve vendor angle orientation / end-point behavior.
    """
    if override in ("0-360", "±180"):
        return override
    if override != "auto":
        raise NotComputable("unknown presentation option")
    if norm_upper is None:
        return "0-360"
    require_finite(norm_upper)
    return "±180" if norm_upper < 135 else "0-360"


@dataclass(frozen=True)
class TypedValue:
    value: float
    unit: str


def dimensioned_subtract(a: TypedValue | None, b: TypedValue | None):
    if a is None or b is None:
        raise NotComputable("unresolved dependency")
    if a.unit != b.unit:
        raise NotComputable("incompatible units")
    require_finite(a.value, b.value)
    return TypedValue(a.value - b.value, a.unit)


ANALYSIS_SCOPED_ML = {
    "Steiner": ("Go", "Gn"),
    "Tweed": ("Go", "Me"),
}


def scoped_line(name, markers):
    if name not in ANALYSIS_SCOPED_ML:
        raise NotComputable("unknown analysis, refuse global alias")
    endpoints = ANALYSIS_SCOPED_ML[name]
    if any(m not in markers for m in endpoints):
        raise NotComputable("unresolved marker")
    return tuple(markers[m] for m in endpoints)


class SyntheticCandidateChecks(unittest.TestCase):
    def test_documented_auto_low(self):
        self.assertEqual(facad_documented_auto_presentation(134.99), "±180")

    def test_documented_auto_threshold(self):
        self.assertEqual(facad_documented_auto_presentation(135), "0-360")

    def test_documented_auto_no_norm(self):
        self.assertEqual(facad_documented_auto_presentation(None), "0-360")

    def test_documented_explicit_override(self):
        self.assertEqual(facad_documented_auto_presentation(90, "0-360"), "0-360")
        self.assertEqual(facad_documented_auto_presentation(None, "±180"), "±180")

    def test_unknown_override_closed(self):
        with self.assertRaises(NotComputable):
            facad_documented_auto_presentation(80, "symmetric")

    def test_nan_norm_closed(self):
        with self.assertRaises(NotComputable):
            facad_documented_auto_presentation(float("nan"))

    def test_unsigned_wrap_candidate(self):
        self.assertEqual(normalized_unsigned_deg(-45), 315)
        self.assertEqual(normalized_unsigned_deg(405), 45)

    def test_signed_wrap_candidate(self):
        self.assertEqual(normalized_signed_deg(225), -135)
        self.assertEqual(normalized_signed_deg(-225), 135)

    def test_signed_endpoint_is_not_vendor_proof(self):
        self.assertEqual(normalized_signed_deg(180), -180)

    def test_directed_angle_is_order_dependent(self):
        x = (1, 0)
        y = (0, 1)
        self.assertAlmostEqual(directed_angle_deg(x, y), 90)
        self.assertAlmostEqual(directed_angle_deg(y, x), -90)

    def test_angle_obtuse_and_reflex_candidates(self):
        self.assertAlmostEqual(directed_angle_deg((1, 0), (-1, 1)), 135)
        self.assertAlmostEqual(directed_angle_deg((1, 0), (-1, -1)), -135)

    def test_zero_length_angle_closed(self):
        with self.assertRaises(NotComputable):
            directed_angle_deg((0, 0), (0, 1))

    def test_calibrated_distance(self):
        self.assertAlmostEqual(distance_mm((0, 0), (3, 4), 0.5), 2.5)

    def test_distance_translation_invariant(self):
        self.assertAlmostEqual(distance_mm((100, -20), (103, -16), 0.5), 2.5)

    def test_distance_rotation_invariant(self):
        self.assertAlmostEqual(distance_mm((0, 0), (-4, 3), 0.5), 2.5)

    def test_distance_requires_calibration(self):
        for factor in (0, -1, float("nan")):
            with self.assertRaises(NotComputable):
                distance_mm((0, 0), (3, 4), factor)

    def test_projection_axis_sign_is_order_dependent(self):
        self.assertAlmostEqual(signed_projection_mm((0, 0), (10, 0), (5, 6), 1), 5)
        self.assertAlmostEqual(signed_projection_mm((10, 0), (0, 0), (5, 6), 1), 5)
        self.assertAlmostEqual(signed_projection_mm((0, 0), (-10, 0), (5, 6), 1), -5)

    def test_projection_orthogonal_zero(self):
        self.assertAlmostEqual(signed_projection_mm((0, 0), (1, 0), (0, 20), 1), 0)

    def test_projection_axis_zero_closed(self):
        with self.assertRaises(NotComputable):
            signed_projection_mm((0, 0), (0, 0), (1, 2), 1)

    def test_line_intersection(self):
        self.assertEqual(intersection((0, 0), (10, 0), (5, -5), (5, 5)), (5, 0))

    def test_parallel_lines_closed(self):
        with self.assertRaises(NotComputable):
            intersection((0, 0), (10, 0), (0, 1), (10, 1))

    def test_coincident_lines_closed(self):
        with self.assertRaises(NotComputable):
            intersection((0, 0), (10, 0), (3, 0), (6, 0))

    def test_pmprime_not_general_pm_alias(self):
        xi, pm, a, pog = (0, 0), (10, 0), (5, -5), (5, 5)
        pmprime = intersection(xi, pm, a, pog)
        self.assertNotEqual(pmprime, pm)
        self.assertAlmostEqual(distance_mm(xi, pmprime, 1), 5)
        self.assertAlmostEqual(distance_mm(xi, pm, 1), 10)

    def test_profile_scoped_ml_differs(self):
        markers = {"Go": (0, 0), "Gn": (4, 0), "Me": (4, 3)}
        steiner = scoped_line("Steiner", markers)
        tweed = scoped_line("Tweed", markers)
        self.assertNotEqual(steiner, tweed)
        self.assertNotEqual(directed_angle_deg(vec(*steiner), (0, 1)),
                            directed_angle_deg(vec(*tweed), (0, 1)))

    def test_unknown_analysis_ml_closed(self):
        with self.assertRaises(NotComputable):
            scoped_line("Global", {"Go": (0, 0), "Gn": (1, 0)})

    def test_missing_marker_ml_closed(self):
        with self.assertRaises(NotComputable):
            scoped_line("Steiner", {"Go": (0, 0)})

    def test_mcnamara_subtract_same_unit(self):
        self.assertEqual(dimensioned_subtract(TypedValue(112, "mm"),
                                              TypedValue(84, "mm")),
                         TypedValue(28, "mm"))

    def test_mcnamara_subtract_unit_mismatch_closed(self):
        with self.assertRaises(NotComputable):
            dimensioned_subtract(TypedValue(112, "mm"),
                                 TypedValue(80, "degrees"))

    def test_mcnamara_subtract_unresolved_closed(self):
        with self.assertRaises(NotComputable):
            dimensioned_subtract(None, TypedValue(80, "mm"))

    def test_nonfinite_geometry_closed(self):
        with self.assertRaises(NotComputable):
            intersection((0, 0), (float("inf"), 5), (2, 4), (1, 7))


if __name__ == "__main__":
    unittest.main(verbosity=2)
