#!/usr/bin/env python3
"""D3E.21: lock the existing Robert UI display. NEVER computes real FACAD/DC parity."""
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
MATRIX=ROOT/"docs/audits/FACAD_314_D3E21_ROBERT_DISPLAY_MATRIX.json"
REFERENCE=ROOT/"docs/audits/FACAD_314_ROBERT_DIRECT_PARITY_BASELINE_2026-10-08.md"
FIXED=json.loads(r'''{"schema":"FACAD_314_D3E21_UI_ROBERT_SOURCE_ONLY_V1","phase":"SOURCE_ONLY_NO_PARITY","reference_commit":"565d3767c2218c8820424e88ab6e936cfae4241d","source_document":"docs/audits/FACAD_314_ROBERT_DIRECT_PARITY_BASELINE_2026-10-08.md","source_run_id":37841266986,"source_kind":"HISTORIC_UIA_SCREEN_ONLY_NOT_DIRECT_EXPORT","facad_profile":"Bergen short","case_alias":"ROBERT_EXAMPLE_QUICK_DEMO","comparator_mode":"NO_SAME_TRACE_COMPARISON"}''')
UNPROVEN=set(["license_verified","source_integrity_verified","offline_activation_verified","native_guest_isolation_verified","host_guest_management_isolated_verified","minimal_egress_approved","independent_privacy_review","independent_science_review","same_trace_dc_verified","dc_calibration_verified","construction_equivalence_verified","direct_numeric_export_verified","clinical_edit_allowed","real_ilexis_writer_proven","shared_app_storage_isolation_verified","converged","native_execution_authorized"])
DISPLAY=[
 ("SNA","67,7","degree","M_SNA_DEG_V1"),
 ("SNB","78,4","degree","M_SNB_DEG_V1"),
 ("ANB","-10,7","degree","M_ANB_DEG_V1"),
 ("SNPog","80,8","degree",None),
 ("NSBa","126,8","degree",None),
 ("ML/NSL","33,9","degree",None),
 ("NL/NSL","4,5","degree",None),
 ("ML/NL","29,4","degree",None),
 ("InterIncisal","140,9","degree","M_INTERINCISAL_DEG_V1"),
 ("ILs/NSL","100,1","degree",None),
 ("ILi/ML","85,1","degree","M_IMPA_GOME_DEG_V1"),
 ("Pog-NB","4,7","mm","M_POG_NB_MM_V1"),
]
ROW_KEYS={"name","value","unit","dc_candidate","identity_status","parity_status"}
class SourceBlocked(ValueError): pass

def unique(pairs):
    result={}
    for key,value in pairs:
        if key in result: raise SourceBlocked("DUPLICATE_KEY")
        result[key]=value
    return result

def check(data):
    if not isinstance(data,dict) or set(data)!=set(FIXED)|UNPROVEN|{"rows"}:
        raise SourceBlocked("SCHEMA_INVALID")
    for key,expected in FIXED.items():
        if type(data[key]) is not type(expected) or data[key]!=expected:
            raise SourceBlocked("SOURCE_PROVENANCE_FORGED")
    if any(data[key] is not False for key in UNPROVEN):
        raise SourceBlocked("UNPROVEN_PROMOTED")
    rows=data["rows"]
    if not isinstance(rows,list) or len(rows)!=len(DISPLAY):
        raise SourceBlocked("MEASUREMENT_ROWS_INCOMPLETE")
    for row,expected in zip(rows,DISPLAY):
        if not isinstance(row,dict) or set(row)!=ROW_KEYS:
            raise SourceBlocked("ROW_SCHEMA_INVALID")
        for key,value in zip(("name","value","unit","dc_candidate"),expected):
            if type(row[key]) is not type(value) or row[key]!=value:
                raise SourceBlocked("UI_VALUE_OR_CANDIDATE_FORGED")
        if row["identity_status"]!="CANDIDATE_ONLY" or row["parity_status"]!="NOT_COMPARABLE":
            raise SourceBlocked("PARITY_FABRICATED")
    nums={r["name"]:Decimal(r["value"].replace(",",".")) for r in rows}
    if nums["SNA"]-nums["SNB"]!=nums["ANB"]:
        raise SourceBlocked("DISPLAY_ARITHMETIC_INVALID")
    return {"count":len(rows),"direct_comparisons":0,"verdict":"D3E21_HISTORIC_UI_LOCKED_PARITY_UNPROVEN"}

def verify_historic_source(source, rows):
    """Verify UI rows from the archival table, independently of the JSON copy."""
    start=source.find("## 2. Données de mesure relevées")
    end=source.find("## 3.",start+1) if start>=0 else -1
    if start<0 or end<start: raise SourceBlocked("REFERENCE_TABLE_MISSING")
    found={}
    expected={r[0] for r in DISPLAY}
    for line in source[start:end].splitlines():
        if not line.startswith("|"): continue
        cells=[part.strip() for part in line.strip().strip("|").split("|")]
        if len(cells)<4: continue
        name,value=cells[0],cells[1].replace("−","-")
        if name in expected:
            if name in found: raise SourceBlocked("DUPLICATE_HISTORIC_MEASUREMENT")
            found[name]=value
    if set(found)!={row["name"] for row in rows}: raise SourceBlocked("HISTORIC_ROWS_MISSING")
    for row in rows:
        if found[row["name"]]!=row["value"]: raise SourceBlocked("HISTORIC_VALUE_MISMATCH")
    return True

def synthetic_compare(left,right,unit1,unit2,tolerance,origin):
    """No patient/export inputs. This function is for synthetic arithmetic tests only."""
    if origin!="SYNTHETIC_ONLY": raise SourceBlocked("REAL_INPUT_NOT_SUPPORTED")
    if unit1 not in ("degree","mm") or unit2 not in ("degree","mm"):
        raise SourceBlocked("INVALID_UNIT")
    try:
        if any(type(x) is not str for x in (left,right,tolerance)):
            raise SourceBlocked("STRINGS_REQUIRED")
        a,b,t=map(Decimal,(left,right,tolerance))
    except InvalidOperation as exc:
        raise SourceBlocked("INVALID_NUMBER") from exc
    if not all(v.is_finite() for v in (a,b,t)) or t<0 or t>1:
        raise SourceBlocked("INVALID_TOLERANCE_OR_NUMBER")
    if unit1!=unit2: return "SYNTHETIC_NOT_COMPARABLE"
    return "SYNTHETIC_MATCH" if abs(a-b)<=t else "SYNTHETIC_DIFFERENT"

def main():
    try:
        if not REFERENCE.is_file() or REFERENCE.is_symlink():
            raise SourceBlocked("HISTORIC_SOURCE_MISSING")
        source=REFERENCE.read_text(encoding="utf-8")
        if "Bergen short" not in source or "PARITÉ CLINIQUE NON VALIDÉE" not in source:
            raise SourceBlocked("HISTORIC_SOURCE_SCOPE_CHANGED")
        if not MATRIX.is_file() or MATRIX.is_symlink() or MATRIX.stat().st_size>12000:
            raise SourceBlocked("MATRIX_MISSING_OR_UNSAFE")
        raw=MATRIX.read_bytes()
        if raw.startswith(bytes([239,187,191])) or bytes([0]) in raw:
            raise SourceBlocked("ENCODING_INVALID")
        matrix=json.loads(raw.decode("utf-8"),object_pairs_hook=unique)
        result=check(matrix)
        verify_historic_source(source,matrix["rows"])
        print("D3E21_VERDICT="+result["verdict"])
        print("D3E21_OBSERVED_UI_ROWS="+str(result["count"]))
        print("D3E21_SAME_TRACE_COMPARISONS=0")
        return 0
    except (SourceBlocked,OSError,UnicodeError,TypeError,ValueError,KeyError):
        print("D3E21_VERDICT=BLOCKED_SOURCE_CHANGED_OR_UNTRUSTED")
        return 2
    finally:
        print("D3E21_SOURCE_ONLY=true")
        print("D3E21_NATIVE_VM_RUN=false")
        print("D3E21_FACAD_EXECUTED=false")
        print("D3E21_DIRECT_PARITY_PROVEN=false")
        print("FAC03_D3=OPEN_RED")
        print("SHARED_APP_STORAGE_ISOLATION=UNVERIFIED")
        print("CLINICAL_EDIT_ALLOWED=false")
        print("CONVERGED=false")

if __name__=="__main__":
    raise SystemExit(main())
