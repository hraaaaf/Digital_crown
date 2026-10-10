#!/usr/bin/env python3
"""D3E.19 offline ISO staging review. SOURCE ONLY: NEVER runs a hypervisor."""
import argparse
import json
from pathlib import Path

BASE_SHA = "f4c49b332f54113244574a0a87b76ca2f60f2e5d"
REQUIRED = {
  "schema": "facad314_d3e19_offline_iso_staging_review_v1",
  "phase": "SOURCE_ONLY_DESIGN",
  "based_on_d3e18_commit": "f4c49b332f54113244574a0a87b76ca2f60f2e5d",
  "intended_subject": "OFFICIAL_NONCLINICAL_ROBERT_QUICK_DEMO_ONLY",
  "hypervisor_option": "HYPERV_GENERATION_2_CANDIDATE_UNVERIFIED",
  "ingress_design": "PREBOOT_READONLY_ISO_NO_HOST_SHARED_FOLDER",
  "guest_egress_design": "BLOCKED_NO_APPROVED_OUTPUT_CHANNEL",
  "publisher_package_status": "NOT_ACQUIRED_NO_BINARY_OR_PATIENT_DATA",
  "network_policy": "NO_VIRTUAL_NIC_NO_SWITCH_DESIGN_ONLY",
  "integration_policy": "NO_GUEST_COPY_NO_POWERSHELL_DIRECT_NO_ENHANCED_SESSION",
  "collection_scope": "ETW_STILL_GUEST_WIDE_IF_LATER_AUTHORIZED",
  "review_status": "INTERNAL_ADVERSARIAL_ONLY_NOT_INDEPENDENT",
  "verdict": "D3E19_OFFLINE_ISO_DESIGN_ONLY_NATIVE_GATES_BLOCKED"
}
FALSE_KEYS = set([
  "publisher_signature_checked",
  "sha256_checked",
  "official_download_provenance_verified",
  "sample_nonclinical_verified",
  "offline_license_authorized_verified",
  "iso_readonly_verified",
  "iso_content_allowlist_verified",
  "media_custody_verified",
  "hyperv_guest_available_verified",
  "secure_boot_verified",
  "nic_absence_verified",
  "vm_switch_absence_verified",
  "guest_service_copy_disabled_verified",
  "powershell_direct_disabled_verified",
  "enhanced_session_disabled_verified",
  "drive_redirect_disabled_verified",
  "clipboard_redirect_disabled_verified",
  "printer_usb_redirect_disabled_verified",
  "checkpoint_and_disk_disposal_verified",
  "host_secrets_absent_verified",
  "host_media_not_exposed_verified",
  "vm_teardown_verified",
  "host_iso_unmounted_after_verified",
  "output_channel_approved_verified",
  "raw_trace_guest_only_verified",
  "trace_loss_bounds_verified",
  "real_ilexis_writer_attributed_verified",
  "independent_privacy_review_approved",
  "independent_scientific_review_approved",
  "native_execution_authorized",
  "native_vm_booted",
  "facad_demo_executed",
  "native_trace_captured",
  "clinical_edit_allowed",
  "shared_storage_isolation_verified",
  "merge_or_deployment_authorized",
  "converged"
])
MAX_BYTES = 20000

class StagingBlocked(ValueError):
    """Fail-closed design or evidence boundary violation."""

def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise StagingBlocked("DUPLICATE_JSON_KEY")
        result[key] = value
    return result

def validate(plan):
    if not isinstance(plan, dict) or set(plan) != set(REQUIRED) | FALSE_KEYS:
        raise StagingBlocked("SCHEMA_KEYS_INVALID")
    for key, expected in REQUIRED.items():
        if type(plan[key]) is not str or plan[key] != expected:
            raise StagingBlocked("DESIGN_SCOPE_OR_PROVENANCE_INVALID")
    for key in FALSE_KEYS:
        if plan[key] is not False:
            raise StagingBlocked("UNVERIFIED_NATIVE_OR_SECURITY_CLAIM")
    return {
        "verdict": "D3E19_STATIC_STAGING_REVIEW_COMPLETE_NATIVE_BLOCKED",
        "native_requirements_unverified": len(FALSE_KEYS),
        "iso_built": False,
        "iso_mounted": False,
        "vm_started": False,
        "capture_authorized": False,
        "real_ilexis_writer_proven": False,
        "independent_reviews_complete": False,
    }

def load_plan(path):
    if not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise StagingBlocked("PLAN_MISSING_OR_TOO_LARGE")
    raw = path.read_bytes()
    if raw.startswith(b"\\xef\\xbb\\xbf") or b"\\x00" in raw:
        raise StagingBlocked("ENCODING_INVALID")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=no_duplicate_keys)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", required=True, type=Path)
    args = parser.parse_args()
    try:
        output = validate(load_plan(args.contract))
        print("D3E19_VERDICT=" + output["verdict"])
        print("D3E19_REQUIREMENTS_UNVERIFIED=" + str(output["native_requirements_unverified"]))
        print("D3E19_SOURCE_ONLY=true")
        return 0
    except (StagingBlocked, ValueError, TypeError, OSError, UnicodeError, KeyError):
        print("D3E19_VERDICT=BLOCKED_INVALID_OR_FORGED_SOURCE_CONTRACT")
        return 2
    finally:
        print("D3E19_ISO_CREATED=false")
        print("D3E19_NATIVE_VM_RUN=false")
        print("D3E19_CAPTURE_AUTHORIZED=false")
        print("FAC03_D3=OPEN_RED")
        print("SHARED_APP_STORAGE_ISOLATION=UNVERIFIED")
        print("CLINICAL_EDIT_ALLOWED=false")

if __name__ == "__main__":
    raise SystemExit(main())
