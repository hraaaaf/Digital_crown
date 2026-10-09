#!/usr/bin/env python3
"""Source-tier and clinical fail-closed gate for Atlas2009 / Facad Ricketts.
Only research metadata, source text summaries and synthetic evidence.
Never runs Facad, opens patient records or purports to authenticate an inaccessible book.
"""
import argparse
import copy
import csv
import json
from pathlib import Path

SCHEMA="FACAD_F01_13_ATLAS2009_SOURCE_AUTHORITY_MATRIX_V1"
MAND_SOURCE="ATLAS_FACSIMILE_EXTENDED_AXIS_GEOMETRY_CANDIDATE"

def verify(d,compare_row,report,facad):
    if d.get("schema")!=SCHEMA: raise ValueError("Source schema mismatched")
    book=d.get("book",{})
    if book.get("isbn13")!="9788493675677" or book.get("year")!=2009:
        raise ValueError("Wrong original book identity")
    if book.get("publisher")!="Ripano" or book.get("edition")!="first":
        raise ValueError("Atlas edition not original first edition")
    if book.get("catalog_pages")!=296:
        raise ValueError("Institutional catalog metadata drift")
    for name in ("publisher_authenticated_chapter_bytes_available","publisher_authenticated_table_13_1_available","publisher_authenticated_table_13_2_available"):
        if book.get(name) is not False:
            raise ValueError("Nonexistent publisher original evidence falsely authenticated: "+name)
    tiers={x.get("id"):x for x in d.get("sources",[])}
    if len(tiers)!=8:raise ValueError("Exact source evidence list altered")
    for name in ("B1","B2","B3","B4","B5"):
        if name not in tiers or "table_rows_and_symbols" in tiers[name].get("supports",[]):
            raise ValueError("Bibliographic source falsely certifies formula tables")
    for name in ("R1","R2"):
        if name not in tiers or not tiers[name].get("tier","").startswith(("THIRD_PARTY","INDEPENDENT_ACADEMIC_SECONDARY")):
            raise ValueError("Secondary witness promoted to primary")
    if "full_tabular_contents" not in tiers["B1"].get("does_not_support",[]):
        raise ValueError("WorldCat record promoted to primary text")
    if tiers["R2"].get("screenshot_result")!="WEB_PDF_SCREENSHOT_CACHE_MISS__TEXT_EXTRACTION_ONLY":
        raise ValueError("Missing academic screenshot limitation")
    mand=d.get("mandibular_body_length_hypothesis",{})
    if mand.get("source_family_alignment")!="GEOMETRY_CONSISTENT_WITH_SECONDARY_ATLAS_FACSIMILE__NOT_AUTHORITATIVE_EQUIVALENCE":
        raise ValueError("Secondary data wrongly certified as Atlas original")
    if mand.get("facad_PM_prime_refs")!=["Xi","PM","A","Pog"] or mand.get("facad_Mand_len_refs")!=["Xi","PM'"]:
        raise ValueError("Manufacturer geometric dependency mutated")
    if mand.get("facad_PM_prime_equals_anatomical_PM_in_general") is not False:
        raise ValueError("Untrue PM-prime direct alias")
    if mand.get("digital_crown_direct_alias_allowed") is not False:
        raise ValueError("Unverified geometry promoted to DC")
    if mand.get("atlas_secondary_text_printed_page")!=235 or mand.get("atlas_figure")!="13.28":
        raise ValueError("Wrong publisher-unaligned diagram locator")
    if len(d.get("separate_mismatches_unchanged",[]))!=4:
        raise ValueError("Residual discrepancies silently omitted")
    if any(row.get("status")!="OPEN" for row in d["separate_mismatches_unchanged"]):
        raise ValueError("Residual formula discrepancy improperly closed")
    if any(value is not False for value in d.get("gates",{}).values()):
        raise ValueError("Publication/parity/clinical gate falsely promoted")
    if "secondary chapter facsimile" not in compare_row["notes"].lower() and "Secondary chapter facsimile" not in compare_row["notes"]:
        raise ValueError("Atlas vs Facad corpus-length comparison not updated")
    if compare_row["research_classification"]!="LANDMARK_ENDPOINT_REVIEW":
        raise ValueError("Unverified Atlas->vendor mapping incorrectly classified")
    if "NOT_AUTHORITATIVE_EQUIVALENCE" not in mand["source_family_alignment"]:
        raise ValueError("Source candidate represented as confirmed")
    if facad["facad_constructions"]["PM'"]["refs"]!=["Xi","PM","A","Pog"]:
        raise ValueError("Official Facad CPH PM-prime source changed")
    if facad["resolutions"]["Mand len"]["dc"]["direct_alias_allowed"] is not False:
        raise ValueError("Manufacturer to DC alias incorrectly activated")
    if not all(x in report for x in (
        "publisher-issued full pages or tables",
        "first edition 2009",
        "secondary reproduction",
        "do not silently rewrite",
    )):
        raise ValueError("Source report downgraded safeguards or provenance")
    return len(tiers)

def get_row(path):
    with path.open("r",encoding="utf-8",newline="") as f:
        r=list(csv.DictReader(f))
    matches=[x for x in r if x.get("source_profile")=="ATLAS_2009_COMPLETE_33" and x.get("atlas_factor_ordinal")=="33"]
    if len(matches)!=1:raise ValueError("Unable to identify Atlas full factor 33 row")
    return matches[0]

def selftest(d,row,report,facad):
    assert verify(d,row,report,facad)==8
    cases=[
        ("FAKE_PUBLISHER_TABLE13_1",lambda x,r,t,f:x["book"].update(publisher_authenticated_table_13_1_available=True)),
        ("FAKE_PUBLISHER_TABLE13_2",lambda x,r,t,f:x["book"].update(publisher_authenticated_table_13_2_available=True)),
        ("FAKE_PRIMARY_FACSIMILE",lambda x,r,t,f:x["sources"][5].update(tier="PUBLISHER_AUTHENTICATED")),
        ("FAKE_PUBLISHER_ORIGINAL",lambda x,r,t,f:x["gates"].update(publisher_original_chapter_authenticated=True)),
        ("FORGED_DC_PM_ALIAS",lambda x,r,t,f:x["mandibular_body_length_hypothesis"].update(digital_crown_direct_alias_allowed=True)),
        ("SHRUNK_FACAD_INTERSECTION",lambda x,r,t,f:x["mandibular_body_length_hypothesis"].update(facad_PM_prime_refs=["Xi","PM"])),
        ("CLOSE_33_VS_32",lambda x,r,t,f:x["separate_mismatches_unchanged"][0].update(status="RESOLVED")),
        ("FORGED_CSV_CLASSIFICATION",lambda x,r,t,f:r.update(research_classification="SOURCE_LOCKED")),
        ("PROMOTE_PATIENT_PARITY",lambda x,r,t,f:x["gates"].update(facad_numerical_parity_certified=True)),
    ]
    for name,mutator in cases:
        dd,rr,tt,ff=map(copy.deepcopy,(d,row,report,facad))
        mutator(dd,rr,tt,ff)
        try: verify(dd,rr,tt,ff)
        except ValueError: print("NEGATIVE_TEST_PASS="+name)
        else: raise AssertionError("False clinical or source promotion accepted: "+name)
    print("ATLAS_SOURCE_AUTHORITY_SELFTEST_PASS=10")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--authority",type=Path,required=True)
    ap.add_argument("--crosswalk",type=Path,required=True)
    ap.add_argument("--vendor",type=Path,required=True)
    ap.add_argument("--report",type=Path,required=True)
    ap.add_argument("--self-test",action="store_true")
    a=ap.parse_args()
    evidence=json.loads(a.authority.read_text(encoding="utf-8"))
    row=get_row(a.crosswalk)
    facad=json.loads(a.vendor.read_text(encoding="utf-8"))
    report=a.report.read_text(encoding="utf-8")
    if a.self_test:selftest(evidence,row,report,facad)
    else:
        assert verify(evidence,row,report,facad)==8
        print("ATLAS2009_FIRST_EDITION_BIBLIOGRAPHIC_PROVENANCE=CONFIRMED")
        print("ATLAS2009_CHAPTER_13_1_13_2_PUBLISHER_ORIGINAL=NOT_AVAILABLE")
        print("ATLAS_XI_PM_EXTENDED_TO_A_POG=SECONDARY_FACSIMILE_CANDIDATE")
        print("FACAD_PM_PRIME_VENDOR_CPH=VERIFIED")
        print("FACAD_TO_DC_PM_PRIME_ALIAS_ALLOWED=false")
        print("UNRESOLVED_33_32_AND_12_13_COMPOSITION_CONFLICTS=OPEN")
        print("SHARED_APP_STORAGE_ISOLATION=UNVERIFIED")
        print("CLINICAL_PARITY_CERTIFIED=false")

if __name__=="__main__":
    main()
