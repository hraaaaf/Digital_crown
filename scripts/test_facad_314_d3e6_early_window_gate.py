"""Synthetic adversarial D3E6 prelaunch window tests. No Facad launch."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


d3e6 = load("d3e6_under_test", "facad_314_d3e6_early_window_gate.py")
d3e5 = load("d3e5_dep_test", "facad_314_d3e5_first_observed_timing_gate.py")
d3e4 = load("d3e4_dep_test", "facad_314_d3e4_unattributed_classification_gate.py")
fixtures = load("d3e4_fixtures_test", "test_facad_314_d3e4_unattributed_classification_gate.py")
H, SCOPE = fixtures.H, fixtures.SCOPE


class EarlyWindowTests(unittest.TestCase):
    def setUp(self):
        self.before = fixtures.shot("before", {H("a"): fixtures.ent(1), H("b"): fixtures.ent(2)})
        self.after = fixtures.shot("after", {H("a"): fixtures.ent(4), H("b"): fixtures.ent(3), H("c"): fixtures.ent(1)})
        self.events = fixtures.evidence(root=[H("a")])
        self.d3e4_aggregate = d3e4.classify(self.before, self.after, self.events)
        self.timeline = {
            "schema": "facad314_d3e5_timeline_local_v1",
            "source": "EPHEMERAL_ILEXIS_METADATA_ONLY",
            "session_id": "test-001",
            "selected_scope": SCOPE,
            "checkpoints": [
                {"stage": stage, "entries": {H("a"): 4, H("b"): (3 if stage == "after_launch" else 3), H("c"): 1}}
                for stage in d3e5.STAGES
            ],
            "shared_app_storage_isolation_verified": False,
            "clinical_edit_allowed": False,
        }
        self.d3e5_aggregate = d3e5.classify(
            self.before, self.after, self.events, self.timeline, self.d3e4_aggregate
        )
        self.prelaunch = {
            "schema": "facad314_d3e6_prelaunch_local_v1",
            "source": "EPHEMERAL_ILEXIS_SIZE_ONLY_BEFORE_FACAD_START",
            "session_id": "test-001",
            "selected_scope": SCOPE,
            "capture_stage": "immediately_before_start_process",
            "entries": {H("a"): 1, H("b"): 2},
            "shared_app_storage_isolation_verified": False,
            "clinical_edit_allowed": False,
        }

    def go(self):
        return d3e6.classify(
            self.before, self.after, self.events, self.timeline,
            self.d3e4_aggregate, self.d3e5_aggregate, self.prelaunch
        )

    def invalid(self):
        with self.assertRaises(d3e6.InvalidEarlyWindow):
            self.go()

    def test_postlaunch_change_bounded_not_attributed(self):
        data = self.go()
        self.assertEqual(data["early_window_counts"]["first_observed_between_prelaunch_and_postlaunch"], 1)
        self.assertFalse(data["root_process_writer_proven"])
        self.assertFalse(data["shared_app_storage_isolation_verified"])

    def test_prelaunch_change_distinguished(self):
        self.prelaunch["entries"][H("b")] = 3
        self.assertEqual(self.go()["early_window_counts"]["already_divergent_before_root_launch"], 1)

    def test_postlaunch_not_yet_divergent(self):
        self.timeline["checkpoints"][0]["entries"][H("b")] = 2
        self.d3e5_aggregate = d3e5.classify(
            self.before, self.after, self.events, self.timeline, self.d3e4_aggregate
        )
        self.assertEqual(self.go()["early_window_counts"]["not_yet_divergent_at_postlaunch"], 1)

    def test_missing_prelaunch_key_is_explicit_unknown(self):
        del self.prelaunch["entries"][H("b")]
        self.assertEqual(self.go()["early_window_counts"]["missing_early_identity"], 1)

    def test_missing_after_launch_key_is_explicit_unknown(self):
        del self.timeline["checkpoints"][0]["entries"][H("b")]
        self.d3e5_aggregate = d3e5.classify(
            self.before, self.after, self.events, self.timeline, self.d3e4_aggregate
        )
        self.assertEqual(self.go()["early_window_counts"]["missing_early_identity"], 1)

    def test_no_unattributed_target_never_proves_isolation(self):
        self.events = fixtures.evidence(root=[H("a"), H("b")])
        self.d3e4_aggregate = d3e4.classify(self.before, self.after, self.events)
        self.d3e5_aggregate = d3e5.classify(
            self.before, self.after, self.events, self.timeline, self.d3e4_aggregate
        )
        result = self.go()
        self.assertEqual(result["unattributed_modified_size_changed_count"], 0)
        self.assertFalse(result["clinical_edit_allowed"])

    def test_mismatched_session_rejected(self):
        self.prelaunch["session_id"] = "other"
        self.invalid()

    def test_wrong_provenance_rejected(self):
        self.prelaunch["capture_stage"] = "after_launch"
        self.invalid()

    def test_suspicious_metadata_key_rejected(self):
        self.prelaunch["entries"]["sensitive-name"] = 17
        self.invalid()

    def test_boolean_or_negative_file_size_rejected(self):
        for value in (True, -1, "1"):
            self.prelaunch["entries"][H("b")] = value
            with self.subTest(value=value):
                self.invalid()

    def test_unexpected_export_field_rejected(self):
        self.prelaunch["raw_path"] = "redacted"
        self.invalid()

    def test_forged_clearance_rejected(self):
        for field in ("clinical_edit_allowed", "shared_app_storage_isolation_verified"):
            self.prelaunch[field] = True
            self.invalid()
            self.prelaunch[field] = False

    def test_d3e5_timing_mismatch_rejected(self):
        self.d3e5_aggregate["causality_proven"] = True
        self.invalid()

    def test_d3e4_classification_mismatch_rejected(self):
        self.d3e4_aggregate["unexplained_modified_size_changed_count"] = 99
        self.invalid()

    def test_cli_emits_counts_only_and_cleans_no_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            names = ("before", "after", "event-keys", "timeline", "classification", "timing", "prelaunch")
            sources = (self.before, self.after, self.events, self.timeline,
                       self.d3e4_aggregate, self.d3e5_aggregate, self.prelaunch)
            argv = []
            for name, value in zip(names, sources):
                path = base / (name + ".json")
                path.write_text(json.dumps(value), encoding="utf8")
                argv.extend(["--" + name, str(path)])
            result_file = base / "safe.json"
            proc = subprocess.run([sys.executable, str(HERE / "facad_314_d3e6_early_window_gate.py"),
                                   *argv, "--output", str(result_file)],
                                  capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            out = result_file.read_text()
            self.assertNotIn(H("a"), out)
            self.assertNotIn(H("b"), out)
            self.assertNotIn("test-001", out)
            self.assertNotIn('"size":', out)
            self.assertIn("UNVERIFIED", proc.stdout)

    def test_cli_fails_closed_without_private_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "out.json"
            proc = subprocess.run([sys.executable, str(HERE / "facad_314_d3e6_early_window_gate.py"),
                                   "--before", str(out), "--after", str(out),
                                   "--event-keys", str(out), "--timeline", str(out),
                                   "--classification", str(out), "--timing", str(out),
                                   "--prelaunch", str(out), "--output", str(out)],
                                  capture_output=True, text=True)
            self.assertEqual(proc.returncode, 2)
            self.assertFalse(out.exists())
            self.assertNotIn("Traceback", proc.stderr)


if __name__ == "__main__":
    unittest.main()
