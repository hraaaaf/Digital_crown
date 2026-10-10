"""D3E12 ETW synthetic feasibility: adversarial schema and false-claim tests."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("d3e12", HERE / "facad_314_d3e12_etw_gate.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def sample():
    return {
        "schema": "facad314_d3e12_synthetic_kernel_file_etw_v1",
        "source": "WINDOWS_EPHEMERAL_SYNTHETIC_FILE_ONLY",
        "provider": "Microsoft-Windows-Kernel-File",
        "provider_discovered": True,
        "trace_started": True,
        "trace_stopped": True,
        "synthetic_write_verified": True,
        "etl_query_status": "events_returned",
        "etl_decoder": "direct_etl",
        "etl_file_present": True,
        "etl_file_nonempty": True,
        "direct_etl_read_status": "events_returned",
        "tracerpt_attempted": False,
        "tracerpt_exit_zero": False,
        "tracerpt_output_file_present": False,
        "tracerpt_output_file_nonempty": False,
        "tracerpt_evtx_read_status": "not_attempted",
        "etl_events_parsed": True,
        "etl_event_count": 10,
        "synthetic_file_matched_write_event_count": 1,
        "synthetic_writer_pid_matched_write_event_count": 1,
        "other_or_unknown_pid_matched_write_event_count": 0,
        "raw_trace_and_worker_deleted": True,
        "raw_etl_exported": False,
        "private_file_identity_exported": False,
        "process_pid_exported": False,
        "clinical_file_touched": False,
        "actual_ilexis_writer_identified": False,
        "file_write_completion_proven": False,
        "complete_etw_delivery_proven": False,
        "shared_app_storage_isolation_verified": False,
        "clinical_edit_allowed": False,
        "verdict": "SYNTHETIC_ETW_FEASIBILITY_NOT_ILEXIS_CAUSALITY",
    }


class FeasibilityTests(unittest.TestCase):
    def setUp(self):
        self.x = sample()

    def go(self):
        return gate.validate(self.x)

    def bad(self):
        with self.assertRaises(gate.InvalidD3E12):
            self.go()

    def test_positive_synthetic_only(self):
        out = self.go()
        self.assertTrue(out["bounded_synthetic_pid_link_observed"])
        self.assertFalse(out["actual_ilexis_writer_identified"])

    def test_no_matching_event_remains_unverified(self):
        self.x.update(etl_query_status="no_matching_events", etl_decoder="none", etl_events_parsed=False,
                      direct_etl_read_status="no_matching_events",
                      tracerpt_attempted=True, tracerpt_exit_zero=False,
                      tracerpt_evtx_read_status="conversion_failed",
                      etl_event_count=0, synthetic_file_matched_write_event_count=0,
                      synthetic_writer_pid_matched_write_event_count=0)
        self.assertFalse(self.go()["bounded_synthetic_pid_link_observed"])

    def test_query_error_remains_unverified(self):
        self.x.update(etl_query_status="query_error", etl_decoder="none", etl_events_parsed=False,
                      direct_etl_read_status="no_matching_events",
                      tracerpt_attempted=True, tracerpt_exit_zero=False,
                      tracerpt_evtx_read_status="conversion_failed",
                      etl_event_count=0, synthetic_file_matched_write_event_count=0,
                      synthetic_writer_pid_matched_write_event_count=0)
        self.assertFalse(self.go()["bounded_synthetic_pid_link_observed"])

    def test_provider_unavailable_supported_as_unverified(self):
        self.x.update(provider_discovered=False, trace_started=False,
                      trace_stopped=False, synthetic_write_verified=False,
                      etl_query_status="unavailable", etl_decoder="none", etl_events_parsed=False,
                      etl_file_present=False, etl_file_nonempty=False,
                      direct_etl_read_status="not_attempted",
                      tracerpt_attempted=False, tracerpt_exit_zero=False,
                      tracerpt_evtx_read_status="not_attempted",
                      etl_event_count=0, synthetic_file_matched_write_event_count=0,
                      synthetic_writer_pid_matched_write_event_count=0)
        self.assertFalse(self.go()["bounded_synthetic_pid_link_observed"])

    def test_tracerpt_fallback_can_be_bounded_synthetic(self):
        self.x.update(etl_decoder="tracerpt_evtx", direct_etl_read_status="other",
                      tracerpt_attempted=True, tracerpt_exit_zero=True,
                      tracerpt_output_file_present=True, tracerpt_output_file_nonempty=True,
                      tracerpt_evtx_read_status="events_returned")
        self.assertTrue(self.go()["bounded_synthetic_pid_link_observed"])

    def test_forged_fallback_without_parsing_rejected(self):
        self.x.update(etl_decoder="tracerpt_evtx", direct_etl_read_status="other",
                      tracerpt_attempted=True, tracerpt_exit_zero=True,
                      tracerpt_output_file_present=True, tracerpt_output_file_nonempty=True,
                      tracerpt_evtx_read_status="events_returned")
        self.x["etl_events_parsed"] = False
        self.bad()

    def test_unknown_decoder_rejected(self):
        self.x["etl_decoder"] = "upload_raw"
        self.bad()

    def test_etl_metadata_missing_is_not_a_green_pid_claim(self):
        self.x["etl_file_nonempty"] = False
        self.bad()

    def test_illegal_raw_error_text_field_rejected(self):
        self.x["raw_exception"] = "C:/secret"
        self.bad()

    def test_nonempty_etl_requires_present_file(self):
        self.x["etl_file_present"] = False
        self.bad()

    def test_fallback_requires_direct_error(self):
        self.x["tracerpt_attempted"] = True
        self.bad()

    def test_fallback_output_requires_attempt(self):
        self.x["tracerpt_output_file_nonempty"] = True
        self.bad()

    def test_invalid_error_category_rejected(self):
        self.x["direct_etl_read_status"] = "full_user_path"
        self.bad()

    def test_only_aggregate_stage_diagnostics_in_checked_result(self):
        out = self.go()
        self.assertTrue(out["etl_file_nonempty"])
        self.assertEqual(out["direct_etl_read_status"], "events_returned")
        self.assertNotIn("raw_etl", out)
        self.assertFalse(out["clinical_edit_allowed"])

    def test_empty_trace_and_no_decoder_remains_unverified(self):
        self.x.update(etl_query_status="probe_error", etl_decoder="none",
                      etl_file_present=False, etl_file_nonempty=False,
                      direct_etl_read_status="not_attempted", etl_events_parsed=False,
                      synthetic_write_verified=False, etl_event_count=0,
                      synthetic_file_matched_write_event_count=0,
                      synthetic_writer_pid_matched_write_event_count=0)
        self.assertFalse(self.go()["bounded_synthetic_pid_link_observed"])

    def test_trace_not_started_cannot_claim_etl_present(self):
        self.x.update(trace_started=False, trace_stopped=False,
                      synthetic_write_verified=False, etl_events_parsed=False,
                      etl_query_status="unavailable", etl_decoder="none",
                      etl_event_count=0, synthetic_file_matched_write_event_count=0,
                      synthetic_writer_pid_matched_write_event_count=0)
        self.bad()

    def test_tracerpt_cannot_run_on_unverified_synthetic_file(self):
        self.x.update(etl_query_status="query_error", etl_decoder="none",
                      direct_etl_read_status="other", etl_events_parsed=False,
                      synthetic_write_verified=False, tracerpt_attempted=True,
                      tracerpt_evtx_read_status="conversion_failed",
                      etl_event_count=0, synthetic_file_matched_write_event_count=0,
                      synthetic_writer_pid_matched_write_event_count=0)
        self.bad()

    def test_other_pid_does_not_prove_writer(self):
        self.x["synthetic_writer_pid_matched_write_event_count"] = 0
        self.x["other_or_unknown_pid_matched_write_event_count"] = 1
        self.assertFalse(self.go()["bounded_synthetic_pid_link_observed"])

    def test_missing_raw_cleanup_rejected(self):
        self.x["raw_trace_and_worker_deleted"] = False
        self.bad()

    def test_mismatched_event_sum_rejected(self):
        self.x["other_or_unknown_pid_matched_write_event_count"] = 1
        self.bad()

    def test_pid_matches_exceed_matched_file_rejected(self):
        self.x["synthetic_writer_pid_matched_write_event_count"] = 2
        self.bad()

    def test_match_exceeds_total_rejected(self):
        self.x["etl_event_count"] = 0
        self.bad()

    def test_trace_started_without_stop_rejected(self):
        self.x["trace_stopped"] = False
        self.bad()

    def test_trace_started_without_provider_rejected(self):
        self.x["provider_discovered"] = False
        self.bad()

    def test_synthetic_write_outside_trace_rejected(self):
        self.x["trace_started"] = False
        self.bad()

    def test_match_without_write_rejected(self):
        self.x["synthetic_write_verified"] = False
        self.bad()

    def test_query_status_vs_parse_flag_rejected(self):
        self.x["etl_query_status"] = "query_error"
        self.bad()

    def test_bad_query_status_rejected(self):
        self.x["etl_query_status"] = "safe_to_edit"
        self.bad()

    def test_forged_sensitive_claims_rejected(self):
        for field in (
            "raw_etl_exported", "private_file_identity_exported", "process_pid_exported",
            "clinical_file_touched", "actual_ilexis_writer_identified",
            "file_write_completion_proven", "complete_etw_delivery_proven",
            "shared_app_storage_isolation_verified", "clinical_edit_allowed",
        ):
            with self.subTest(field=field):
                self.x[field] = True
                self.bad()
                self.x[field] = False

    def test_extra_path_rejected(self):
        self.x["private_file_path"] = "secret"
        self.bad()

    def test_extra_pid_rejected(self):
        self.x["writer_pid"] = 1234
        self.bad()

    def test_boolean_as_count_rejected(self):
        self.x["etl_event_count"] = True
        self.bad()

    def test_negative_and_large_counts_rejected(self):
        for n in (-1, 20001, "1"):
            with self.subTest(value=n):
                self.x["etl_event_count"] = n
                self.bad()
                self.x = sample()

    def test_wrong_source_rejected(self):
        self.x["source"] = "REAL_PATIENT"
        self.bad()

    def test_wrong_provider_rejected(self):
        self.x["provider"] = "untrusted"
        self.bad()

    def test_wrong_verdict_rejected(self):
        self.x["verdict"] = "ISOLATION_VERIFIED"
        self.bad()

    def test_cli_success_no_private_info(self):
        with tempfile.TemporaryDirectory() as d:
            inp = Path(d) / "in.json"; out = Path(d) / "out.json"
            inp.write_text(json.dumps(self.x), encoding="utf8")
            p = subprocess.run([sys.executable, str(HERE/"facad_314_d3e12_etw_gate.py"),
                                "--input", str(inp), "--output", str(out)],
                               capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
            result = json.loads(out.read_text())
            self.assertFalse(result["actual_ilexis_writer_identified"])
            self.assertNotIn("process_pid_exported", result)

    def test_cli_missing_input_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            p = subprocess.run([sys.executable, str(HERE/"facad_314_d3e12_etw_gate.py"),
                                "--input", str(Path(d)/"missing"), "--output", str(Path(d)/"out")],
                               capture_output=True, text=True)
            self.assertEqual(p.returncode, 2)
            self.assertIn("CLINICAL_EDIT_ALLOWED=false", p.stdout)
            self.assertNotIn("Traceback", p.stderr)


if __name__ == "__main__":
    unittest.main()
