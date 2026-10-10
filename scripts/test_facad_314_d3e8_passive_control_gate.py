"""D3E8 synthetic bounded no-SACL control tests. No Facad startup."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent

def mod(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj

gate = mod("d3e8_module", "facad_314_d3e8_passive_control_gate.py")
d3e7_tests = mod("d3e7_tests_ref", "test_facad_314_d3e7_preflight_gate.py")
H = d3e7_tests.H


class D3E8Tests(unittest.TestCase):
    def setUp(self):
        f = d3e7_tests.PreflightTests(methodName="test_no_change_at_prelaunch")
        f.setUp()
        self.args = f.inputs + [f.preflight, f.go()]
        self.control = {
            "schema": "facad314_d3e8_passive_control_local_v1",
            "source": "EPHEMERAL_SIZE_ONLY_PASSIVE_SACL_CONTROL",
            "session_id": "test-001",
            "selected_scope": d3e7_tests.SCOPE,
            "checkpoints": [
                {"stage": stage, "entries": {H("a"): 1, H("b"): 2}}
                for stage in gate.CONTROL_STAGES
            ],
            "passive_control_seconds": 2,
            "post_sacl_rest_seconds": 2,
            "shared_app_storage_isolation_verified": False,
            "clinical_edit_allowed": False,
        }

    def go(self):
        return gate.classify(*self.args, self.control)

    def invalid(self):
        with self.assertRaises(gate.InvalidControl):
            self.go()

    def set_prelaunch(self, size):
        self.args[6]["entries"][H("b")] = size
        d3e6 = d3e7_tests.d3e6_fixture.d3e6
        self.args[7] = d3e6.classify(*self.args[:7])
        self.args[9] = d3e7_tests.gate.classify(*self.args[:9])

    def test_no_change_before_launch_not_clearance(self):
        result = self.go()
        self.assertEqual(result["control_interval_counts"]["not_divergent_before_launch"], 1)
        self.assertFalse(result["shared_app_storage_isolation_verified"])
        self.assertFalse(result["sacl_caused_content_write_proven"])

    def test_before_control_already_diverged(self):
        self.args[8]["checkpoints"][1]["entries"][H("b")] = 3
        self.set_prelaunch(3)
        self.assertEqual(self.go()["control_interval_counts"]["already_divergent_before_passive_control"], 1)

    def test_idle_control_first_observed(self):
        self.control["checkpoints"][0]["entries"][H("b")] = 3
        self.set_prelaunch(3)
        self.assertEqual(self.go()["control_interval_counts"]["first_observed_during_passive_no_sacl_control"], 1)

    def test_sacl_bracket_first_observed(self):
        self.args[8]["checkpoints"][2]["entries"][H("b")] = 3
        self.set_prelaunch(3)
        self.assertEqual(self.go()["control_interval_counts"]["first_observed_between_control_and_post_sacl"], 1)

    def test_rest_after_sacl_first_observed(self):
        self.control["checkpoints"][1]["entries"][H("b")] = 3
        self.set_prelaunch(3)
        self.assertEqual(self.go()["control_interval_counts"]["first_observed_during_post_sacl_rest"], 1)

    def test_late_change_first_observed(self):
        self.set_prelaunch(3)
        self.assertEqual(self.go()["control_interval_counts"]["first_observed_after_post_sacl_rest_before_launch"], 1)

    def test_missing_control_identity_keeps_unknown(self):
        del self.control["checkpoints"][0]["entries"][H("b")]
        self.assertEqual(self.go()["control_interval_counts"]["missing_intermediate_identity"], 1)

    def test_stage_swap_rejected(self):
        self.control["checkpoints"].reverse()
        self.invalid()

    def test_private_name_rejected(self):
        self.control["checkpoints"][0]["entries"]["raw_filename"] = 2
        self.invalid()

    def test_size_bool_and_negative_rejected(self):
        for n in (True, -1, "5"):
            self.control["checkpoints"][0]["entries"][H("b")] = n
            with self.subTest(n=n):
                self.invalid()

    def test_forged_control_flags_rejected(self):
        for flag in ("clinical_edit_allowed", "shared_app_storage_isolation_verified"):
            self.control[flag] = True
            self.invalid()
            self.control[flag] = False

    def test_forged_control_duration_rejected(self):
        for n in (0, 2.0, True, 3):
            self.control["passive_control_seconds"] = n
            with self.subTest(n=n):
                self.invalid()

    def test_unexpected_file_metadata_rejected(self):
        self.control["path"] = "private"
        self.invalid()

    def test_cross_gate_forgery_rejected(self):
        self.args[9]["sacl_caused_content_write_proven"] = True
        self.invalid()

    def test_wrong_session_rejected(self):
        self.control["session_id"] = "invalid"
        self.invalid()

    def test_no_unattributed_target_not_isolation(self):
        fixture = d3e7_tests.PreflightTests(methodName="test_no_change_at_prelaunch")
        fixture.setUp()
        before, after, events, timeline, e4, e5, prelaunch, e6 = fixture.inputs
        tests6 = d3e7_tests.d3e6_fixture
        events = tests6.fixtures.evidence(root=[H("a"), H("b")])
        e4 = tests6.d3e4.classify(before, after, events)
        e5 = tests6.d3e5.classify(before, after, events, timeline, e4)
        e6 = tests6.d3e6.classify(before, after, events, timeline, e4, e5, prelaunch)
        e7 = d3e7_tests.gate.classify(before, after, events, timeline, e4, e5, prelaunch, e6, fixture.preflight)
        self.args = [before, after, events, timeline, e4, e5, prelaunch, e6, fixture.preflight, e7]
        output = self.go()
        self.assertEqual(output["unattributed_modified_size_changed_count"], 0)
        self.assertFalse(output["clinical_edit_allowed"])

    def test_cli_exports_aggregate_only(self):
        with tempfile.TemporaryDirectory() as folder:
            parent = Path(folder)
            names = ("before", "after", "event-keys", "timeline", "classification", "timing",
                     "prelaunch", "early-window", "preflight", "preflight-aggregate", "control")
            args = []
            for name, entry in zip(names, self.args + [self.control]):
                path = parent / (name + ".json")
                path.write_text(json.dumps(entry), encoding="utf8")
                args.extend(["--" + name, str(path)])
            out = parent / "public.json"
            p = subprocess.run(
                [sys.executable, str(HERE / "facad_314_d3e8_passive_control_gate.py"),
                 *args, "--output", str(out)], capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
            safe = out.read_text()
            self.assertNotIn(H("b"), safe)
            self.assertNotIn("test-001", safe)
            self.assertNotIn('"size":', safe)
            self.assertIn("UNVERIFIED", p.stdout)

    def test_cli_missing_private_input_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            missing = Path(folder) / "missing"
            p = [sys.executable, str(HERE / "facad_314_d3e8_passive_control_gate.py")]
            for name in ("before", "after", "event-keys", "timeline", "classification",
                         "timing", "prelaunch", "early-window", "preflight",
                         "preflight-aggregate", "control", "output"):
                p.extend(["--" + name, str(missing)])
            done = subprocess.run(p, capture_output=True, text=True)
            self.assertEqual(done.returncode, 2)
            self.assertFalse(missing.exists())
            self.assertNotIn("Traceback", done.stderr)


if __name__ == "__main__":
    unittest.main()
