"""G5 LAB Bézier editable controls — synthetic-only geometry and V1 consistency."""
from __future__ import annotations

from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from unittest import TestCase

source=Path(__file__).resolve().parents[1]/"backend/services/ortho_g5_bezier_profile.py"
spec=spec_from_file_location("g5_bezier_pure_lab",source)
assert spec and spec.loader
mod=module_from_spec(spec)
spec.loader.exec_module(mod)

IMG=(1935,2400)
NODES=[
    {"anchor":[150.0,250.0],"incoming":[150.0,250.0],"outgoing":[200.0,250.0]},
    {"anchor":[300.0,250.0],"incoming":[250.0,250.0],"outgoing":[350.0,300.0]},
    {"anchor":[500.0,450.0],"incoming":[450.0,400.0],"outgoing":[500.0,450.0]},
]


def contours_from_nodes(nodes=NODES):
    return [{"id":"soft_tissue_profile",
             "points":mod.sample_bezier_profile(nodes,image_size=IMG)}]


class G5BezierProfileContract(TestCase):
    def test_endpoints_source_pixels_and_repeatability(self):
        one=mod.sample_bezier_profile(NODES,image_size=IMG)
        two=mod.sample_bezier_profile(deepcopy(NODES),image_size=IMG)
        self.assertEqual(one,two)
        self.assertEqual(one[0],[150.,250.])
        self.assertEqual(one[-1],[500.,450.])
        self.assertLessEqual(len(one),600)
        self.assertGreaterEqual(len(one),16)
        for x,y in one:
            self.assertGreaterEqual(x,0)
            self.assertGreaterEqual(y,0)
            self.assertLess(x,IMG[0])
            self.assertLess(y,IMG[1])

    def test_valid_control_geometry_exactly_matches_approved_v1_samples(self):
        samples=contours_from_nodes()
        checked=mod.verify_bezier_profile_matches(NODES,contours=samples,image_size=IMG)
        self.assertEqual(len(checked),3)

    def test_legacy_five_pixel_bezier_drafts_remain_exactly_readable(self):
        old_points=mod.sample_bezier_profile(
            NODES,image_size=IMG,step_pixels=5)
        contours=[{"id":"soft_tissue_profile","points":old_points}]
        restored=mod.verify_bezier_profile_matches(
            NODES,contours=contours,image_size=IMG)
        self.assertEqual(len(restored),len(NODES))
        new_points=mod.sample_bezier_profile(NODES,image_size=IMG)
        self.assertLessEqual(len(new_points),len(old_points))
        self.assertNotEqual(new_points,old_points)

    def test_forged_v1_polyline_is_rejected(self):
        forged=contours_from_nodes()
        forged[0]["points"][15][0]+=3
        with self.assertRaisesRegex(mod.G5BezierRejected,"SAMPLES_DIFFER"):
            mod.verify_bezier_profile_matches(NODES,contours=forged,image_size=IMG)

    def test_changed_handles_must_trigger_new_sample_and_new_approval(self):
        forged_nodes=deepcopy(NODES)
        forged_nodes[1]["incoming"][0]+=30
        with self.assertRaisesRegex(mod.G5BezierRejected,"SAMPLES_DIFFER"):
            mod.verify_bezier_profile_matches(
                forged_nodes,contours=contours_from_nodes(),image_size=IMG)

    def test_fail_closed_on_nan_outside_image_and_invalid_schema(self):
        for change in (
            lambda n:n[0]["anchor"].__setitem__(0,float("nan")),
            lambda n:n[0]["outgoing"].__setitem__(0,-1),
            lambda n:n[0].update({"unexpected":"value"}),
        ):
            nodes=deepcopy(NODES)
            change(nodes)
            with self.assertRaises(mod.G5BezierRejected):
                mod.sample_bezier_profile(nodes,image_size=IMG)

    def test_rejects_degenerate_and_overbudget_geometry(self):
        nodes=deepcopy(NODES)
        nodes[1]["anchor"]=[150.1,250.0]
        with self.assertRaisesRegex(mod.G5BezierRejected,"DEGENERATE"):
            mod.sample_bezier_profile(nodes,image_size=IMG)
        big=deepcopy(NODES)
        big[0]["anchor"]=[0,0]
        big[0]["outgoing"]=[500,2000]
        big[1]["incoming"]=[1200,1800]
        big[1]["anchor"]=[1900,2000]
        big[2]["anchor"]=[1920,2300]
        with self.assertRaisesRegex(mod.G5BezierRejected,"TOO_MANY"):
            mod.sample_bezier_profile(big,image_size=IMG)
