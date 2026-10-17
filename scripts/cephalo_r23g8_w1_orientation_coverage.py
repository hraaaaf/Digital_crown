"""R23-G8-W1 authoritative source-obligation coverage ledger; NO clinical unlocking.

The four orientation methods ALREADY EXIST in the canonical backend. This
audit locks identities and conditions against source contracts. Runtime values,
provenance, images and geometry must be separately verified by typed evidence.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path

from scripts.cephalo_r23g7_source_coverage import ROOT, PROTOCOL_ID, build_ledger as previous_ledger

W1_PATH = ROOT / "docs/audits/schemas/cephalo_r23g8_w1_atlas33_orientation_dependencies_v1.json"
BACKEND_PATH = ROOT / "backend/services/cephalo_canonical_analysis_v2.py"
CONSTRUCTIONS_PATH = ROOT / "backend/services/cephalo_canonical_constructions_v2.py"
EXPECTED = {
    4: ("M_RICKETTS_OVERBITE_FOP_MM_V1", "RICKETTS_OVERBITE_FOP_CANONICAL_MM_V2",
        ("U1_incisal", "L1_incisal"),
        ("RICKETTS_FUNCTIONAL_OCCLUSAL_PLANE_BICUSPID_MOLAR_V1",), True, ()),
    14: ("M_RICKETTS_OCCLUSAL_PLANE_XI_MM_V1", "RICKETTS_OCCLUSAL_PLANE_XI_CANONICAL_MM_V2",
        (), ("RICKETTS_FUNCTIONAL_OCCLUSAL_PLANE_BICUSPID_MOLAR_V1",
             "RICKETTS_XI_RAMAL_RECTANGLE_R1_R4_FH_V1"), True, ()),
    18: ("M_RICKETTS_COMMISSURE_FOP_MM_V1", "RICKETTS_COMMISSURE_FOP_CANONICAL_MM_V2",
        ("LABIAL_COMMISSURE_Ricketts",),
        ("RICKETTS_FUNCTIONAL_OCCLUSAL_PLANE_BICUSPID_MOLAR_V1",),
        True, ("LABIAL_COMMISSURE_Ricketts",)),
    24: ("M_RICKETTS_PALATAL_PLANE_FH_DEG_V1", "RICKETTS_PALATAL_PLANE_FH_CANONICAL_DEG_V2",
        ("Po_anatomic", "Or", "ANS", "PNS_Ricketts"), (),
        False, ("PNS_Ricketts",)),
}
SEGMENTS = {
    4: ("# #4 Overbite", "# #14 Occlusal plane to Xi", "overbite_ids"),
    14: ("# #14 Occlusal plane to Xi", "# #18 Labial commissure to FOP", "fop_xi_ids"),
    18: ("# #18 Labial commissure to FOP", "# #24 Palatal plane signed", "commissure_ids"),
    24: ("# #24 Palatal plane signed", "# Atlas/33 Wave B source-locked", "palatal_ids"),
}
CONSTRUCTION_CONSTS = {
    "RICKETTS_FUNCTIONAL_OCCLUSAL_PLANE_BICUSPID_MOLAR_V1":
        "RICKETTS_FUNCTIONAL_OCCLUSAL_PLANE_CONSTRUCTION_ID",
    "RICKETTS_XI_RAMAL_RECTANGLE_R1_R4_FH_V1": "RICKETTS_XI_CONSTRUCTION_ID",
}


def build_w1_ledger() -> dict:
    previous = previous_ledger()
    source = json.loads(W1_PATH.read_text(encoding="utf-8"))
    atlas = json.loads((ROOT / source["source_atlas"]).read_text(encoding="utf-8"))
    backend = BACKEND_PATH.read_text(encoding="utf-8")
    constructions = CONSTRUCTIONS_PATH.read_text(encoding="utf-8")
    if source["protocol_id"] != PROTOCOL_ID or source["authority"] != (
        "SOURCE_ORIENTATION_OBLIGATIONS_PREVIEW_ONLY__NOT_RUNTIME_MEASUREMENT_AUTHORITY"
    ):
        raise ValueError("W1 source authority / protocol mismatch")
    if source.get("rule") != "DESCRIPTIONS_ONLY__NO_ACTIVE_ORIENTATION_ASSERTION__NO_NUMERIC_OR_SVG_FOCUS_PROMOTION":
        raise ValueError("W1 cannot promote clinical runtime evidence")
    orientation = source.get("orientation_requirement", {})
    if orientation.get("model") != "ImageOrientationEvidence" or orientation.get("source_ref") != "exact_current_source_image_ref" or (
        orientation.get("active_evidence") != "required_not_inferred_from_screen_axes"
    ):
        raise ValueError("W1 must not infer anatomical axes")
    if len(source.get("measurements", [])) != 4:
        raise ValueError("W1 precisely four source factors required")
    by_order = {row["source_order"]: row for row in source["measurements"]}
    if set(by_order) != set(EXPECTED):
        raise ValueError("W1 duplicated/missing or unexpected source factor")
    atlas_by_order = {row["order"]: row for row in atlas["measurements"]}
    if len(atlas_by_order) != 33:
        raise ValueError("Original source Atlas33 drift")
    if 'image_orientation.source_image_ref != source_ref' not in backend or (
        'image_orientation.availability_status != AvailabilityStatus.AVAILABLE' not in backend
    ):
        raise ValueError("Runtime orientation fail-closed source gate missing")
    for index, expected in EXPECTED.items():
        row = by_order[index]
        mid, method, landmarks, constructs, calib, manual = expected
        a = atlas_by_order[index]
        if row["measurement_id"] != mid or a["measurement_id"] != mid or (
            a["state"] != "CONDITIONAL_EXECUTABLE"
        ):
            raise ValueError("W1 Atlas exact measurement drift")
        if row["method_id"] != method or row["availability_gate"] != a["gate"] or (
            a["gate"] != "VERSIONED_IMAGE_ORIENTATION_EVIDENCE_REQUIRED"
        ):
            raise ValueError("W1 original Atlas gate/method drift")
        if tuple(row["required_landmarks"]) != landmarks or tuple(row["required_constructions"]) != constructs or (
            row["requires_calibration"] is not calib
        ) or tuple(row["required_manual_landmarks"]) != manual or (
            row["requires_same_image_orientation"] is not True
        ):
            raise ValueError("W1 explicit anatomical and orientation identity drift")
        if not all((ROOT / src).is_file() for src in row["source_contracts"]):
            raise ValueError("W1 referenced source file missing")
        start, stop, variable = SEGMENTS[index]
        if start not in backend or stop not in backend:
            raise ValueError("W1 backend source segment not found")
        segment = backend.split(start, 1)[1].split(stop, 1)[0]
        # Exact function's method + ID must occur in the same source block.
        if f'method="{method}"' not in segment or f'canonical_id="{mid}"' not in segment:
            raise ValueError("W1 method/canonical source bridge mismatch")
        m = re.search(r'\b' + variable + r'\s*=\s*(\([^\n]*\))', segment)
        if m is None or tuple(ast.literal_eval(m.group(1))) != landmarks:
            raise ValueError("W1 implementation landmark tuple mismatch")
        for const_id in constructs:
            const_name = CONSTRUCTION_CONSTS[const_id]
            if f'{const_name} = "{const_id}"' not in constructions or (
                f'constructions.get({const_name})' not in segment
            ):
                raise ValueError("W1 source-locked construction missing")
        if '_orientation_for_source(' not in segment:
            raise ValueError("W1 backend missing same-image orientation gate")
        if calib and '_calibrated_px(' not in segment:
            raise ValueError("W1 backend calibrated length gate missing")
        for required_manual in manual:
            if required_manual not in segment or "LandmarkOrigin.MANUAL" not in segment:
                raise ValueError("W1 manual verification gate missing: " + required_manual)

    entries = []
    for row in previous["rows"]:
        updated = dict(row)
        if row["measurement_id"] in {x[0] for x in EXPECTED.values()}:
            updated["source_dependency_status"] = "W1_ORIENTATION_OBLIGATION_PREVIEW_ONLY"
            updated["declared_landmarks"] = list(next(
                x[2] for x in EXPECTED.values() if x[0] == row["measurement_id"]
            ))
        updated["active_runtime_focus_authorized"] = False
        updated["clinical_value_authorized_by_this_ledger"] = False
        entries.append(updated)
    counts = {status: sum(r["source_dependency_status"] == status for r in entries) for status in (
        "LOT06_PUBLISHED_SOURCE_DEPENDENCIES", "G7_ATLAS_SOURCE_PREVIEW_ONLY",
        "W1_ORIENTATION_OBLIGATION_PREVIEW_ONLY", "HOLD_NO_PUBLISHED_FOCUS_DEPENDENCIES"
    )}
    if list(counts.values()) != [8, 3, 4, 18]:
        raise ValueError("W1 source coverage cardinality changed: " + str(counts))
    return {
        "schema_version": "CEPHALO_R23G8_W1_ORIENTATION_COVERAGE_LEDGER_V1",
        "protocol_id": PROTOCOL_ID, "counts": counts, "rows": entries,
        "orientation_clinical_evidence_verified": False,
        "clinical_release": False,
        "source_w1": str(W1_PATH.relative_to(ROOT)),
        "limitation": "Source dependencies only; no active orientation validation, no Focus, no clinical value.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = build_w1_ledger()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("W1 orientation source obligations: 8 LOT06 + 3 G7 + 4 W1 preview + 18 HOLD; clinical_release=false")


if __name__ == "__main__":
    main()
