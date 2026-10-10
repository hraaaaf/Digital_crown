"""FAC-03 D3E.11 source-only negative tests. Never opens an Ilexis file."""
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
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gate = load("d3e11", "facad_314_d3e11_observation_gate.py")
d3e9_fixture = load("d3e9_fixture", "test_facad_314_d3e9_arm_gate.py")


def observation(arm="sacl_1"):
    return {
        "schema": "facad314_d3e11_fsw_sacl_aggregate_v1",
        "source": "NATIVE_CHANGE_NOTIFICATION_AND_FILE_AUDIT_RULE_METADATA_ONLY",
        "arm": arm,
        "changed_size_file_count": 1,
        "filesystem_watcher_started": True,
        "filesystem_watcher_error_reported": False,
        "filesystem_watcher_received_event_count": 2,
        "changed_size_files_with_notification_count": 1,
        "file_sacl_checked_changed_file_count": 1,
        "file_sacl_unchecked_changed_file_count": 0,
        "changed_files_with_current_sid_write_audit_count": 1,
        "changed_files_with_inherited_current_sid_write_audit_count": 1,
        "file_content_read": False,
        "file_identifiers_or_paths_or_sizes_exported": False,
        "notification_delivery_complete_proven": False,
        "writer_pid_proven": False,
        "change_caused_by_set_acl_proven": False,
        "shared_app_storage_isolation_verified": False,
        "clinical_edit_allowed": False,
        "verdict": "FSW_SACL_COVERAGE_OBSERVATION_NOT_CAUSALITY",
    }


class ObsTest(unittest.TestCase):
    def setUp(self):
        self.arm = "sacl_1"
        self.prior = d3e9_fixture.sample()
        self.obs = observation()

    def go(self):
        return gate.validate(self.prior, self.obs, self.arm)

    def bad(self):
        with self.assertRaises(gate.InvalidD3E11):
            self.go()

    def test_valid_result_not_causality(self):
        x = self.go()
        self.assertEqual(x["changed_size_file_count"], 1)
        self.assertFalse(x["writer_pid_proven"])

    def test_no_notification_does_not_clear_writer(self):
        self.obs["filesystem_watcher_received_event_count"] = 0
        self.obs["changed_size_files_with_notification_count"] = 0
        self.assertFalse(self.go()["notification_delivery_complete_proven"])

    def test_watcher_error_makes_match_unknown(self):
        self.obs["filesystem_watcher_error_reported"] = True
        self.bad()
        self.obs["changed_size_files_with_notification_count"] = 0
        self.assertFalse(self.go()["notification_delivery_complete_proven"])

    def test_ace_not_inherited_does_not_claim_it(self):
        self.obs["changed_files_with_inherited_current_sid_write_audit_count"] = 0
        self.assertEqual(self.go()["changed_files_with_inherited_current_sid_write_audit_count"], 0)

    def test_missing_sacl_coverage_does_not_clear(self):
        self.obs["changed_files_with_current_sid_write_audit_count"] = 0
        self.obs["changed_files_with_inherited_current_sid_write_audit_count"] = 0
        self.assertFalse(self.go()["clinical_edit_allowed"])

    def test_sacl_acl_read_failure_not_silent_success(self):
        self.obs["file_sacl_checked_changed_file_count"] = 0
        self.obs["file_sacl_unchecked_changed_file_count"] = 1
        self.obs["changed_files_with_current_sid_write_audit_count"] = 0
        self.obs["changed_files_with_inherited_current_sid_write_audit_count"] = 0
        self.assertEqual(self.go()["sacl_unchecked_changed_file_count"], 1)

    def test_sacl_inspection_missing_count_rejected(self):
        self.obs["file_sacl_unchecked_changed_file_count"] = 1
        self.bad()

    def test_audited_more_than_checked_rejected(self):
        self.obs["changed_files_with_current_sid_write_audit_count"] = 2
        self.bad()

    def test_inherited_more_than_audited_rejected(self):
        self.obs["changed_files_with_inherited_current_sid_write_audit_count"] = 2
        self.bad()

    def test_notification_more_than_changed_rejected(self):
        self.obs["changed_size_files_with_notification_count"] = 2
        self.bad()

    def test_notification_more_than_events_rejected(self):
        self.obs["filesystem_watcher_received_event_count"] = 0
        self.bad()

    def test_no_drift_remains_closed(self):
        self.prior["changed_size_count"] = 0
        self.obs["changed_size_file_count"] = 0
        self.obs["changed_size_files_with_notification_count"] = 0
        self.obs["file_sacl_checked_changed_file_count"] = 0
        self.obs["changed_files_with_current_sid_write_audit_count"] = 0
        self.obs["changed_files_with_inherited_current_sid_write_audit_count"] = 0
        self.assertFalse(self.go()["shared_app_storage_isolation_verified"])

    def test_other_arm_requires_both_matching(self):
        self.obs["arm"] = "passive_1"
        self.bad()

    def test_forged_source(self):
        self.obs["source"] = "FAKE"
        self.bad()

    def test_forged_schema(self):
        self.obs["schema"] = "fake"
        self.bad()

    def test_extra_pii_field_rejected(self):
        self.obs["patient_identifier"] = "pii"
        self.bad()

    def test_extra_path_rejected(self):
        self.obs["file_path"] = "private"
        self.bad()

    def test_extra_filename_hash_rejected(self):
        self.obs["file_hash"] = "deadbeef"
        self.bad()

    def test_false_watcher_started_rejected(self):
        self.obs["filesystem_watcher_started"] = False
        self.bad()

    def test_boolean_as_count_rejected(self):
        self.obs["filesystem_watcher_received_event_count"] = True
        self.bad()

    def test_negative_counts_rejected(self):
        for field in ("changed_size_file_count", "file_sacl_unchecked_changed_file_count",
                      "changed_size_files_with_notification_count"):
            with self.subTest(field=field):
                self.obs[field] = -1
                self.bad()
                self.obs = observation()

    def test_over_cap_count_rejected(self):
        self.obs["filesystem_watcher_received_event_count"] = 5001
        self.bad()

    def test_forged_unsafe_claim_rejected(self):
        for key in ("file_content_read", "file_identifiers_or_paths_or_sizes_exported",
                    "notification_delivery_complete_proven", "writer_pid_proven",
                    "change_caused_by_set_acl_proven", "shared_app_storage_isolation_verified",
                    "clinical_edit_allowed"):
            with self.subTest(key=key):
                self.obs[key] = True
                self.bad()
                self.obs[key] = False

    def test_prior_forgery_rejected(self):
        self.prior["matched_counterfactual_proven"] = True
        self.bad()

    def test_cli_export_aggregate_only(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            a = folder / "a.json"; b = folder / "b.json"; c = folder / "c.json"
            a.write_text(json.dumps(self.prior), encoding="utf8")
            b.write_text(json.dumps(self.obs), encoding="utf8")
            proc = subprocess.run([sys.executable, str(HERE / "facad_314_d3e11_observation_gate.py"),
                "--d3e9-arm", str(a), "--d3e11-evidence", str(b), "--arm", self.arm,
                "--output", str(c)], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stdout+proc.stderr)
            result = json.loads(c.read_text())
            self.assertNotIn("file_path", result)
            self.assertFalse(result["writer_pid_proven"])

    def test_cli_missing_input_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder)/"missing"
            p = subprocess.run([sys.executable, str(HERE / "facad_314_d3e11_observation_gate.py"),
                "--d3e9-arm", str(source), "--d3e11-evidence", str(source),
                "--output", str(Path(folder)/"out"), "--arm", self.arm],
                capture_output=True, text=True)
            self.assertEqual(p.returncode, 2)
            self.assertIn("CLINICAL_EDIT_ALLOWED=false", p.stdout)
            self.assertNotIn("Traceback", p.stderr)


if __name__ == "__main__":
    unittest.main()
