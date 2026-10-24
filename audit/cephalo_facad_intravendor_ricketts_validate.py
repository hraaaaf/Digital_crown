"""FACAD 13F vs 32F historical editor-signature/norm comparison, READ-ONLY.

Same FACAD editor calc type + Arg1..Arg4 does not prove vendor runtime numeric
equality, nor any Digital Crown clinical equivalence. Do not copy vendor norm
strings into clinical runtime. Uses no FACAD executable, EULA or patient data.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from zipfile import ZipFile

from audit import cephalo_facad_historical_roster_verify as hv

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "docs/audits/schemas"
CROSSWALK = SCHEMAS / "ortho_lot08_facad_ricketts_13f_vs_32f_gui_definitions_v1.json"
ROSTER = SCHEMAS / "ortho_lot08_facad_ricketts_editor_uia_45_roster_v1.json"


def require(ok: bool, why: str) -> None:
    if not ok:
        raise ValueError(why)


def signatures(raw: bytes, expected_profile: str) -> dict[str, dict]:
    """First measurements grid ONLY: type + four references + displayed norm."""
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError("historic editor UIA must be UTF8") from exc
    require("ControlType.Window|Edit Cephalometric Analysis|" in text
            and f"ControlType.Edit|{expected_profile}|AUTOID=" in text,
            "FACAD editor/profile identity mismatch")
    start = text.find("ControlType.DataGrid|")
    require(start >= 0, "no measurements grid")
    lines = text[start:].splitlines()
    rows = []
    for line in lines[1:]:
        if line.startswith("ControlType.DataGrid|"):
            break
        if line.startswith("ControlType.DataItem|"):
            rows.append([line.split("|", 2)[1], []])
        elif rows and line.startswith("ControlType.Text|"):
            rows[-1][1].append(line.split("|", 2)[1])
    data = {}
    for name, cells in rows:
        require(len(cells) >= 9 and name == cells[0],
                "malformed vendor UIA measurement row")
        if cells[1] == "Heading":
            continue
        require(name not in data and bool(cells[1]), "duplicate/bad factor")
        data[name] = {
            "calc_type": cells[1],
            "arg_refs": [x for x in cells[2:6] if x],
            "norm": cells[6],
        }
    return data


def validate_schema(cross: dict, roster: dict) -> dict:
    require(cross["schema_version"] == "ORTHO_LOT08_FACAD_RICKETTS_13F_VS_32F_GUI_DEFINITIONS_V1"
            and cross["status"] == "HISTORICAL_EDITOR_SIGNATURE_COMPARISON_ONLY_NOT_RUNTIME_PARITY"
            and cross["scientific_authority"] is False
            and cross["compatibility_only"] is True
            and all(x is True for x in cross["safety_rules"].values()),
            "source status/safety contract violated")
    require(roster["schema_version"] == "ORTHO_LOT08_FACAD_RICKETTS_EDITOR_UIA_45_ROSTER_V1"
            and roster["status"] == "HISTORICAL_EDITOR_DEFINITION_UIA_OBSERVED_ONLY",
            "historical GUI roster guard violated")
    profiles = {p["profile_target_id"]: p for p in roster["profile_rosters"]}
    require(len(profiles) == 2, "expected exact FACAD 32F and 13F profiles")
    p32 = profiles["FACAD_RICKETTS_32F_COMPATIBILITY_TARGET"]
    p13 = profiles["FACAD_RICKETTS_13F_COMPATIBILITY_TARGET"]
    require(cross["source_artifacts"] == {
            "profile_32f": p32["source_artifact_id"],
            "profile_13f": p13["source_artifact_id"],
        }, "historical source artifact ID mismatch")
    require(cross["source_roster"] == "docs/audits/schemas/ortho_lot08_facad_ricketts_editor_uia_45_roster_v1.json",
            "wrong source roster path")
    rows = cross["pairings"]
    require(len(rows) == 13 and len({x["facad_label"] for x in rows}) == 13,
            "13 distinct Ricketts factors required")
    names13 = [x["facad_label"] for x in p13["ordered_factor_labels"]]
    names32 = [x["facad_label"] for x in p32["ordered_factor_labels"]]
    require(len(names13) == 13 and len(names32) == 32,
            "historical 13F/32F factor counts mismatch")
    require(names13 == [x["facad_label"] for x in rows],
            "the ordered FACAD 13F editor roster was modified")
    different = []
    for i, row in enumerate(rows, start=1):
        require(type(row["facad_13f_order"]) is int and row["facad_13f_order"] == i
                and row["facad_32f_label"] == row["facad_label"]
                and row["facad_label"] in names32,
                "FACAD profile factor identity/order mismatch")
        require(type(row["calc_type"]) is str and row["calc_type"] and
                type(row["arg_refs"]) is list and 1 <= len(row["arg_refs"]) <= 4 and
                all(type(x) is str and bool(x) for x in row["arg_refs"]),
                "invalid displayed editor calc type/landmarks")
        require(type(row["norm_13f"]) is str and type(row["norm_32f"]) is str
                and row["norm_13f"] and row["norm_32f"],
                "displayed norms missing")
        same_norm = row["norm_13f"] == row["norm_32f"]
        require(row["norm_display_same"] is same_norm
                and row["same_vendor_editor_calc_type_and_refs"] is True
                and row["numeric_same_trace_observed"] is False
                and row["digital_crown_geometry_parity_observed"] is False,
                "false clinical equivalence or norm equality asserted")
        if not same_norm:
            different.append(row["facad_label"])
    require(cross["same_editor_signature_count"] == 13
            and cross["distinct_display_norm_count"] == len(different)
            and different == ["Facial axis", "ML/FH", "LFH", "Convexity"],
            "historical four vendor norm differences drifted")
    return {
        "status": "HISTORICAL_VENDOR_EDITOR_SIGNATURES_SOURCE_LOCKED",
        "same_displayed_calc_type_and_refs": 13,
        "different_displayed_norms": len(different),
        "distinct_norm_labels": different,
        "source_zip_verification_performed": False,
        "numeric_parity_observed": 0,
        "digital_crown_cross_product_parity_observed": 0,
        "clinical_no_go": True,
    }


def verify_original_archives(cross: dict, roster: dict,
                             archive32: Path, archive13: Path) -> dict:
    sources = {
        "FACAD_RICKETTS_32F_COMPATIBILITY_TARGET": archive32,
        "FACAD_RICKETTS_13F_COMPATIBILITY_TARGET": archive13,
    }
    hv.verify_pair(roster, sources)  # verify actual bytes and all 45 positions first
    profiles = {p["profile_target_id"]: p for p in roster["profile_rosters"]}
    extracted = {}
    for profile_id, file in sources.items():
        meta = profiles[profile_id]
        with ZipFile(file, "r") as z:
            raw = z.read(meta["source_uia_member_name"])
        expected = "Ricketts (32 F)" if "32F" in profile_id else "Ricketts (13 F)"
        extracted[profile_id] = signatures(raw, expected)
    f32 = extracted["FACAD_RICKETTS_32F_COMPATIBILITY_TARGET"]
    f13 = extracted["FACAD_RICKETTS_13F_COMPATIBILITY_TARGET"]
    require(len(f32) == 32 and len(f13) == 13, "unexpected original editor factor count")
    for row in cross["pairings"]:
        label = row["facad_label"]
        expected = {"calc_type": row["calc_type"], "arg_refs": row["arg_refs"]}
        require(label in f13 and label in f32,
                "historic FACAD 13F factor not present in 32F")
        for f in (f13[label], f32[label]):
            require({k: f[k] for k in ("calc_type", "arg_refs")} == expected,
                    "13F / 32F original FACAD editor calculation signature mismatch")
        require(f13[label]["norm"] == row["norm_13f"] and
                f32[label]["norm"] == row["norm_32f"],
                "FACAD profile-specific original norm string mismatch")
    result = validate_schema(cross, roster)
    result["status"] = "HISTORIC_ORIGINAL_ZIP_EDITOR_SIGNATURES_VERIFIED"
    result["source_zip_verification_performed"] = True
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ricketts32f-zip", type=Path)
    parser.add_argument("--ricketts13f-zip", type=Path)
    args = parser.parse_args()
    try:
        require(bool(args.ricketts32f_zip) == bool(args.ricketts13f_zip),
                "both actual historical ZIPs are required together")
        cross = json.loads(CROSSWALK.read_text(encoding="utf-8"))
        roster = json.loads(ROSTER.read_text(encoding="utf-8"))
        result = (verify_original_archives(cross, roster, args.ricketts32f_zip,
                                         args.ricketts13f_zip)
                  if args.ricketts32f_zip else validate_schema(cross, roster))
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"FACAD_INTRA_VENDOR_FAIL_CLOSED={type(exc).__name__}: {exc}")
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
