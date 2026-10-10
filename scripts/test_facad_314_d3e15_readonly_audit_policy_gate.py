"""D3E.15 adversarial read-only per-user policy evidence tests."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "d3e15", ROOT / "facad_314_d3e15_readonly_audit_policy_gate.py"
)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def sample():
    return {
        "schema": "facad314_d3e15_readonly_per_user_policy_v1",
        "source": "CURRENT_EPHEMERAL_WINDOWS_RUNNER_READ_ONLY",
        "file_system_audit_subcategory": "FILE_SYSTEM",
        "auditpol_system_query_succeeded": True,
        "auditpol_user_query_succeeded": True,
        "system_success_audit_status": "success_not_configured",
        "per_user_inclusion_success_audit_status": "success_not_configured",
        "runner_admin_membership_check_succeeded": True,
        "runner_is_local_administrator": True,
        "global_policy_modified": False,
        "per_user_policy_modified": False,
        "security_events_queried": False,
        "global_kernel_etw_capture_used": False,
        "synthetic_or_clinical_files_touched": False,
        "raw_auditpol_output_exported": False,
        "sid_or_username_exported": False,
        "private_paths_or_process_ids_exported": False,
        "per_user_audit_is_exclusive_to_one_file_proven": False,
        "real_ilexis_writer_proven": False,
        "shared_app_storage_isolation_verified": False,
        "clinical_edit_allowed": False,
        "verdict": "READ_ONLY_PER_USER_AUDIT_POLICY_OBSERVATION_NOT_CAPTURE_AUTHORIZATION",
    }


class A_PrivacyAndMutationSafetyTests(unittest.TestCase):
    def setUp(self):
        self.x = sample()

    def bad(self):
        with self.assertRaises(gate.InvalidD3E15):
            gate.validate(self.x)

    def test_baseline_not_authorization(self):
        out = gate.validate(self.x)
        self.assertFalse(out["capture_authorized"])
        self.assertFalse(out["clinical_edit_allowed"])

    def test_no_export_sid(self):
        self.x["sid_or_username_exported"] = True
        self.bad()

    def test_no_raw_csv_export(self):
        self.x["raw_auditpol_output_exported"] = True
        self.bad()

    def test_no_pid_or_path_export(self):
        self.x["private_paths_or_process_ids_exported"] = True
        self.bad()

    def test_no_system_policy_mutation(self):
        self.x["global_policy_modified"] = True
        self.bad()

    def test_no_user_policy_mutation(self):
        self.x["per_user_policy_modified"] = True
        self.bad()

    def test_no_etw(self):
        self.x["global_kernel_etw_capture_used"] = True
        self.bad()

    def test_no_security_event_access(self):
        self.x["security_events_queried"] = True
        self.bad()

    def test_no_file_access(self):
        self.x["synthetic_or_clinical_files_touched"] = True
        self.bad()

    def test_no_ilexis_claim(self):
        self.x["real_ilexis_writer_proven"] = True
        self.bad()

    def test_no_shared_storage_claim(self):
        self.x["shared_app_storage_isolation_verified"] = True
        self.bad()

    def test_no_clinical_edits(self):
        self.x["clinical_edit_allowed"] = True
        self.bad()

    def test_no_false_file_scope(self):
        self.x["per_user_audit_is_exclusive_to_one_file_proven"] = True
        self.bad()

    def test_extra_user_sid_rejected(self):
        self.x["user_sid"] = "S-1-private"
        self.bad()

    def test_extra_account_name_rejected(self):
        self.x["runner_username"] = "private"
        self.bad()

    def test_wrong_provenance_rejected(self):
        self.x["source"] = "REAL_PATIENT"
        self.bad()

    def test_unknown_field_rejected(self):
        self.x["raw_auditpol_row"] = "private"
        self.bad()

    def test_bool_type_strict(self):
        self.x["global_policy_modified"] = 0
        self.bad()


class B_EvidenceAndCounterfactualTests(unittest.TestCase):
    def setUp(self):
        self.x = sample()

    def bad(self):
        with self.assertRaises(gate.InvalidD3E15):
            gate.validate(self.x)

    def test_per_user_success_configured_not_capture_go(self):
        self.x["per_user_inclusion_success_audit_status"] = "success_configured"
        self.assertFalse(gate.validate(self.x)["capture_authorized"])

    def test_both_success_configured_not_ilexis_go(self):
        self.x["per_user_inclusion_success_audit_status"] = "success_configured"
        self.x["system_success_audit_status"] = "success_configured"
        self.assertFalse(gate.validate(self.x)["real_ilexis_writer_proven"])

    def test_policy_disabled_not_no_writer(self):
        self.assertFalse(gate.validate(self.x)["shared_app_storage_isolation_verified"])

    def test_user_query_unavailable_is_allowed_inconclusive(self):
        self.x["auditpol_user_query_succeeded"] = False
        self.x["per_user_inclusion_success_audit_status"] = "unavailable"
        self.assertFalse(gate.validate(self.x)["capture_authorized"])

    def test_query_error_with_fake_state_rejected(self):
        self.x["auditpol_user_query_succeeded"] = False
        self.bad()

    def test_system_query_unavailable_requires_unknown(self):
        self.x["auditpol_system_query_succeeded"] = False
        self.bad()

    def test_unavailable_system_query_is_inconclusive(self):
        self.x["auditpol_system_query_succeeded"] = False
        self.x["system_success_audit_status"] = "unavailable"
        self.assertFalse(gate.validate(self.x)["capture_authorized"])

    def test_query_success_cannot_be_unavailable(self):
        self.x["system_success_audit_status"] = "unavailable"
        self.bad()

    def test_parsing_unknown_kept_inconclusive(self):
        self.x["per_user_inclusion_success_audit_status"] = "parse_error"
        self.assertFalse(gate.validate(self.x)["capture_authorized"])

    def test_query_undetermined_not_no_policy_claim(self):
        self.x["per_user_inclusion_success_audit_status"] = "undetermined"
        self.assertFalse(gate.validate(self.x)["capture_authorized"])

    def test_unknown_status_rejected(self):
        self.x["per_user_inclusion_success_audit_status"] = "all_safe"
        self.bad()

    def test_principal_membership_check_required(self):
        self.x["runner_admin_membership_check_succeeded"] = False
        self.bad()

    def test_non_admin_supported_without_clearance(self):
        self.x["runner_is_local_administrator"] = False
        self.assertFalse(gate.validate(self.x)["capture_authorized"])

    def test_schema_forgery_rejected(self):
        self.x["schema"] = "CLINICAL_CLEARANCE"
        self.bad()

    def test_file_system_guid_scope_constant(self):
        self.x["file_system_audit_subcategory"] = "ALL_OBJECT_ACCESS"
        self.bad()

    def test_no_events_generated_by_policy_query(self):
        self.assertFalse(gate.validate(self.x)["security_events_queried"])

    def test_only_safe_aggregate_output(self):
        out = gate.validate(self.x)
        self.assertEqual(out["verdict"], "READONLY_POLICY_INFO_NOT_A_CAPTURE_OR_ISOLATION_PROOF")
        self.assertNotIn("SID", json.dumps(out))
        self.assertNotIn("path", out)

    def test_cli_success_with_safe_json(self):
        with tempfile.TemporaryDirectory() as d:
            inp = Path(d) / "input.json"
            out = Path(d) / "output.json"
            inp.write_text(json.dumps(self.x), encoding="utf-8")
            p = subprocess.run([
                sys.executable, str(ROOT / "facad_314_d3e15_readonly_audit_policy_gate.py"),
                "--input", str(inp), "--output", str(out)
            ], capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr + p.stdout)
            self.assertFalse(json.loads(out.read_text())["capture_authorized"])
            self.assertIn("CLINICAL_EDIT_ALLOWED=false", p.stdout)

    def test_cli_missing_input_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            p = subprocess.run([
                sys.executable, str(ROOT / "facad_314_d3e15_readonly_audit_policy_gate.py"),
                "--input", str(Path(d) / "missing"),
                "--output", str(Path(d) / "output")
            ], capture_output=True, text=True)
            self.assertEqual(p.returncode, 2)
            self.assertIn("CLINICAL_EDIT_ALLOWED=false", p.stdout)
            self.assertNotIn("Traceback", p.stderr)


if __name__ == "__main__":
    unittest.main()
