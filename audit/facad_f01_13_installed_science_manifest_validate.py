#!/usr/bin/env python3
"""Fail-closed verifier of official Facad Quick demo DOCUMENT METADATA only.

Input is Github Actions metadata artifact #11642105521. Never reads PDF
files, patient files, analysis binary definitions, or copyrighted full text.
The scientific profile equivalence gates stay OPEN after successful checks.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

SCHEMA = "FACAD_314_INSTALLED_SCIENCE_PDF_PROVENANCE_V1"


def verify(meta: dict, pinned: dict) -> list[dict]:
    if pinned["schema"] != SCHEMA:
        raise ValueError("Pinned schema unexpectedly changed")
    if pinned["provenance"]["run_id"] != 37981554220:
        raise ValueError("Original source-run identity changed")
    if pinned["provenance"]["run_exact_head"] != "e91a25e230258e3a2653df226df73937a5dd4a70":
        raise ValueError("Original evidence HEAD changed")
    if meta.get("schema") != "FACAD_314_F01_13_INSTALLED_RELEASE_DOC_INDEX_V1":
        raise ValueError("Unrecognized installed inventory format")
    if meta.get("pdf_count") != 145 or len(meta.get("pdfs", [])) != 145:
        raise ValueError("145 originally observed installed PDF entries missing")
    if meta.get("scientific_filename_matches") != 75:
        raise ValueError("75 scientific filename hits changed")
    actual_matches = [x for x in meta["pdfs"] if x.get("subject_keywords_in_path")]
    if len(actual_matches) != 75:
        raise ValueError("Scientific names and counts differ")
    if meta.get("patient_tracing_opened") is not False:
        raise ValueError("Patient workflow falsely categorized as read-only")
    if meta.get("export_invoked") is not False or meta.get("patient_file_read") is not False:
        raise ValueError("Patient access or clinical export cannot pass scientific gate")
    if pinned["limits"]["clinical_parity_verified"] is not False:
        raise ValueError("Clinical parity falsely certified")
    if pinned["limits"]["atlas_2009_editor_authenticated"] is not False:
        raise ValueError("Atlas edition not editor-authenticated")
    rows = pinned["all_75_filename_matches"]
    if len(rows) != 75 or pinned["inventory"]["total_pdf_files"] != 145:
        raise ValueError("Pinned metadata inconsistent")
    byname = {x["relative_pdf_path"]: x for x in actual_matches}
    if len(byname) != 75:
        raise ValueError("Duplicate vendor document paths")
    if sorted(byname) != sorted(x["relative_pdf_path"] for x in rows):
        raise ValueError("Vendor PDF name catalog drift")
    for item in rows:
        candidate = byname[item["relative_pdf_path"]]
        if candidate["sha256"].lower() != item["sha256"].lower():
            raise ValueError(f"Content SHA mismatch at {item['relative_pdf_path']}")
        if candidate.get("clinical_equivalence_certified") is not False:
            raise ValueError("Unexpected automatic clinical assertion in index")
        if candidate.get("source_scope") != "VENDOR_ARCHIVE_PDF_METADATA_ONLY":
            raise ValueError("Source scope changed")
    priority = pinned["priority_sources"]
    if len(priority) != 12:
        raise ValueError("Priority source list was diluted")
    output = []
    for item in priority:
        original = byname[item["relative_pdf_path"]]
        output.append({
            "relative_pdf_path": item["relative_pdf_path"],
            "sha256": item["sha256"],
            "pages": original.get("page_count"),
            "extract_status": original.get("pdf_extract_status", "NOT_ATTEMPTED"),
            "keyword_page_locations_1based": original.get("keyword_page_locations_1based", {}),
            "clinical_equivalence_certified": False,
        })
    return output


def self_test(pinned: dict) -> None:
    # Generate a synthetic index that can test the contract OFFLINE.
    expected = copy.deepcopy(pinned["all_75_filename_matches"])
    index = {
        "schema": "FACAD_314_F01_13_INSTALLED_RELEASE_DOC_INDEX_V1",
        "pdf_count": 145,
        "scientific_filename_matches": 75,
        "pdfs": [
            {**row, "subject_keywords_in_path": ["ricketts"],
             "source_scope": "VENDOR_ARCHIVE_PDF_METADATA_ONLY",
             "clinical_equivalence_certified": False}
            for row in expected
        ] + [
            {"relative_pdf_path": f"Non-cephalo-unmatched-{n}.pdf",
             "subject_keywords_in_path": [],
             "clinical_equivalence_certified": False}
            for n in range(70)
        ],
        "patient_tracing_opened": False,
        "export_invoked": False,
        "patient_file_read": False,
    }
    assert len(verify(index, pinned)) == 12
    for name, mutator in [
        ("SHA_MISMATCH", lambda x, p: x["pdfs"][0].update(sha256="0" * 64)),
        ("PATIENT_FILE_READ", lambda x, p: x.update(patient_file_read=True)),
        ("FAKE_CLINICAL_EQUIVALENCE", lambda x, p: p["limits"].update(clinical_parity_verified=True)),
        ("MISSING_PDF", lambda x, p: x["pdfs"].pop()),
        ("MADE_UP_ATLAS_AUTH", lambda x, p: p["limits"].update(atlas_2009_editor_authenticated=True)),
    ]:
        test_index, test_pinned = copy.deepcopy(index), copy.deepcopy(pinned)
        mutator(test_index, test_pinned)
        try:
            verify(test_index, test_pinned)
        except ValueError:
            print(f"NEGATIVE_TEST_PASS={name}")
        else:
            raise AssertionError(f"False-evidence scenario accepted: {name}")
    print("SCIENTIFIC_MANIFEST_SELFTEST_PASS=6")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", type=Path)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--self-test", action="store_true")
    opts = parser.parse_args()
    pinned = json.loads(opts.manifest.read_text(encoding="utf-8"))
    if opts.self_test:
        self_test(pinned)
        return
    if opts.inventory is None:
        raise ValueError("--inventory is required outside self-test")
    meta = json.loads(opts.inventory.read_text(encoding="utf-8"))
    rows = verify(meta, pinned)
    print("INSTALLED_VENDOR_PDF_INVENTORY_ROWS=145")
    print("INSTALLED_VENDOR_SCIENCE_FILENAME_MATCHES=75")
    print("INSTALLED_VENDOR_PDF_PINNED_SHAS=75")
    print("SCIENTIFIC_PRIORITY_DOCUMENTS=12")
    print("CLINICAL_EQUIVALENCE_CERTIFIED=false")
    print("NO_PATIENT_DATA_OR_PDF_REHOSTING=true")
    print(json.dumps({"schema": "FACAD_SCIENTIFIC_PRIORITY_PDF_PAGES_V1",
                      "priority_sources": rows}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
