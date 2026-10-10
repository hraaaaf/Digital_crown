"""D3E7 adversarial synthetic pre-flight timing tests; never launches Facad."""
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
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


gate = mod("d3e7_under_test", "facad_314_d3e7_preflight_gate.py")
d3e6_fixture = mod("d3e6_fixture", "test_facad_314_d3e6_early_window_gate.py")
H = d3e6_fixture.H
SCOPE = d3e6_fixture.SCOPE


class PreflightTests(unittest.TestCase):
    def setUp(self):
        f = d3e6_fixture.EarlyWindowTests(methodName="test_postlaunch_change_bounded_not_attributed")
        f.setUp()
        self.inputs = [
                           f.before, f.after, f.events, f.timeline, f.d3e4_aggregate,
                           f.d3e5_aggregate, f.prelaunch,
                           d3e6_fixture.d3e6.classify(f.before, f.after, f.events, f.timeline,
                                                     f.d3e4_aggregate, f.d3e5_aggregate, f.prelaunch)]
        self.preflight = {
            "schema": "facad314_d3e7_preflight_local_v1",
            "source": "EPHEMERAL_SIZE_ONLY_OBSERVER_AUDIT_SACL_STAGES",
            "session_id": "test-001",
            "selected_scope": SCOPE,
            "checkpoints": [
                {"stage": stage, "entries": {H("a"): 1, H("b"): 2}}
                for stage in gate.STAGES
            ],
            "shared_app_storage_isolation_verified": False,
            "clinical_edit_allowed": False,
        }

    def go(self):
        return gate.classify(*self.inputs, self.preflight)

    def invalid(self):
        with self.assertRaises(gate.InvalidPreflight):
            self.go()

    def test_rest_of_prelaunch_phase(self):
        self.inputs[6]["entries"][H("b")] = 3
        self.inputs[7] = d3e6_fixture.d3e6.classify(*self.inputs[:7])
        result = self.go()
        self.assertEqual(result["preflight_counts"]["first_observed_after_sacl_before_process_launch"], 1)
        self.assertFalse(result["audit_policy_or_sacl_causality_proven"])

    def test_first_observed_at_observer_entry(self):
        self.preflight["checkpoints"][0]["entries"][H("b")] = 3
        self.inputs[6]["entries"][H("b")] = 3
        self.inputs[7] = d3e6_fixture.d3e6.classify(*self.inputs[:7])
        self.assertEqual(self.go()["preflight_counts"]["already_divergent_at_observer_entry"], 1)

    def test_during_audit_policy_preparation(self):
        self.preflight["checkpoints"][1]["entries"][H("b")] = 3
        self.inputs[6]["entries"][H("b")] = 3
        self.inputs[7] = d3e6_fixture.d3e6.classify(*self.inputs[:7])
        self.assertEqual(self.go()["preflight_counts"]["first_observed_during_audit_preparation"], 1)

    def test_during_sacl_application(self):
        self.preflight["checkpoints"][2]["entries"][H("b")] = 3
        self.inputs[6]["entries"][H("b")] = 3
        self.inputs[7] = d3e6_fixture.d3e6.classify(*self.inputs[:7])
        self.assertEqual(self.go()["preflight_counts"]["first_observed_during_sacl_application"], 1)

    def test_no_change_at_prelaunch(self):
        self.assertEqual(self.go()["preflight_counts"]["not_yet_divergent_before_process_launch"], 1)

    def test_missing_identity_does_not_guess(self):
        del self.preflight["checkpoints"][1]["entries"][H("b")]
        self.assertEqual(self.go()["preflight_counts"]["missing_preflight_identity"], 1)

    def test_wrong_stage_order(self):
        self.preflight["checkpoints"].reverse()
        self.invalid()

    def test_wrong_session(self):
        self.preflight["session_id"] = "forged"
        self.invalid()

    def test_wrong_source(self):
        self.preflight["source"] = "USER_CONTENT"
        self.invalid()

    def test_inject_raw_filename(self):
        self.preflight["checkpoints"][0]["entries"]["some-raw-file"] = 5
        self.invalid()

    def test_invalid_size(self):
        for value in (-1, True, "5"):
            self.preflight["checkpoints"][0]["entries"][H("b")] = value
            with self.subTest(value=value):
                self.invalid()

    def test_forged_clearance(self):
        for flag in ("clinical_edit_allowed", "shared_app_storage_isolation_verified"):
            self.preflight[flag] = True
            self.invalid()
            self.preflight[flag] = False

    def test_extra_privacy_leakage_field(self):
        self.preflight["pid"] = 123
        self.invalid()

    def test_tampered_d3e6_evidence(self):
        self.inputs[7]["early_window_counts"]["already_divergent_before_root_launch"] = 99
        self.invalid()

    def test_no_target_does_not_clear_isolation(self):
        f = d3e6_fixture.EarlyWindowTests()
        f.setUp()
        f.events = d3e6_fixture.fixtures.evidence(root=[H("a"), H("b")])
        f.d3e4_aggregate = d3e6_fixture.d3e4.classify(f.before, f.after, f.events)
        f.d3e5_aggregate = d3e6_fixture.d3e5.classify(
            f.before, f.after, f.events, f.timeline, f.d3e4_aggregate)
        self.inputs = [f.before, f.after, f.events, f.timeline,
                       f.d3e4_aggregate, f.d3e5_aggregate, f.prelaunch,
                       d3e6_fixture.d3e6.classify(
                           f.before, f.after, f.events, f.timeline,
                           f.d3e4_aggregate, f.d3e5_aggregate, f.prelaunch)]
        self.assertEqual(self.go()["unattributed_modified_size_changed_count"], 0)
        self.assertFalse(self.go()["shared_app_storage_isolation_verified"])

    def test_cli_aggregate_only(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            names = ("before", "after", "event-keys", "timeline",
                     "classification", "timing", "prelaunch", "early-window", "preflight")
            argv = []
            for name, item in zip(names, self.inputs + [self.preflight]):
                file = base / (name + ".json")
                file.write_text(json.dumps(item), encoding="utf-8")
                argv.extend(["--" + name, str(file)])
            target = base / "aggregate.json"
            proc = subprocess.run([sys.executable, str(HERE / "facad_314_d3e7_preflight_gate.py"),
                                   *argv, "--output", str(target)], text=True, capture_output=True)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            raw = target.read_text()
            self.assertNotIn(H("b"), raw)
            self.assertNotIn("test-001", raw)
            self.assertNotIn('"size":', raw)
            self.assertIn("UNVERIFIED", proc.stdout)

    def test_cli_fail_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            missing = Path(folder) / "missing"
            cmd = [sys.executable, str(HERE / "facad_314_d3e7_preflight_gate.py")]
            for name in ("before", "after", "event-keys", "timeline", "classification",
                         "timing", "prelaunch", "early-window", "preflight", "output"):
                cmd.extend(["--" + name, str(missing)])
            p = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(p.returncode, 2)
            self.assertFalse(missing.exists())
            self.assertNotIn("Traceback", p.stderr)


if __name__ == "__main__":
    unittest.main()
