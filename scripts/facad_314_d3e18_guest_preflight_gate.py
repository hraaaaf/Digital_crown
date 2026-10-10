#!/usr/bin/env python3
"""D3E.18 source-only Windows guest preflight. NEVER starts Windows Sandbox.

A static .wsb template cannot verify hypervisor isolation, effective Windows
policy, hardware, guest teardown or any Facad file provenance. CI green never
authorizes native capture or clinical editing.
"""
import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path

BASE_SHA = "2b9985c78dececde8e697b4d923022592b2927ea"
REQUIRED_XML = {
    "VGpu": "Disable",
    "Networking": "Disable",
    "AudioInput": "Disable",
    "VideoInput": "Disable",
    "ProtectedClient": "Enable",
    "PrinterRedirection": "Disable",
    "ClipboardRedirection": "Disable",
}
REQUIRED_NONBOOLEAN = {
    "schema": "facad314_d3e18_isolated_guest_preflight_v1",
    "phase": "STATIC_DESIGN_ONLY",
    "based_on_d3e17_commit": BASE_SHA,
    "config_format": "WINDOWS_SANDBOX_WSB_TEMPLATE_NOT_LAUNCHABLE",
    "guest_config_path":
        "docs/audits/FACAD_314_D3E18_ISOLATED_GUEST_DESIGN.wsb.template",
    "intended_subject": "OFFICIAL_NONCLINICAL_ROBERT_QUICK_DEMO_ONLY",
    "collection_scope": "KERNEL_ETW_WOULD_STILL_BE_GUEST_WIDE",
    "verdict": "GUEST_BLUEPRINT_SOURCE_ONLY_NATIVE_PROOF_BLOCKED",
}
MUST_REMAIN_UNPROVEN = {
    "import_of_official_demo_resolved",
    "sandbox_available_on_runner_verified",
    "host_hypervisor_configuration_verified",
    "enterprise_policy_overrides_excluded",
    "guest_network_disabled_at_runtime_verified",
    "host_file_mounts_absent_at_runtime_verified",
    "clipboard_disabled_at_runtime_verified",
    "host_printers_media_disabled_at_runtime_verified",
    "credentials_and_host_secrets_absent_verified",
    "demo_source_license_and_integrity_verified",
    "no_patient_or_clinical_data_present_verified",
    "raw_trace_guest_only_proven",
    "guest_cleanup_and_destruction_verified",
    "event_delivery_loss_free_proven",
    "real_ilexis_writer_proven",
    "independent_privacy_reviewer_approved",
    "independent_scientific_reviewer_approved",
    "explicit_future_native_capture_permission",
    "native_sandbox_launched",
    "actual_facad_run_performed",
    "clinical_edit_allowed",
    "shared_app_storage_isolation_verified",
    "converge_claim",
    "merge_or_deployment_authorized",
}


class GuestPreflightBlocked(ValueError):
    pass


def check_wsb(source: str) -> dict:
    if not isinstance(source, str) or len(source.encode("utf-8")) > 8192:
        raise GuestPreflightBlocked("WSB_SIZE_INVALID")
    # No DTD, external entities, mixed content, comments or directives.
    for bad in ("<!", "<?", "<!--", "<![CDATA["):
        if bad in source:
            raise GuestPreflightBlocked("WSB_UNSAFE_XML_CONSTRUCT")
    try:
        root = ET.fromstring(source)
    except ET.ParseError as exc:
        raise GuestPreflightBlocked("WSB_XML_INVALID") from exc
    if root.tag != "Configuration" or root.attrib or (root.text or "").strip():
        raise GuestPreflightBlocked("WSB_ROOT_INVALID")
    actual = {}
    for elem in root:
        if (elem.tag not in REQUIRED_XML or elem.tag in actual
                or elem.attrib or len(elem) or (elem.tail or "").strip()):
            raise GuestPreflightBlocked("WSB_UNEXPECTED_OPTION")
        actual[elem.tag] = (elem.text or "").strip()
    if actual != REQUIRED_XML:
        raise GuestPreflightBlocked("WSB_OPTION_MISSING_OR_UNSAFE")
    return {
        "sandbox_config_checked": True,
        "network_requested_off": True,
        "mapped_folders_declared": False,
        "logon_command_declared": False,
        "host_clipboard_requested_off": True,
        "host_devices_requested_off": True,
        "protected_client_requested_on": True,
        "runtime_isolation_proven": False,
    }


def check_contract(data: dict) -> dict:
    if not isinstance(data, dict) or set(data) != (
            set(REQUIRED_NONBOOLEAN) | MUST_REMAIN_UNPROVEN):
        raise GuestPreflightBlocked("CONTRACT_KEYS_INVALID")
    for key, expected in REQUIRED_NONBOOLEAN.items():
        if type(data[key]) is not type(expected) or data[key] != expected:
            raise GuestPreflightBlocked("CONTRACT_PROVENANCE_OR_SCOPE_INVALID")
    for key in MUST_REMAIN_UNPROVEN:
        if data[key] is not False:
            raise GuestPreflightBlocked("UNPROVEN_SECURITY_CLAIM")
    return {
        "source_contract_checked": True,
        "checks_remaining_unverified_count": len(MUST_REMAIN_UNPROVEN),
        "sandbox_native_run_performed": False,
        "kernel_etw_guest_wide_if_later_enabled": True,
        "capture_authorized": False,
        "clinical_edit_allowed": False,
        "shared_app_storage_isolation_verified": False,
        "independent_reviews_converged": False,
        "verdict": "D3E18_STATIC_CONFIGURATION_VALID_NATIVE_GATES_BLOCKED",
    }


def validate_contract_and_template(plan, template):
    return {**check_wsb(template), **check_contract(plan)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--contract", required=True, type=Path)
    ap.add_argument("--template", required=True, type=Path)
    args = ap.parse_args()
    try:
        if args.contract.stat().st_size > 16000:
            raise GuestPreflightBlocked("CONTRACT_SIZE_INVALID")
        plan = json.loads(args.contract.read_text(encoding="utf-8-sig"))
        template = args.template.read_text(encoding="utf-8-sig")
        result = validate_contract_and_template(plan, template)
        # No raw config/paths/IDs or native user/clinical evidence printed.
        print("D3E18_STATIC_WSB_OPTIONS_CHECKED=true")
        print("D3E18_REQUIREMENTS_UNVERIFIED=" +
              str(result["checks_remaining_unverified_count"]))
        print("D3E18_VERDICT=" + result["verdict"])
        print("D3E18_NATIVE_SANDBOX_RUN=false")
        print("D3E18_CAPTURE_AUTHORIZED=false")
        return 0
    except (GuestPreflightBlocked, ValueError, TypeError,
            OSError, UnicodeError, KeyError):
        print("D3E18_VERDICT=BLOCKED_UNSAFE_OR_INCOMPLETE_BLUEPRINT")
        return 2
    finally:
        print("FAC03_D3=OPEN_RED")
        print("SHARED_APP_STORAGE_ISOLATION=UNVERIFIED")
        print("CLINICAL_EDIT_ALLOWED=false")


if __name__ == "__main__":
    raise SystemExit(main())
