#!/usr/bin/env python3
"""Read-only evidence of Facad's PUBLIC official v3.14 PDF documentation.

Downloads to runner memory, never checks PDFs into GitHub. No patient data,
commercial analysis binaries, clinical editor action, or vendor login.
Any missing PDF or expected passage fails closed. --self-test is offline.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import urllib.request
from pathlib import Path

MANIFEST = Path(__file__).resolve().parents[1] / "docs/audits/data/FACAD_314_OFFICIAL_PDF_SOURCE_MANIFEST_2026-10-09.json"

FILES = {
    "FACAD_314_REFERENCE_MANUAL": {
        "url": "https://www.facad.com/dox/dox314/FacadRefMan.pdf",
        "min_pages": 100,
        "needles": (
            "Facad 3.14",
            "Cephalometry>Export>Analysis Values",
            "Cephalometry>Export>Analysis Properties",
            "Cephalometry>Export>Object Values",
            "Cephalometry>Export>Object Properties",
            "Distance (Dist2p)",
            "Angle between lines (4pt)",
        ),
    },
    "FACAD_314_TRACING_GUIDE": {
        "url": "https://www.facad.com/dox/dox314/FacadTracingUsersGuide_ENG.pdf",
        "min_pages": 15,
        "needles": ("Help > Manuals > Cephalometry",),
    },
    "FACAD_312_RELEASE_NOTES": {
        "url": "https://www.facad.com/wp/wp-content/uploads/2020/12/FacadReleaseNotes_3.12.pdf",
        "min_pages": 2,
        "needles": ("Ricketts (32 F)", "Ricketts (13 F)", "Atlas Cefalometr"),
    },
}


def canonical(txt: str) -> str:
    # Ignore PDF line breaks and the optional space around menu breadcrumb delimiters.
    return re.sub(r"\s+", " ", txt).strip().replace(" > ", ">").casefold()


def match_pages(pages: list[str], needle: str) -> list[int]:
    query = canonical(needle)
    if not query:
        raise ValueError("Blank evidence string")
    return [i + 1 for i, page in enumerate(pages) if query in canonical(page)]


def analyze_pdf(name: str, data: bytes, expected: dict) -> dict:
    if len(data) < 4096 or not data.startswith(b"%PDF-"):
        raise ValueError(f"{name}: invalid PDF header or unexpectedly short")
    from pypdf import PdfReader
    r = PdfReader(io.BytesIO(data), strict=False)
    if len(r.pages) < expected["min_pages"]:
        raise ValueError(f"{name}: only {len(r.pages)} pages")
    pages = [(page.extract_text() or "") for page in r.pages]
    hits = {}
    for needle in expected["needles"]:
        loc = match_pages(pages, needle)
        if not loc:
            raise ValueError(f"{name}: REQUIRED PDF passage absent: {needle!r}")
        hits[needle] = loc
    return {
        "document": name,
        "source_url": expected["url"],
        "bytes": len(data),
        "pdf_sha256": hashlib.sha256(data).hexdigest(),
        "page_count": len(pages),
        "needle_pages_1_based": hits,
        "source_level": "VENDOR_ORIGINAL_PDF_BYTES_READ_AND_MATCHED",
        "patient_data_present": False,
        "clinical_equivalence_certified": False,
        "export_executed": False,
    }


def confirm_pinned_manifest(actual: list[dict], manifest: dict) -> None:
    if manifest.get("schema") != "FACAD_314_OFFICIAL_VENDOR_PDF_SOURCE_MANIFEST_V1":
        raise ValueError("Manifest schema changed; manual review required")
    if manifest.get("basis", {}).get("source_result") != "SUCCESS":
        raise ValueError("Historical source verification not anchored")
    expected = manifest.get("docs", [])
    if len(actual) != 3 or len(expected) != 3:
        raise ValueError("Unexpected count: manufacturer original PDFs")
    perid = {row["id"]: row for row in expected}
    if set(perid) != set(FILES):
        raise ValueError("Unknown/missing official source identity")
    for row in actual:
        pinned = perid[row["document"]]
        for actual_key, manifest_key in (
            ("source_url", "url"), ("bytes", "bytes"),
            ("page_count", "pages"), ("pdf_sha256", "sha256"),
        ):
            if row[actual_key] != pinned[manifest_key]:
                raise ValueError(f"{row['document']}: official vendor PDF changed at {actual_key}")
        for term, pages in pinned["verified_pages_1_based"].items():
            if row["needle_pages_1_based"].get(term) != pages:
                raise ValueError(f"{row['document']}: evidence page for {term!r} changed")
        if "CLINICAL" in pinned["proof_scope"] and not pinned["proof_scope"].endswith("NOT_CLINICAL_FORMULA_PARITY"):
            raise ValueError("Vendor manifest falsely certifies clinical parity")
    if manifest.get("scientific_gates", {}).get("facad_numerical_parity") != "NOT_TESTED":
        raise ValueError("Scientific parity gate was silently promoted")


def live() -> None:
    evidence = []
    for name, expected in FILES.items():
        # No requests to any patient/user endpoints or private app APIs.
        req = urllib.request.Request(
            expected["url"],
            headers={"User-Agent": "DigitalCrown-F01.13-ReadOnlyResearch/1.0"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=45) as response:
            if response.geturl().split("/")[2].lower() != "www.facad.com":
                raise ValueError(f"{name}: unexpected host redirect")
            data = response.read(20 * 1024 * 1024 + 1)
        if len(data) > 20 * 1024 * 1024:
            raise ValueError(f"{name}: safety size threshold exceeded")
        document = analyze_pdf(name, data, expected)
        evidence.append(document)
        print(f"PDF_SOURCE_VERIFIED={name} sha256={document['pdf_sha256']} pages={document['page_count']}")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    confirm_pinned_manifest(evidence, manifest)
    print("OFFICIAL_VENDOR_SHA_MANIFEST_REPRODUCED=true")
    print(json.dumps({"schema": "FACAD_VENDOR_PDF_SOURCE_CHECK_V1", "records": evidence},
                     indent=2, ensure_ascii=False))
    print("OFFICIAL_FACAD_314_PDF_SOURCES_VERIFIED=3")
    print("NO_PATIENT_WRITE_OR_EXPORT=true")


def self_test() -> None:
    assert canonical("  Cephalometry > Export > Analysis \n Values  ") == canonical(
        "Cephalometry>Export>Analysis Values")
    assert match_pages(["first page", "Cephalometry > Export > Object Values", "x"],
                       "Cephalometry>Export>Object Values") == [2]
    assert match_pages(["No matching text"], "Analysis Properties") == []
    assert len(FILES) == 3
    assert sum(len(x["needles"]) for x in FILES.values()) == 11
    pin = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert set(x["id"] for x in pin["docs"]) == set(FILES)
    assert pin["scientific_gates"]["ceph08_protocols_verified"] == "OPEN"
    print("F01_13_PDF_SOURCE_VERIFIER_SELFTEST=7")


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--self-test", action="store_true")
    args = cli.parse_args()
    if args.self_test:
        self_test()
    else:
        live()
