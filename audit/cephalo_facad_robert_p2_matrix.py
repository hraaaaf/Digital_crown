"""Machine-readable 45-factor FACAD Robert compatibility tracking, no clinical parity.

The authentic FACAD editor roster describes 32F+13F=45 factor occurrences.
The public Robert fixture exposes 9+5=14 numerically populated occurrences.
No factor is marked as clinically matched from math-helper proximity.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from audit import cephalo_facad_robert_public_ci as pub
from audit import cephalo_facad_robert_p2_geometry_gate as p2

ROOT = Path(__file__).resolve().parents[1]
ROSTER_PATH = ROOT / "docs/audits/schemas/ortho_lot08_facad_ricketts_editor_uia_45_roster_v1.json"
CONFLICTING_VENDOR = {
    "Xi-OL", "Xi-PM/OL", "Upper lip len", "STi-OL",
    "Facial cone angle", "Mand arc", "Mand len",
}
FH_MISSING = {"Convexity", "Ii to A-Pog", "Is to A-Pog", "Li-EL"}
ANATOMY_MISMATCH = {"Upper lip len"}
FACAD_VENDOR_TARGETS = {
    "32F": "FACAD_RICKETTS_32F_COMPATIBILITY_TARGET",
    "13F": "FACAD_RICKETTS_13F_COMPATIBILITY_TARGET",
}


def require(test: bool, reason: str) -> None:
    if not test:
        raise ValueError(reason)


def matrix(fixture: dict, roster: dict, p2_result: dict) -> dict:
    require(roster.get("schema_version") == "ORTHO_LOT08_FACAD_RICKETTS_EDITOR_UIA_45_ROSTER_V1"
            and roster.get("scientific_authority") is False
            and roster.get("compatibility_only") is True,
            "FACAD historical roster evidence authority drift")
    require(p2_result["candidate_quantization_consistent"] == 3 and
            p2_result["known_anatomical_alias_conflicts"] == 1 and
            p2_result["cross_product_clinical_parities"] == 0 and
            p2_result["clinical_no_go"] is True, "P2 prerequisite invalid")
    rosters = roster.get("profile_rosters", [])
    require(isinstance(rosters, list) and len(rosters) == 2,
            "two independent FACAD profiles required")
    unique_targets = set()
    rows = []
    for item in rosters:
        target = item.get("profile_target_id")
        require(target in set(FACAD_VENDOR_TARGETS.values()) and target not in unique_targets,
                "unknown or duplicate FACAD profile")
        unique_targets.add(target)
        profile = next(x for x, name in FACAD_VENDOR_TARGETS.items() if target == name)
        expected = 32 if profile == "32F" else 13
        source_roster = item.get("ordered_factor_labels")
        require(isinstance(source_roster, list) and len(source_roster) == expected and
                item.get("observed_factor_count") == expected,
                "FACAD expected number of factors changed")
        labels = [r.get("facad_label") for r in source_roster]
        require(len(set(labels)) == expected and
                [r.get("order") for r in source_roster] == list(range(1, expected+1)),
                "FACAD factor ordering/identity changed")
        values = fixture["facad_values"][profile]
        require(set(values).issubset(set(labels)), "numeric FACAD factor missing in editor roster")
        for number, label in enumerate(labels, 1):
            match = values.get(label)
            evidence = "NOT_OBSERVED_ON_ROBERT"
            if match is not None:
                if label in p2.CANDIDATE_METHODS:
                    evidence = "GEOMETRIC_ROUNDING_CONSISTENT_NOT_CLINICAL_PARITY"
                elif label in FH_MISSING:
                    evidence = "BLOCKED_SIGN_ORIENTATION_FH_UNOBSERVED"
                elif label in ANATOMY_MISMATCH:
                    evidence = "BLOCKED_HARD_ANATOMICAL_IDENTITY_MISMATCH"
                elif label == "Facial cone angle":
                    evidence = "BLOCKED_VENDOR_GO_ME_VS_DC_RICKETTS_MP"
                else:
                    raise ValueError("unclassified FACAD numeric factor")
            rows.append({
                "profile": profile,
                "order": number,
                "facad_label": label,
                "facad_value": match["value"] if match is not None else None,
                "facad_unit": match["unit"] if match is not None else None,
                "numeric_evidence": evidence,
                "vendor_alias_policy": ("NO_DIRECT_CLINICAL_ALIAS"
                                        if label in CONFLICTING_VENDOR else
                                        "MANUAL_SOURCE_SPECIFIC_MAPPING_REQUIRED"),
                "canonical_dc_id": (
                    p2.CANDIDATE_METHODS.get(label)
                    or ("M_RICKETTS_FACIAL_TAPER_NPOG_MP_DEG_V1"
                        if label == "Facial cone angle" else None)
                ),
                "clinical_parity_validated": False,
            })
    counts = Counter(x["numeric_evidence"] for x in rows)
    require(len(rows) == 45 and
            sum(x["facad_value"] is not None for x in rows) == 14 and
            counts["GEOMETRIC_ROUNDING_CONSISTENT_NOT_CLINICAL_PARITY"] == 5 and
            counts["NOT_OBSERVED_ON_ROBERT"] == 31 and
            counts["BLOCKED_SIGN_ORIENTATION_FH_UNOBSERVED"] == 7 and
            counts["BLOCKED_HARD_ANATOMICAL_IDENTITY_MISMATCH"] == 1 and
            counts["BLOCKED_VENDOR_GO_ME_VS_DC_RICKETTS_MP"] == 1 and
            sum(counts.values()) == 45, "FACAD 45-factor evidence count mismatch")
    require(all(x["clinical_parity_validated"] is False for x in rows),
            "unsafe clinical parity promotion")
    return {
        "schema_version": "FACAD_ROBERT_P2_45_FACTOR_COMPATIBILITY_MATRIX_V1",
        "roster_observed": 45,
        "facad_numeric_observations": 14,
        "facad_unique_numeric_factors": 9,
        "geometric_candidate_occurrences_non_clinical": 5,
        "numeric_blocked_occurrences": 9,
        "numeric_unobserved_occurrences": 31,
        "cross_product_clinical_parities": 0,
        "clinical_no_go": True,
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--github-summary", action="store_true")
    args = parser.parse_args()
    try:
        fixture = json.loads(pub.FIXTURE.read_text(encoding="utf-8"))
        pub.read_checked_fixture(pub.FIXTURE)  # exact pinned public file integrity
        atlas = json.loads(p2.ATLAS.read_text(encoding="utf-8"))
        source_locks = p2.FACAD_FINAL_SEVEN.read_text(encoding="utf-8")
        p2_result = p2.assess_p2(fixture, atlas, source_locks)
        historical = json.loads(ROSTER_PATH.read_text(encoding="utf-8"))
        out = matrix(fixture, historical, p2_result)
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as exc:
        print("FACAD_P2_MATRIX=FAIL_CLOSED_" + type(exc).__name__)
        return 2
    print("FACAD_P2_MATRIX=45_FACTORS_TRACKED")
    print("FACAD_NUMERIC_OBSERVATIONS=14")
    print("FACAD_NUMERIC_CANDIDATES_NONCLINICAL=5")
    print("FACAD_NUMERIC_BLOCKED=9")
    print("FACAD_NUMERIC_UNOBSERVED=31")
    print("FACAD_CLINICAL_PARITIES=0")
    print("CLINICAL_NO_GO=true")
    if args.github_summary:
        import os
        dest = os.environ.get("GITHUB_STEP_SUMMARY")
        if dest:
            with open(dest, "a", encoding="utf-8") as stream:
                stream.write("\n### FACAD P2 — All 45 vendor factor occurrences\n")
                stream.write("5 non-clinical geometric candidates + 9 numerically blocked + 31 not observed.\n")
                stream.write("| Profile | # | FACAD factor | Value | Status |\n")
                stream.write("|---|---:|---|---:|---|\n")
                for row in out["rows"]:
                    entry = (str(row["facad_value"]) + " " + str(row["facad_unit"])
                             if row["facad_value"] is not None else "—")
                    stream.write("| " + row["profile"] + " | " + str(row["order"]) +
                                 " | " + row["facad_label"] + " | " + entry +
                                 " | " + row["numeric_evidence"] + " |\n")
                stream.write("\n**CLINICAL NO-GO — no runtime clinical parities certified.**\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
