"""D3E.19 source-only adversarial security and evidentiary integrity tests."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GATE = ROOT / "scripts/facad_314_d3e19_iso_staging_gate.py"
CONTRACT = ROOT / "docs/audits/FACAD_314_D3E19_ISO_STAGING_CONTRACT.json"
spec = importlib.util.spec_from_file_location("d3e19_gate", GATE)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

class A_HostBoundaryAndSupplyChain(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads(CONTRACT.read_text(encoding="utf-8"))

    def blocked(self):
        with self.assertRaises(gate.StagingBlocked):
            gate.validate(self.plan)

    def test_valid_design_still_blocks_native(self):
        result = gate.validate(self.plan)
        self.assertFalse(result["vm_started"])
        self.assertFalse(result["capture_authorized"])
        self.assertFalse(result["iso_built"])
        self.assertEqual(result["native_requirements_unverified"], len(gate.FALSE_KEYS))

    def test_network_access_fails(self):
        self.plan["network_policy"] = "NETWORK_ENABLED_TEMPORARILY"
        self.blocked()

    def test_shared_folder_design_fails(self):
        self.plan["ingress_design"] = "READONLY_HOST_MOUNT"
        self.blocked()

    def test_clipboard_or_power_shell_direct_fails(self):
        self.plan["integration_policy"] = "ENHANCED_SESSION_FOR_SETUP"
        self.blocked()

    def test_source_forgery_fails(self):
        self.plan["based_on_d3e18_commit"] = "0" * 40
        self.blocked()

    def test_binary_claim_fails(self):
        self.plan["publisher_package_status"] = "DOWNLOADED_VERIFIED"
        self.blocked()

    def test_egress_assumption_fails(self):
        self.plan["guest_egress_design"] = "COPY_GUEST_TRACE_TO_HOST"
        self.blocked()

    def test_schema_typos_fail(self):
        self.plan["network_polciy"] = self.plan.pop("network_policy")
        self.blocked()

    def test_unknown_sensitive_field_fail(self):
        self.plan["patient_path"] = "C:/sensitive"
        self.blocked()

    def test_bool_as_zero_fail(self):
        self.plan["native_vm_booted"] = 0
        self.blocked()

    def test_null_check_fails(self):
        self.plan["iso_readonly_verified"] = None
        self.blocked()

class B_TruthAndIndependence(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads(CONTRACT.read_text(encoding="utf-8"))


    def test_policy_oracle_is_frozen_independently_of_gate(self):
        # Independent expected controls, not derived from gate.FALSE_KEYS.
        expected_keys = set(["checkpoint_and_disk_disposal_verified","clinical_edit_allowed","clipboard_redirect_disabled_verified","converged","drive_redirect_disabled_verified","enhanced_session_disabled_verified","facad_demo_executed","guest_service_copy_disabled_verified","host_iso_unmounted_after_verified","host_media_not_exposed_verified","host_secrets_absent_verified","hyperv_guest_available_verified","independent_privacy_review_approved","independent_scientific_review_approved","iso_content_allowlist_verified","iso_readonly_verified","media_custody_verified","merge_or_deployment_authorized","native_execution_authorized","native_trace_captured","native_vm_booted","nic_absence_verified","official_download_provenance_verified","offline_license_authorized_verified","output_channel_approved_verified","powershell_direct_disabled_verified","printer_usb_redirect_disabled_verified","publisher_signature_checked","raw_trace_guest_only_verified","real_ilexis_writer_attributed_verified","sample_nonclinical_verified","secure_boot_verified","sha256_checked","shared_storage_isolation_verified","trace_loss_bounds_verified","vm_switch_absence_verified","vm_teardown_verified"])
        expected_design = {
        "based_on_d3e18_commit": "f4c49b332f54113244574a0a87b76ca2f60f2e5d",
        "phase": "SOURCE_ONLY_DESIGN",
        "ingress_design": "PREBOOT_READONLY_ISO_NO_HOST_SHARED_FOLDER",
        "guest_egress_design": "BLOCKED_NO_APPROVED_OUTPUT_CHANNEL",
        "network_policy": "NO_VIRTUAL_NIC_NO_SWITCH_DESIGN_ONLY",
        "integration_policy": "NO_GUEST_COPY_NO_POWERSHELL_DIRECT_NO_ENHANCED_SESSION",
        "publisher_package_status": "NOT_ACQUIRED_NO_BINARY_OR_PATIENT_DATA",
        "review_status": "INTERNAL_ADVERSARIAL_ONLY_NOT_INDEPENDENT",
        "collection_scope": "ETW_STILL_GUEST_WIDE_IF_LATER_AUTHORIZED"
}
        self.assertEqual(len(expected_keys), 37)
        self.assertEqual(gate.FALSE_KEYS, expected_keys)
        for key, expected in expected_design.items():
            self.assertEqual(gate.REQUIRED[key], expected)

    def test_cannot_infer_etw_is_file_scoped(self):
        self.plan["collection_scope"] = "ETW_FILE_SCOPED"
        with self.assertRaises(gate.StagingBlocked):
            gate.validate(self.plan)

    def test_cannot_claim_external_review(self):
        self.plan["review_status"] = "INDEPENDENT_CONVERGED"
        with self.assertRaises(gate.StagingBlocked):
            gate.validate(self.plan)

    def test_cannot_convert_phase_to_capture(self):
        self.plan["phase"] = "NATIVE_CAPTURE"
        with self.assertRaises(gate.StagingBlocked):
            gate.validate(self.plan)

    def test_invalid_top_level_object(self):
        with self.assertRaises(gate.StagingBlocked):
            gate.validate([self.plan])

    def test_json_duplicate_key_fails(self):
        with self.assertRaises(gate.StagingBlocked):
            gate.no_duplicate_keys([("phase", "A"), ("phase", "B")])

    def test_cli_design_success_never_claims_clearance(self):
        proc = subprocess.run([sys.executable, str(GATE), "--contract", str(CONTRACT)],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("D3E19_NATIVE_VM_RUN=false", proc.stdout)
        self.assertIn("D3E19_CAPTURE_AUTHORIZED=false", proc.stdout)
        self.assertIn("CLINICAL_EDIT_ALLOWED=false", proc.stdout)
        self.assertIn("D3E19_SOURCE_ONLY=true", proc.stdout)

    def test_cli_duplicate_json_fails_closed_without_leak(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "bad.json"
            p.write_text('{"phase":"A","phase":"B"}', encoding="utf-8")
            proc = subprocess.run([sys.executable, str(GATE), "--contract", str(p)],
                                  capture_output=True, text=True)
            self.assertEqual(proc.returncode, 2)
            self.assertNotIn("Traceback", proc.stderr)
            self.assertIn("FAC03_D3=OPEN_RED", proc.stdout)

    def test_cli_missing_file_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            proc = subprocess.run(
                [sys.executable, str(GATE), "--contract", str(Path(td) / "absent")],
                capture_output=True, text=True)
            self.assertEqual(proc.returncode, 2)
            self.assertIn("D3E19_CAPTURE_AUTHORIZED=false", proc.stdout)

    def test_cli_oversized_contract_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "large.json"
            path.write_bytes(b" " * (gate.MAX_BYTES + 1))
            proc = subprocess.run([sys.executable, str(GATE), "--contract", str(path)],
                                  capture_output=True, text=True)
            self.assertEqual(proc.returncode, 2)

    def test_explicit_bom_rejection_before_json_decode(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "bom.json"
            path.write_bytes(b"\xef\xbb\xbf" + CONTRACT.read_bytes())
            with self.assertRaisesRegex(gate.StagingBlocked, "ENCODING_INVALID"):
                gate.load_plan(path)

    def test_explicit_nul_rejection_before_json_decode(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "nul.json"
            path.write_bytes(CONTRACT.read_bytes() + b"\x00")
            with self.assertRaisesRegex(gate.StagingBlocked, "ENCODING_INVALID"):
                gate.load_plan(path)

    def test_cli_bom_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "bom.json"
            path.write_bytes(b"\xef\xbb\xbf" + CONTRACT.read_bytes())
            proc = subprocess.run([sys.executable, str(GATE), "--contract", str(path)],
                                  capture_output=True, text=True)
            self.assertEqual(proc.returncode, 2)

def _make_flag_test(flag):
    def test(self):
        plan = json.loads(CONTRACT.read_text(encoding="utf-8"))
        plan[flag] = True
        with self.assertRaises(gate.StagingBlocked):
            gate.validate(plan)
    return test

for flag in sorted(gate.FALSE_KEYS):
    setattr(B_TruthAndIndependence, "test_forged_" + flag, _make_flag_test(flag))

if __name__ == "__main__":
    unittest.main()
