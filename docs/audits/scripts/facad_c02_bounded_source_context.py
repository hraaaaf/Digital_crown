#!/usr/bin/env python3
"""Minimum quotations from SHA-locked FACAD C02 for a private scientific audit.

Exports ONLY at most 10 tiny contexts (<=16 words each, <=160 total) from ten
known page/label anchors; no full page, figures, installer, patient, or PDF.
Contexts are preliminary evidence, not authoritative math/clinical parity.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

REL = "Program/Doc/Cephalometry/C_Cephalometry Library/C02_Lateral Cephalometry Library - Measurements.pdf"
SHA = "4dbd3fa8419b684529fcbc17f615f49f7486cdf037fcfff025b1b307c0c0a548"
ANCHORS = ((5, "SNA"), (5, "SNB"), (5, "ANB"),
           (10, "InterIncisal"), (19, "PFH"), (20, "PFH"),
           (22, "Max-Mand"), (24, "Xi"), (24, "CF"), (30, "Max-Mand"))
MAX_WORDS_PER_CONTEXT = 16
MAX_TOTAL_WORDS = 160
MAX_CONTEXTS = 10

def matches(term: str, text: str) -> bool:
    return bool(re.search(r"(?<![A-Za-z0-9])" + re.escape(term) +
                          r"(?![A-Za-z0-9])", text, re.IGNORECASE))

def clip_words(text: str, budget: int = MAX_WORDS_PER_CONTEXT) -> str:
    # Preserve delimiters/signs in printed evidence; single spaces only.
    words = text.split()
    if budget < 1:
        raise ValueError("no budget")
    return " ".join(words[:budget])

def one_context(page_text: str, term: str) -> dict:
    lines = page_text.splitlines()
    choices = [i for i, line in enumerate(lines) if matches(term, line)]
    if not choices:
        raise ValueError("known page/term anchor absent")
    # Heading standalone is preferable; never quote multiple occurrences.
    priority = sorted(choices, key=lambda i:(len(lines[i]) > 45, i))
    pos = priority[0]
    # Original FACAD PDF line breaks are not sentences; include only three
    # following lines, strict word cap and exact hash for auditability.
    raw = " ".join(line.strip() for line in lines[pos:pos+4] if line.strip())
    clipped = clip_words(raw)
    if not matches(term, clipped):
        raise ValueError("anchor lost through cropping")
    if len(clipped.split()) > MAX_WORDS_PER_CONTEXT:
        raise ValueError("context overflow")
    return {
        "extracted_text_line_1based": pos + 1,
        "selected_line_sha256": hashlib.sha256(lines[pos].encode("utf-8")).hexdigest(),
        "context": clipped,
        "context_words": len(clipped.split()),
        "context_is_truncated_to_budget": len(raw.split()) > MAX_WORDS_PER_CONTEXT,
        "contains_math_definition_verified": False,
    }

def scan(root: Path, manifest_file: Path, index_file: Path) -> dict:
    from pypdf import PdfReader
    root = root.resolve(strict=True)
    if root.name.lower() != "facad":
        raise ValueError("wrong trusted source root")
    path = (root / REL).resolve(strict=True)
    if path.suffix.lower() != ".pdf" or not path.is_relative_to(root):
        raise ValueError("PDF escapes trusted FACAD root")
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    target = [item for item in manifest.get("priority_sources", [])
              if item.get("relative_pdf_path") == REL]
    if len(target) != 1 or target[0].get("sha256") != SHA or target[0].get("pages_pdf_1_based") != 34:
        raise ValueError("source manifest mismatch")
    if hashlib.sha256(path.read_bytes()).hexdigest() != SHA:
        raise ValueError("C02 source bytes changed")
    old = json.loads(index_file.read_text(encoding="utf-8"))
    if old.get("source_sha256") != SHA or old.get("source_page_count") != 34:
        raise ValueError("old source evidence invalid")
    doc = PdfReader(path, strict=False)
    if len(doc.pages) != 34:
        raise ValueError("source PDF page count mismatch")
    out = []
    for number, term in ANCHORS:
        page_text = doc.pages[number-1].extract_text() or ""
        pinned = old["page_metadata"][number-1]
        if pinned["pdf_page_1based"] != number or hashlib.sha256(page_text.encode("utf-8")).hexdigest() != pinned["text_sha256"]:
            raise ValueError("PDF text layer changed from original source run")
        evidence = one_context(page_text, term)
        out.append({"pdf_page_1based": number, "label": term, **evidence})
    if len(out) != MAX_CONTEXTS or sum(x["context_words"] for x in out) > MAX_TOTAL_WORDS:
        raise ValueError("snippet count or word-budget violation")
    result = {
        "schema": "FACAD_314_C02_MINIMAL_PAGE_QUOTATIONS_RESEARCH_V1",
        "source_sha256": SHA, "source_pages": 34,
        "original_source_index_sha256": hashlib.sha256(index_file.read_bytes()).hexdigest(),
        "word_limit_per_context": MAX_WORDS_PER_CONTEXT,
        "word_limit_total": MAX_TOTAL_WORDS,
        "total_quoted_words": sum(x["context_words"] for x in out),
        "contexts": out,
        "no_full_pdf_or_page_text": True,
        "no_patient_data": True,
        "formula_geometry_sign_or_endpoint_verified": False,
        "clinical_equivalence_certified": False,
        "fac03_d3": "OPEN_RED",
    }
    payload = json.dumps(result, ensure_ascii=False)
    if len(payload.encode("utf-8")) > 12000:
        raise ValueError("bounded excerpt payload unexpectedly huge")
    return result

def self_test():
    assert matches("Xi", "Xi OL")
    assert not matches("Xi", "Maxillary")
    assert matches("ANB", "ANB:")
    assert not matches("ANB", "dANBv")
    assert matches("PM'", "PM' / Xi")
    assert clip_words("A B C D", 2) == "A B"
    assert one_context("SNA\nA to N\nSN reference angle\nContinued", "SNA")["context_words"] == 9
    assert one_context("Xi\nOL\npoint", "Xi")["context"] == "Xi OL point"
    assert len(ANCHORS) == MAX_CONTEXTS and MAX_TOTAL_WORDS == MAX_CONTEXTS * MAX_WORDS_PER_CONTEXT
    assert all(1 <= x <= 34 for x, _ in ANCHORS)
    assert not any("patient" in x.lower() for x in ("".join(k for _, k in ANCHORS),))
    print("C02_MINIMAL_SOURCE_QUOTE_SELFTEST=11")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--root", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--index", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if not all((args.root, args.manifest, args.index, args.out)):
        raise ValueError("missing source requirements")
    result = scan(args.root, args.manifest, args.index)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, sort_keys=True, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("C02_PAGE_SOURCE_CONTEXTS=" + str(len(result["contexts"])))
    print("C02_SOURCE_CONTEXT_WORDS=" + str(result["total_quoted_words"]))
    print("C02_SOURCE_VERBATIM_WORDS_LIMIT_160=true")
    print("C02_NO_FULL_PDF_PATIENT_OR_PAGE_EXPORT=true")
    print("C02_FORMULA_EQUIVALENCE_NOT_VERIFIED=true")

if __name__ == "__main__":
    main()
