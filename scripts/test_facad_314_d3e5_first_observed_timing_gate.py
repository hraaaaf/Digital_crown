"""Synthetic D3E5 timing contract tests; never launches Facad."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).parent
def mod(name, file):
    spec = importlib.util.spec_from_file_location(name, HERE / file)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj
timing = mod("d3e5_under_test", "facad_314_d3e5_first_observed_timing_gate.py")
d3e4 = mod("d3e4_fixtures", "facad_314_d3e4_unattributed_classification_gate.py")
fixtures = mod("d3e4_test_fixtures", "test_facad_314_d3e4_unattributed_classification_gate.py")
H, SCOPE = fixtures.H, fixtures.SCOPE
def checkpoint(stage, size):
    return {"stage": stage, "entries": {H("a"): 4, H("b"): size, H("c"): 1}}
class FirstDivergenceTests(unittest.TestCase):
    def setUp(self):
        self.before = fixtures.shot("before", {H("a"): fixtures.ent(1), H("b"): fixtures.ent(2)})
        self.after = fixtures.shot("after", {H("a"): fixtures.ent(4), H("b"): fixtures.ent(3), H("c"): fixtures.ent(1)})
        self.events = fixtures.evidence(root=[H("a")])
        self.classification = d3e4.classify(self.before, self.after, self.events)
        self.timeline = {
            "schema": "facad314_d3e5_timeline_local_v1",
            "source": "EPHEMERAL_ILEXIS_METADATA_ONLY",
            "session_id": "test-001",
            "selected_scope": SCOPE,
            "checkpoints": [checkpoint(stage, 2) for stage in timing.STAGES],
            "shared_app_storage_isolation_verified": False,
            "clinical_edit_allowed": False,
        }
    def go(self):
        return timing.classify(self.before, self.after, self.events, self.timeline, self.classification)
    def invalid(self):
        with self.assertRaises(timing.InvalidTiming):
            self.go()
    def test_after_post_stop_first_detected(self):
        o = self.go()
        self.assertEqual(o["first_observed_size_divergence"]["first_observed_after_post_stop"], 1)
        self.assertFalse(o["causality_proven"])
        self.assertFalse(o["continuous_change_tracking"])
    def test_at_first_post_launch_checkpoint(self):
        self.timeline["checkpoints"][0]["entries"][H("b")] = 3
        self.assertEqual(self.go()["first_observed_size_divergence"]["first_observed_by_post_launch"], 1)
    def test_before_stop_while_running(self):
        self.timeline["checkpoints"][1]["entries"][H("b")] = 3
        self.assertEqual(self.go()["first_observed_size_divergence"]["first_observed_while_root_running"], 1)
    def test_shutdown_interval(self):
        self.timeline["checkpoints"][2]["entries"][H("b")] = 3
        self.assertEqual(self.go()["first_observed_size_divergence"]["first_observed_during_stop_interval"], 1)
    def test_missing_midpoint_is_inconclusive(self):
        del self.timeline["checkpoints"][0]["entries"][H("b")]
        o = self.go()
        self.assertEqual(o["first_observed_size_divergence"]["intermediate_identity_missing"], 1)
    def test_no_size_target_is_never_clearance(self):
        self.events = fixtures.evidence(root=[H("a"), H("b")])
        self.classification = d3e4.classify(self.before, self.after, self.events)
        o = self.go()
        self.assertEqual(o["unattributed_modified_size_changed_count"], 0)
        self.assertFalse(o["shared_app_storage_isolation_verified"])
    def test_wrong_session(self):
        self.timeline["session_id"] = "other"
        self.invalid()
    def test_wrong_stage_order(self):
        self.timeline["checkpoints"].reverse()
        self.invalid()
    def test_bad_identity_or_size(self):
        self.timeline["checkpoints"][0]["entries"]["raw-name"] = 4
        self.invalid()
        del self.timeline["checkpoints"][0]["entries"]["raw-name"]
        self.timeline["checkpoints"][0]["entries"][H("b")] = True
        self.invalid()
    def test_forged_flags(self):
        for flag in ("shared_app_storage_isolation_verified", "clinical_edit_allowed"):
            self.timeline[flag] = True
            with self.subTest(flag=flag):
                self.invalid()
            self.timeline[flag] = False
    def test_mismatch_final_classification(self):
        self.classification["unexplained_modified_size_changed_count"] = 999
        self.invalid()
    def test_extra_leaking_field_rejected(self):
        self.timeline["name"] = "sensitive"
        self.invalid()
    def test_cli_no_pseudonymous_identity_export(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            sources = (self.before, self.after, self.events, self.timeline, self.classification)
            names = ("before", "after", "event-keys", "timeline", "classification")
            args = []
            for name, source in zip(names, sources):
                f = base / (name + ".json")
                f.write_text(json.dumps(source), encoding="utf8")
                args.extend(["--" + name, str(f)])
            out = base / "aggregate.json"
            result = subprocess.run([sys.executable, str(HERE / "facad_314_d3e5_first_observed_timing_gate.py"),
                                     *args, "--output", str(out)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            exported = out.read_text()
            self.assertNotIn(H("b"), exported)
            self.assertNotIn("test-001", exported)
            self.assertNotIn('"size":', exported)
            self.assertIn("UNVERIFIED", result.stdout)


if __name__ == "__main__":
    unittest.main()
