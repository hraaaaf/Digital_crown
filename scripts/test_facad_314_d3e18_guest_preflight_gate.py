"""D3E.18 independent-lens internal adversarial reviews, source only."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTRACT = ROOT / "docs/audits/FACAD_314_D3E18_GUEST_PREFLIGHT_CONTRACT.json"
WSB = ROOT / "docs/audits/FACAD_314_D3E18_ISOLATED_GUEST_DESIGN.wsb.template"
GATE = ROOT / "scripts/facad_314_d3e18_guest_preflight_gate.py"
spec = importlib.util.spec_from_file_location("d3e18_gate", GATE)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class A_GuestConfigurationPrivacy(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.template = WSB.read_text(encoding="utf-8")

    def bad(self):
        with self.assertRaises(gate.GuestPreflightBlocked):
            gate.validate_contract_and_template(self.plan, self.template)

    def test_valid_template_still_no_capture(self):
        out = gate.validate_contract_and_template(self.plan, self.template)
        self.assertEqual(out["verdict"],
                         "D3E18_STATIC_CONFIGURATION_VALID_NATIVE_GATES_BLOCKED")
        self.assertFalse(out["runtime_isolation_proven"])

    def test_networking_cannot_enable(self):
        self.template = self.template.replace("<Networking>Disable</Networking>",
                                              "<Networking>Enable</Networking>")
        self.bad()

    def test_vgpu_cannot_enable(self):
        self.template = self.template.replace("<VGpu>Disable</VGpu>",
                                              "<VGpu>Enable</VGpu>")
        self.bad()

    def test_audioinput_cannot_enable(self):
        self.template = self.template.replace("<AudioInput>Disable</AudioInput>",
                                              "<AudioInput>Enable</AudioInput>")
        self.bad()

    def test_videoinput_cannot_enable(self):
        self.template = self.template.replace("<VideoInput>Disable</VideoInput>",
                                              "<VideoInput>Enable</VideoInput>")
        self.bad()

    def test_printerredirection_cannot_enable(self):
        self.template = self.template.replace("<PrinterRedirection>Disable</PrinterRedirection>",
                                              "<PrinterRedirection>Enable</PrinterRedirection>")
        self.bad()

    def test_clipboardredirection_cannot_enable(self):
        self.template = self.template.replace("<ClipboardRedirection>Disable</ClipboardRedirection>",
                                              "<ClipboardRedirection>Enable</ClipboardRedirection>")
        self.bad()
    def test_protected_client_cannot_disable(self):
        self.template = self.template.replace("<ProtectedClient>Enable</ProtectedClient>",
                                              "<ProtectedClient>Disable</ProtectedClient>")
        self.bad()

    def test_cannot_forge_import_of_official_demo_resolved(self):
        self.plan["import_of_official_demo_resolved"] = True
        self.bad()

    def test_cannot_forge_sandbox_available_on_runner_verified(self):
        self.plan["sandbox_available_on_runner_verified"] = True
        self.bad()

    def test_cannot_forge_host_hypervisor_configuration_verified(self):
        self.plan["host_hypervisor_configuration_verified"] = True
        self.bad()

    def test_cannot_forge_enterprise_policy_overrides_excluded(self):
        self.plan["enterprise_policy_overrides_excluded"] = True
        self.bad()

    def test_cannot_forge_guest_network_disabled_at_runtime_verified(self):
        self.plan["guest_network_disabled_at_runtime_verified"] = True
        self.bad()

    def test_cannot_forge_host_file_mounts_absent_at_runtime_verified(self):
        self.plan["host_file_mounts_absent_at_runtime_verified"] = True
        self.bad()

    def test_cannot_forge_clipboard_disabled_at_runtime_verified(self):
        self.plan["clipboard_disabled_at_runtime_verified"] = True
        self.bad()

    def test_cannot_forge_host_printers_media_disabled_at_runtime_verified(self):
        self.plan["host_printers_media_disabled_at_runtime_verified"] = True
        self.bad()

    def test_cannot_forge_credentials_and_host_secrets_absent_verified(self):
        self.plan["credentials_and_host_secrets_absent_verified"] = True
        self.bad()

    def test_cannot_forge_demo_source_license_and_integrity_verified(self):
        self.plan["demo_source_license_and_integrity_verified"] = True
        self.bad()

    def test_cannot_forge_no_patient_or_clinical_data_present_verified(self):
        self.plan["no_patient_or_clinical_data_present_verified"] = True
        self.bad()

    def test_cannot_forge_raw_trace_guest_only_proven(self):
        self.plan["raw_trace_guest_only_proven"] = True
        self.bad()

    def test_cannot_forge_guest_cleanup_and_destruction_verified(self):
        self.plan["guest_cleanup_and_destruction_verified"] = True
        self.bad()

    def test_cannot_forge_event_delivery_loss_free_proven(self):
        self.plan["event_delivery_loss_free_proven"] = True
        self.bad()

    def test_cannot_forge_real_ilexis_writer_proven(self):
        self.plan["real_ilexis_writer_proven"] = True
        self.bad()

    def test_cannot_forge_independent_privacy_reviewer_approved(self):
        self.plan["independent_privacy_reviewer_approved"] = True
        self.bad()

    def test_cannot_forge_independent_scientific_reviewer_approved(self):
        self.plan["independent_scientific_reviewer_approved"] = True
        self.bad()

    def test_cannot_forge_explicit_future_native_capture_permission(self):
        self.plan["explicit_future_native_capture_permission"] = True
        self.bad()

    def test_cannot_forge_native_sandbox_launched(self):
        self.plan["native_sandbox_launched"] = True
        self.bad()

    def test_cannot_forge_actual_facad_run_performed(self):
        self.plan["actual_facad_run_performed"] = True
        self.bad()

    def test_cannot_forge_clinical_edit_allowed(self):
        self.plan["clinical_edit_allowed"] = True
        self.bad()

    def test_cannot_forge_shared_app_storage_isolation_verified(self):
        self.plan["shared_app_storage_isolation_verified"] = True
        self.bad()

    def test_cannot_forge_converge_claim(self):
        self.plan["converge_claim"] = True
        self.bad()

    def test_cannot_forge_merge_or_deployment_authorized(self):
        self.plan["merge_or_deployment_authorized"] = True
        self.bad()


    def test_mapped_folders_writeable_rejected(self):
        self.template = self.template.replace("</Configuration>",
            "<MappedFolders><MappedFolder><HostFolder>C:\\Users</HostFolder>"
            "<ReadOnly>false</ReadOnly></MappedFolder></MappedFolders>"
            "</Configuration>")
        self.bad()

    def test_readonly_mount_is_still_rejected(self):
        self.template = self.template.replace("</Configuration>",
            "<MappedFolders><MappedFolder><ReadOnly>true</ReadOnly>"
            "</MappedFolder></MappedFolders></Configuration>")
        self.bad()

    def test_logon_command_rejected(self):
        self.template = self.template.replace("</Configuration>",
            "<LogonCommand><Command>notepad.exe</Command></LogonCommand>"
            "</Configuration>")
        self.bad()

    def test_unrecognized_option_rejected(self):
        self.template = self.template.replace("</Configuration>",
            "<NetworkPolicy>Safe</NetworkPolicy></Configuration>")
        self.bad()

    def test_duplicate_networking_rejected(self):
        self.template = self.template.replace("</Configuration>",
            "<Networking>Disable</Networking></Configuration>")
        self.bad()

    def test_template_comment_rejected(self):
        self.template = self.template.replace("<Configuration>",
            "<Configuration><!-- no-run -->")
        self.bad()

    def test_doctype_external_entity_rejected(self):
        self.template = self.template.replace("<Configuration>",
            "<!DOCTYPE Configuration [<!ENTITY x SYSTEM \"file:///etc/passwd\">]>"
            "<Configuration>")
        self.bad()

    def test_non_whitespace_hidden_text_rejected(self):
        self.template = self.template.replace("<Configuration>",
            "<Configuration>unsafe")
        self.bad()

    def test_xml_attribute_rejected(self):
        self.template = self.template.replace("<Networking>",
            '<Networking safe="yes">')
        self.bad()

    def test_guest_nested_xml_rejected(self):
        self.template = self.template.replace("<Networking>Disable</Networking>",
            "<Networking><Value>Disable</Value></Networking>")
        self.bad()

    def test_extra_contract_key_rejected(self):
        self.plan["host_patient_path"] = "private"
        self.bad()

    def test_contract_phase_forgery_rejected(self):
        self.plan["phase"] = "LIVE_CAPTURE"
        self.bad()

    def test_contract_hash_forgery_rejected(self):
        self.plan["based_on_d3e17_commit"] = "f" * 40
        self.bad()

    def test_contract_claim_about_scope_rejected(self):
        self.plan["collection_scope"] = "ETW_SINGLE_FILE_ONLY"
        self.bad()

    def test_contract_wrong_filetype_rejected(self):
        self.plan["config_format"] = "DIRECTLY_EXECUTABLE_WSB"
        self.bad()

    def test_contract_bool_as_int_rejected(self):
        self.plan["native_sandbox_launched"] = 0
        self.bad()

    def test_cli_success_gives_no_native_clearance(self):
        p = subprocess.run(
            [sys.executable, str(GATE), "--contract", str(CONTRACT),
             "--template", str(WSB)],
            capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("D3E18_NATIVE_SANDBOX_RUN=false", p.stdout)
        self.assertIn("D3E18_CAPTURE_AUTHORIZED=false", p.stdout)
        self.assertIn("CLINICAL_EDIT_ALLOWED=false", p.stdout)

    def test_cli_missing_template_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            p = subprocess.run(
                [sys.executable, str(GATE), "--contract", str(CONTRACT),
                 "--template", str(Path(td) / "missing")],
                capture_output=True, text=True)
            self.assertEqual(p.returncode, 2)
            self.assertNotIn("Traceback", p.stderr)


if __name__ == "__main__":
    unittest.main()
