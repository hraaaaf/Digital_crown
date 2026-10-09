#!/usr/bin/env python3
"""Fail-closed, metadata-only validation of five installed vendor science PDFs."""
import argparse
import copy
import json
import re
from pathlib import Path

EXPECTED_FILES = (
    "Ricketts (32 F).pdf",
    "Ricketts (13 F).pdf",
    "C01_Lateral Cephalometry Library - Lines and Contructed markers.pdf",
    "C02_Lateral Cephalometry Library - Measurements.pdf",
    "Overview of Landmarks.pdf",
)
EXPECTED_PAGES = (8, 5, 12, 34, 2)

def verify(evidence, manifest):
    if evidence.get("schema") != "FACAD_F01_13_FIVE_PDF_LEXICAL_EVIDENCE_V1":
        raise ValueError("Wrong evidence schema")
    if evidence.get("vendor_science_documents") != 5:
        raise ValueError("Not five scientific references")
    if evidence.get("scientific_formula_equivalence") != "NOT_VERIFIED":
        raise ValueError("False formula scientific certification")
    if evidence.get("clinical_parity") != "NOT_TESTED":
        raise ValueError("False clinical validation")
    if evidence.get("full_vendor_pdf_redistributed") is not False or evidence.get("patient_data_exported") is not False:
        raise ValueError("PDF/PHI redistribution risk")
    if manifest.get("schema") != "FACAD_314_INSTALLED_SCIENCE_PDF_PROVENANCE_V1":
        raise ValueError("Invalid published science manifest")
    documents = evidence.get("documents")
    if not isinstance(documents, list) or len(documents) != 5:
        raise ValueError("Missing document")
    pins = {p["relative_pdf_path"]: p for p in manifest["priority_sources"]}
    seen=set()
    summary=[]
    for row,basename,pages in zip(documents,EXPECTED_FILES,EXPECTED_PAGES):
        name=row.get("name")
        if name!=basename or name in seen:
            raise ValueError("Wrong document order or duplicate")
        seen.add(name)
        matches=[x for x in pins if x.endswith("/"+name)]
        if len(matches)!=1:
            raise ValueError("Unresolved vendor PDF identity")
        pin=pins[matches[0]]
        if row.get("sha256")!=pin["sha256"]:
            raise ValueError("PDF SHA drift")
        if row.get("pages")!=pages or row["pages"]!=pin["pages_pdf_1_based"]:
            raise ValueError("PDF page count drift")
        kw=row.get("keyword_pages")
        if not isinstance(kw,dict):
            raise ValueError("Missing lexical page index")
        for page,words in kw.items():
            if not re.fullmatch(r"[1-9][0-9]*",page) or not (1<=int(page)<=pages):
                raise ValueError("Out-of-range scientific page signal")
            if not isinstance(words,list) or not words or any(not isinstance(word,str) or len(word)>40 for word in words):
                raise ValueError("Malformed page signal")
        summary.append({"source":name,"pages":pages,"keyword_pages":kw,"sha256":pin["sha256"]})
    return summary

def selftest(m):
    # Metadata-only synthetic proof, never needs vendor PDFs.
    records=[]
    for name,pages in zip(EXPECTED_FILES,EXPECTED_PAGES):
        pin=next(x for x in m["priority_sources"] if x["relative_pdf_path"].endswith("/"+name))
        records.append({"name":name,"sha256":pin["sha256"],"pages":pages,"keyword_pages":{"1":["Xi"]}})
    sample={"schema":"FACAD_F01_13_FIVE_PDF_LEXICAL_EVIDENCE_V1",
            "documents":records,"vendor_science_documents":5,
            "scientific_formula_equivalence":"NOT_VERIFIED","clinical_parity":"NOT_TESTED",
            "full_vendor_pdf_redistributed":False,"patient_data_exported":False}
    assert len(verify(sample,m))==5
    tests=(
        ("TAMPER_SHA",lambda x:x["documents"][0].update(sha256="0"*64)),
        ("TAMPER_PAGE",lambda x:x["documents"][0].update(pages=9)),
        ("OUT_OF_RANGE_PAGE",lambda x:x["documents"][0].update(keyword_pages={"9":["Xi"]})),
        ("FAKE_FORMULA_VALIDATION",lambda x:x.update(scientific_formula_equivalence="CERTIFIED")),
        ("FAKE_CLINICAL_PARITY",lambda x:x.update(clinical_parity="PASS")),
        ("PATIENT_EXPORT",lambda x:x.update(patient_data_exported=True)),
        ("MISSING_DOCUMENT",lambda x:x["documents"].pop()),
    )
    for label,mutate in tests:
        x=copy.deepcopy(sample)
        mutate(x)
        try:
            verify(x,m)
        except ValueError:
            print("NEGATIVE_TEST_PASS="+label)
        else:
            raise AssertionError("False evidence accepted: "+label)
    print("F01_13_FIVE_PDF_REPLAY_TESTS_PASS=8")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--evidence",type=Path)
    ap.add_argument("--manifest",type=Path,required=True)
    ap.add_argument("--expected-matrix",type=Path)
    ap.add_argument("--self-test",action="store_true")
    args=ap.parse_args()
    m=json.loads(args.manifest.read_text(encoding="utf-8"))
    if args.self_test:
        selftest(m)
        return
    if args.evidence is None:
        raise ValueError("--evidence required")
    e=json.loads(args.evidence.read_text(encoding="utf-8-sig"))
    rows=verify(e,m)
    if args.expected_matrix is None:
        raise ValueError("Pinned source text page evidence not supplied")
    expected=json.loads(args.expected_matrix.read_text(encoding="utf-8"))
    if expected.get("schema")!="FACAD_F01_13_V314_FIVE_PDF_TERM_PAGE_MATRIX_V1":
        raise ValueError("Unrecognized locked source matrix")
    byname={row["source"]:row for row in rows}
    pinned=expected.get("sources",[])
    if len(pinned)!=5 or set(x["name"] for x in pinned)!=set(byname):
        raise ValueError("Missing exact source reference")
    for item in pinned:
        original=byname[item["name"]]
        if item["sha256"]!=original["sha256"] or item["pages"]!=original["pages"]:
            raise ValueError("Locked science PDF identity or page changed")
        if item["hits"]!=original["keyword_pages"]:
            raise ValueError("Locked source term/page matrix drift")
    if expected["boundary"]["numeric_parity_tested"] is not False:
        raise ValueError("Clinical parity cannot be promoted from token matches")
    print("FIVE_SCIENTIFIC_PDF_TERM_PAGE_MATRIX_LOCK_PASS=5")
    for row in rows:
        print("SOURCE_PDF_SHA_VERIFIED="+row["source"]+"|"+row["sha256"])
        for page,terms in sorted(row["keyword_pages"].items(),key=lambda x:int(x[0])):
            print("SOURCE_LEXICAL_PAGE="+row["source"]+"|"+page+"|"+",".join(terms))
    print("FIVE_VENDOR_PDF_SOURCES_METADATA_PASS=5")
    print("F01_13_SOURCE_TERMS_ONLY=true")
    print("FACAD_FORMULA_PARITY_CERTIFIED=false")
    print("NO_PATIENT_IO=true")

if __name__=="__main__":
    main()
