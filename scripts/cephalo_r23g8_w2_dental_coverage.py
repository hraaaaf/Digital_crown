"""R23-G8 W2 source-backed obligations: seven dental/manual Atlas33 rows ONLY.

No patient data, formula, numerical values, diagnostic norms or SVG Focus.
Upstream verified source chain retains sole clinical authority.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path

from scripts.cephalo_r23g7_source_coverage import ROOT, PROTOCOL_ID
from scripts.cephalo_r23g8_w1_orientation_coverage import build_w1_ledger

SOURCE = ROOT / "docs/audits/schemas/cephalo_r23g8_w2_atlas33_dental_manual_dependencies_v1.json"
BACKEND = ROOT / "backend/services/cephalo_canonical_analysis_v2.py"
CONSTRUCTIONS = ROOT / "backend/services/cephalo_canonical_constructions_v2.py"
FOP = "RICKETTS_FUNCTIONAL_OCCLUSAL_PLANE_BICUSPID_MOLAR_V1"
XI = "RICKETTS_XI_RAMAL_RECTANGLE_R1_R4_FH_V1"
PTV = "RICKETTS_PTV_PR_POSTERIOR_PPF_PERP_FH_V1"
EXPECTED = {
    1: ("M_RICKETTS_MOLAR_RELATION_FOP_MM_V1", "RICKETTS_MOLAR_RELATION_FOP_CANONICAL_MM_V2",
        ("L6_DISTAL_Ricketts", "U6_DISTAL_Ricketts"), (FOP,),
        ("L6_DISTAL_Ricketts", "U6_DISTAL_Ricketts"), True, ()),
    2: ("M_RICKETTS_CANINE_RELATION_FOP_MM_V1", "RICKETTS_CANINE_RELATION_FOP_CANONICAL_MM_V2",
        ("L3_CUSP_Ricketts", "U3_CUSP_Ricketts"), (FOP,),
        ("L3_CUSP_Ricketts", "U3_CUSP_Ricketts"), True, ()),
    3: ("M_RICKETTS_OVERJET_FOP_MM_V1", "RICKETTS_OVERJET_FOP_CANONICAL_MM_V2",
        ("L1_incisal", "U1_incisal"), (FOP,), (), True, ()),
    5: ("M_RICKETTS_L1_OCCLUSAL_EXTRUSION_MM_V1", "RICKETTS_L1_OCCLUSAL_EXTRUSION_CANONICAL_MM_V2",
        ("L1_incisal", "L1_apex"), (FOP,), (), True, ()),
    9: ("M_U6_PTV_MM_V1", "RICKETTS_U6_PTV_CANONICAL_MM_V2",
        ("U6_DISTAL_Ricketts",), (PTV,), ("U6_DISTAL_Ricketts",), True, ("PR_Ricketts_PTV",)),
    15: ("M_RICKETTS_OCCLUSAL_PLANE_XIPM_DEG_V1", "RICKETTS_OCCLUSAL_PLANE_XIPM_CANONICAL_DEG_V2",
         ("Pm_Ricketts",), (FOP, XI), ("Pm_Ricketts",), False,
         ("R1_Ricketts", "R2_Ricketts", "R3_Ricketts", "R4_Ricketts")),
    17: ("M_RICKETTS_UPPER_LIP_LENGTH_ANS_COMMISSURE_MM_V1",
         "RICKETTS_UPPER_LIP_LENGTH_CANONICAL_MM_V2",
         ("ANS", "LABIAL_COMMISSURE_Ricketts"), (), ("LABIAL_COMMISSURE_Ricketts",), True, ()),
}
METHOD_BLOCKS = {
    5: ("ricketts_extrusion_ids=", "facial_axis_ids=", "ricketts_extrusion_ids"),
    9: ("ricketts_u6_ids=", "def convexity():", "ricketts_u6_ids"),
    15: ("ricketts_op_inclination_ids=", "ricketts_lip_ids=", "ricketts_op_inclination_ids"),
    17: ("ricketts_lip_ids=", "ricketts_taper_ids=", "ricketts_lip_ids"),
}
CONSTS = {
    FOP: "RICKETTS_FUNCTIONAL_OCCLUSAL_PLANE_CONSTRUCTION_ID",
    XI: "RICKETTS_XI_CONSTRUCTION_ID",
    PTV: "RICKETTS_PTV_CONSTRUCTION_ID",
}


def build_w2_ledger() -> dict:
    base = build_w1_ledger()
    doc = json.loads(SOURCE.read_text(encoding="utf-8"))
    atlas = json.loads((ROOT / doc["source_atlas"]).read_text(encoding="utf-8"))
    backend = BACKEND.read_text(encoding="utf-8")
    constructions = CONSTRUCTIONS.read_text(encoding="utf-8")
    if (doc.get("protocol_id") != PROTOCOL_ID or
        doc.get("authority") != "SOURCE_DENTAL_MANUAL_OBLIGATIONS_PREVIEW_ONLY__NO_MEASUREMENT_AUTHORITY" or
        doc.get("rule") != "MUST_USE_TYPED_CURRENT_SOURCE_EVIDENCE__NO_INFERRED_FOCUS_OR_VALUES"):
        raise ValueError("W2 preview source authority mismatch")
    rows = doc.get("measurements")
    if not isinstance(rows, list) or len(rows) != 7:
        raise ValueError("W2 exact seven dental source rows required")
    indexed = {row["source_order"]: row for row in rows}
    if set(indexed) != set(EXPECTED):
        raise ValueError("W2 missing/duplicate/extra factor")
    atlas_rows = {row["order"]: row for row in atlas["measurements"]}
    if len(atlas_rows) != 33 or len(base["rows"]) != 33:
        raise ValueError("W2 Atlas base has drifted")
    for order, spec in EXPECTED.items():
        mid, method, direct, cons, manual, calibration, indirect = spec
        row = indexed[order]
        source = atlas_rows[order]
        if (source["measurement_id"] != mid or source["state"] != "CONDITIONAL_EXECUTABLE" or
            row["measurement_id"] != mid or row["method_id"] != method or
            row["availability_gate"] != source["gate"]):
            raise ValueError(f"W2 Atlas source/method identity mismatch at {order}")
        if (tuple(row["required_landmarks"]) != direct or
            tuple(row["required_constructions"]) != cons or
            tuple(row["required_manual_landmarks"]) != manual or
            tuple(row["indirect_construction_manual_landmarks"]) != indirect or
            row["requires_calibration"] is not calibration or
            row["requires_same_image_source"] is not True):
            raise ValueError(f"W2 canonical manual/dental identities drift: {order}")
        if not row["source_contracts"] or not all((ROOT / x).is_file() for x in row["source_contracts"]):
            raise ValueError("W2 source documents missing")
        if order in (1, 2, 3):
            call = re.search(
                r'_fop_projection_measure\(\s*name="[^"]+"\s*,\s*method="' +
                re.escape(method) + r'"\s*,\s*canonical_id="' + re.escape(mid) +
                r'"\s*,\s*first_id="([^"]+)"\s*,\s*second_id="([^"]+)"\s*,\s*require_manual=(True|False)',
                backend,
            )
            if call is None or (call.group(1),call.group(2)) != direct or (
                (call.group(3)=="True") != (len(manual)>0)
            ):
                raise ValueError(f"W2 source-backed FOP call mismatch at {order}")
            segment = backend.split("def _fop_projection_measure(", 1)[1].split(
                "_fop_projection_measure(\n        name=", 1)[0]
        else:
            start, end, varname = METHOD_BLOCKS[order]
            if start not in backend or end not in backend:
                raise ValueError("W2 canonical method block missing")
            segment = backend.split(start, 1)[1].split(end, 1)[0]
            m = re.search(r'\b' + re.escape(varname) + r'\s*=\s*(\([^\n]*\))',
                          start + segment)
            if m is None or tuple(ast.literal_eval(m.group(1))) != direct:
                raise ValueError(f"W2 backend required landmark tuple mismatch at {order}")
            if f'method="{method}"' not in segment or f'canonical_id="{mid}"' not in segment:
                raise ValueError(f"W2 canonical method bridge drift at {order}")
        if not all(f'{CONSTS[c]} = "{c}"' in constructions for c in cons):
            raise ValueError(f"W2 canonical construction identifier drift at {order}")
        if calibration and '_calibrated_px(' not in segment:
            raise ValueError(f"W2 millimetric calibration enforcement missing at {order}")
        if cons and not all(f'constructions.get({CONSTS[c]})' in segment for c in cons):
            raise ValueError(f"W2 required construction missing at {order}")
        if manual and 'LandmarkOrigin.MANUAL' not in segment:
            raise ValueError(f"W2 manual source gate missing at {order}")
        if order == 9 and not all(x in constructions for x in indirect):
            raise ValueError("W2 Ricketts PTV manual PR source missing")
        if order == 15 and not all(x in constructions for x in indirect):
            raise ValueError("W2 Ricketts Xi manual R1-R4 source missing")
        if order == 17:
            # Lip segment relies on _deps for exact same-image ANS/commissure
            # rather than repeating source_image_ref in its body.
            if "_deps(landmarks,ricketts_lip_ids)" not in segment or (
                "if len({x.source_image_ref for x in present})!=1:" not in backend
            ):
                raise ValueError("W2 upper-lip exact image source gate missing")
        elif "source_image_ref" not in segment:
            raise ValueError(f"W2 source-image match enforcement missing at {order}")

    w2_ids={v[0] for v in EXPECTED.values()}
    results=[]
    for old in base["rows"]:
        item=dict(old)
        if item["measurement_id"] in w2_ids:
            if item["source_dependency_status"]!="HOLD_NO_PUBLISHED_FOCUS_DEPENDENCIES":
                raise ValueError("W2 contract overlaps prior Focus published source")
            item["source_dependency_status"]="W2_DENTAL_MANUAL_OBLIGATION_PREVIEW_ONLY"
            item["declared_landmarks"]=list(next(v[2] for v in EXPECTED.values()
                                                  if v[0]==item["measurement_id"]))
        item["active_runtime_focus_authorized"]=False
        item["clinical_value_authorized_by_this_ledger"]=False
        results.append(item)
    keys=["LOT06_PUBLISHED_SOURCE_DEPENDENCIES","G7_ATLAS_SOURCE_PREVIEW_ONLY",
          "W1_ORIENTATION_OBLIGATION_PREVIEW_ONLY","W2_DENTAL_MANUAL_OBLIGATION_PREVIEW_ONLY",
          "HOLD_NO_PUBLISHED_FOCUS_DEPENDENCIES"]
    counts={key:sum(x["source_dependency_status"]==key for x in results) for key in keys}
    if list(counts.values()) != [8,3,4,7,11]:
        raise ValueError("W2 Atlas33 source counts drift: "+str(counts))
    return {"schema_version":"CEPHALO_R23G8_W2_ATLAS33_SOURCE_COVERAGE_V1",
            "protocol_id":PROTOCOL_ID,"counts":counts,"rows":results,
            "clinical_release":False,"manual_patient_evidence_verified":False,
            "source_w2":str(SOURCE.relative_to(ROOT)),
            "caveat":"Source documentation only; NO numeric Focus, clinical measure, diagnosis or patient origin authority."}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args=parser.parse_args()
    audit=build_w2_ledger()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(audit,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("Atlas33 W2: 8 LOT06 + 3 G7 + 4 W1 + 7 W2 previews + 11 HOLD; clinical_release=false")


if __name__=="__main__":
    main()
