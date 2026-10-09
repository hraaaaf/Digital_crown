#!/usr/bin/env python3
"""F01.13: assert the published-vs-vendor Ricketts composition discrepancy ledger.

Strictly observational: validates exact Facad editor UIA factors and quarantine
states; it cannot establish clinical or geometric equivalence.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIFF = "docs/audits/data/FACAD_314_F01_13_RICKETTS_ATLAS_FACAD_COMPOSITION_DIFF_2026-10-09.csv"
R32 = "docs/audits/data/FACAD_314_D1C_RICKETTS32F_EDITOR_MEASUREMENTS_UIA_2026-10-09.csv"
R13 = "docs/audits/data/FACAD_314_D1C_RICKETTS13F_EDITOR_MEASUREMENTS_UIA_2026-10-09.csv"
COLUMNS = (
    "reference_version", "reference_factor_ordinal", "reference_factor_label",
    "facad_editor_profile", "facad_ui_row_ordinal", "facad_ceph_name",
    "facad_measurement_type", "facad_arg1", "facad_arg2", "facad_arg3",
    "facad_arg4", "facad_norm_literal", "finding_code",
    "finding_scope", "facad_source_blob_sha", "reference_source",
    "research_provenance_note",
)

EXPECTED_32_UI_ROWS = (
    2, 3, 4, 5, 6, 7, 9, 10, 12, 13, 14, 15, 16, 17, 18, 20,
    21, 22, 24, 25, 26, 27, 28, 29, 30, 32, 33, 34,
    35, 36, 37, 38,
)
EXPECTED_12_UI_ROWS = (2, 3, 6, 4, 5, 7, 9, 10, 12, 13, 14, 17)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        result = list(reader)
    if any(None in x for x in result):
        raise ValueError("CSV row with unexpected extra columns")
    return result


def git_blob(path: Path) -> str:
    b = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest()


def validate(diff_path: Path = ROOT / DIFF) -> None:
    all_rows = rows(diff_path)
    fac32_path, fac13_path = ROOT / R32, ROOT / R13
    p32 = rows(fac32_path)
    p13 = rows(fac13_path)
    data32 = {x["row_ordinal"]: x for x in p32 if x["Type"] != "Heading"}
    data13 = {x["row_ordinal"]: x for x in p13 if x["Type"] != "Heading"}
    if (len(all_rows), len(p32), len(p13), len(data32), len(data13)) != (46, 38, 17, 32, 13):
        raise ValueError("Source or crosswalk factor count unexpected")
    expected32 = tuple(str(x) for x in EXPECTED_32_UI_ROWS)
    expected13 = tuple(str(x) for x in EXPECTED_12_UI_ROWS + (15,))
    if set(data32) != set(expected32) or set(data13) != set(expected13):
        raise ValueError("Observed vendor factor list changed; manual science re-review required")
    if [x["reference_version"] for x in all_rows] != (
        ["ATLAS_2009_COMPLETE_33"] * 33 + ["ATLAS_2009_SUMMARY_12"] * 13
    ):
        raise ValueError("Reference version/order mismatch")
    for j, row in enumerate(all_rows):
        if tuple(row) != COLUMNS:
            raise ValueError(f"Unexpected schema at row {j+1}")
        is32 = j < 33
        expected_ord = j + 1 if is32 else j - 32
        if row["reference_factor_ordinal"] != str(expected_ord):
            raise ValueError(f"Reference ordinal mismatch {j}")
        if row["facad_editor_profile"] != ("Ricketts (32 F)" if is32 else "Ricketts (13 F)"):
            raise ValueError(f"Facad variant has been relabelled: {j}")
        expected_facad_ord = (
            EXPECTED_32_UI_ROWS[j] if is32 and j != 28 else
            None if is32 else EXPECTED_12_UI_ROWS[j - 33] if j < 45 else 15
        )
        if j > 28 and is32:
            expected_facad_ord = EXPECTED_32_UI_ROWS[j-1]
        expected_facad_ord = str(expected_facad_ord) if expected_facad_ord is not None else ""
        if row["facad_ui_row_ordinal"] != expected_facad_ord:
            raise ValueError(f"Missing/extra/unexpected Facad UIA factor at {j}")
        known = data32 if is32 else data13
        src = known.get(expected_facad_ord)
        fields = {
            "facad_ceph_name": "Ceph name",
            "facad_measurement_type": "Type",
            "facad_arg1": "Arg 1",
            "facad_arg2": "Arg 2",
            "facad_arg3": "Arg 3",
            "facad_arg4": "Arg 4",
            "facad_norm_literal": "Norm",
        }
        for key, source_key in fields.items():
            if row[key] != (src[source_key] if src else ""):
                raise ValueError(f"Tampered observed Facad source: row={j} field={key}")
        if row["facad_source_blob_sha"] != git_blob(fac32_path if is32 else fac13_path):
            raise ValueError(f"Incorrect Facad source provenance at {j}")
        if row["finding_scope"] != "COMPOSITION_COMPARISON_ONLY__GEOMETRY_AND_NORMS_NOT_CERTIFIED":
            raise ValueError(f"Scientific equivalence falsely certified at {j}")
        expected_findings = {
            26: "LABEL_NORM_IDENTITY_REVIEW",
            28: "REFERENCE_FACTOR_NOT_OBSERVED",
            32: "LANDMARK_ENDPOINT_REVIEW",
            35: "ANGULAR_LINEAR_UNIT_MISMATCH",
            45: "VENDOR_FACTOR_EXTRA_TO_ATLAS12",
        }
        if row["finding_code"] != expected_findings.get(j, "ORDERED_LABEL_CANDIDATE_ONLY"):
            raise ValueError(f"Discrepancy classification changed at {j}")
        if not row["reference_factor_label"] or not row["reference_source"] or not row["research_provenance_note"]:
            raise ValueError(f"Missing source research evidence row {j}")
    if all_rows[28]["facad_ui_row_ordinal"] or all_rows[28]["reference_factor_ordinal"] != "29":
        raise ValueError("Atlas 33 slot 29 must remain unobserved in Facad 32")
    if (all_rows[35]["facad_ceph_name"], all_rows[35]["facad_measurement_type"], all_rows[35]["facad_norm_literal"]) != ("PFH", "Dist2p", "63±3.5"):
        raise ValueError("Atlas 12 vs Facad 13 PFH angular-vs-linear clash hidden")
    if (all_rows[45]["facad_ceph_name"], all_rows[45]["facad_measurement_type"]) != ("InterIncisal", "Angle4p"):
        raise ValueError("Facad 13th observed factor hidden")
    print("RICKETTS_ATLAS_FACTORS=33+12")
    print("FACAD_RICKETTS_FACTORS=32+13")
    print("RICKETTS_COMPARISON_ROWS=46")
    print("RICKETTS_COMPOSITION_DISCREPANCIES_PRESERVED=5")
    print("FACAD_TO_ATLAS_FORMULA_EQUIVALENCE_CERTIFIED=false")


def self_test() -> None:
    original = rows(ROOT / DIFF)
    faults = [
        ("remove_atlas_29", lambda r: r.pop(28)),
        ("fake_atlas_29_mapping", lambda r: r[28].update(facad_ui_row_ordinal="34")),
        ("promote_geometry", lambda r: r[1].update(finding_scope="SOURCE_LOCKED")),
        ("hide_angular_linear_clash", lambda r: r[35].update(facad_measurement_type="Angle4p", finding_code="ORDERED_LABEL_CANDIDATE_ONLY")),
        ("hide_extra_interincisal", lambda r: r[45].update(finding_code="ORDERED_LABEL_CANDIDATE_ONLY")),
        ("wrong_facad_variant", lambda r: r[44].update(facad_editor_profile="Ricketts (32 F)")),
    ]
    for label, modifier in faults:
        local = [dict(x) for x in original]
        modifier(local)
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / Path(DIFF).name
            with p.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(local)
            try:
                validate(p)
            except ValueError:
                print(f"NEGATIVE_PASS={label}")
            else:
                raise AssertionError(f"Research diff fail-open: {label}")
    print("RICKETTS_SCIENCE_NEGATIVE_TESTS_PASS=6")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    opts = parser.parse_args()
    validate()
    if opts.self_test:
        self_test()
