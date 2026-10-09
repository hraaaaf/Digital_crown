#!/usr/bin/env python3
"""Verify manufacturer CPH geometry lineage against exact PDF label evidence.

Research-only: validates source identities and dimensions; never patient parity.
"""
from __future__ import annotations
import argparse
import copy
import csv
import json
from pathlib import Path

def get_row(path, name):
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        rows=[r for r in csv.DictReader(f) if r.get("Ceph name")==name]
    if len(rows)!=1:
        raise ValueError("Missing or duplicate vendor ceph measurement "+name)
    return rows[0]

def verify(ptv,final,manual,ui13,ui32):
    p=ptv["facad_constructions"]
    must={
        "FH":("Line",["P","Or"]),
        "PtV":("Normal",["FH","Pt"]),
        "CF":("Inter2ln",["FH","PtV"]),
        "Xi":("Intersect",["R23","R14","R13","R24"]),
    }
    for name,(kind,refs) in must.items():
        if p[name]["calc_type"]!=kind or p[name]["refs"]!=refs:
            raise ValueError("Source-locked vendor geometry chain drift: "+name)
    if final["facad_constructions"]["PM'"]["calc_type"]!="Intersect":
        raise ValueError("PM prime construction changed")
    if final["facad_constructions"]["PM'"]["refs"]!=["Xi","PM","A","Pog"]:
        raise ValueError("PM prime endpoint substituted")
    for name,record in final["resolutions"].items():
        if name=="Mand len":
            if record["facad"]["calc_type"]!="Dist2p" or record["facad"]["refs"]!=["Xi","PM'"]:
                raise ValueError("Vendor Mand len distance geometry mismatch")
            if record["dc"]["direct_alias_allowed"] is not False:
                raise ValueError("Unverified Xi-PM' to Xi-Pm clinical alias")
    pfh=ptv["resolutions"]["PFH"]
    if pfh["facad"]["calc_type"]!="Dist2p" or pfh["facad"]["refs"]!=["CF","Go"]:
        raise ValueError("Vendor posterior facial height is no longer a distance")
    if pfh["facad"]["norm"]!="63±3.5" or pfh["dc"]["direct_alias_allowed"] is not False:
        raise ValueError("Vendor norm or identity gate unexpectedly altered")
    for row in (ui13["PFH"],ui32["PFH"]):
        if [row["Type"],row["Arg 1"],row["Arg 2"],row["Norm"]]!=["Dist2p","CF","Go","63±3.5"]:
            raise ValueError("Vendor PFH measurement semantics altered")
    if [ui13["InterIncisal"][x] for x in ("Type","Arg 1","Arg 2","Arg 3","Arg 4","Norm")]!=[
        "Angle4p","Iia","Ii","Isa","Is","130±10"]:
        raise ValueError("Vendor interincisal angle semantics altered")
    if manual["schema"]!="FACAD_F01_13_CORRECTED_WHOLE_TOKEN_PDF_SNIPPET_LOCK_V1":
        raise ValueError("Unverified original source context lock")
    names={x["name"]:x for x in manual["targets"]}
    if len(names)!=3 or not manual["boundary"]["xi_verified_entry_page_2"]:
        raise ValueError("Manufacturer glossary identity not confirmed")
    if manual["boundary"]["xi_word_at_page_1"] is not False:
        raise ValueError("Manufacturer Xi substring false positive promoted")
    library=next(x for k,x in names.items() if k.startswith("C01_"))
    labels={x["term"]:x for x in library["terms"]}
    for name,page in (("PtV",1),("CF",2),("Xi",2)):
        if labels[name]["page"]!=page:
            raise ValueError("Wrong original vendor technical dictionary page")
        if not labels[name]["context"].startswith(name+" "):
            raise ValueError("Non-lexical word token (Maxillary contamination)")
    short=names["Ricketts (13 F).pdf"]
    snippets={x["term"]:x for x in short["terms"]}
    if not snippets["PFH"]["context"].startswith("PFH The distance") or not snippets["InterIncisal"]["context"].startswith("InterIncisal The angle"):
        raise ValueError("Vendor manufacturer wording not corroborated")
    for key in ("atlas_2009_original_tables_verified","facad_dc_numeric_parity_verified","clinical_edit_allowed"):
        if manual["boundary"][key] is not False:
            raise ValueError("Prohibited clinical/publisher promotion")
    return 7

def self_test(ptv,final,manual,u13,u32):
    assert verify(ptv,final,manual,u13,u32)==7
    changes=[
        ("PTV_WRONG_DIRECTION",lambda p,f,m,a,b:p["facad_constructions"]["PtV"].update(calc_type="Line")),
        ("CF_WRONG_DEPENDENCY",lambda p,f,m,a,b:p["facad_constructions"]["CF"].update(refs=["FH","N"])),
        ("XI_INVALID_CORNERS",lambda p,f,m,a,b:p["facad_constructions"]["Xi"].update(refs=["Xi","PM"])),
        ("PM_PRIME_COLLAPSE",lambda p,f,m,a,b:f["facad_constructions"]["PM'"].update(refs=["Xi","PM"])),
        ("FORGED_DIRECT_ALIAS",lambda p,f,m,a,b:p["resolutions"]["PFH"]["dc"].update(direct_alias_allowed=True)),
        ("FORGED_ANGLE_PFH",lambda p,f,m,a,b:a["PFH"].update(Type="Angle4p")),
        ("FORGED_INTERINCISAL_DISTANCE",lambda p,f,m,a,b:a["InterIncisal"].update(Type="Dist2p")),
        ("XI_SUBSTRING_FALSE_POSITIVE",lambda p,f,m,a,b:m["boundary"].update(xi_word_at_page_1=True)),
        ("FORGED_ATLAS_AUTHORITY",lambda p,f,m,a,b:m["boundary"].update(atlas_2009_original_tables_verified=True)),
    ]
    for label,fn in changes:
        p,f,m,a,b=map(copy.deepcopy,(ptv,final,manual,u13,u32))
        fn(p,f,m,a,b)
        try: verify(p,f,m,a,b)
        except ValueError: print("NEGATIVE_TEST_PASS="+label)
        else: raise AssertionError("Invalid source falsely accepted: "+label)
    print("FACAD_CONSTRUCTION_CHAIN_TESTS_PASS=10")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--ptv",type=Path,required=True)
    ap.add_argument("--final-seven",type=Path,required=True)
    ap.add_argument("--manual",type=Path,required=True)
    ap.add_argument("--ricketts13",type=Path,required=True)
    ap.add_argument("--ricketts32",type=Path,required=True)
    ap.add_argument("--self-test",action="store_true")
    a=ap.parse_args()
    ptv=json.loads(a.ptv.read_text(encoding="utf-8"))
    final=json.loads(a.final_seven.read_text(encoding="utf-8"))
    manual=json.loads(a.manual.read_text(encoding="utf-8"))
    ui13={name:get_row(a.ricketts13,name) for name in ("PFH","InterIncisal")}
    ui32={"PFH":get_row(a.ricketts32,"PFH")}
    if a.self_test:self_test(ptv,final,manual,ui13,ui32)
    else:
        assert verify(ptv,final,manual,ui13,ui32)==7
        print("FACAD_VENDOR_FH_PTV_CF_XI_PMPRIME_CHAIN_SOURCE_LOCK=PASS")
        print("FACAD_VENDOR_PFH_DIMENSION=LINEAR_DIST2P_CF_GO")
        print("FACAD_VENDOR_INTERINCISAL_DIMENSION=ANGLE4P")
        print("VENDOR_GLOSSARY_XI_CF_WHOLE_TOKEN_PDF_PAGE=2")
        print("NO_DIRECT_FACAD_DC_ALIAS=true")
        print("CLINICAL_PARITY_NOT_TESTED=true")
if __name__=="__main__":
    main()
