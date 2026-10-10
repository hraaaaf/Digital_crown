"""FAC-03 D3E14 source-only adversarial synthetic SACL/audit gate."""
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "d3e14", HERE / "facad_314_d3e14_sacl_calibration_gate.py"
)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def sample():
    return {
        "schema": "facad314_d3e14_synthetic_object_sacl_v1",
        "source": "SYNTHETIC_FILE_OBJECT_AUDIT_ONLY",
        "audit_policy_queried": True,
        "audit_file_system_success_policy": "success_configured",
        "global_audit_policy_modified": False,
        "object_sacl_applied": True,
        "object_sacl_readback_confirmed": True,
        "synthetic_child_write_verified": True,
        "security_4663_query_outcome": "records_returned",
        "security_4663_query_error": False,
        "security_records_read_count": 6,
        "matching_synthetic_file_write_access_event_count": 1,
        "matching_synthetic_child_pid_access_event_count": 1,
        "matching_unknown_or_other_pid_access_event_count": 0,
        "synthetic_sacl_restored": True,
        "private_synthetic_files_deleted": True,
        "used_global_kernel_etw_capture": False,
        "raw_security_event_exported": False,
        "private_filename_or_pid_exported": False,
        "clinical_or_ilexis_file_touched": False,
        "write_completion_proven": False,
        "real_ilexis_writer_proven": False,
        "shared_app_storage_isolation_verified": False,
        "clinical_edit_allowed": False,
        "verdict": "SYNTHETIC_OBJECT_SCOPED_AUDIT_CALIBRATION_NOT_CLINICAL_CAUSALITY",
    }


class SyntheticSaclAuditTests(unittest.TestCase):
    def setUp(self):
        self.x = sample()

    def go(self):
        return gate.validate(self.x)

    def rejects(self):
        with self.assertRaises(gate.InvalidD3E14):
            self.go()

    def test_success_not_configured_does_not_exonerate_writer(self):
        self.x["audit_file_system_success_policy"] = "success_not_configured"
        self.assertFalse(self.go()["real_ilexis_writer_proven"])

    def test_policy_unknown_does_not_exonerate_writer(self):
        self.x["audit_file_system_success_policy"] = "undetermined"
        self.assertFalse(self.go()["clinical_edit_allowed"])

    def test_illegal_policy_claim_rejected(self):
        self.x["audit_file_system_success_policy"] = "all_files_safe"
        self.rejects()

    def test_claim_configured_without_query_rejected(self):
        self.x["audit_policy_queried"] = False
        self.rejects()

    def test_synthetic_pid_link_is_not_ilexis_causality(self):
        self.assertTrue(self.go()["object_scoped_synthetic_4663_pid_link_observed"])
        self.assertFalse(self.go()["real_ilexis_writer_proven"])

    def test_no_events_stays_unverified(self):
        self.x.update(security_4663_query_outcome="no_matching_events",
                      security_records_read_count=0,
                      matching_synthetic_file_write_access_event_count=0,
                      matching_synthetic_child_pid_access_event_count=0)
        self.assertFalse(self.go()["object_scoped_synthetic_4663_pid_link_observed"])

    def test_query_error_no_events_stays_unverified(self):
        self.x.update(security_4663_query_outcome="query_error",
                      security_4663_query_error=True, security_records_read_count=0,
                      matching_synthetic_file_write_access_event_count=0,
                      matching_synthetic_child_pid_access_event_count=0)
        self.assertFalse(self.go()["object_scoped_synthetic_4663_pid_link_observed"])

    def test_probe_error_without_sacl_is_unverified(self):
        self.x.update(audit_policy_queried=False,
                      audit_file_system_success_policy="undetermined",
                      object_sacl_applied=False,
                      object_sacl_readback_confirmed=False,
                      synthetic_child_write_verified=False,
                      security_4663_query_outcome="probe_error",
                      security_records_read_count=0,
                      matching_synthetic_file_write_access_event_count=0,
                      matching_synthetic_child_pid_access_event_count=0,
                      synthetic_sacl_restored=False)
        self.assertFalse(self.go()["object_scoped_synthetic_4663_pid_link_observed"])

    def test_other_pid_does_not_prove_child(self):
        self.x["matching_synthetic_child_pid_access_event_count"] = 0
        self.x["matching_unknown_or_other_pid_access_event_count"] = 1
        self.assertFalse(self.go()["object_scoped_synthetic_4663_pid_link_observed"])

    def test_sacl_effective_without_events_does_not_clear(self):
        self.x.update(security_4663_query_outcome="no_matching_events",
                      security_records_read_count=0,
                      matching_synthetic_file_write_access_event_count=0,
                      matching_synthetic_child_pid_access_event_count=0)
        self.assertFalse(self.go()["clinical_edit_allowed"])

    def test_gobal_audit_policy_change_rejected(self):
        self.x["global_audit_policy_modified"] = True
        self.rejects()

    def test_kernel_etw_capture_rejected(self):
        self.x["used_global_kernel_etw_capture"] = True
        self.rejects()

    def test_synthetic_only_contract(self):
        self.x["source"] = "REAL_ILEXIS"
        self.rejects()

    def test_clinical_file_claim_rejected(self):
        self.x["clinical_or_ilexis_file_touched"] = True
        self.rejects()

    def test_cleanup_required(self):
        self.x["private_synthetic_files_deleted"] = False
        self.rejects()

    def test_sacl_restoration_required(self):
        self.x["synthetic_sacl_restored"] = False
        self.rejects()

    def test_restoration_without_application_rejected(self):
        self.x["object_sacl_applied"] = False
        self.rejects()

    def test_readback_without_applied_sacl_rejected(self):
        self.x["object_sacl_applied"] = False
        self.x["synthetic_sacl_restored"] = False
        self.rejects()

    def test_child_write_without_sacl_readback_rejected(self):
        self.x["object_sacl_readback_confirmed"] = False
        self.rejects()

    def test_events_without_worker_write_rejected(self):
        self.x["synthetic_child_write_verified"] = False
        self.rejects()

    def test_no_matching_claim_cannot_have_events(self):
        self.x["security_4663_query_outcome"] = "no_matching_events"
        self.rejects()

    def test_query_error_bool_cannot_be_forged(self):
        self.x["security_4663_query_outcome"] = "query_error"
        self.rejects()

    def test_unavailable_query_must_not_claim_records(self):
        self.x["security_4663_query_outcome"] = "invalid_event"
        self.x["security_4663_query_error"] = True
        self.rejects()

    def test_match_count_bound_to_total(self):
        self.x["matching_synthetic_file_write_access_event_count"] = 7
        self.rejects()

    def test_pid_count_bound_to_match(self):
        self.x["matching_synthetic_child_pid_access_event_count"] = 3
        self.rejects()

    def test_pid_partition_exact(self):
        self.x["matching_unknown_or_other_pid_access_event_count"] = 2
        self.rejects()

    def test_boolean_as_count_rejected(self):
        self.x["security_records_read_count"] = True
        self.rejects()

    def test_negative_count_rejected(self):
        self.x["matching_synthetic_file_write_access_event_count"] = -1
        self.rejects()

    def test_excessive_count_rejected(self):
        self.x["security_records_read_count"] = 10001
        self.rejects()

    def test_extra_pid_rejected(self):
        self.x["actual_child_pid"] = 999
        self.rejects()

    def test_extra_filename_rejected(self):
        self.x["filename"] = "private"
        self.rejects()

    def test_extra_raw_event_rejected(self):
        self.x["event_xml"] = "<private>"
        self.rejects()

    def test_raw_security_event_export_forbidden(self):
        self.x["raw_security_event_exported"] = True
        self.rejects()

    def test_individual_identity_export_forbidden(self):
        self.x["private_filename_or_pid_exported"] = True
        self.rejects()

    def test_write_completion_not_claimed(self):
        self.x["write_completion_proven"] = True
        self.rejects()

    def test_real_writer_not_claimed(self):
        self.x["real_ilexis_writer_proven"] = True
        self.rejects()

    def test_shared_isolation_not_claimed(self):
        self.x["shared_app_storage_isolation_verified"] = True
        self.rejects()

    def test_clinical_edit_not_allowed(self):
        self.x["clinical_edit_allowed"] = True
        self.rejects()

    def test_unknown_outcome_rejected(self):
        self.x["security_4663_query_outcome"] = "no_writer"
        self.rejects()

    def test_false_schema_rejected(self):
        self.x["schema"] = "approved"
        self.rejects()

    def test_cli_success_has_only_aggregates(self):
        with tempfile.TemporaryDirectory() as d:
            a = Path(d) / "synthetic.json"
            b = Path(d) / "checked.json"
            a.write_text(json.dumps(self.x), encoding="utf-8")
            p = subprocess.run([sys.executable, str(HERE / "facad_314_d3e14_sacl_calibration_gate.py"),
                                "--input", str(a), "--output", str(b)],
                               capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr + p.stdout)
            result = json.loads(b.read_text())
            self.assertTrue(result["object_scoped_synthetic_4663_pid_link_observed"])
            self.assertFalse(result["clinical_edit_allowed"])
            self.assertNotIn("ProcessId", result)

    def test_cli_bad_input_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            p = subprocess.run([sys.executable, str(HERE / "facad_314_d3e14_sacl_calibration_gate.py"),
                                "--input", str(Path(d) / "missing"),
                                "--output", str(Path(d) / "out")],
                               capture_output=True, text=True)
            self.assertEqual(p.returncode, 2)
            self.assertIn("CLINICAL_EDIT_ALLOWED=false", p.stdout)
            self.assertNotIn("Traceback", p.stderr)


if __name__ == "__main__":
    unittest.main()
