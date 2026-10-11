#!/usr/bin/env python3
"""Wave 3 FAC05: source-pinned Digital Crown geometry, synthetic fixtures only.

Never asserts proprietary FACAD semantics, clinical norms or patient parity.
The comparison here is between real DC module functions and independent math.
"""
from __future__ import annotations

import importlib.util
import math
import os
from pathlib import Path
import sys
import unittest


def load(name: str, path: Path):
    if not path.is_file():
        raise RuntimeError("Pinned DC source not found")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("DC source cannot be imported")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


root = Path(os.environ["FAC05_PINNED_SOURCE_ROOT"]).resolve(strict=True)
tweed = load("fac05_dc_tweed_v1", root / "backend/services/cephalo_tweed_merrifield_geometry.py")
mcnamara = load("fac05_dc_mcnamara_v1", root / "backend/services/cephalo_mcnamara_geometry.py")
ricketts = load("fac05_dc_ricketts_v1", root / "backend/services/cephalo_ricketts_geometry.py")
candidate = load("fac05_candidate_math_v1", root / "docs/audits/scripts/facad_c02_synthetic_geometry_contract.py")


class Wave3SyntheticDC(unittest.TestCase):
    def test_tweed_fma_orthogonal(self):
        self.assertAlmostEqual(tweed.tweed_fma_deg_v1((0,0),(2,0),(0,0),(0,2)),90)

    def test_tweed_fmia_coincident_axes(self):
        self.assertAlmostEqual(tweed.tweed_fmia_deg_v1((0,0),(2,0),(0,0),(2,0)),0)

    def test_tweed_impa_supplementary(self):
        self.assertAlmostEqual(tweed.tweed_impa_deg_v1((0,0),(0,2),(0,0),(2,0)),90)
        self.assertAlmostEqual(tweed.tweed_impa_deg_v1((0,0),(1,1),(0,0),(2,0)),135)

    def test_tweed_ml_must_not_alias_steiner_ml(self):
        markers={"Go":(0,0),"Me":(0,3),"Gn":(2,0)}
        st=candidate.scoped_line("Steiner",markers)
        tw=candidate.scoped_line("Tweed",markers)
        self.assertNotEqual(st,tw)
        self.assertAlmostEqual(tweed.tweed_fma_deg_v1(*tw,(0,0),(2,0)),90)

    def test_tweed_merrifield_requires_unique_most_protrusive_lip(self):
        self.assertIsNone(tweed.merrifield_z_angle_deg_v1(
            (0,0),(2,0),(0,0),(5,1),(5,-1)))
        self.assertAlmostEqual(tweed.merrifield_z_angle_deg_v1(
            (0,0),(2,0),(0,0),(5,1),(3,1)),
            math.degrees(math.atan2(1,5)))

    def test_tweed_nonfinite_geometry_closed(self):
        self.assertIsNone(tweed.tweed_fma_deg_v1(
            (0,0),(float("nan"),1),(0,0),(1,1)))

    def test_mcnamara_px_mm_explicit_calibration(self):
        self.assertAlmostEqual(mcnamara.mcnamara_linear_distance_px_v1(
            (0,0),(3,4)),5)
        self.assertAlmostEqual(mcnamara.mcnamara_co_a_mm_v1(
            (0,0),(3,4),0.5),2.5)

    def test_mcnamara_max_mand_difference_dependency_units(self):
        co=(0,0)
        co_gn=mcnamara.mcnamara_co_gn_mm_v1(co,(6,8),0.5)
        co_a=mcnamara.mcnamara_co_a_mm_v1(co,(3,4),0.5)
        self.assertEqual(candidate.dimensioned_subtract(
            candidate.TypedValue(co_gn,"mm"),candidate.TypedValue(co_a,"mm")),
            candidate.TypedValue(2.5,"mm"))

    def test_mcnamara_absent_calibration_closed(self):
        for scale in (None,0,-1,float("nan")):
            self.assertIsNone(mcnamara.mcnamara_co_a_mm_v1(
                (0,0),(3,4),scale))

    def test_mcnamara_missing_landmark_closed(self):
        self.assertIsNone(mcnamara.mcnamara_co_gn_mm_v1((0,0),None,0.5))
        self.assertIsNone(mcnamara.mcnamara_linear_distance_px_v1((0,0),(0,0)))

    def test_ricketts_constructed_gn_requires_intersection(self):
        n,pog,go,me=(0,0),(10,0),(5,-5),(5,5)
        self.assertEqual(ricketts.ricketts_constructed_gn_v1(n,pog,go,me),(5,0))
        self.assertNotEqual(ricketts.ricketts_constructed_gn_v1(n,pog,go,me),pog)

    def test_ricketts_constructed_gn_parallel_closed(self):
        self.assertIsNone(ricketts.ricketts_constructed_gn_v1(
            (0,0),(10,0),(0,1),(10,1)))

    def test_ricketts_facial_depth_geometric_candidate(self):
        self.assertAlmostEqual(ricketts.ricketts_facial_depth_deg_v1(
            (0,0),(10,0),(5,10),(5,0)),90)

    def test_ricketts_facial_axis_geometric_candidate(self):
        self.assertAlmostEqual(ricketts.ricketts_facial_axis_deg_v1(
            (0,0),(0,10),(0,0),(10,0)),90)

    def test_ricketts_e_line_v2_differs_from_legacy_v1(self):
        po,or_,prn,pog,lip=(0,0),(10,0),(0,0),(10,10),(0,10)
        v1=ricketts.ricketts_e_line_horizontal_signed_distance_px_v1(
            lip,prn,pog,po,or_)
        v2=ricketts.ricketts_e_line_perpendicular_signed_distance_px_v2(
            lip,prn,pog,po,or_)
        self.assertAlmostEqual(v1,-10)
        self.assertAlmostEqual(v2,-math.sqrt(50))
        self.assertNotAlmostEqual(v1,v2)

    def test_ricketts_e_line_signed_direction(self):
        args=((0,0),(0,10),(0,0),(10,0))
        self.assertAlmostEqual(ricketts.ricketts_e_line_perpendicular_signed_distance_px_v2(
            (3,5),*args),3)
        self.assertAlmostEqual(ricketts.ricketts_e_line_perpendicular_signed_distance_px_v2(
            (-3,5),*args),-3)

    def test_ricketts_invalid_facial_axis_closed(self):
        self.assertIsNone(ricketts.ricketts_facial_axis_deg_v1(
            (0,0),(0,0),(0,0),(10,0)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
