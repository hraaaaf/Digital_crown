"""FAC-03 D3E13: two adversarial lenses on design-only capture readiness."""
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
CONTRACT = ROOT / "docs/audits/FACAD_314_D3E13_CAPTURE_READINESS_CONTRACT.json"
spec = importlib.util.spec_from_file_location(
    "d3e13_gate", HERE / "facad_314_d3e13_capture_readiness_gate.py"
)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def fixture():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


class A_PrivacyAndScopeTests(unittest.TestCase):
    def setUp(self):
        self.x = fixture()

    def reject(self):
        with self.assertRaises(gate.InvalidReadiness):
            gate.validate(self.x)

    def test_baseline_never_authorizes_capture(self):
        result = gate.validate(self.x)
        self.assertFalse(result["capture_authorized"])
        self.assertFalse(result["clinical_edit_allowed"])

    def test_unrelated_etw_system_events_must_be_acknowledged(self):
        self.x["kernel_etw_captures_unrelated_system_activity"] = False
        self.reject()

    def test_raw_trace_sensitive_paths_must_be_acknowledged(self):
        self.x["raw_traces_may_contain_sensitive_file_paths"] = False
        self.reject()

    def test_requirement_ephemeral_only(self):
        self.x["requirement_runner_is_ephemeral_and_nonclinical"] = False
        self.reject()

    def test_official_nonclinical_demo_only(self):
        self.x["authorized_subject"] = "REAL_PATIENT"
        self.reject()

    def test_no_private_paths_or_pids_export(self):
        self.x["requirement_never_export_paths_pids_hashes_precise_timestamps"] = False
        self.reject()

    def test_no_patient_load_save(self):
        self.x["requirement_no_patient_load_save_or_license_profile_inspection"] = False
        self.reject()

    def test_cleanup_before_artifacts(self):
        self.x["requirement_terminate_trace_and_delete_raw_before_upload"] = False
        self.reject()

    def test_no_raw_output(self):
        self.x["requirement_aggregate_only_public_output"] = False
        self.reject()

    def test_matching_private_only(self):
        self.x["requirement_private_in_memory_correlation_only"] = False
        self.reject()

    def test_no_silent_loss(self):
        self.x["requirement_fail_closed_on_lost_events_or_cleanup_errors"] = False
        self.reject()

    def test_extra_patient_identifier_rejected(self):
        self.x["patient_id"] = "private"
        self.reject()

    def test_extra_private_etl_path_rejected(self):
        self.x["etl_path"] = "private"
        self.reject()

    def test_never_export_raw_event_xml(self):
        self.x["raw_event_xml"] = "secret"
        self.reject()

    def test_invalid_type_not_coerced(self):
        self.x["clinical_edit_allowed"] = 0
        self.reject()

    def test_user_data_is_not_returned(self):
        out = gate.validate(self.x)
        for name in ("event_path", "pid", "filename", "file_hash", "raw_trace"):
            self.assertNotIn(name, out)

    def test_trailing_unknown_keys_rejected(self):
        self.x["debug"] = True
        self.reject()

    def test_cli_fails_closed_on_wrong_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "bad.json"
            self.x["schema"] = "not-a-design-contract"
            source.write_text(json.dumps(self.x), encoding="utf-8")
            p = subprocess.run(
                [sys.executable, str(HERE / "facad_314_d3e13_capture_readiness_gate.py"),
                 "--contract", str(source)],
                text=True, capture_output=True,
            )
            self.assertEqual(p.returncode, 2)
            self.assertIn("CLINICAL_EDIT_ALLOWED=false", p.stdout)
            self.assertNotIn("private", p.stdout)


class B_EvidenceAndAuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.x = fixture()

    def reject(self):
        with self.assertRaises(gate.InvalidReadiness):
            gate.validate(self.x)

    def test_synthetic_run_not_live_writer(self):
        out = gate.validate(self.x)
        self.assertEqual(out["based_on_synthetic_windows_run"], 38079398064)
        self.assertFalse(out["real_quickdemo_etw_trial_performed"])

    def test_cannot_replace_sha(self):
        self.x["validated_synthetic_commit"] = "f" * 40
        self.reject()

    def test_cannot_replace_run_id(self):
        self.x["validated_synthetic_windows_run"] = 42
        self.reject()

    def test_cannot_claim_independent_privacy_review(self):
        self.x["independent_privacy_review_complete"] = True
        self.reject()

    def test_cannot_claim_independent_evidence_review(self):
        self.x["independent_evidence_review_complete"] = True
        self.reject()

    def test_cannot_claim_live_quickdemo_executed(self):
        self.x["real_quickdemo_etw_trial_performed"] = True
        self.reject()

    def test_cannot_authorize_collector(self):
        self.x["live_capture_authorized"] = True
        self.reject()

    def test_cannot_claim_capture_script_exists(self):
        self.x["actual_capture_script_implemented"] = True
        self.reject()

    def test_cannot_claim_writer(self):
        self.x["writer_causality_proven"] = True
        self.reject()

    def test_cannot_claim_complete_event_delivery(self):
        self.x["complete_event_delivery_proven"] = True
        self.reject()

    def test_cannot_claim_isolated_storage(self):
        self.x["shared_app_storage_isolation_verified"] = True
        self.reject()

    def test_cannot_claim_clinical_edit(self):
        self.x["clinical_edit_allowed"] = True
        self.reject()

    def test_cannot_change_etw_provider(self):
        self.x["kernel_etw_provider"] = "Other"
        self.reject()

    def test_cannot_increase_trace_volume(self):
        self.x["planned_max_etl_megabytes"] = 1024
        self.reject()

    def test_cannot_expand_bounded_duration(self):
        self.x["planned_max_capture_seconds"] = 600
        self.reject()

    def test_cannot_silently_reduce_arms(self):
        self.x["planned_independent_arms"] = 1
        self.reject()

    def test_cannot_expand_event_limit(self):
        self.x["planned_max_event_records"] = 1000000
        self.reject()

    def test_cannot_change_keyword_mask(self):
        self.x["kernel_etw_keyword_mask"] = "0x2B0"
        self.reject()

    def test_cannot_turn_into_execution_mode(self):
        self.x["phase"] = "LIVE_CAPTURE"
        self.reject()

    def test_no_approval_by_verdict_forgery(self):
        self.x["verdict"] = "D3_GREEN"
        self.reject()

    def test_source_repo_guard_checks_normal_workflows(self):
        self.assertTrue(gate.check_repository(ROOT))

    def test_source_repo_guard_rejects_accidental_native_wiring(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workflows = root / ".github/workflows"
            workflows.mkdir(parents=True)
            (workflows / "facad-314-d3-snapshot-validator.yml").write_text("safe")
            (workflows / "facad-314-d3e12-etw-feasibility.yml").write_text(
                "D3E12_REAL_ILEXIS_TRACE_CAPTURED=false")
            (workflows / "unsafe.yml").write_text(gate.NATIVE_CAPTURE_MARKER)
            with self.assertRaises(gate.InvalidReadiness):
                gate.check_repository(root)

    def test_source_repo_guard_requires_synthetic_claim(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workflows = root / ".github/workflows"
            workflows.mkdir(parents=True)
            (workflows / "facad-314-d3-snapshot-validator.yml").write_text("safe")
            (workflows / "facad-314-d3e12-etw-feasibility.yml").write_text("wrong")
            with self.assertRaises(gate.InvalidReadiness):
                gate.check_repository(root)

    def test_cli_baseline_reports_blocked_capture(self):
        p = subprocess.run(
            [sys.executable, str(HERE / "facad_314_d3e13_capture_readiness_gate.py"),
             "--contract", str(CONTRACT), "--repo-root", str(ROOT)],
            capture_output=True, text=True,
        )
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("D3E13_CAPTURE_AUTHORIZED=false", p.stdout)
        self.assertIn("FAC03_D3=OPEN_RED", p.stdout)
        self.assertIn("CLINICAL_EDIT_ALLOWED=false", p.stdout)


if __name__ == "__main__":
    unittest.main()
