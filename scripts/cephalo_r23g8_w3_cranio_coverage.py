"""R23-G8 W3: final 11 Atlas2009 cranio-mandibular source obligations.

Audit is a DESCRIPTOR check: never authorizes a patient value, Focus, diagnosis
or clinical release. Includes exact transitive CC/Gn and CF/PTV identities.
"""
from __future__ import annotations
import argparse
import ast
import json
import re
from pathlib import Path

from scripts.cephalo_r23g7_source_coverage import ROOT, PROTOCOL_ID
from scripts.cephalo_r23g8_w2_dental_coverage import build_w2_ledger

SOURCE = ROOT / "docs/audits/schemas/cephalo_r23g8_w3_atlas33_craniomandibular_dependencies_v1.json"
BACKEND = ROOT / "backend/services/cephalo_canonical_analysis_v2.py"
CONSTRUCTORS = ROOT / "backend/services/cephalo_canonical_constructions_v2.py"
XI = "RICKETTS_XI_RAMAL_RECTANGLE_R1_R4_FH_V1"
PTV = "RICKETTS_PTV_PR_POSTERIOR_PPF_PERP_FH_V1"
CF = "RICKETTS_CF_FH_PTV_INTERSECTION_V1"
GN = "RICKETTS_GN_CONSTRUCTED_NPOG_GOME_V1"
CC = "RICKETTS_CC_ATLAS2009_BAN_PTGN_INTERSECTION_V1"
MP = "RICKETTS_MANDIBULAR_PLANE_ANGLE_MENTON_V1"
CONSTRUCTIONS = {
    XI: ("RICKETTS_XI_CONSTRUCTION_ID",
         ("R1_Ricketts","R2_Ricketts","R3_Ricketts","R4_Ricketts","Po_anatomic","Or"),
         (XI,)),
    PTV: ("RICKETTS_PTV_CONSTRUCTION_ID",
          ("PR_Ricketts_PTV","Po_anatomic","Or"), (PTV,)),
    CF: ("RICKETTS_CF_CONSTRUCTION_ID",
         ("PR_Ricketts_PTV","Po_anatomic","Or"), (CF,PTV)),
    GN: ("RICKETTS_GN_CONSTRUCTION_ID",
         ("N","Pog_hard","Go","Me"), (GN,)),
    CC: ("RICKETTS_CC_ATLAS2009_CONSTRUCTION_ID",
         ("Ba","N","Pt_Ricketts","Pog_hard","Go","Me"), (CC,GN)),
    MP: ("RICKETTS_MANDIBULAR_PLANE_CONSTRUCTION_ID",
         ("MP_ANGLE_INFERIOR_Ricketts","Me"), (MP,)),
}
REQUIRED_TUPLES = {
    XI:"RICKETTS_XI_REQUIRED_LANDMARKS",
    PTV:"RICKETTS_PTV_REQUIRED_LANDMARKS",
    GN:"RICKETTS_GN_REQUIRED_LANDMARKS",
    MP:"RICKETTS_MANDIBULAR_PLANE_REQUIRED_LANDMARKS",
}
EXPECTED = {
    8: ("M_ORAL_GNOMON_ANS_XI_PM_DEG_V1", "RICKETTS_LOWER_FACIAL_HEIGHT_CANONICAL_DEG_V2",
        ("ANS","Pm_Ricketts"), (XI,), ("Pm_Ricketts",), False, "ricketts_lfh_ids"),
    21: ("M_RICKETTS_FACIAL_TAPER_NPOG_MP_DEG_V1", "RICKETTS_FACIAL_TAPER_CANONICAL_DEG_V2",
         ("N","Pog_hard"), (MP,), (), False, "ricketts_taper_ids"),
    23: ("M_RICKETTS_MAXILLARY_HEIGHT_NCFA_DEG_V1", "RICKETTS_MAXILLARY_HEIGHT_CANONICAL_DEG_V2",
         ("N","A"), (CF,), (), False, "ricketts_mx_height_ids"),
    25: ("M_RICKETTS_MANDIBULAR_PLANE_FH_DEG_V1", "RICKETTS_MANDIBULAR_PLANE_FH_CANONICAL_DEG_V2",
         ("Po_anatomic","Or","MP_ANGLE_INFERIOR_Ricketts","Me"), (MP,), (), False, "ricketts_mp_ids"),
    27: ("M_RICKETTS_ANTERIOR_CRANIAL_LENGTH_CC_N_MM_V1", "RICKETTS_ANTERIOR_CRANIAL_LENGTH_CANONICAL_MM_V2",
         ("N",), (CC,), (), True, "ricketts_acl_ids"),
    28: ("M_RICKETTS_POSTERIOR_FACIAL_HEIGHT_GO_CF_MM_V1", "RICKETTS_POSTERIOR_FACIAL_HEIGHT_CANONICAL_MM_V2",
         ("GO_Ricketts_PFH",), (CF,), ("GO_Ricketts_PFH",), True, "ricketts_pfh_ids"),
    29: ("M_RICKETTS_TOTAL_FACIAL_HEIGHT_BAN_XIPM_DEG_V1", "RICKETTS_TOTAL_FACIAL_HEIGHT_CANONICAL_DEG_V2",
         ("Ba","N","Pm_Ricketts"), (XI,), ("Pm_Ricketts",), False, "ricketts_tfh_ids"),
    30: ("M_RICKETTS_RAMUS_POSITION_FH_CFXI_DEG_V1", "RICKETTS_RAMUS_POSITION_CANONICAL_DEG_V2",
         ("Po_anatomic","Or"), (CF,XI), (), False, "ricketts_ramus_ids"),
    31: ("M_RICKETTS_PORION_LOCATION_PTV_MM_V1", "RICKETTS_PORION_LOCATION_CANONICAL_MM_V2",
         ("Po_anatomic",), (PTV,), (), True, "ricketts_porion_ids"),
    32: ("M_RICKETTS_MANDIBULAR_ARC_DCXI_XIPM_DEG_V1", "RICKETTS_MANDIBULAR_ARC_CANONICAL_DEG_V2",
         ("DC_Ricketts","Pm_Ricketts"), (XI,), ("DC_Ricketts","Pm_Ricketts"), False, "ricketts_arc_ids"),
    33: ("M_RICKETTS_CORPUS_LENGTH_XI_PM_MM_V1", "RICKETTS_CORPUS_LENGTH_CANONICAL_MM_V2",
         ("Pm_Ricketts",), (XI,), ("Pm_Ricketts",), True, "ricketts_corpus_ids"),
}


def _literal_assignment(source: str, identifier: str):
    # Exactly one literal tuple assignment (the backend names one tuple per
    # method). Extract the line, not a partial function body: parse only the
    # tuple AST; AST-parsing a cut-off block would be invalid by construction.
    match = re.search(
        r"\b" + re.escape(identifier) + r"\s*=\s*(\([^\n]*\))",
        source,
    )
    if match is None:
        raise ValueError("W3 missing canonical source tuple " + identifier)
    try:
        value = ast.literal_eval(match.group(1))
    except (ValueError, TypeError, SyntaxError):
        raise ValueError("W3 nonliteral canonical source tuple " + identifier) from None
    if not isinstance(value, tuple):
        raise ValueError("W3 source is not an explicit tuple " + identifier)
    return value

def build_w3_ledger() -> dict:
    previous = build_w2_ledger()
    doc = json.loads(SOURCE.read_text(encoding="utf-8"))
    atlas = json.loads((ROOT / doc["source_atlas"]).read_text(encoding="utf-8"))
    backend = BACKEND.read_text(encoding="utf-8")
    constructors = CONSTRUCTORS.read_text(encoding="utf-8")
    if (doc.get("protocol_id") != PROTOCOL_ID or
        doc.get("authority") != "SOURCE_CRANIOMANDIBULAR_OBLIGATIONS_PREVIEW_ONLY__NO_RUNTIME_AUTHORITY" or
        doc.get("clinical_release") is not False or
        doc.get("rule") != "DESCRIPTIONS_ONLY__NO_ACTIVE_VALUES_FOCUS_NOR_NORMS"):
        raise ValueError("W3 clinical authority or source protocol mismatch")
    source_rows = doc.get("measurements")
    if not isinstance(source_rows, list) or len(source_rows) != 11:
        raise ValueError("W3 must contain exactly 11 canonical rows")
    by_order = {r["source_order"]:r for r in source_rows}
    if set(by_order) != set(EXPECTED):
        raise ValueError("W3 source order duplicated, missing or aliased")
    atlas_rows = {r["order"]:r for r in atlas["measurements"]}
    if len(atlas_rows)!=33 or len(previous["rows"])!=33:
        raise ValueError("Atlas33 authority/cardinality drift")
    for order, spec in EXPECTED.items():
        mid, method, direct, deps, manual, calib, variable = spec
        row = by_order[order]
        original = atlas_rows[order]
        if (row["measurement_id"] != mid or original["measurement_id"] != mid or
            original["state"]!="CONDITIONAL_EXECUTABLE" or
            row["availability_gate"] != original["gate"] or
            row["method_id"] != method or
            row["backend_landmark_tuple_var"] != variable):
            raise ValueError(f"W3 Atlas source method/gate drift at {order}")
        if (tuple(row["required_landmarks"]) != direct or
            tuple(row["required_constructions"]) != deps or
            tuple(row["required_manual_landmarks"]) != manual or
            row["requires_calibration"] is not calib or
            row["requires_same_image_source"] is not True):
            raise ValueError(f"W3 canonical direct/manual/scale dependency mismatch at {order}")
        expected_upstream = {d:list(CONSTRUCTIONS[d][1]) for d in deps}
        expected_chains = {d:list(CONSTRUCTIONS[d][2]) for d in deps}
        if (row.get("construction_transitive_landmarks") != expected_upstream or
            row.get("construction_dependency_chain") != expected_chains):
            raise ValueError(f"W3 false transitive construction identities at {order}")
        # Manual identity in an INDIRECT construction must be displayed as
        # explicitly as a manual DIRECT measurement landmark. Prevent a
        # source list alone from being misread as an automatic coordinate.
        constructor_manual = {
            XI: ("R1_Ricketts","R2_Ricketts","R3_Ricketts","R4_Ricketts"),
            PTV: ("PR_Ricketts_PTV",),
            CF: ("PR_Ricketts_PTV",),
            CC: ("Pt_Ricketts",),
            MP: (),
        }
        manual_expected = {d:list(constructor_manual[d]) for d in deps}
        if row.get("construction_manual_landmarks") != manual_expected:
            raise ValueError(f"W3 transitive manual landmark authority drift at {order}")

        if not row["source_contracts"] or not all((ROOT / x).is_file() for x in row["source_contracts"]):
            raise ValueError("W3 canonical source file missing")
        # Exact backend variable's literal tuple, and correct canonical method
        # in the SAME body block; never infer source from similarly named IDs.
        start=backend.find(variable+"=")
        if start<0:
            raise ValueError("W3 backend source tuple not found: "+variable)
        end=backend.find('canonical_id="'+mid+'"',start)
        if end<0 or end-start>6000:
            raise ValueError(f"W3 backend method block not found at {order}")
        section=backend[start:end+len(mid)+35]
        if tuple(_literal_assignment(section,variable)) != direct:
            raise ValueError(f"W3 backend literal landmark identity drift at {order}")
        if 'method="'+method+'"' not in section:
            raise ValueError(f"W3 canonical backend method drift at {order}")
        if not all('constructions.get('+CONSTRUCTIONS[d][0]+')' in section for d in deps):
            raise ValueError(f"W3 backend construction retrieval missing at {order}")
        if manual and "LandmarkOrigin.MANUAL" not in section:
            raise ValueError(f"W3 runtime manual landmark gate lost at {order}")
        if calib and "_calibrated_px(" not in section:
            raise ValueError(f"W3 verified mm calibration gate lost at {order}")
        for d in deps:
            constant, upstream, chain = CONSTRUCTIONS[d]
            if (f'{constant} = "{d}"' not in constructors or
                d not in constructors):
                raise ValueError(f"W3 canonical constructor definition lost: {d}")
            if d in REQUIRED_TUPLES:
                if tuple(_literal_assignment(constructors,REQUIRED_TUPLES[d])) != upstream:
                    raise ValueError(f"W3 constructor upstream landmark drift: {d}")
        if CF in deps and ('cf_refs = list(ptv.landmark_refs)' not in constructors or
                           '"upstream_construction_id": ptv.construction_id' not in constructors):
            raise ValueError("W3 CF must depend on exact source PTV")
        if CC in deps and ('for landmark_id in ("Ba", "N", "Pt_Ricketts"):' not in constructors or
                           '"upstream_construction_id": construction.construction_id' not in constructors or
                           'landmark_id == "Pt_Ricketts"' not in constructors):
            raise ValueError("W3 CC must use manual Pt and constructed Gn")
        if order==29 and "RICKETTS_TOTAL_FACIAL_HEIGHT" not in section:
            raise ValueError("W3 Atlas factor29 dimensional conflict reintroduced")
    ids={r[0] for r in EXPECTED.values()}
    rows=[]
    for original in previous["rows"]:
        row=dict(original)
        if row["measurement_id"] in ids:
            if row["source_dependency_status"]!="HOLD_NO_PUBLISHED_FOCUS_DEPENDENCIES":
                raise ValueError("W3 overlaps previously published source contract")
            row["source_dependency_status"]="W3_CRANIOMANDIBULAR_OBLIGATION_PREVIEW_ONLY"
            row["declared_landmarks"]=list(next(v[2] for v in EXPECTED.values() if v[0]==row["measurement_id"]))
        row["active_runtime_focus_authorized"]=False
        row["clinical_value_authorized_by_this_ledger"]=False
        rows.append(row)
    keys=["LOT06_PUBLISHED_SOURCE_DEPENDENCIES","G7_ATLAS_SOURCE_PREVIEW_ONLY",
          "W1_ORIENTATION_OBLIGATION_PREVIEW_ONLY","W2_DENTAL_MANUAL_OBLIGATION_PREVIEW_ONLY",
          "W3_CRANIOMANDIBULAR_OBLIGATION_PREVIEW_ONLY","HOLD_NO_PUBLISHED_FOCUS_DEPENDENCIES"]
    counts={k:sum(row["source_dependency_status"]==k for row in rows) for k in keys}
    if list(counts.values()) != [8,3,4,7,11,0]:
        raise ValueError("W3 source descriptor ledger incomplete: "+str(counts))
    return {"schema_version":"CEPHALO_R23G8_W3_ATLAS33_SOURCE_COVERAGE_V1",
            "protocol_id":PROTOCOL_ID,"counts":counts,"rows":rows,
            "source_w3":str(SOURCE.relative_to(ROOT)),
            "clinical_release":False,"clinical_measurements_newly_authorized":0,
            "patient_source_goldset_verified":False,"independent_clinical_review":False,
            "caveat":"33/33 SOURCE DESCRIPTORS != 33 clinically validated measurements or runtime Focus."}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    data=build_w3_ledger()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("Atlas33 8 LOT06 + 3 G7 + 4 W1 + 7 W2 + 11 W3 source descriptions; 0 HOLD; CLINICAL NO-GO")


if __name__=="__main__":
    main()
