#!/usr/bin/env python3
"""Read-only C02 SHA-locked minimal PDF index. No PDF or full page text exported.
This proves vendor PDF source and lexical occurrence, not formula equivalence.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

SCHEMA = "FACAD_314_C02_OFFICIAL_INSTALLED_PDF_MINIMAL_INDEX_V1"
EXPECTED_RELATIVE = "Program/Doc/Cephalometry/C_Cephalometry Library/C02_Lateral Cephalometry Library - Measurements.pdf"
EXPECTED_SHA = "4dbd3fa8419b684529fcbc17f615f49f7486cdf037fcfff025b1b307c0c0a548"
EXPECTED_PAGES = 34
TARGETS = [
    "SNA", "SNB", "ANB", "PFH", "Xi", "CF", "PM'", "InterIncisal",
    "FMA", "IMPA", "McNamara", "Ricketts", "Steiner", "Tweed",
    "Angle2ln", "Angle3p", "Angle4p", "Dist2p", "DistLine",
    "Dist3p", "ProjLine", "Proj90Line", "Max-Mand", "Go-Gn", "Go-Me",
]

def whole_token(text: str, term: str) -> bool:
    return re.search(r"(?<![A-Za-z0-9])" + re.escape(term) + r"(?![A-Za-z0-9])", text, flags=re.IGNORECASE) is not None

def self_test() -> None:
    assert not whole_token("Maxillary", "Xi")
    assert whole_token("Xi A constructed point", "Xi")
    assert not whole_token("insideSNAword", "SNA")
    assert whole_token("SNA: 82", "SNA")
    assert whole_token("PM' = ...", "PM'")
    assert not whole_token("PMPrime", "PM'")
    assert not whole_token("ProjLineX", "ProjLine")
    assert whole_token("ProjLine(OL,Ii,Is)", "ProjLine")
    assert EXPECTED_RELATIVE.endswith("C02_Lateral Cephalometry Library - Measurements.pdf")
    assert EXPECTED_PAGES == 34 and len(EXPECTED_SHA) == 64
    print("C02_MINIMAL_SOURCE_INDEX_SELFTEST=9")

def index(root: Path, manifest_path: Path) -> dict:
    root = root.resolve(strict=True)
    if root.name.lower() != "facad":
        raise ValueError("Unexpected Facad install root")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    records = [a for a in manifest["priority_sources"] if a.get("relative_pdf_path") == EXPECTED_RELATIVE]
    if len(records) != 1:
        raise ValueError("Source manifest missing exact C02 entry")
    pin = records[0]
    if pin.get("sha256") != EXPECTED_SHA or pin.get("pages_pdf_1_based") != EXPECTED_PAGES:
        raise ValueError("C02 metadata pin disagreement")
    path = (root / EXPECTED_RELATIVE).resolve(strict=True)
    if not path.is_relative_to(root) or path.suffix.lower() != ".pdf":
        raise ValueError("Unexpected C02 path")
    raw = path.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if sha != EXPECTED_SHA:
        raise ValueError("C02 content SHA256 changed; fail closed")
    from pypdf import PdfReader
    pdf = PdfReader(path, strict=False)
    if len(pdf.pages) != EXPECTED_PAGES:
        raise ValueError("C02 page count changed; fail closed")
    page_meta = []
    hits = {term: [] for term in TARGETS}
    for number, page in enumerate(pdf.pages, start=1):
        page_text = page.extract_text() or ""
        page_meta.append({
            "pdf_page_1based": number,
            "text_chars": len(page_text),
            "text_sha256": hashlib.sha256(page_text.encode("utf-8")).hexdigest(),
        })
        for term in TARGETS:
            if whole_token(page_text, term):
                hits[term].append(number)
    result = {
        "schema": SCHEMA,
        "source_name": path.name,
        "source_relative_path": EXPECTED_RELATIVE,
        "source_sha256": sha,
        "source_page_count": len(pdf.pages),
        "source_size_bytes": len(raw),
        "pdf_text_layer_pages_ge_80chars": sum(x["text_chars"] >= 80 for x in page_meta),
        "page_metadata": page_meta,
        "whole_token_terms_pages_1based": hits,
        "source_observation_state": "OFFICIAL_PDF_SHA_VERIFIED_LEXICAL_INDEX_ONLY",
        "formula_definition_verified": False,
        "clinical_equivalence_certified": False,
        "patient_data_processed": False,
        "complete_vendor_pdf_redistributed": False,
        "full_page_text_redistributed": False,
        "numeric_parity_verified": False,
        "fac03_d3": "OPEN_RED",
    }
    payload = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if len(payload.encode("utf-8")) > 30000:
        raise ValueError("Unexpectedly large research metadata; fail closed")
    return result

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path)
    ap.add_argument("--manifest", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--self-test", action="store_true")
    opts = ap.parse_args()
    if opts.self_test:
        self_test()
        return
    if not (opts.root and opts.manifest and opts.out):
        raise ValueError("Missing required root/manifest/out argument")
    result = index(opts.root, opts.manifest)
    opts.out.parent.mkdir(parents=True, exist_ok=True)
    opts.out.write_text(json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("C02_SOURCE_SHA_VERIFIED=" + result["source_sha256"])
    print("C02_SOURCE_PAGES=" + str(result["source_page_count"]))
    print("C02_TEXT_LAYER_PAGES=" + str(result["pdf_text_layer_pages_ge_80chars"]))
    print("C02_LEXICAL_INDEX_ONLY=true")
    print("NO_PATIENT_PROCESSING=true")
    print("VENDOR_PDF_NOT_EXPORTED=true")
    print("CLINICAL_FORMULA_NOT_CERTIFIED=true")

if __name__ == "__main__":
    main()
