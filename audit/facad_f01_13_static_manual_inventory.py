#!/usr/bin/env python3
"""Static, read-only document inventory in the official Facad 3.14.1.1111 release.

Never starts Facad or reads .fcd, patient files, application configuration,
licensed analysis binary definitions or clinical exports.
Reports ONLY PDF-document metadata, hashes, narrow keyword/page locations.
Does NOT distribute licensed/copyrighted PDF content.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

MAX_FILE_SIZE = 35 * 1024 * 1024
MAX_PDF_COUNT = 350
DOCUMENT_HINTS = ("ricketts", "cephalometr", "landmark", "analys", "library", "manual")
TARGETS = {
    "RICKETTS_32F": ("Ricketts (32 F)", "Ricketts 32"),
    "RICKETTS_13F": ("Ricketts (13 F)", "Ricketts 13"),
    "RICKETTS_SUMMARY": ("Ricketts Summary",),
    "PM_PRIME": ("PM'", "Pm'"),
    "FACIAL_HEIGHT": ("Total Facial Height", "Posterior Facial Height"),
}


def classify(path: Path) -> list[str]:
    name = path.as_posix().lower()
    return [key for key in DOCUMENT_HINTS if key in name]


def collect(base: Path) -> dict:
    from pypdf import PdfReader
    if not base.is_dir():
        raise ValueError("Official extracted release directory missing")
    # Only *.pdf. No PHI or proprietary analysis binaries are opened.
    pdfs = sorted((p for p in base.rglob("*") if p.is_file() and p.suffix.lower() == ".pdf"),
                  key=lambda p: p.as_posix().lower())
    if len(pdfs) > MAX_PDF_COUNT:
        raise ValueError("Unexpectedly large vendor documentation inventory; refuse")
    docs = []
    for p in pdfs:
        size = p.stat().st_size
        if size < 100 or size > MAX_FILE_SIZE:
            raise ValueError(f"Unexpected PDF file size at {p.name!r}")
        rel = p.relative_to(base).as_posix()
        entry = {
            "relative_pdf_path": rel,
            "bytes": size,
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "subject_keywords_in_path": classify(p.relative_to(base)),
            "source_scope": "VENDOR_ARCHIVE_PDF_METADATA_ONLY",
            "clinical_equivalence_certified": False,
        }
        # Content inspection only for specifically named scientific document PDFs.
        # Never upload copied text, only whether a keyword was encountered and page indexes.
        if entry["subject_keywords_in_path"]:
            try:
                pdf = PdfReader(p, strict=False)
                entry["page_count"] = len(pdf.pages)
                hits = {key: [] for key in TARGETS}
                for page_idx, page in enumerate(pdf.pages):
                    content = re.sub(r"\s+", " ", page.extract_text() or "").casefold()
                    for key, phrases in TARGETS.items():
                        if any(phrase.casefold() in content for phrase in phrases):
                            hits[key].append(page_idx + 1)
                entry["keyword_page_locations_1based"] = {k: v for k, v in hits.items() if v}
                entry["pdf_extract_status"] = "TEXT_EXTRACTION_ATTEMPTED"
            except (ValueError, RuntimeError, TypeError) as exc:
                entry["pdf_extract_status"] = type(exc).__name__
        docs.append(entry)
    matches = [x for x in docs if x["subject_keywords_in_path"]]
    result = {
        "schema": "FACAD_314_F01_13_INSTALLED_RELEASE_DOC_INDEX_V1",
        "input_origin": "Facad-Installer-3.14.1.1111.exe > FacadRelease-3.14.1.1111.zip",
        "scope": "VENDOR_STATIC_PDF_METADATA_ONLY;_NO_CLINICAL_WORKFLOWS",
        "pdf_count": len(docs),
        "scientific_filename_matches": len(matches),
        "pdfs": docs,
        "f01_13_scientific_source_authority": "UNVERIFIED_UNTIL_PER_PAGE_SOURCE_REVIEW",
        "patient_tracing_opened": False,
        "export_invoked": False,
        "patient_file_read": False,
    }
    if len(docs) != result["pdf_count"] or any(len(x["sha256"]) != 64 for x in docs):
        raise ValueError("Index consistency mismatch")
    return result


def self_test() -> None:
    assert classify(Path("Docs/Ricketts (32 F).pdf")) == ["ricketts"]
    assert classify(Path("Docs/Cephalometry Library.pdf")) == ["cephalometr", "library"]
    assert classify(Path("Examples/Robert-2.0.fcd")) == []
    assert len(TARGETS) == 5
    assert MAX_FILE_SIZE < 40 * 1024 * 1024
    print("STATIC_MANUAL_INVENTORY_SELFTEST=5")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if args.root is None or args.out is None:
        raise ValueError("--root and --out required for actual inventory")
    result = collect(args.root.resolve())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
    print(f"STATIC_VENDOR_PDF_COUNT={result['pdf_count']}")
    print(f"STATIC_SCIENTIFIC_FILENAME_MATCHES={result['scientific_filename_matches']}")
    print("NO_PATIENT_READ_OR_EXPORT=true")
    for item in result["pdfs"]:
        if item["subject_keywords_in_path"]:
            print(f"VENDOR_PDF_CANDIDATE={item['relative_pdf_path']} sha256={item['sha256']}")


if __name__ == "__main__":
    main()
