#!/usr/bin/env python3
"""Facad D3 *source coverage* audit: NEVER an app, data, or clinical isolation test.

Only parses checked-in PowerShell/Python source files. No Windows processes,
patient files, configurations, registry values, secrets, or network access.
All reported categories are predetermined and path-free.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

# Vendor-authored Facad 3.14 manual/release note. They are provenance records,
# not permissions to access the listed files.
SOURCE_MANUAL = "https://www.facad.com/dox/dox314/FacadRefMan.pdf"
SOURCE_NOTES = "https://www.facad.com/wp/wp-content/uploads/2024/01/FacadReleaseNotes_3.14.pdf"

# A scoped 'Facad' folder is NOT the vendor's Roaming/Ilexis settings root.
# Patient Data Root/Node may point to network storage via configured paths.
REQUIRED_CATEGORIES = (
    "FACAD_PATIENT_DATA_ROOT_CONFIGURED",
    "FACAD_PATIENT_DATA_NODE_CONFIGURED",
    "FACAD_WORK_LIST_AND_IMPORT_TARGET",
    "FACAD_ROAMING_ILEXIS_SETTINGS",
    "FACAD_ADMINISTRATOR_SETTINGS_AT_EXE",
    "FACAD_LICENSE_ROOT_PROTECTED",
    "FACAD_SHARED_OR_UNC_ROOTS",
    "PROCESS_AND_CHILD_WRITE_PATH_ATTRIBUTION",
    "REGISTRY_WRITE_EVENT_ATTRIBUTION",  # metadata-only event, never values
)

def inspect(collector: str, observer: str, comparator: str) -> dict:
    """Conservative static assessment: string matches never prove runtime isolation."""
    if not all(isinstance(z, str) and z for z in (collector, observer, comparator)):
        raise ValueError("Missing or invalid checked-in source input")

    # Existing snapshot v1 has no configured patient data scope. No instruction
    # in this routine reads settings to resolve sensitive configured paths.
    facts = {
        "FACAD_PATIENT_DATA_ROOT_CONFIGURED": (
            "facad_patient_data_root=TreeScope" in collector
            and "'facad_patient_data_root': 'filetree'" in comparator
        ),
        "FACAD_PATIENT_DATA_NODE_CONFIGURED": (
            "facad_patient_data_node=TreeScope" in collector
            and "'facad_patient_data_node': 'filetree'" in comparator
        ),
        "FACAD_WORK_LIST_AND_IMPORT_TARGET": (
            "facad_work_list=TreeScope" in collector
            and "'facad_work_list': 'filetree'" in comparator
        ),
        "FACAD_ROAMING_ILEXIS_SETTINGS": (
            "facad_appdata_roaming_ilexis=TreeScope (Join-Path $env:APPDATA 'Ilexis') $false" in collector
            and "'facad_appdata_roaming_ilexis': 'filetree'" in comparator
        ),
        "FACAD_ADMINISTRATOR_SETTINGS_AT_EXE": (
            "FACAD_ADMIN_SETTINGS_METADATA_OBSERVED=true" in collector
            and "Facad.Administrator.settings" in collector
        ),
        "FACAD_LICENSE_ROOT_PROTECTED": (
            "FACAD_LICENSE_ROOT_PROTECTED_METADATA_ONLY=true" in collector
            and "LICENSE_CONTENT_READ=false" in collector
        ),
        "FACAD_SHARED_OR_UNC_ROOTS": (
            "FACAD_CONFIGURED_UNC_ROOTS_RESOLVED=true" in collector
        ),
        "PROCESS_AND_CHILD_WRITE_PATH_ATTRIBUTION": (
            "path_attribution_available=$true" in observer
            and "complete_child_process_coverage=$true" in observer
        ),
        "REGISTRY_WRITE_EVENT_ATTRIBUTION": (
            "FACAD_REGISTRY_WRITE_EVENTS_ATTRIBUTED=true" in collector
        ),
    }
    missing = [key for key in REQUIRED_CATEGORIES if not facts[key]]
    # Neither a string token nor an immaculate monitored-files snapshot proves
    # negative writes to unobserved paths, persistence of isolation after app
    # startup, or rights separation. A real, independent witness is mandatory.
    return {
        "schema": "FACAD_D3_VENDOR_STORAGE_AUTHORITY_GAPS_V1",
        "source": "STATIC_REPOSITORY_TEXT_ONLY",
        "source_manual": SOURCE_MANUAL,
        "source_release_notes": SOURCE_NOTES,
        "required_category_count": len(REQUIRED_CATEGORIES),
        "documented_coverage_category_count": len(REQUIRED_CATEGORIES) - len(missing),
        "missing_category_ids": missing,
        "verdict": ("BLOCKED_INCOMPLETE_VENDOR_STORAGE_SCOPE"
                    if missing else "INCONCLUSIVE_STATIC_COVERAGE_NOT_RUNTIME_ISOLATION"),
        "path_attribution_proven_by_this_audit": False,
        "real_machine_storage_roots_verified": False,
        "shared_app_storage_isolation_verified": False,
        "d3_isolation_verified": False,
        "clinical_edit_allowed": False,
        "facad_numerical_parity_certified": False,
        "no_patient_files_or_settings_read": True,
        "patient_data_root_may_be_network_shared": True,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--collector", type=Path, required=True)
    p.add_argument("--observer", type=Path, required=True)
    p.add_argument("--comparator", type=Path, required=True)
    a = p.parse_args()
    verdict = inspect(
        a.collector.read_text(encoding="utf-8"),
        a.observer.read_text(encoding="utf-8"),
        a.comparator.read_text(encoding="utf-8"),
    )
    print(json.dumps(verdict, sort_keys=True))
    print("D3_VENDOR_SOURCE_COVERAGE_AUDIT_PASS=true")
    print("D3_STORAGE_ISOLATION=UNVERIFIED")
    print("CLINICAL_EDIT_ALLOWED=false")
    # Exit 0 means this gap detector executed correctly; NEVER D3 success.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
