#!/usr/bin/env python3
"""Synthetic candidate geometry versus pinned Digital Crown contract, NOT Facad parity.

No Facad executable, file, patient, export, norms, calibration inference or clinical
assertion. Unknown vendor Angle3p semantics remain UNKNOWN after these tests.
"""
from __future__ import annotations

import importlib.util
import math
import os
from pathlib import Path
import sys
import unittest


def _load(name: str, path: Path):
    if not path.is_file():
        raise RuntimeError("Source-only bridge: pinned module missing")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Source-only bridge: unimportable pinned module")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


source = Path(os.environ["FAC05_PINNED_SOURCE_ROOT"]).resolve(strict=True)
dc = _load("fac05_pinned_dc_steiner", source / "backend/services/cephalo_steiner_geometry.py")
candidate = _load(
    "fac05_pinned_independent_candidate",
    source / "docs/audits/scripts/facad_c02_synthetic_geometry_contract.py",
)


class Fac05DcSourceOnlyChecks(unittest.TestCase):
    def test_steiner_sna_snb_are_ray_angles_in_dc(self):
        n, s = (0., 0.), (-1., 0.)
        a, b = (-1., 1.), (-1., -1.)
        self.assertAlmostEqual(dc.steiner_sna_deg_v1(s, n, a), 45.)
        self.assertAlmostEqual(dc.steiner_snb_deg_v1(s, n, b), 45.)

    def test_anb_label_does_not_prove_vendor_angle3p_equivalence(self):
        n, s = (0., 0.), (-1., 0.)
        a, b = (-1., 1.), (-1., -1.)
        dc_result = dc.steiner_anb_deg_v1(s, n, a, b)
        candidate_signed_angle = candidate.directed_angle_deg(
            candidate.vec(n, a), candidate.vec(n, b))
        self.assertAlmostEqual(dc_result, 0.)
        self.assertAlmostEqual(candidate_signed_angle, 90.)
        self.assertNotAlmostEqual(dc_result, candidate_signed_angle)

    def test_dc_anb_rounding_is_part_of_dc_contract_only(self):
        s, n = (-1., 0.), (0., 0.)
        a, b = (-1., 1.), (-1., 2.)
        sna = dc.steiner_sna_deg_v1(s, n, a)
        snb = dc.steiner_snb_deg_v1(s, n, b)
        self.assertAlmostEqual(dc.steiner_anb_deg_v1(s, n, a, b),
                               round(sna, 1) - round(snb, 1))
        self.assertNotEqual(dc.steiner_anb_deg_v1(s, n, a, b),
                            sna - snb)

    def test_sna_signed_candidate_and_dc_nonreflex_differ(self):
        n, s, a = (0., 0.), (-1., 0.), (-1., 1.)
        self.assertAlmostEqual(dc.steiner_sna_deg_v1(s, n, a), 45.)
        self.assertAlmostEqual(
            candidate.directed_angle_deg(candidate.vec(n, s), candidate.vec(n, a)),
            -45.)

    def test_missing_dependency_refuses_number_in_both_contracts(self):
        self.assertIsNone(dc.steiner_sna_deg_v1(None, (0, 0), (1, 1)))
        with self.assertRaises(candidate.NotComputable):
            candidate.directed_angle_deg((0, 0), (1, 0))

    def test_different_ml_scoped_steiner_and_tweed(self):
        markers = {"Go": (0, 0), "Gn": (1, 0), "Me": (1, 1)}
        st = candidate.scoped_line("Steiner", markers)
        tw = candidate.scoped_line("Tweed", markers)
        self.assertNotEqual(st, tw)
        self.assertAlmostEqual(dc.steiner_sn_mp_deg_v1((0, 0), (2, 0), *st), 0.)
        self.assertAlmostEqual(candidate.directed_angle_deg(
            candidate.vec(*tw), (1, 0)), -45.)

    def test_explicit_facial_crown_marker_required_for_linear_steiner(self):
        self.assertIsNone(dc.steiner_u1_na_mm_v1(
            None, (0., 0.), (0., 10.), 0.5))

    def test_calibration_and_point_to_line_geometry_are_explicit(self):
        self.assertAlmostEqual(
            dc.steiner_pog_nb_mm_v1((3, 4), (0, 0), (0, 10), 0.5), 1.5)
        self.assertIsNone(
            dc.steiner_pog_nb_mm_v1((3, 4), (0, 0), (0, 10), None))
        with self.assertRaises(candidate.NotComputable):
            candidate.distance_mm((0, 0), (3, 4), None)

    def test_nonfinite_and_degenerate_are_not_numbers(self):
        self.assertIsNone(dc.steiner_sna_deg_v1((0, 0), (0, 0), (-1, 1)))
        self.assertIsNone(dc.steiner_sna_deg_v1((float("nan"), 0), (0, 0), (-1, 1)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
