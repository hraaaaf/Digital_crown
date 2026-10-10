"""D3E16 two internal adversarial perspectives on read-only policy visibility."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "d3e16", HERE / "facad_314_d3e16_readonly_policy_diagnostic_gate.py"
)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def sample():
    return {
        "schema": "facad314_d3e16_user_auditpol_presence_diagnostic_v1",
        "source": "EPHEMERAL_RUNNER_CURRENT_SID_READ_ONLY",
        "previous_get_user_unavailable_observed": True,
        "get_user_sid_syntax": "braced_current_sid",
        "policy_list_users_verbose_csv_query_result": "zero",
        "current_sid_in_policy_listing": "not_seen_in_successful_listing",
        "current_sid_subcategory_get_result": "nonzero",
        "current_sid_category_all_get_result": "nonzero",
        "used_only_current_sid_for_get_queries": True,
        "raw_user_policy_inventory_kept_in_memory_only": True,
        "auditpol_system_policy_modified": False,
        "auditpol_per_user_policy_modified": False,
        "user_accounts_or_sid_exported": False,
        "auditpol_stdout_stderr_exported": False,
        "security_events_or_files_read": False,
        "registry_or_clinical_resources_read": False,
        "global_kernel_file_etw_used": False,
        "file_scoped_policy_proven": False,
        "user_policy_configurable_proven": False,
        "actual_ilexis_writer_proven": False,
        "shared_app_storage_isolation_verified": False,
        "clinical_edit_allowed": False,
        "verdict": "PER_USER_POLICY_READONLY_DIAGNOSTIC_NOT_CAPTURE_AUTHORIZATION",
    }


class A_PrivacyAndOperationTests(unittest.TestCase):
    def setUp(self):
        self.x = sample()

    def rejects(self):
        with self.assertRaises(gate.InvalidD3E16):
            gate.validate(self.x)

    def test_baseline_valid_without_clinical_claims(self):
        result = gate.validate(self.x)
        self.assertFalse(result["clinical_edit_allowed"])
        self.assertFalse(result["missing_per_user_policy_definitively_proven"])

    def test_no_user_accounts_or_sid_export(self):
        self.x["user_accounts_or_sid_exported"] = True
        self.rejects()

    def test_no_auditpol_output_export(self):
        self.x["auditpol_stdout_stderr_exported"] = True
        self.rejects()

    def test_no_global_mutation(self):
        self.x["auditpol_system_policy_modified"] = True
        self.rejects()

    def test_no_user_mutation(self):
        self.x["auditpol_per_user_policy_modified"] = True
        self.rejects()

    def test_no_security_event_read(self):
        self.x["security_events_or_files_read"] = True
        self.rejects()

    def test_no_registry_or_clinical_resources(self):
        self.x["registry_or_clinical_resources_read"] = True
        self.rejects()

    def test_no_kernel_etw(self):
        self.x["global_kernel_file_etw_used"] = True
        self.rejects()

    def test_full_inventory_stays_in_ram(self):
        self.x["raw_user_policy_inventory_kept_in_memory_only"] = False
        self.rejects()

    def test_current_sid_only(self):
        self.x["used_only_current_sid_for_get_queries"] = False
        self.rejects()

    def test_extra_pid_rejected(self):
        self.x["pid"] = "private"
        self.rejects()

    def test_extra_username_rejected(self):
        self.x["account_name"] = "private"
        self.rejects()

    def test_extra_sid_rejected(self):
        self.x["runner_sid"] = "private"
        self.rejects()

    def test_other_target_account_source_rejected(self):
        self.x["source"] = "ALL_USERS_PUBLIC"
        self.rejects()

    def test_invalid_boolean_type_rejected(self):
        self.x["auditpol_per_user_policy_modified"] = 0
        self.rejects()

    def test_privilege_not_inferred(self):
        result = gate.validate(self.x)
        self.assertFalse(result["user_policy_configurable_proven"])


class B_ProofAndCounterfactualTests(unittest.TestCase):
    def setUp(self):
        self.x = sample()

    def rejects(self):
        with self.assertRaises(gate.InvalidD3E16):
            gate.validate(self.x)

    def test_no_entry_seen_does_not_mean_unconfigurable(self):
        result = gate.validate(self.x)
        self.assertTrue(result["no_explicit_current_user_entry_seen_in_successful_listing"])
        self.assertFalse(result["missing_per_user_policy_definitively_proven"])

    def test_current_sid_present_is_not_writer_proof(self):
        self.x["current_sid_in_policy_listing"] = "exact_current_sid_seen"
        self.assertFalse(gate.validate(self.x)["real_ilexis_writer_proven"])

    def test_category_zero_subcategory_nonzero_is_inconclusive(self):
        self.x["current_sid_category_all_get_result"] = "zero"
        self.assertFalse(gate.validate(self.x)["user_policy_configurable_proven"])

    def test_category_and_subcategory_zero_not_clinical(self):
        self.x["current_sid_category_all_get_result"] = "zero"
        self.x["current_sid_subcategory_get_result"] = "zero"
        self.assertFalse(gate.validate(self.x)["clinical_edit_allowed"])

    def test_listing_query_unavailable_requires_undetermined(self):
        self.x["policy_list_users_verbose_csv_query_result"] = "unavailable"
        self.rejects()

    def test_nonzero_listing_needs_undetermined(self):
        self.x["policy_list_users_verbose_csv_query_result"] = "nonzero"
        self.x["current_sid_in_policy_listing"] = "undetermined"
        self.assertFalse(gate.validate(self.x)["user_policy_configurable_proven"])

    def test_zero_listing_requires_exact_comparison(self):
        self.x["current_sid_in_policy_listing"] = "undetermined"
        self.rejects()

    def test_listing_nonzero_cannot_claim_seen(self):
        self.x["policy_list_users_verbose_csv_query_result"] = "nonzero"
        self.x["current_sid_in_policy_listing"] = "exact_current_sid_seen"
        self.rejects()

    def test_unknown_listing_match_rejected(self):
        self.x["current_sid_in_policy_listing"] = "policy_disabled"
        self.rejects()

    def test_unknown_query_outcome_rejected(self):
        self.x["current_sid_subcategory_get_result"] = "no_user"
        self.rejects()

    def test_wrong_sid_syntax_rejected(self):
        self.x["get_user_sid_syntax"] = "all_sid"
        self.rejects()

    def test_previous_evidence_required(self):
        self.x["previous_get_user_unavailable_observed"] = False
        self.rejects()

    def test_live_ilexis_claim_rejected(self):
        self.x["actual_ilexis_writer_proven"] = True
        self.rejects()

    def test_isolation_forgery_rejected(self):
        self.x["shared_app_storage_isolation_verified"] = True
        self.rejects()

    def test_clinical_clearance_forgery_rejected(self):
        self.x["clinical_edit_allowed"] = True
        self.rejects()

    def test_cannot_forge_scoped_policy(self):
        self.x["file_scoped_policy_proven"] = True
        self.rejects()

    def test_cannot_forge_policy_configurable(self):
        self.x["user_policy_configurable_proven"] = True
        self.rejects()

    def test_schema_forgery_rejected(self):
        self.x["schema"] = "D3_GREEN"
        self.rejects()

    def test_checked_result_has_no_user_identity(self):
        text = json.dumps(gate.validate(self.x))
        self.assertNotIn("user_sid", text)
        self.assertNotIn("account_name", text)
        self.assertNotIn("pid", text)

    def test_cli_valid(self):
        with tempfile.TemporaryDirectory() as root:
            inp = Path(root) / "input.json"
            out = Path(root) / "checked.json"
            inp.write_text(json.dumps(self.x), encoding="utf8")
            p = subprocess.run([
                sys.executable, str(HERE / "facad_314_d3e16_readonly_policy_diagnostic_gate.py"),
                "--input", str(inp), "--output", str(out)],
                text=True, capture_output=True)
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
            self.assertFalse(json.loads(out.read_text())["clinical_edit_allowed"])

    def test_cli_missing_fails_closed(self):
        with tempfile.TemporaryDirectory() as root:
            p = subprocess.run([
                sys.executable, str(HERE / "facad_314_d3e16_readonly_policy_diagnostic_gate.py"),
                "--input", str(Path(root) / "missing"),
                "--output", str(Path(root) / "out")],
                text=True, capture_output=True)
            self.assertEqual(p.returncode, 2)
            self.assertIn("CLINICAL_EDIT_ALLOWED=false", p.stdout)
            self.assertNotIn("Traceback", p.stderr)


if __name__ == "__main__":
    unittest.main()
