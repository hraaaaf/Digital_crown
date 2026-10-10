"""D3E.10 adversarial synthetic safety tests. No clinical access, no Windows runner."""
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
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

gate = load("d3e10", "facad_314_d3e10_provenance_gate.py")
fixture = load("d3e9_fixture", "test_facad_314_d3e9_arm_gate.py")


def evidence(arm="sacl_1"):
    return {
        "schema": "facad314_d3e10_prelaunch_metadata_audit_v1",
        "source": "EPHEMERAL_D3E9_ARM_SIZE_TIMESTAMP_AND_4663_MATCH_AGGREGATE",
        "arm": arm,
        "changed_size_count": 1,
        "changed_size_and_last_write_timestamp_count": 1,
        "changed_size_without_timestamp_change_count": 0,
        "unchanged_size_changed_timestamp_count": 0,
        "security_4663_query_attempted": True,
        "security_4663_records_available": False,
        "security_4663_query_outcome": "query_error",
        "matching_write_data_or_append_access_event_count": 0,
        "same_powershell_pid_matching_file_count": 0,
        "other_pid_matching_file_count": 0,
        "process_identity_exported": False,
        "file_identity_or_size_or_timestamp_exported": False,
        "file_content_read": False,
        "full_event_delivery_proven": False,
        "file_write_causality_proven": False,
        "clinical_edit_allowed": False,
        "shared_app_storage_isolation_verified": False,
        "verdict": "METADATA_4663_BOUNDED_NOT_WRITER_CAUSALITY",
    }


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.arm = "sacl_1"
        self.source = fixture.sample(self.arm)
        self.meta = evidence(self.arm)

    def go(self):
        return gate.validate(self.source, self.meta, self.arm)

    def bad(self):
        with self.assertRaises(gate.InvalidD3E10):
            self.go()

    def test_valid_metadata_remains_not_causal(self):
        output = self.go()
        self.assertEqual(output["size_and_timestamp_changed_count"], 1)
        self.assertFalse(output["writer_causality_proven"])

    def test_size_change_without_timestamp_change_is_observable(self):
        self.meta["changed_size_and_last_write_timestamp_count"] = 0
        self.meta["changed_size_without_timestamp_change_count"] = 1
        self.assertEqual(self.go()["size_changed_timestamp_unchanged_count"], 1)

    def test_same_size_timestamp_change_is_only_metadata(self):
        self.meta["unchanged_size_changed_timestamp_count"] = 1
        self.assertEqual(self.go()["same_size_timestamp_changed_count"], 1)

    def test_no_drift_does_not_clear_clinical_edit(self):
        self.source["changed_size_count"] = 0
        self.meta["changed_size_count"] = 0
        self.meta["changed_size_and_last_write_timestamp_count"] = 0
        self.assertFalse(self.go()["clinical_edit_allowed"])

    def test_no_audit_events_never_proves_absence(self):
        self.assertFalse(self.go()["audit_event_records_available"])
        self.assertFalse(self.go()["writer_causality_proven"])

    def test_empty_query_is_distinct_from_inaccessible(self):
        self.meta["security_4663_query_outcome"] = "no_matching_events"
        self.assertEqual(self.go()["audit_query_outcome"], "no_matching_events")
        self.assertFalse(self.go()["writer_causality_proven"])

    def test_query_error_is_not_misreported_as_empty(self):
        self.assertEqual(self.go()["audit_query_outcome"], "query_error")

    def test_invalid_event_remains_fail_closed(self):
        self.meta["security_4663_query_outcome"] = "invalid_event"
        self.assertFalse(self.go()["audit_event_records_available"])

    def test_forged_query_outcome_rejected(self):
        self.meta["security_4663_query_outcome"] = "not_attempted"
        self.bad()

    def test_inconsistent_available_flag_rejected(self):
        self.meta["security_4663_query_outcome"] = "no_matching_events"
        self.meta["security_4663_records_available"] = True
        self.bad()

    def test_own_process_write_use_does_not_prove_writer(self):
        self.meta["security_4663_records_available"] = True
        self.meta["security_4663_query_outcome"] = "records_returned"
        self.meta["matching_write_data_or_append_access_event_count"] = 1
        self.meta["same_powershell_pid_matching_file_count"] = 1
        self.assertFalse(self.go()["writer_causality_proven"])

    def test_other_pid_write_use_does_not_prove_writer(self):
        self.meta["security_4663_records_available"] = True
        self.meta["security_4663_query_outcome"] = "records_returned"
        self.meta["matching_write_data_or_append_access_event_count"] = 1
        self.meta["other_pid_matching_file_count"] = 1
        self.assertFalse(self.go()["writer_causality_proven"])

    def test_wrong_source_arm(self):
        self.source["arm"] = "passive_1"
        self.bad()

    def test_wrong_metadata_arm(self):
        self.meta["arm"] = "passive_2"
        self.bad()

    def test_extra_raw_filename(self):
        self.meta["filename"] = "private"
        self.bad()

    def test_extra_hash(self):
        self.meta["hashes"] = ["a"*64]
        self.bad()

    def test_extra_process_pid(self):
        self.meta["process_pid"] = 123
        self.bad()

    def test_extra_timestamp_field(self):
        self.meta["mtime_ticks"] = 900000
        self.bad()

    def test_bogus_positive_when_events_unavailable(self):
        self.meta["matching_write_data_or_append_access_event_count"] = 1
        self.bad()

    def test_own_and_other_file_counts_cannot_exceed_size_targets(self):
        self.meta["security_4663_records_available"] = True
        self.meta["security_4663_query_outcome"] = "records_returned"
        self.meta["matching_write_data_or_append_access_event_count"] = 20
        self.meta["other_pid_matching_file_count"] = 2
        self.bad()

    def test_forced_true_claims(self):
        for field in ("process_identity_exported", "file_identity_or_size_or_timestamp_exported",
                      "file_content_read", "full_event_delivery_proven", "file_write_causality_proven",
                      "clinical_edit_allowed", "shared_app_storage_isolation_verified"):
            with self.subTest(field=field):
                self.meta[field] = True
                self.bad()
                self.meta[field] = False

    def test_bad_counts(self):
        for key in ("changed_size_count", "changed_size_and_last_write_timestamp_count",
                    "changed_size_without_timestamp_change_count", "unchanged_size_changed_timestamp_count",
                    "matching_write_data_or_append_access_event_count"):
            for value in (-1, True, 4001, "1"):
                with self.subTest(key=key, value=value):
                    self.meta[key] = value
                    self.bad()
                    self.meta = evidence()

    def test_missing_event_query_attempt(self):
        self.meta["security_4663_query_attempted"] = False
        self.bad()

    def test_timestamps_not_reconciled(self):
        self.meta["changed_size_and_last_write_timestamp_count"] = 0
        self.bad()

    def test_cli_aggregates_only(self):
        with tempfile.TemporaryDirectory() as d:
            a, b, c = (Path(d)/name for name in ("arm.json", "meta.json", "out.json"))
            a.write_text(json.dumps(self.source), encoding="utf8")
            b.write_text(json.dumps(self.meta), encoding="utf8")
            result = subprocess.run([sys.executable, str(HERE/"facad_314_d3e10_provenance_gate.py"),
                "--d3e9-arm", str(a), "--d3e10-evidence", str(b), "--arm", self.arm,
                "--output", str(c)], text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
            self.assertNotIn("filename", c.read_text())
            self.assertFalse(json.loads(c.read_text())["clinical_edit_allowed"])

    def test_cli_missing_input_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            cmd = [sys.executable, str(HERE/"facad_314_d3e10_provenance_gate.py"),
                   "--d3e9-arm", str(Path(d)/"missing"), "--d3e10-evidence", str(Path(d)/"missing"),
                   "--arm", self.arm, "--output", str(Path(d)/"out")]
            p = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(p.returncode, 2)
            self.assertNotIn("Traceback", p.stderr)


if __name__ == "__main__":
    unittest.main()
