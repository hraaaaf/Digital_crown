"""R23-G7: source-derived Atlas 33 dependency ledger, never clinical authorization.

Generated rows are evidence inventory only; no diagnostic calculation or Focus
is activated. Contract drift fails closed, including source landmark identity.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ATLAS_PATH = ROOT / "backend/data/cephalometry/ricketts_atlas2009_complete33_protocol_profile_v1.json"
G7_PATH = ROOT / "docs/audits/schemas/cephalo_r23g7_atlas33_source_dependencies_v1.json"
LOT06_PATH = ROOT / "frontend/src/features/ortho/cephaloLot06FocusRegistry.generated.ts"
IMPLEMENTATION_PATH = ROOT / "backend/services/cephalo_canonical_analysis_v2.py"
PROTOCOL_ID = "RICKETTS_ATLAS_2009_COMPLETE_33_PROTOCOL_V1"
EXPECTED_NEW = {
    "M_RICKETTS_U1_APOG_PROTRUSION_MM_V1": (
        "U1_incisal", "A", "Pog_hard", "Po_anatomic", "Or"
    ),
    "M_RICKETTS_U1_APOG_INCLINATION_DEG_V1": (
        "U1_incisal", "U1_apex", "A", "Pog_hard"
    ),
    "M_RICKETTS_CRANIAL_DEFLECTION_FH_BAN_DEG_V1": (
        "Po_anatomic", "Or", "Ba", "N"
    ),
}


def build_ledger() -> dict:
    atlas = json.loads(ATLAS_PATH.read_text(encoding="utf-8"))
    g7 = json.loads(G7_PATH.read_text(encoding="utf-8"))
    lot06_ids = set(re.findall(
        r'^  "(M_[A-Z0-9_]+)": \{', LOT06_PATH.read_text(encoding="utf-8"), re.M
    ))
    implementation = IMPLEMENTATION_PATH.read_text(encoding="utf-8")
    if atlas.get("protocol_id") != PROTOCOL_ID or g7.get("protocol_id") != PROTOCOL_ID:
        raise ValueError("Source protocol identity mismatch")
    if g7.get("authority") != "SOURCE_DEPENDENCY_PREVIEW_ONLY__NOT_RUNTIME_MEASUREMENT_AUTHORITY":
        raise ValueError("G7 claims unauthorized clinical authority")
    atlas_rows = atlas.get("measurements")
    if not isinstance(atlas_rows, list) or len(atlas_rows) != 33:
        raise ValueError("Atlas 2009 exact 33 rows required")
    ids = [row["measurement_id"] for row in atlas_rows]
    if len(set(ids)) != 33 or [row["order"] for row in atlas_rows] != list(range(1, 34)):
        raise ValueError("Atlas order / canonical identity drift")
    if any(row["state"] not in {"EXECUTABLE", "CONDITIONAL_EXECUTABLE"} for row in atlas_rows):
        raise ValueError("Atlas runtime source-state drift")

    published = g7.get("measurements")
    if not isinstance(published, list) or len(published) != 3:
        raise ValueError("G7 explicitly source-backed three-row increment only")
    g7_by_id = {row["measurement_id"]: row for row in published}
    if set(g7_by_id) != set(EXPECTED_NEW):
        raise ValueError("Unexpected or duplicated G7 source preview")
    for mid, required in EXPECTED_NEW.items():
        row = g7_by_id[mid]
        source_row = atlas_rows[ids.index(mid)]
        if mid in lot06_ids or source_row["state"] != "EXECUTABLE":
            raise ValueError("G7 overlapping LOT06 or non-executable Atlas source")
        if row["source_order"] != source_row["order"]:
            raise ValueError("G7 Atlas source order mismatch")
        if tuple(row["required_landmarks"]) != required:
            raise ValueError("Canonical anatomical identities changed: " + mid)
        if len(set(required)) != len(required) or row["required_constructions"] != []:
            raise ValueError("G7 lacks independent geometry source-contract proof: " + mid)
        if source_row.get("gate") and row["availability_gate"] != source_row["gate"]:
            raise ValueError("G7 source gate mismatch: " + mid)
        if not row["source_contracts"] or not all((ROOT / file).is_file() for file in row["source_contracts"]):
            raise ValueError("Missing local source contract file: " + mid)
        # The executable canonical backend names these EXACT manual/anatomic
        # sources after the identifier. No aliases, inferred primitives, or
        # generic sella/pogonion alternatives are permitted.
        match = re.search(r'"' + re.escape(mid) + r'"\s*,\s*(\([^)]*\))', implementation)
        if not match or ast.literal_eval(match.group(1)) != required:
            raise ValueError("Executable backend landmark signature does not match: " + mid)

    rows = []
    for row in atlas_rows:
        mid = row["measurement_id"]
        if mid in lot06_ids:
            status = "LOT06_PUBLISHED_SOURCE_DEPENDENCIES"
        elif mid in g7_by_id:
            status = "G7_ATLAS_SOURCE_PREVIEW_ONLY"
        else:
            status = "HOLD_NO_PUBLISHED_FOCUS_DEPENDENCIES"
        rows.append({
            "order": row["order"],
            "measurement_id": mid,
            "atlas_contract_state": row["state"],
            "atlas_availability_gate": row.get("gate"),
            "source_dependency_status": status,
            "declared_landmarks": g7_by_id[mid]["required_landmarks"] if mid in g7_by_id else None,
            "active_runtime_focus_authorized": False,
            "clinical_value_authorized_by_this_ledger": False,
        })
    counts = {status: sum(row["source_dependency_status"] == status for row in rows)
              for status in ("LOT06_PUBLISHED_SOURCE_DEPENDENCIES",
                             "G7_ATLAS_SOURCE_PREVIEW_ONLY",
                             "HOLD_NO_PUBLISHED_FOCUS_DEPENDENCIES")}
    if tuple(counts.values()) != (8, 3, 22):
        raise ValueError(f"Atlas dependency coverage unexpectedly changed: {counts}")
    return {
        "schema_version": "CEPHALO_R23G7_ATLAS33_COVERAGE_LEDGER_V1",
        "protocol_id": PROTOCOL_ID,
        "source_atlas": str(ATLAS_PATH.relative_to(ROOT)),
        "source_lot06": str(LOT06_PATH.relative_to(ROOT)),
        "source_g7": str(G7_PATH.relative_to(ROOT)),
        "counts": counts,
        "clinical_release": False,
        "classification_authority": False,
        "caveat": "Focus-dependency coverage is not a measured/verified clinical value or user-authorized Focus.",
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build_ledger()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Atlas source-locked dependency ledger: 8 LOT06 + 3 G7 display-only + 22 HOLD; clinical_release=false")


if __name__ == "__main__":
    main()
