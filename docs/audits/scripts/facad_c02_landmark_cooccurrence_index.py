#!/usr/bin/env python3
"""FACAD C02 lexical co-occurrence research, no source prose export.

This does NOT define FACAD measurements. It generates a source-locked,
page-scoped line-adjacency map for independently checking candidate landmark
dependencies. Read-only official PDF on a disposable GitHub runner.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

EXPECTED_RELATIVE = "Program/Doc/Cephalometry/C_Cephalometry Library/C02_Lateral Cephalometry Library - Measurements.pdf"
EXPECTED_SHA = "4dbd3fa8419b684529fcbc17f615f49f7486cdf037fcfff025b1b307c0c0a548"
EXPECTED_PAGES = 34
TARGETS = {"SNA": (5,), "SNB": (5,), "ANB": (5,), "PFH": (19, 20),
           "InterIncisal": (10,), "Xi": (24,), "CF": (24,),
           "Max-Mand": (22, 30)}
LANDMARK_TOKENS = ("Go-Gn", "Go-Me", "Co-Gn", "Co-A", "PtV", "PM'", "Pog",
                   "CF", "Xi", "Pt", "Gn", "Go", "Me", "Ba", "FH", "FL",
                   "OL", "SN", "ANS", "PNS", "Iia", "Isa", "Ii", "Is")
# Kept well below accidental, copyrighted text payload: output only
# official source metadata, canonical identifiers and cryptographic digests.
MAX_MATCHES_PER_TARGET_PAGE = 12

def whole_token(pattern: str, text: str, *, case_sensitive: bool = False):
    """Do not match the false 'Xi' substring in 'Maxillary'."""
    flags = 0 if case_sensitive else re.IGNORECASE
    return re.search(r"(?<![A-Za-z0-9])" + re.escape(pattern) +
                     r"(?![A-Za-z0-9])", text, flags=flags) is not None

def scan_page(text: str, targets: tuple[str, ...]):
    rows = []
    lines = text.splitlines()
    for pos, line in enumerate(lines):
        for target in targets:
            if not whole_token(target, line):
                continue
            # Exact source line (not neighbors). Hash supports reproducibility,
            # without publishing proprietary explanatory sentences.
            landmarks = sorted({p for p in LANDMARK_TOKENS if
                                p != target and whole_token(p, line,
                                                       case_sensitive=True)})
            rows.append({"target": target,
                         "line_number_1based": pos + 1,
                         "line_sha256": hashlib.sha256(line.encode("utf-8")).hexdigest(),
                         "line_characters": len(line),
                         "landmark_labels_same_extracted_line": landmarks,
                         "landmark_relationship_verified": False})
    return rows

def run(root: Path, manifest_path: Path, prior_index_path: Path) -> dict:
    root = root.resolve(strict=True)
    if root.name.lower() != "facad":
        raise ValueError("wrong document root")
    doc_path = (root / EXPECTED_RELATIVE).resolve(strict=True)
    if not doc_path.is_relative_to(root) or doc_path.suffix.lower() != ".pdf":
        raise ValueError("outside trusted Facad PDF root")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = [x for x in manifest["priority_sources"] if
                x.get("relative_pdf_path") == EXPECTED_RELATIVE]
    if len(expected) != 1 or expected[0]["sha256"] != EXPECTED_SHA:
        raise ValueError("official manifest pin mismatch")
    raw = doc_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED_SHA:
        raise ValueError("original PDF source SHA mismatch")
    prior = json.loads(prior_index_path.read_text(encoding="utf-8"))
    if prior.get("source_sha256") != EXPECTED_SHA or prior.get("source_page_count") != EXPECTED_PAGES:
        raise ValueError("prior source index does not match")
    if prior.get("source_observation_state") != "OFFICIAL_PDF_SHA_VERIFIED_LEXICAL_INDEX_ONLY":
        raise ValueError("prior source index verdict unknown")
    from pypdf import PdfReader
    doc = PdfReader(doc_path, strict=False)
    if len(doc.pages) != EXPECTED_PAGES:
        raise ValueError("page count mismatch")
    sections = []
    for page in sorted({n for nums in TARGETS.values() for n in nums}):
        src = doc.pages[page - 1].extract_text() or ""
        ref = prior["page_metadata"][page - 1]
        if ref["pdf_page_1based"] != page or            hashlib.sha256(src.encode("utf-8")).hexdigest() != ref["text_sha256"]:
            raise ValueError("page text hash changed from pinned run")
        wanted = tuple(key for key, nums in TARGETS.items() if page in nums)
        rows = scan_page(src, wanted)
        if len(rows) > len(wanted) * MAX_MATCHES_PER_TARGET_PAGE:
            raise ValueError("too many source contexts; fail closed")
        sections.append({"pdf_page_1based": page, "labels_searched": list(wanted),
                         "matching_extracted_lines": rows,
                         "matched_line_count": len(rows)})
    obj = {
        "schema": "FACAD_314_C02_PAGE_SCOPED_LEXICAL_LANDMARK_COOCCURRENCE_V1",
        "source_sha256": EXPECTED_SHA,
        "page_count": EXPECTED_PAGES,
        "source_index_sha256": hashlib.sha256(prior_index_path.read_bytes()).hexdigest(),
        "sections": sections,
        "source_text_redistributed": False,
        "patient_data_processed": False,
        "vendor_formula_verified": False,
        "landmark_dependencies_verified": False,
        "clinical_equivalence_certified": False,
        "fac03_d3": "OPEN_RED",
        "evidence_type": "SAME_EXTRACTED_LINE_LEXICAL_ONLY",
    }
    if len(json.dumps(obj).encode("utf-8")) > 50000:
        raise ValueError("metadata exceeds safe output bound")
    return obj

def self_test():
    assert not whole_token("Xi", "Maxillary")
    assert whole_token("Xi", "Xi: constructed point")
    assert not whole_token("CF", "FCF")
    assert not whole_token("Go-Gn", "prefixGo-GnSuffix")
    assert whole_token("Go-Gn", "Go-Gn / FH")
    assert not whole_token("PtV", "PtV2")
    rows = scan_page("PFH\nPFH is in the same line as CF and Go.\nXi: Maxillary", ("PFH", "Xi"))
    assert len(rows) == 3
    assert rows[1]["landmark_labels_same_extracted_line"] == ["CF", "Go"]
    assert rows[2]["landmark_labels_same_extracted_line"] == []
    assert all("text" not in r and "quote" not in r for r in rows)
    assert all(x in range(1, EXPECTED_PAGES + 1) for z in TARGETS.values() for x in z)
    print("C02_COOCCURRENCE_SELFTEST=11")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--root", type=Path)
    p.add_argument("--manifest", type=Path)
    p.add_argument("--prior-index", type=Path)
    p.add_argument("--out", type=Path)
    args = p.parse_args()
    if args.self_test:
        self_test()
        return
    if not (args.root and args.manifest and args.prior_index and args.out):
        raise ValueError("missing trusted source or output parameter")
    result = run(args.root, args.manifest, args.prior_index)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2,
                                   ensure_ascii=False) + "\n", encoding="utf-8")
    print("C02_SOURCE_SHA_VERIFIED=" + EXPECTED_SHA)
    print("C02_COOCCURRENCE_PAGES=" + str(len(result["sections"])))
    print("C02_COOCCURRENCE_ONLY_NO_FORMULA_CLAIM=true")
    print("C02_PDF_OR_EXPLANATORY_TEXT_EXPORTED=false")

if __name__ == "__main__":
    main()
