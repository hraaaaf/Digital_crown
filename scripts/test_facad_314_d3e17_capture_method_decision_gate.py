"""Adversarial perspectives A/B for D3E17 review-only contract."""
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CONTRACT = ROOT / "docs/audits/FACAD_314_D3E17_CAPTURE_METHOD_DECISION.json"
spec = importlib.util.spec_from_file_location(
    "d3e17", HERE / "facad_314_d3e17_capture_method_decision_gate.py"
)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def sample():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


class A_PrivacyAndUnauthorizedCaptureTests(unittest.TestCase):
    def setUp(self):
        self.document = sample()

    def bad(self):
        with self.assertRaises(gate.UnsafeD3E17):
            gate.validate(self.document)

    def test_baseline_clears_no_capture(self):
        x = gate.validate(self.document)
        self.assertFalse(x["capture_ready"])
        self.assertFalse(x["clinical_edit_allowed"])
        self.assertFalse(x["converged"])

    def test_phase_cannot_be_live(self):
        self.document["phase"] = "LIVE_CAPTURE"
        self.bad()

    def test_baseline_sha_cannot_change(self):
        self.document["baseline_sha"] = "ffffffffffffffffffffffffffffffffffffffff"
        self.bad()

    def test_baseline_ci_run_cannot_change(self):
        self.document["baseline_ci_run_id"] = 99
        self.bad()

    def test_baseline_windows_run_cannot_change(self):
        self.document["baseline_windows_readonly_run_id"] = 77
        self.bad()

    def test_recommendation_cannot_authorize_guest(self):
        self.document["recommendation"] = "GUEST_APPROVED"
        self.bad()

    def test_reason_cannot_claim_provenance(self):
        self.document["reason"] = "FILE_WRITER_PROVEN"
        self.bad()

    def test_verdict_cannot_claim_green(self):
        self.document["verdict"] = "D3_GREEN"
        self.bad()

    def test_converged_cannot_be_forged(self):
        self.document["converged"] = True
        self.bad()

    def test_capture_authorized_cannot_be_forged(self):
        self.document["live_capture_authorized"] = True
        self.bad()

    def test_unknown_field_rejected(self):
        self.document["patient_identifier"] = "private"
        self.bad()

    def test_unknown_schema_rejected(self):
        self.document["schema"] = "D3E17_ALLOW_ALL"
        self.bad()
    def test_no_forged_isolated_guest_verified(self):
        self.document["checks"]["isolated_guest_verified"] = True
        self.bad()

    def test_no_forged_host_mounts_absent_verified(self):
        self.document["checks"]["host_mounts_absent_verified"] = True
        self.bad()

    def test_no_forged_production_secrets_absent_verified(self):
        self.document["checks"]["production_secrets_absent_verified"] = True
        self.bad()

    def test_no_forged_official_demo_provenance_verified(self):
        self.document["checks"]["official_demo_provenance_verified"] = True
        self.bad()

    def test_no_forged_source_filters_complete_verified(self):
        self.document["checks"]["source_filters_complete_verified"] = True
        self.bad()

    def test_no_forged_raw_trace_non_export_verified(self):
        self.document["checks"]["raw_trace_non_export_verified"] = True
        self.bad()

    def test_no_forged_cleanup_and_guest_destruction_verified(self):
        self.document["checks"]["cleanup_and_guest_destruction_verified"] = True
        self.bad()

    def test_no_forged_fileobject_pid_correlation_verified_on_quickdemo(self):
        self.document["checks"]["fileobject_pid_correlation_verified_on_quickdemo"] = True
        self.bad()

    def test_no_forged_event_loss_excluded(self):
        self.document["checks"]["event_loss_excluded"] = True
        self.bad()

    def test_no_forged_independent_privacy_review_complete(self):
        self.document["checks"]["independent_privacy_review_complete"] = True
        self.bad()

    def test_no_forged_independent_evidence_review_complete(self):
        self.document["checks"]["independent_evidence_review_complete"] = True
        self.bad()

    def test_no_forged_explicit_experiment_authorization(self):
        self.document["checks"]["explicit_experiment_authorization"] = True
        self.bad()

    def test_no_forged_real_quickdemo_trace_performed(self):
        self.document["checks"]["real_quickdemo_trace_performed"] = True
        self.bad()

    def test_no_forged_real_ilexis_writer_proven(self):
        self.document["checks"]["real_ilexis_writer_proven"] = True
        self.bad()

    def test_no_forged_shared_app_storage_isolation_verified(self):
        self.document["checks"]["shared_app_storage_isolation_verified"] = True
        self.bad()

    def test_no_forged_clinical_edit_allowed(self):
        self.document["checks"]["clinical_edit_allowed"] = True
        self.bad()

    def test_no_forged_merge_or_deployment_authorized(self):
        self.document["checks"]["merge_or_deployment_authorized"] = True
        self.bad()
    def test_method_________________not_capture_authorized(self):
        self.document["methods"][0]["capture_authorized"] = True
        self.bad()

    def test_method________________not_capture_authorized(self):
        self.document["methods"][1]["capture_authorized"] = True
        self.bad()

    def test_method__________________4663_not_capture_authorized(self):
        self.document["methods"][2]["capture_authorized"] = True
        self.bad()

    def test_method___________________not_capture_authorized(self):
        self.document["methods"][3]["capture_authorized"] = True
        self.bad()

    def test_method________not_capture_authorized(self):
        self.document["methods"][4]["capture_authorized"] = True
        self.bad()

    def test_method___________________not_capture_authorized(self):
        self.document["methods"][5]["capture_authorized"] = True
        self.bad()

    def test_method______________not_capture_authorized(self):
        self.document["methods"][6]["capture_authorized"] = True
        self.bad()

    def test_method_____________________not_capture_authorized(self):
        self.document["methods"][7]["capture_authorized"] = True
        self.bad()

    def test_guest_requires_no_shared_storage(self):
        self.document["guest_architecture_requirements"].remove(
            "NO_SHARED_STORAGE_OR_HOST_CLINICAL_MOUNTS")
        self.bad()

    def test_guest_requires_independent_review(self):
        self.document["guest_architecture_requirements"].remove(
            "TWO_REAL_INDEPENDENT_REVIEWS_ON_SAME_HEAD")
        self.bad()

    def test_guest_requires_no_secret_mounts(self):
        self.document["guest_architecture_requirements"].remove(
            "NO_ACCOUNT_CONNECTORS_OR_PRODUCTION_SECRETS")
        self.bad()

    def test_guest_requires_raw_trace_nonexport(self):
        self.document["guest_architecture_requirements"].remove(
            "NO_GUEST_TO_HOST_EXPORT_OF_RAW_EVENTS")
        self.bad()

    def test_guest_requires_cleanup_verification(self):
        self.document["guest_architecture_requirements"].remove(
            "TRACE_STOP_CLEANUP_GUEST_DESTRUCTION_VERIFIED")
        self.bad()

    def test_guest_requirements_must_be_strings(self):
        self.document["guest_architecture_requirements"][0] = True
        self.bad()

    def test_guest_requirements_duplicate_rejected(self):
        self.document["guest_architecture_requirements"][1] = (
            self.document["guest_architecture_requirements"][0])
        self.bad()

    def test_external_pid_filter_is_not_kernel_proof(self):
        self.document["methods"][1]["writer_pid_proof"] = "KERNEL_FILTER_VERIFIED"
        self.bad()

    def test_minifilter_signed_kernel_risk_cannot_be_erased(self):
        self.document["methods"][5]["risk"] = "NO_RISK"
        self.bad()

    def test_sysmon_filter_is_not_capture_confinement(self):
        self.document["methods"][4]["scope"] = "SINGLE_FILE_CONFIRMED"
        self.bad()

    def test_filesystemwatcher_does_not_produce_pid(self):
        self.document["methods"][3]["writer_pid_proof"] = "PID_KNOWN"
        self.bad()

    def test_unknown_method_rejected(self):
        self.document["methods"].append(self.document["methods"][0].copy())
        self.bad()

    def test_removed_method_rejected(self):
        self.document["methods"].pop()
        self.bad()

    def test_method_fields_cannot_export_patient_info(self):
        self.document["methods"][0]["patient_file"] = "private"
        self.bad()

    def test_workflow_guard_checks_repo(self):
        self.assertTrue(gate.verify_repo_design_only(ROOT))

    def test_workflow_guard_rejects_native_capture_marker(self):
        with tempfile.TemporaryDirectory() as folder:
            d = Path(folder)
            workflows = d / ".github" / "workflows"
            workflows.mkdir(parents=True)
            (workflows / "facad-314-d3-snapshot-validator.yml").write_text(
                "source only", encoding="utf-8")
            (workflows / "unsafe.yml").write_text(
                "D3E17_REAL_CAPTURE_ENABLED", encoding="utf-8")
            with self.assertRaises(gate.UnsafeD3E17):
                gate.verify_repo_design_only(d)


class B_EvidenceAndDecisionTests(unittest.TestCase):
    def test_current_proof_not_overstated(self):
        decision = gate.validate(sample())
        self.assertEqual(decision["alternatives_reviewed_count"], 8)
        self.assertFalse(decision["writer_proven"])
        self.assertFalse(decision["shared_app_storage_isolation_verified"])
        self.assertEqual(decision["recommended_next"],
                         "ISOLATED_GUEST_SECURITY_REVIEW_ONLY")

    def test_not_a_live_windows_capture(self):
        decision = gate.validate(sample())
        self.assertFalse(decision["live_capture_performed"])
        self.assertFalse(decision["independent_privacy_review_complete"])

    def test_cli_approves_design_only(self):
        with tempfile.TemporaryDirectory() as folder:
            p = subprocess.run([
                sys.executable, str(HERE / "facad_314_d3e17_capture_method_decision_gate.py"),
                "--contract", str(CONTRACT), "--repo-root", str(ROOT)
            ], capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
            self.assertIn("D3E17_CAPTURE_AUTHORIZED=false", p.stdout)
            self.assertIn("FAC03_D3=OPEN_RED", p.stdout)

    def test_cli_tampered_file_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            document = sample()
            document["live_capture_authorized"] = True
            path = Path(folder) / "bad.json"
            path.write_text(json.dumps(document), encoding="utf8")
            p = subprocess.run([
                sys.executable, str(HERE / "facad_314_d3e17_capture_method_decision_gate.py"),
                "--contract", str(path)
            ], capture_output=True, text=True)
            self.assertEqual(p.returncode, 2)
            self.assertIn("CLINICAL_EDIT_ALLOWED=false", p.stdout)

    def test_cli_missing_input_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            p = subprocess.run([
                sys.executable, str(HERE / "facad_314_d3e17_capture_method_decision_gate.py"),
                "--contract", str(Path(folder) / "missing")
            ], capture_output=True, text=True)
            self.assertEqual(p.returncode, 2)
            self.assertNotIn("Traceback", p.stderr)

    def test_baseline_evidence_exact(self):
        x = gate.validate(sample())
        self.assertEqual(
            x["baseline_sha"],
            "eb9f2c2bd316ef85ff91e76759f293e869fec655"
        )


if __name__ == "__main__":
    unittest.main()
