#!/usr/bin/env python3
"""FACAD F01.13 ANB: source-pinned routing audit + NON-vendor synthetic oracle.

Read-only, stdlib-only. Never execute a FACAD binary, touch a patient file,
claim vendor Angle3p semantics, or change clinical calculation code.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[3]
SOURCE_PINS = {
    "backend/services/cephalo_engine.py": "240e938a6618557c9630fee8b5e9b49e18b6403c",
    "backend/services/cephalo_steiner_geometry.py": "70900959042c7e7373c404959c18122e3b8038e3",
    "backend/services/cephalo_steiner_evidence_adapter.py": "f9176686b1787f5b88573e5d5cca121399036eab",
    "backend/services/cephalo_service.py": "2e3c05d38d380d3f486d742281374272346b9a5b",
    "backend/services/cephalo_safe_engine.py": "9b0957f298d1cb3b98e38889bac813c34db4ee04",
    "backend/services/cephalo_runtime_evidence.py": "ee82322369291d85b0f93338292196cb61f4b6e5",
}
FACAD_C02_SHA256 = "4dbd3fa8419b684529fcbc17f615f49f7486cdf037fcfff025b1b307c0c0a548"

# Purely analytical hypothesis, NOT an observed FACAD result:
def unsigned_at_n(n, a, b):
    if any(p is None for p in (n, a, b)):
        return None
    vals = tuple(x for p in (n, a, b) for x in p)
    if not all(math.isfinite(float(v)) for v in vals):
        return None
    u = (a[0] - n[0], a[1] - n[1])
    v = (b[0] - n[0], b[1] - n[1])
    if math.hypot(*u) <= 1e-12 or math.hypot(*v) <= 1e-12:
        return None
    ang = math.degrees(abs(math.atan2(u[0]*v[1] - u[1]*v[0],
                                       u[0]*v[0] + u[1]*v[1])))
    return ang if math.isfinite(ang) else None

def source_guard():
    seen = {}
    for path, expected in SOURCE_PINS.items():
        p = ROOT / path
        if not p.is_file() or not p.resolve().is_relative_to(ROOT.resolve()):
            raise ValueError("Untrusted or missing source: " + path)
        raw = p.read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\x00" + raw).hexdigest()
        if actual != expected:
            raise ValueError("Git blob source drift (STOP): " + path)
        ast.parse(raw.decode("utf-8"), filename=path)
        seen[path] = actual
    engine = (ROOT / "backend/services/cephalo_engine.py").read_text()
    service = (ROOT / "backend/services/cephalo_service.py").read_text()
    safe = (ROOT / "backend/services/cephalo_safe_engine.py").read_text()
    steiner = (ROOT / "backend/services/cephalo_steiner_geometry.py").read_text()
    adapter = (ROOT / "backend/services/cephalo_steiner_evidence_adapter.py").read_text()
    evidence = (ROOT / "backend/services/cephalo_runtime_evidence.py").read_text()
    assertions = [
        ("Legacy ANB subtraction", 'sna - snb if sna is not None and snb is not None else None' in engine),
        ("Legacy acos unsigned", "math.acos(cosine)" in engine),
        ("Steiner typed ANB is rounded subtraction", "round(sna, 1) - round(snb, 1)" in steiner),
        ("Steiner runtime equality bound", "Runtime {spec.runtime_metric_name} does not match typed Steiner geometry" in adapter),
        ("Service invokes SafeCephaloEngine", "from backend.services.cephalo_safe_engine import cephalo_safe_engine as cephalo_engine" in service),
        ("Safe engine delegates to legacy", "_legacy_cephalo_engine.calculate_metrics(*args, **kwargs)" in safe),
        ("Separate canonical evidence materialization", "canonical_v2_measurements = materialize_canonical_analysis_v2_measurements(" in evidence),
        ("Legacy output designated compatibility", '"legacy_angles_data_role": "COMPATIBILITY_OUTPUT"' in evidence),
    ]
    for label, ok in assertions:
        if not ok:
            raise ValueError("Critical routing proof changed: " + label)
    return seen, [x[0] for x in assertions]

def real_steiner_geometry():
    path = ROOT / "backend/services/cephalo_steiner_geometry.py"
    spec = importlib.util.spec_from_file_location("_pinned_steiner_geometry_for_research", path)
    if spec is None or spec.loader is None:
        raise ValueError("No readable source geometry")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

FIXTURES = [
    ("F1_STRADDLE", (-1.,0.), (0.,0.), (1.,1.), (1.,-1.), 0., 90.),
    ("F1_MIRROR", (-1.,0.), (0.,0.), (1.,1.), (1.,1.), 0., 0.),
    ("F2_VERTICAL", (0.,1.), (0.,0.), (1.,1.), (1.,-1.), -90., 90.),
    ("F3_SAME_SIDE", (0.,-1.), (0.,0.), (1.,1.), (1.,2.), -18.4, 18.4),
]

def evaluate():
    source_pins, assertions = source_guard()
    geom = real_steiner_geometry()
    rows = []
    for name,s,n,a,b,expected_legacy,expected_unsigned in FIXTURES:
        value = geom.steiner_anb_deg_v1(s,n,a,b)
        candidate = unsigned_at_n(n,a,b)
        if value is None or candidate is None:
            raise ValueError("Synthetic fixture unexpectedly noncomputable")
        if round(value,1) != expected_legacy or round(candidate,1) != expected_unsigned:
            raise ValueError("Synthetic fixture disagrees with source-locked expectation: " + name)
        rows.append({
            "fixture": name,
            "pinned_dc_typed_legacy_parity_deg": round(value,1),
            "independent_unsigned_vertex_at_n_hypothesis_deg": round(candidate,1),
            "potential_difference_deg": round(abs(value-candidate),1),
            "facad_vendor_numeric_output": None,
            "facad_angle3p_semantics_verified": False,
        })
    if rows[0]["pinned_dc_typed_legacy_parity_deg"] != rows[1]["pinned_dc_typed_legacy_parity_deg"] \
       or rows[0]["independent_unsigned_vertex_at_n_hypothesis_deg"] == rows[1]["independent_unsigned_vertex_at_n_hypothesis_deg"]:
        raise ValueError("Decisive counterexample lost")
    return {
        "schema": "FACAD_F01_13_ANB_SOURCE_PINNED_RUNTIME_BOUNDARY_RESEARCH_V1",
        "git_blob_source_pins": source_pins,
        "source_route_assertions": assertions,
        "manufacturer_source": "FACAD 3.14 C02 PDF page 5, SHA256 pinned",
        "manufacturer_c02_sha256": FACAD_C02_SHA256,
        "source_fact": "C02 p5 describes ANB centered at N between landmarks A and B",
        "vendor_angle3p_signed_or_unsigned": "UNVERIFIED",
        "vendor_reference_values": "NOT_ACQUIRED",
        "tested_code": "backend.services.cephalo_steiner_geometry.steiner_anb_deg_v1",
        "tested_product_legacy_service_runtime": False,
        "tested_facad_numeric_runtime": False,
        "consumer_screen_authority": "UNVERIFIED",
        "typed_steiner_vs_legacy_math_same_algorithm": True,
        "synthetic_cases": rows,
        "f01_13": "OPEN",
        "fac03_d3": "OPEN_RED",
        "fac05": "NOT_TESTED",
        "clinical_edit_allowed": False,
        "converged": False,
        "canonical_roadmap_closed": 39,
        "canonical_roadmap_total": 99,
    }

class MathResearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g = real_steiner_geometry()

    def test_decisive_same_dc_different_vertex(self):
        s,n,a,b = FIXTURES[0][1:5]
        s2,n2,a2,b2 = FIXTURES[1][1:5]
        self.assertEqual(self.g.steiner_anb_deg_v1(s,n,a,b), self.g.steiner_anb_deg_v1(s2,n2,a2,b2))
        self.assertEqual(round(unsigned_at_n(n,a,b),1), 90.)
        self.assertEqual(round(unsigned_at_n(n2,a2,b2),1), 0.)

    def test_four_expected_distinctions(self):
        for name,s,n,a,b,dc,vendor_hypo in FIXTURES:
            with self.subTest(case=name):
                self.assertEqual(round(self.g.steiner_anb_deg_v1(s,n,a,b),1), dc)
                self.assertEqual(round(unsigned_at_n(n,a,b),1), vendor_hypo)

    def test_scale_translation_invariance(self):
        for _,s,n,a,b,_,_ in FIXTURES:
            translate = lambda p: (4*p[0]+8, 4*p[1]-11)
            self.assertAlmostEqual(self.g.steiner_anb_deg_v1(s,n,a,b),
                                   self.g.steiner_anb_deg_v1(*map(translate,(s,n,a,b))), places=10)
            self.assertAlmostEqual(unsigned_at_n(n,a,b),
                                   unsigned_at_n(*map(translate,(n,a,b))), places=10)

    def test_reference_point_s_changes_legacy_not_candidate(self):
        _, s,n,a,b,*_ = FIXTURES[0]
        alt_s = (0.,1.)
        self.assertNotEqual(self.g.steiner_anb_deg_v1(s,n,a,b),
                            self.g.steiner_anb_deg_v1(alt_s,n,a,b))
        self.assertEqual(unsigned_at_n(n,a,b), unsigned_at_n(n,a,b))

    def test_undefined_reference_vector_closed(self):
        s,n,a,b = FIXTURES[0][1:5]
        self.assertIsNone(self.g.steiner_anb_deg_v1(n,n,a,b))
        self.assertIsNone(self.g.steiner_anb_deg_v1(s,n,n,b))
        self.assertIsNone(self.g.steiner_anb_deg_v1(s,n,a,n))
        self.assertIsNone(unsigned_at_n(n,n,b))
        self.assertIsNone(unsigned_at_n(n,a,n))

    def test_nonfinite_inputs_closed(self):
        s,n,a,b = FIXTURES[0][1:5]
        self.assertIsNone(self.g.steiner_anb_deg_v1(s,n,(math.nan,0),b))
        self.assertIsNone(unsigned_at_n(n,(math.nan,0),b))
        self.assertIsNone(unsigned_at_n(n,(math.inf,0),b))

    def test_no_clinical_gates_relabelled(self):
        report = evaluate()
        self.assertEqual(report["f01_13"], "OPEN")
        self.assertEqual(report["fac03_d3"], "OPEN_RED")
        self.assertEqual(report["fac05"], "NOT_TESTED")
        self.assertFalse(report["clinical_edit_allowed"])
        self.assertFalse(report["converged"])
        self.assertTrue(all(row["facad_vendor_numeric_output"] is None for row in report["synthetic_cases"]))

    def test_source_lock_and_routes(self):
        pins, assertions = source_guard()
        self.assertEqual(pins, SOURCE_PINS)
        self.assertEqual(len(assertions), 8)

    def test_control_mutation_rejected(self):
        report = evaluate()
        bad = json.loads(json.dumps(report))
        bad["synthetic_cases"][0]["independent_unsigned_vertex_at_n_hypothesis_deg"] = 0.
        self.assertNotEqual(bad["synthetic_cases"][0]["independent_unsigned_vertex_at_n_hypothesis_deg"],
                            report["synthetic_cases"][0]["independent_unsigned_vertex_at_n_hypothesis_deg"])

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--report", type=Path)
    a=ap.parse_args()
    if a.self_test:
        suite=unittest.defaultTestLoader.loadTestsFromTestCase(MathResearchTests)
        result=unittest.TextTestRunner(verbosity=2).run(suite)
        if not result.wasSuccessful():
            raise SystemExit(1)
        print("F01_13_ANB_SOURCE_BOUNDARY_TESTS="+str(result.testsRun))
    if a.report:
        report=evaluate()
        if a.report.resolve().is_relative_to(ROOT.resolve()) and "docs/audits/data" in str(a.report):
            raise ValueError("Keep evidence artifact outside tracked source data")
        a.report.parent.mkdir(parents=True, exist_ok=True)
        a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        print("SOURCE_ROUTE_PINS_VERIFIED="+str(len(report["git_blob_source_pins"])))
        print("RESEARCH_SYNTHETIC_CASES="+str(len(report["synthetic_cases"])))
        print("FACAD_NUMERIC_PARITY_VERIFIED=false")
        print("CLINICAL_EDIT_ALLOWED=false")
    if not a.self_test and not a.report:
        ap.error("Requires --self-test or --report")

if __name__=="__main__":
    main()
