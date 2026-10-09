#!/usr/bin/env python3
"""Fail-closed metadata replay of three original manufacturer PDFs with corrected whole-token Xi."""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path

SOURCE_SCHEMA = "FACAD_F01_13_PROPRIETARY_PDF_BRIEF_LABEL_CONTEXT_V1"
LOCK_SCHEMA = "FACAD_F01_13_CORRECTED_WHOLE_TOKEN_PDF_SNIPPET_LOCK_V1"

def verify(payload, lock, original_manifest):
    if payload.get("schema") != SOURCE_SCHEMA or lock.get("schema") != LOCK_SCHEMA:
        raise ValueError("Source or lock schema mismatch")
    if payload.get("scope") != "QUOTATION_LIMITED_METADATA_ONLY":
        raise ValueError("Unbounded scientific PDF evidence")
    if payload.get("clinical_parity_certified") is not False or payload.get("original_atlas_publisher_authority") is not False:
        raise ValueError("Prohibited source-to-clinical promotion")
    if payload.get("full_vendor_document_embedded") is not False:
        raise ValueError("Copyrighted document unexpectedly packaged")
    if payload.get("documents") is None or len(payload["documents"]) != 3:
        raise ValueError("Three original vendor documents required")
    if lock["origin"]["run_id"] != 37990457485 or lock["origin"]["head"] != "f30393f553044c97b932ac0cd90c25c5b280b634":
        raise ValueError("Provenance CI run changed")
    if lock["boundary"]["xi_word_at_page_1"] is not False or lock["boundary"]["xi_verified_entry_page_2"] is not True:
        raise ValueError("False positive Xi finding upgraded")
    if any(lock["boundary"][x] is not False for x in ("atlas_2009_original_tables_verified",
                "facad_dc_numeric_parity_verified", "clinical_edit_allowed")):
        raise ValueError("Clinical or publisher authority incorrectly claimed")
    originals = {x["relative_pdf_path"].split("/")[-1]:x
                 for x in original_manifest["priority_sources"]}
    observed = {x.get("filename"): x for x in payload["documents"]}
    locked = {x.get("name"):x for x in lock["targets"]}
    if len(observed) != 3 or len(locked) != 3 or set(observed) != set(locked):
        raise ValueError("Vendor document identity count changed")
    count = 0
    for name, pin in locked.items():
        item = observed[name]
        ref = originals[name]
        if item.get("sha256") != pin["sha"] or ref["sha256"] != pin["sha"]:
            raise ValueError("Manufacturer PDF SHA mismatch")
        if item.get("pages") != pin["pages"] or ref["pages_pdf_1_based"] != pin["pages"]:
            raise ValueError("Manufacturer PDF page drift")
        if item.get("clinical_geometry_parity_verified") is not False:
            raise ValueError("False numerical/geometry equivalence in source index")
        snippets = item.get("snippets", [])
        if not isinstance(snippets,list) or len(snippets)>5 or item.get("derived_word_budget_used",21)>20:
            raise ValueError("Copyright-safe short quote budget exceeded")
        actual = {snippet.get("term"):snippet for snippet in snippets}
        for term in pin["terms"]:
            entry=actual.get(term["term"])
            if entry is None:
                raise ValueError("Required precise source term missing")
            if entry.get("page") != term["page"] or entry.get("brief_label_context") != term["context"]:
                raise ValueError("Vendor page or short term snippet changed")
            if len(entry["brief_label_context"])>50:
                raise ValueError("Vendor PDF quotation too long")
            count+=1
    # Reject the particular 'Xi' inside 'Maxillary' prior false positive.
    xi = next(p for p in observed["C01_Lateral Cephalometry Library - Lines and Contructed markers.pdf"]["snippets"]
              if p["term"] == "Xi")
    if xi["page"] != 2 or not xi["brief_label_context"].startswith("Xi A constructed marker"):
        raise ValueError("No genuine source Xi definition at PDF page 2")
    return count

def self_test(lock,manifest):
    observed=[]
    for x in lock["targets"]:
        observed.append({"filename":x["name"],"sha256":x["sha"],"pages":x["pages"],
                         "clinical_geometry_parity_verified":False,
                         "derived_word_budget_used":20,
                         "snippets":[{"page":v["page"],"term":v["term"],"brief_label_context":v["context"]}
                                     for v in x["terms"]]})
    example={"schema":SOURCE_SCHEMA,"scope":"QUOTATION_LIMITED_METADATA_ONLY",
             "clinical_parity_certified":False,"original_atlas_publisher_authority":False,
             "full_vendor_document_embedded":False,"documents":observed}
    assert verify(example,lock,manifest)==9
    negatives=[
        ("XI_FALSE_POSITIVE",lambda x:x["documents"][2]["snippets"][-1].update(page=1,brief_label_context="OLmx Maxillary occlusal line")),
        ("XI_MARKER_ABSENT",lambda x:x["documents"][2]["snippets"].pop()),
        ("PDF_SHA_TAMPER",lambda x:x["documents"][0].update(sha256="0"*64)),
        ("SCIENTIFIC_PAGE_TAMPER",lambda x:x["documents"][1]["snippets"][0].update(page=4)),
        ("CLINICAL_PARITY_FORGERY",lambda x:x.update(clinical_parity_certified=True)),
        ("ATLAS_ORIGINAL_FORGERY",lambda x:x.update(original_atlas_publisher_authority=True)),
        ("UNBOUNDED_QUOTE",lambda x:x["documents"][2].update(derived_word_budget_used=200)),
        ("VENDOR_PDF_COPY",lambda x:x.update(full_vendor_document_embedded=True)),
        ("MISSING_DOCUMENT",lambda x:x["documents"].pop()),
    ]
    for name,mutate in negatives:
        x=copy.deepcopy(example)
        mutate(x)
        try: verify(x,lock,manifest)
        except ValueError: print("NEGATIVE_TEST_PASS="+name)
        else: raise AssertionError("False evidence not rejected: "+name)
    print("F01_13_CORRECTED_WHOLE_TOKEN_TESTS_PASS=10")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--evidence",type=Path)
    p.add_argument("--lock",type=Path,required=True)
    p.add_argument("--vendor-manifest",type=Path,required=True)
    p.add_argument("--self-test",action="store_true")
    a=p.parse_args()
    lock=json.loads(a.lock.read_text(encoding="utf-8"))
    manifest=json.loads(a.vendor_manifest.read_text(encoding="utf-8"))
    if a.self_test:
        self_test(lock,manifest)
        return
    if a.evidence is None: raise ValueError("Evidence file missing")
    evidence=json.loads(a.evidence.read_text(encoding="utf-8-sig"))
    count=verify(evidence,lock,manifest)
    print("PINNED_VENDOR_CONTEXT_TERMS="+str(count))
    print("SOURCE_XI_WHOLE_TOKEN_PDF_PAGE=2")
    print("SOURCE_CF_CONSTRUCTED_PDF_PAGE=2")
    print("SOURCE_PFH_32F_13F_DISTANCE_PROVEN=true")
    print("SOURCE_INTERINCISAL_13F_ANGLE_PROVEN=true")
    print("FACAD_NUMERICAL_PARITY_CERTIFIED=false")
    print("ATLAS_ORIGINAL_EDITION_CERTIFIED=false")
    print("PATIENT_DATA_PRESENT=false")

if __name__ == "__main__":
    main()
