"""LOT05/J11D synthetic-only taxonomy, integrity, privacy tests."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

p=Path(__file__).with_name("lot05_j11d_fdi_anomaly_autotriage.py")
spec=importlib.util.spec_from_file_location("j11d_test",p)
assert spec and spec.loader
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

U,L=(.42,.62)

class TestAutotriage(unittest.TestCase):
    def test_exact_duplicate(self):
        box=(.31,.43,.05,.17)
        self.assertEqual(m.kind([box,box],(U,L)),"exact_same_coordinates")
    def test_same_region_high_overlap(self):
        box=(.31,.43,.05,.17)
        other=(.312,.432,.05,.17)
        self.assertEqual(m.kind([box,other],(U,L)),"strongly_overlapping_boxes")
    def test_wrong_arch(self):
        self.assertEqual(m.kind([(.53,.62,.02,.15),(.57,.43,.03,.13)],(U,L)),
                         "cross_arch_suspected")
    def test_lateral_split(self):
        self.assertEqual(m.kind([(.27,.62,.05,.15),(.73,.62,.05,.15)],(U,L)),
                         "widely_separated_lateral")
    def test_nearby_distinct(self):
        self.assertEqual(m.kind([(.57,.61,.03,.18),(.62,.615,.03,.18)],(U,L)),
                         "nearby_distinct_boxes")
    def test_nearest_class_context_does_not_force_relabel(self):
        group={17:[(.54,.62,.02,.14),(.57,.43,.03,.13)],
               10:[(.56,.43,.03,.13)],11:[(.59,.43,.03,.13)],
               16:[(.51,.62,.02,.15)],12:[(.62,.45,.03,.16)],
               7:[(.26,.42,.06,.13)]}
        result=m.analyze(group)
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]["kind"],"cross_arch_suspected")
        self.assertEqual(result[0]["wrong_arch_boxes_candidate"],1)
        self.assertGreaterEqual(result[0]["overlaps_other_existing_class_boxes"],1)
    def test_unknown_context_fails_closed(self):
        with self.assertRaises(m.PretriageError):
            m.medians({0:[(.25,.45,.06,.18)],17:[(.55,.46,.02,.15)]})
    def test_no_real_input_does_not_pass(self):
        with tempfile.TemporaryDirectory() as path:
            with self.assertRaises(m.PretriageError):
                m.triage(Path(path))
    def test_cli_failure_reports_no_names_or_coordinates(self):
        with tempfile.TemporaryDirectory() as path:
            r=subprocess.run([sys.executable,str(p),"--labels-dir",path],
                             capture_output=True,text=True)
            self.assertEqual(r.returncode,1)
            self.assertEqual(json.loads(r.stdout),
                             {"schema":m.SCHEMA,"status":"FAIL_CLOSED"})
            self.assertEqual(r.stderr,"")

if __name__=="__main__":
    unittest.main()
