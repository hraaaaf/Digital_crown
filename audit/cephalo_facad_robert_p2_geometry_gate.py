"""FACAD P2: public educational geometric agreement with mathematically bounded rounding.

This deliberately does NOT certify a vendor-to-DC clinical measurement parity.
The vendor source uses 0.1-mm-rounded points; a displayed angle has a further
0.05-degree quantization bound. Numeric closeness alone is NOT anatomical parity.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from audit import cephalo_facad_robert_public_ci as public

ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "backend/data/cephalometry/ricketts_atlas2009_complete33_protocol_profile_v1.json"
FACAD_FINAL_SEVEN = ROOT / "docs/audits/CEPHALO_LOT08_RICKETTS32_FACAD_FINAL_SEVEN_RESOLUTION.md"

CANDIDATE_METHODS = {
    "ILi/A-Pog": "M_RICKETTS_L1_APOG_INCLINATION_DEG_V1",
    "ILs/A-Pog": "M_RICKETTS_U1_APOG_INCLINATION_DEG_V1",
    "InterIncisal": "M_INTERINCISAL_DEG_V1",
}
BLOCKED_VENDOR_VARIANT = "Facial cone angle"
DEG_HALF_DISPLAY_ROUNDING = 0.05
METRIC_COORDINATE_STEP = 0.1


def fail_unless(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def source_lock_check(atlas: dict, final_seven: str) -> None:
    """Enforce existing clinical protocol gates before reporting candidate geometry."""
    measurements = atlas.get("measurements")
    fail_unless(type(measurements) is list, "missing canonical Ricketts atlas profile")
    by_id = {x.get("measurement_id"): x for x in measurements}
    fail_unless(len(by_id) == len(measurements), "duplicate canonical Ricketts measurement")
    for source_id in CANDIDATE_METHODS.values():
        m = by_id.get(source_id)
        fail_unless(isinstance(m, dict) and m.get("state") == "EXECUTABLE",
                    "candidate measurement missing from executable canonical profile")
    taper = by_id.get("M_RICKETTS_FACIAL_TAPER_NPOG_MP_DEG_V1")
    fail_unless(isinstance(taper, dict) and
                taper.get("gate") == "SOURCE_LOCKED_RICKETTS_MANDIBULAR_PLANE_REQUIRED"
                and taper.get("state") == "CONDITIONAL_EXECUTABLE",
                "canonical Ricketts taper gate changed")
    fail_unless("Facial cone angle" in final_seven and
                "generic Go-Me substitution is forbidden" in final_seven and
                "Facad uses generic Go-Me vs N-Pog" in final_seven,
                "known vendor facial cone vs canonical taper conflict unverified")


def _direction(p: dict, a: str, b: str) -> tuple[float, float]:
    return (p[b][0] - p[a][0], p[b][1] - p[a][1])


def _endpoint_quantization_angle_bound_deg(direction: tuple[float, float],
                                           step_mm: float) -> float:
    """Tight circular max deviation: each coordinate ±step/2, Δvector ≤√2*step.

    If v is the rounded vector and |Δv|≤r<|v|, maximal angular displacement
    of v+Δv is ≤asin(r/|v|). This also bounds min/max supplementary angles.
    """
    magnitude = math.hypot(*direction)
    error_radius = math.sqrt(2.0) * step_mm
    fail_unless(math.isfinite(magnitude) and magnitude > error_radius,
                "rounding dominates the observed cephalometric direction")
    return math.degrees(math.asin(error_radius / magnitude))


def angle_rounding_bound_deg(p: dict, factor: str, step_mm: float = METRIC_COORDINATE_STEP) -> float:
    fail_unless(type(step_mm) in (int, float) and math.isfinite(step_mm)
                and 0 < step_mm <= 0.1, "unverified coordinate resolution")
    paths = {
        "ILi/A-Pog": (("Ii", "Iia"), ("A", "Pog")),
        "ILs/A-Pog": (("Is", "Isa"), ("A", "Pog")),
        "InterIncisal": (("Isa", "Is"), ("Iia", "Ii")),
        "Facial cone angle": (("Go", "Me"), ("N", "Pog")),
    }
    fail_unless(factor in paths, "no audited vector decomposition")
    a, b = paths[factor]
    return (
        _endpoint_quantization_angle_bound_deg(_direction(p, *a), step_mm)
        + _endpoint_quantization_angle_bound_deg(_direction(p, *b), step_mm)
        + DEG_HALF_DISPLAY_ROUNDING
    )


def assess_p2(fixture: dict, atlas: dict, final_seven: str) -> dict:
    source_lock_check(atlas, final_seven)
    raw = public.validate_fixture(fixture)
    p = {name: tuple(point) for name, point in fixture["points_mm"].items()}
    records = {row["factor"]: row for row in raw["rows"]}
    fail_unless(len(records) == 9, "partial FACAD observed factor roster")
    outcomes = []
    for factor, measurement_id in CANDIDATE_METHODS.items():
        row = records[factor]
        fail_unless(row["unit"] == "°" and row["dc_helper"] is not None,
                    "DC helper absent or incorrect angle unit")
        bound = angle_rounding_bound_deg(p, factor)
        delta = abs(row["raw_delta"])
        fail_unless(delta <= bound + 1e-6,
                    "observed vendor-vs-DC angle outside maximal rounding bound")
        outcomes.append({
            "factor": factor, "canonical_dc_id": measurement_id,
            "facad_display_deg": row["facad_value"],
            "dc_versioned_geometry_deg": row["dc_helper"],
            "absolute_delta_deg": round(delta, 6),
            "conservative_rounding_bound_deg": round(bound, 6),
            "status": "GEOMETRIC_ROUNDING_CONSISTENT_NOT_CLINICAL_PARITY",
            "adapter_proven_same_case": False,
        })
    facad = records[BLOCKED_VENDOR_VARIANT]
    fail_unless(facad["dc_helper"] is not None and facad["clinical_parity"] is False,
                "generic cone helper unavailable or incorrectly promoted")
    outcomes.append({
        "factor": BLOCKED_VENDOR_VARIANT,
        "canonical_dc_id": "M_RICKETTS_FACIAL_TAPER_NPOG_MP_DEG_V1",
        "facad_display_deg": facad["facad_value"],
        "dc_versioned_geometry_deg": facad["dc_helper"],
        "absolute_delta_deg": abs(facad["raw_delta"]),
        "status": "BLOCKED_VENDOR_GO_ME_VS_DC_RICKETTS_MP",
        "adapter_proven_same_case": False,
    })
    fail_unless(len(outcomes) == 4 and raw["clinical_numeric_parities_verified"] == 0
                and raw["clinical_no_go"] is True,
                "invalid P2 status promotion")
    return {
        "status": "FACAD_P2_EDUCATIONAL_ROUNDING_CONSISTENCY",
        "candidate_quantization_consistent": 3,
        "known_anatomical_alias_conflicts": 1,
        "cross_product_clinical_parities": 0,
        "full_runtime_adapter_validated": False,
        "clinical_no_go": True,
        "input_coordinate_resolution_mm": METRIC_COORDINATE_STEP,
        "facad_angle_display_quantization_deg": DEG_HALF_DISPLAY_ROUNDING,
        "rows": outcomes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--github-summary", action="store_true")
    args = parser.parse_args()
    try:
        fixture = json.loads(public.FIXTURE.read_text(encoding="utf-8"))
        public.read_checked_fixture(public.FIXTURE)  # Byte-exact SHA-256 and PII guard.
        atlas = json.loads(ATLAS.read_text(encoding="utf-8"))
        final_seven = FACAD_FINAL_SEVEN.read_text(encoding="utf-8")
        result = assess_p2(fixture, atlas, final_seven)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print("FACAD_P2=FAIL_CLOSED_" + type(exc).__name__)
        return 2
    print("FACAD_P2=REAL_DC_MATH_HELPERS_QUANTIZATION_AUDITED")
    print("FACAD_P2_ROUNDING_CONSISTENT_NON_CLINICAL=3")
    print("FACAD_P2_HARD_FACIAL_CONE_ALIAS_BLOCKED=1")
    print("FACAD_P2_FULL_RUNTIME_ADAPTER=NOT_VERIFIED")
    print("FACAD_P2_CLINICAL_PARITIES=0")
    print("CLINICAL_NO_GO=true")
    if args.github_summary:
        import os
        target = os.environ.get("GITHUB_STEP_SUMMARY")
        if target:
            lines = [
                "### FACAD P2 — rounded-geometry gate (not clinical parity)",
                "Source: public Robert demo, FACAD 30 rounded-mm points; actual DC helpers.",
                "| FACAD | DC helper | Δ° | Upper rounding bound° | Evidence |",
                "|---|---:|---:|---:|---|",
            ]
            for row in result["rows"]:
                bound = row.get("conservative_rounding_bound_deg")
                lines.append("| " + row["factor"] + " | "
                             + str(round(row["dc_versioned_geometry_deg"], 3)) + "° | "
                             + str(round(row["absolute_delta_deg"], 3)) + "° | "
                             + (str(round(bound, 3)) + "°" if bound is not None else "—")
                             + " | " + ("Within rounding bound; NOT clinical parity"
                                        if bound is not None else
                                        "FORBIDDEN ALIAS: FACAD Go–Me != DC Ricketts MP")
                             + " |")
            lines.append("**3 geometric candidates only; 1 incompatible anatomical construction. 0/45 clinical parity; NO-GO.**")
            with open(target, "a", encoding="utf-8") as out:
                out.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
