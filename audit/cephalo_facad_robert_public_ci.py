"""Read-only public educational Robert fixture to versioned DC math helper bridge.

No clinical adapter, patient identifiers, raw FACAD files or vendor executables.
The optional JSON fixture is intentionally NOT bundled by this file; the runner
must be explicit about MISSING vs VERIFIED and must never silently synthesize it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from audit import cephalo_facad_dc_private_subset_probe as dc

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "audit/fixtures/facad_robert_public_example_20261024_v1.json"
EXPECTED_SHA256 = "2ea42e215a614faa3663b8d97fa18cdaca85aa647d04c3084278890c7bdbda18"


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def validate_fixture(data: dict) -> dict:
    require(type(data) is dict and
            data.get("schema_version") == "FACAD_ROBERT_PUBLIC_EDUCATIONAL_GEOMETRY_V1",
            "wrong educational fixture schema")
    require(data.get("source_proof_level") ==
            "OPERATOR_ONLY_GUI_NOT_INDEPENDENTLY_VERIFIED" and
            data.get("clinical_authority") is False and
            data.get("clinical_parity_proven") is False and
            data.get("signed_measurements_may_not_be_compared_without_FH") is True,
            "unsafe promotion of demonstration evidence")
    require(data.get("coordinate_system") ==
            "FACAD_EXPORTED_ORIGINAL_SAGITTAL_VERTICAL_MM_UNSPECIFIED_ORIENTATION"
            and data.get("coordinate_rounding_mm") == 0.1,
            "FACAD coordinates have unverified frame or precision")
    raw_points = data.get("points_mm")
    require(type(raw_points) is dict and len(raw_points) == 30,
            "expected 30 educational reference points")
    points = {}
    for name, pair in raw_points.items():
        require(type(name) is str and bool(name) and type(pair) is list
                and len(pair) == 2 and
                all(type(v) in (int, float) and math.isfinite(v) for v in pair),
                "invalid educational point")
        points[name] = (float(pair[0]), float(pair[1]))
    require({"Ii", "Iia", "Is", "Isa", "A", "Pog", "Go", "Me", "N"} <= set(points),
            "required DC geometry points are missing")
    profiles = data.get("facad_values")
    require(type(profiles) is dict and set(profiles) == {"32F", "13F"},
            "both FACAD educational profiles required")
    parsed = {}
    for profile, expected in (("32F", dc.FACTOR_32), ("13F", dc.FACTOR_13)):
        raw = profiles[profile]
        require(type(raw) is dict and set(raw) == expected,
                "unexpected 9/5 educational factor roster")
        vals = {}
        for label, entry in raw.items():
            require(type(entry) is dict and set(entry) == {"value", "unit"},
                    "malformed educational result")
            value, unit = entry["value"], entry["unit"]
            require(type(value) in (int, float) and math.isfinite(value),
                    "invalid educational numerical value")
            dimension = ("mm" if label in
                         {"Convexity", "Ii to A-Pog", "Is to A-Pog",
                          "Li-EL", "Upper lip len"} else "°")
            require(unit == dimension, "unexpected FACAD unit")
            vals[label] = (float(value), unit)
        parsed[profile] = vals
    result = dc.comparison(parsed["32F"], parsed["13F"], points, points.copy())
    require(result["dc_geometry_helpers_executed"] == 4 and
            result["clinical_numeric_parities_verified"] == 0 and
            result["dc_full_runtime_adapter_executed"] is False and
            result["clinical_no_go"] is True, "unsafe clinical comparison promotion")
    return result


def read_checked_fixture(path: Path = FIXTURE) -> dict:
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == EXPECTED_SHA256,
            "educational fixture content/hash changed")
    for forbidden in (b"850101-", b"01/01/1985", b"benmoussa",
                      b"C:\\Users", b"patient_id"):
        require(forbidden.lower() not in raw.lower(),
                "demo fixture includes a demographic or private path")
    return validate_fixture(json.loads(raw.decode("utf-8")))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--github-summary", action="store_true")
    p.add_argument("--require-fixture", action="store_true")
    args = p.parse_args()
    if not FIXTURE.is_file() and not args.require_fixture:
        print("FACAD_PUBLIC_ROBERT=NOT_EXECUTED_FIXTURE_MISSING")
        print("FACAD_CLINICAL_NO_GO=true")
        return 0
    try:
        result = read_checked_fixture(FIXTURE)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print("FACAD_PUBLIC_ROBERT=FAIL_CLOSED_" + type(exc).__name__)
        return 2
    print("FACAD_PUBLIC_ROBERT=REAL_DC_GEOMETRY_HELPERS_EXECUTED")
    print("FACAD_PUBLIC_ROBERT_32F_VALUES=" + str(result["vendor_factor_count_32f"]))
    print("FACAD_PUBLIC_ROBERT_13F_VALUES=" + str(result["vendor_factor_count_13f"]))
    print("FACAD_PUBLIC_DC_HELPERS=" + str(result["dc_geometry_helpers_executed"]))
    print("FACAD_CLINICAL_PARITIES=0")
    print("FACAD_CLINICAL_NO_GO=true")
    if args.github_summary:
        import os
        target = os.environ.get("GITHUB_STEP_SUMMARY")
        if target:
            lines = ["### Robert educational example (not clinical parity)",
                     "Educational transcription (30 rounded points, 9/5 vendor results).",
                     "Real versioned DC math helpers: 4; full clinical adapter not executed.",
                     "| Factor | FACAD | DC helper | Delta |",
                     "|---|---:|---:|---:|"]
            for row in result["rows"]:
                if row["dc_helper"] is not None:
                    lines.append(f"| {row['factor']} | {row['facad_value']} {row['unit']} | "
                                 f"{row['dc_helper']:.3f} {row['unit']} | "
                                 f"{row['raw_delta']:+.3f} {row['unit']} |")
            lines.append("**CLINICAL NO-GO: 0/45 certified parity rows.**")
            with open(target, "a", encoding="utf-8") as out:
                out.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
