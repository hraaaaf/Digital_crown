"""D3E9 source-only adversarial checks (never starts Facad or edits ACL)."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("gate", HERE / "facad_314_d3e9_arm_gate.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def sample(arm="sacl_1"):
    return {
        "schema": "facad314_d3e9_independent_arm_v1",
        "source": "BOUNDED_INDEPENDENT_WINDOWS_RUNNER_METADATA_ONLY",
        "arm": arm,
        "intervention": "sacl_applied" if arm.startswith("sacl_") else "passive_no_sacl",
        "pre_intervention_file_count": 3,
        "post_intervention_file_count": 3,
        "changed_size_count": 1,
        "created_count": 0,
        "removed_count": 0,
        "passive_wait_seconds": 2,
        "sacl_restored": True,
        "audit_policy_restored": True,
        "separate_ephemeral_windows_runner": True,
        "facad_root_launched_during_trial": False,
        "raw_file_metadata_exported": False,
        "file_identity_or_path_exported": False,
        "matched_counterfactual_proven": False,
        "writer_causality_proven": False,
        "complete_audit_event_delivery": False,
        "shared_app_storage_isolation_verified": False,
        "clinical_edit_allowed": False,
        "verdict": "BOUNDED_CONTROLLED_ARM_NOT_CAUSALITY",
    }


class ArmTests(unittest.TestCase):
    def setUp(self):
        self.doc = sample()

    def bad(self):
        with self.assertRaises(gate.InvalidD3E9):
            gate.validate(self.doc, self.doc["arm"])

    def test_four_supported_arms(self):
        for arm in sorted(gate.ARMS):
            output = gate.validate(sample(arm), arm)
            self.assertEqual(output["arm"], arm)
            self.assertFalse(output["causality_proven"])

    def test_forged_claims_all_rejected(self):
        for key in ("sacl_restored", "audit_policy_restored", "separate_ephemeral_windows_runner",
                    "facad_root_launched_during_trial", "raw_file_metadata_exported",
                    "file_identity_or_path_exported", "matched_counterfactual_proven",
                    "writer_causality_proven", "complete_audit_event_delivery",
                    "shared_app_storage_isolation_verified", "clinical_edit_allowed"):
            with self.subTest(key=key):
                self.doc[key] = not self.doc[key]
                self.bad()
                self.doc[key] = not self.doc[key]

    def test_no_drift_is_not_isolation(self):
        self.doc["changed_size_count"] = 0
        self.assertFalse(gate.validate(self.doc, "sacl_1")["clinical_edit_allowed"])

    def test_wrong_intervention_rejected(self):
        self.doc["intervention"] = "passive_no_sacl"
        self.bad()

    def test_mismatched_expected_arm_rejected(self):
        with self.assertRaises(gate.InvalidD3E9):
            gate.validate(self.doc, "sacl_2")

    def test_unknown_arm_rejected(self):
        self.doc["arm"] = "clinical"
        self.bad()

    def test_extra_patient_information_rejected(self):
        self.doc["patient_name"] = "not_allowed"
        self.bad()

    def test_file_identity_rejected(self):
        self.doc["relative_hashes"] = ["a" * 64]
        self.bad()

    def test_removed_or_created_count_invalid(self):
        self.doc["created_count"] = 1
        self.bad()

    def test_changed_count_exceeds_total(self):
        self.doc["changed_size_count"] = 4
        self.bad()

    def test_bad_types_rejected(self):
        for key in ("changed_size_count", "pre_intervention_file_count", "post_intervention_file_count",
                    "passive_wait_seconds"):
            for value in (True, -1, "2", 2.0):
                with self.subTest(key=key, value=value):
                    self.doc[key] = value
                    self.bad()
                    self.doc = sample()

    def test_wrong_provenance(self):
        self.doc["source"] = "USER_FILE"
        self.bad()

    def test_bad_verdict(self):
        self.doc["verdict"] = "D3_ISOLATION_PASSED"
        self.bad()

    def test_output_contains_counts_only(self):
        p = gate.validate(self.doc, "sacl_1")
        self.assertEqual(set(p), {"schema", "arm", "intervention", "changed_size_count",
                                  "created_count", "removed_count", "clinical_edit_allowed",
                                  "shared_app_storage_isolation_verified", "causality_proven", "verdict"})

    def test_cli_success(self):
        with tempfile.TemporaryDirectory() as d:
            inp, out = Path(d) / "input.json", Path(d) / "out.json"
            inp.write_text(json.dumps(self.doc), encoding="utf8")
            p = subprocess.run([sys.executable, str(HERE / "facad_314_d3e9_arm_gate.py"),
                                "--input", str(inp), "--output", str(out), "--arm", "sacl_1"],
                               text=True, capture_output=True)
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
            self.assertNotIn("relative_hashes", out.read_text())
            self.assertFalse(json.loads(out.read_text())["causality_proven"])

    def test_cli_missing_evidence_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            p = subprocess.run([sys.executable, str(HERE / "facad_314_d3e9_arm_gate.py"),
                                "--input", str(Path(d) / "missing"), "--output",
                                str(Path(d) / "out"), "--arm", "passive_1"],
                               text=True, capture_output=True)
            self.assertEqual(p.returncode, 2)
            self.assertNotIn("Traceback", p.stderr)


if __name__ == "__main__":
    unittest.main()
