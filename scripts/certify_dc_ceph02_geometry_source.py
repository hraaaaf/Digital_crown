#!/usr/bin/env python3
"""Source-only DC-CEPH-02A: 38 LOT06 function bindings and selected geometry invariants.

Never imports FACAD, reads patient data, computes clinical norms, or mutates runtime.
A callable symbol existing in source is NOT evidence of runtime reachability.
"""
from __future__ import annotations

import ast
import copy
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
CONTRACT = ROOT / "docs/audits/schemas/cephalo_vnext_lot06_executable_measurement_contract_v1.json"
ALLOWED_MODULES = {
    "backend.services.cephalo_constructions",
    "backend.services.cephalo_steiner_geometry",
    "backend.services.cephalo_mcnamara_geometry",
    "backend.services.cephalo_downs_geometry",
    "backend.services.cephalo_tweed_merrifield_geometry",
    "backend.services.cephalo_craniom_angular",
    "backend.services.cephalo_ricketts_geometry",
    "backend.services.cephalo_canonical_analysis_v2",
}


class Ceph02GateError(ValueError):
    pass


def require(ok: bool, code: str) -> None:
    if not ok:
        raise Ceph02GateError(code)


def validate_bindings(doc: dict) -> dict:
    require(doc.get("schema_version") == "CEPHALO_LOT06_EXECUTABLE_MEASUREMENT_CONTRACT_V1", "SCHEMA")
    require(doc.get("status") == "EXECUTABLE_38_CANONICAL_MEASUREMENTS", "STATUS")
    require(doc.get("clinical_interpretation") is False, "NO_CLINICAL_AUTHORITY")
    items = doc.get("measurements")
    require(isinstance(items, list) and len(items) == 38, "EXACT_38")
    ids = [x.get("measurement_id") for x in items]
    require(len(set(ids)) == 38 and all(isinstance(v, str) and v.startswith("M_") for v in ids),
            "UNIQUE_IDENTITIES")
    used_modules: set[str] = set()
    parsed: dict[str, set[str]] = {}
    units = {"mm": 0, "°": 0}
    for m in items:
        mid = m["measurement_id"]
        unit = m.get("unit")
        require(unit in units, "UNKNOWN_UNIT_" + mid)
        units[unit] += 1
        require(m.get("requires_calibration") is (unit == "mm"), "CALIBRATION_UNIT_" + mid)
        require(isinstance(m.get("required_landmarks"), list) and m["required_landmarks"],
                "REQUIRED_LANDMARKS_" + mid)
        require(all(isinstance(v, str) and v.strip() for v in m["required_landmarks"])
                and len(set(m["required_landmarks"])) == len(m["required_landmarks"]),
                "LANDMARK_IDENTITY_" + mid)
        require(isinstance(m.get("required_constructions"), list)
                and len(set(m["required_constructions"])) == len(m["required_constructions"]),
                "CONSTRUCTIONS_" + mid)
        require(isinstance(m.get("availability_gate"), str) and m["availability_gate"].strip(),
                "AVAILABILITY_GATE_" + mid)
        sources = m.get("source_contracts")
        require(isinstance(sources, list) and sources, "SOURCE_EMPTY_" + mid)
        for source in sources:
            require(isinstance(source, str)
                    and (source.startswith("docs/") or source.startswith("backend/"))
                    and ".." not in Path(source).parts and (ROOT / source).is_file(),
                    "SOURCE_NOT_FOUND_" + mid)
        impl = m.get("implementation", "")
        require(isinstance(impl, str) and impl.count(":") == 1, "IMPLEMENTATION_FORMAT_" + mid)
        module, symbol = impl.split(":")
        require(module in ALLOWED_MODULES and symbol.isidentifier() and not symbol.startswith("_"),
                "MODULE_OR_SYMBOL_NOT_ALLOWLISTED_" + mid)
        if module not in parsed:
            src = ROOT / (module.replace(".", "/") + ".py")
            require(src.is_file(), "IMPLEMENTATION_SOURCE_MISSING_" + mid)
            tree = ast.parse(src.read_text(encoding="utf-8"), filename=module)
            parsed[module] = {
                node.name for node in tree.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
        require(symbol in parsed[module], "IMPLEMENTATION_FUNCTION_MISSING_" + mid)
        used_modules.add(module)
    require(used_modules == ALLOWED_MODULES, "EIGHT_SOURCE_MODULES")
    return {"bindings": len(items), "modules": len(used_modules), "angle_contracts": units["°"],
            "mm_contracts": units["mm"], "sources_all_present": True}


def run_negative_controls(doc: dict) -> int:
    mutations = (
        lambda d: d.update(clinical_interpretation=True),
        lambda d: d["measurements"].pop(),
        lambda d: d["measurements"][0].update(measurement_id=d["measurements"][1]["measurement_id"]),
        lambda d: d["measurements"][0].update(implementation="backend.services.cephalo_constructions:no_such_symbol"),
        lambda d: d["measurements"][0].update(implementation="backend.services.non_source:impl"),
        lambda d: d["measurements"][0].update(requires_calibration=False),
        lambda d: d["measurements"][1].update(requires_calibration=True),
        lambda d: d["measurements"][0].update(required_landmarks=[]),
        lambda d: d["measurements"][0].update(availability_gate=""),
        lambda d: d["measurements"][0].update(source_contracts=["docs/nonexistent_dc_ceph02.md"]),
        lambda d: d["measurements"][0].update(source_contracts=["../private.txt"]),
        lambda d: d["measurements"][0].update(unit="cm"),
    )
    for n, mutation in enumerate(mutations):
        poisoned = copy.deepcopy(doc)
        mutation(poisoned)
        try:
            validate_bindings(poisoned)
        except Ceph02GateError:
            continue
        raise Ceph02GateError(f"NEGATIVE_CONTROL_FALSE_PASS_{n}")
    return len(mutations)


def run_geometry_invariants() -> int:
    # These source-specific primitives are chosen for distinct failure modes.
    # The tests do not substitute for a clinical/real-image study or all 38 runtime paths.
    from backend.services.cephalo_steiner_geometry import steiner_anb_deg_v1
    from backend.services.cephalo_mcnamara_geometry import mcnamara_co_a_mm_v1
    from backend.services.cephalo_constructions import (
        craniom_ab_prime_mm_v1, nasion_vertical_offset_mm_v1,
    )
    from backend.services.cephalo_ricketts_geometry import (
        ricketts_e_line_perpendicular_signed_distance_px_v2,
    )

    checked = 0

    def ok(condition: bool, code: str) -> None:
        nonlocal checked
        require(condition, "GEOMETRY_" + code)
        checked += 1

    def eq(v: float | None, expected: float) -> bool:
        return v is not None and math.isclose(v, expected, rel_tol=0, abs_tol=1e-9)

    def move(p: tuple[float, float], dx: float = 17, dy: float = -31):
        return p[0] + dx, p[1] + dy

    # Steiner ANB: translation invariant, missing/zero-length landmarks fail closed,
    # editing A changes the angle and never infers a classification or norm.
    s, n, a, b = (0., 0.), (10., 0.), (15., 10.), (14., 20.)
    anb = steiner_anb_deg_v1(s, n, a, b)
    ok(anb is not None and math.isfinite(anb), "ANB_FINITE")
    ok(eq(steiner_anb_deg_v1(*(move(p) for p in (s, n, a, b))), anb), "ANB_TRANSLATION")
    edited = steiner_anb_deg_v1(s, n, (16., 10.), b)
    ok(edited is not None and not eq(edited, anb), "ANB_LANDMARK_CORRECTION_PROPAGATES")
    ok(steiner_anb_deg_v1(s, n, None, b) is None, "ANB_MISSING")
    ok(steiner_anb_deg_v1(n, n, a, b) is None, "ANB_ZERO_SN")
    ok(steiner_anb_deg_v1(s, n, n, b) is None, "ANB_ZERO_NA")

    co, point_a = (0., 0.), (3., 4.)
    ok(eq(mcnamara_co_a_mm_v1(co, point_a, .2), 1.), "MCNAMARA_DISTANCE")
    ok(eq(mcnamara_co_a_mm_v1(co, point_a, .4), 2.), "MCNAMARA_CALIBRATION_SCALE")
    ok(eq(mcnamara_co_a_mm_v1(move(co), move(point_a), .2), 1.), "MCNAMARA_TRANSLATION")
    ok(mcnamara_co_a_mm_v1(co, point_a, None) is None, "MCNAMARA_UNCALIBRATED")
    ok(mcnamara_co_a_mm_v1(co, point_a, 0.) is None, "MCNAMARA_ZERO_RATIO")
    ok(mcnamara_co_a_mm_v1(co, point_a, float("nan")) is None, "MCNAMARA_NAN_RATIO")
    ok(mcnamara_co_a_mm_v1(co, co, .2) is None, "MCNAMARA_DEGENERATE_SEGMENT")
    ok(mcnamara_co_a_mm_v1(co, None, .2) is None, "MCNAMARA_MISSING_ANATOMY")

    po, or_ = (0., 1.), (10., 1.)
    ahead, behind = (8., 5.), (3., 5.)
    ok(eq(craniom_ab_prime_mm_v1(ahead, behind, po, or_, .2), 1.), "CRANIOM_ABP_SIGN")
    ok(eq(craniom_ab_prime_mm_v1(behind, ahead, po, or_, .2), -1.), "CRANIOM_ABP_REVERSE")
    ok(eq(craniom_ab_prime_mm_v1(*(move(p) for p in (ahead, behind, po, or_)), .2), 1.),
       "CRANIOM_ABP_TRANSLATION")
    ok(craniom_ab_prime_mm_v1(ahead, behind, po, po, .2) is None, "CRANIOM_ABP_DEGENERATE_FH")
    ok(craniom_ab_prime_mm_v1(ahead, behind, po, or_, None) is None, "CRANIOM_ABP_UNCALIBRATED")

    n0 = (0., 0.)
    ok(eq(nasion_vertical_offset_mm_v1((5., 3.), n0, po, or_, .2), 1.), "NPERP_ANTERIOR")
    ok(eq(nasion_vertical_offset_mm_v1((-5., 3.), n0, po, or_, .2), -1.), "NPERP_POSTERIOR")
    ok(eq(nasion_vertical_offset_mm_v1(move((5., 3.)), move(n0), move(po), move(or_), .2), 1.),
       "NPERP_TRANSLATION")
    ok(nasion_vertical_offset_mm_v1((5., 3.), n0, po, po, .2) is None, "NPERP_DEGENERATE_FH")
    ok(nasion_vertical_offset_mm_v1((5., 3.), n0, po, or_, 0.) is None, "NPERP_UNCALIBRATED")

    prn, pog_soft, lip, rpo, ror = (0., 0.), (0., 10.), (4., 5.), (0., 20.), (10., 20.)
    e = ricketts_e_line_perpendicular_signed_distance_px_v2
    ok(eq(e(lip, prn, pog_soft, rpo, ror), 4.), "ELINE_POSITIVE")
    ok(eq(e((-4., 5.), prn, pog_soft, rpo, ror), -4.), "ELINE_NEGATIVE")
    ok(eq(e(*(move(p) for p in (lip, prn, pog_soft, rpo, ror))), 4.), "ELINE_TRANSLATION")
    ok(e(lip, prn, prn, rpo, ror) is None, "ELINE_DEGENERATE_AXIS")
    ok(e(lip, prn, pog_soft, rpo, rpo) is None, "ELINE_DEGENERATE_FH")
    return checked


def main() -> None:
    doc = json.loads(CONTRACT.read_text(encoding="utf-8"))
    static = validate_bindings(doc)
    negatives = run_negative_controls(doc)
    geometry_checks = run_geometry_invariants()
    require(negatives == 12 and geometry_checks >= 20, "COUNTS")
    print(json.dumps({
        "schema": "DC_CEPH02_GEOMETRY_SOURCE_GATE_V1",
        "verdict": "SELECTED_GEOMETRY_AND_BINDINGS_PASS_ONLY",
        "contract_bindings_verified": static["bindings"],
        "distinct_implementation_modules": static["modules"],
        "angular_contracts": static["angle_contracts"],
        "linear_mm_contracts": static["mm_contracts"],
        "source_contract_paths_verified": static["sources_all_present"],
        "synthetic_geometry_invariants_passed": geometry_checks,
        "contract_mutations_rejected": negatives,
        "geometry_primitive_families_exercised": 5,
        "all_38_runtime_paths_executed": False,
        "clinical_numeric_parity_certified": False,
        "scientific_validation_complete": False,
        "facad_executed": False,
        "patient_data_accessed": False,
        "production_modified": False,
        "ceph_engine_concordant": False,
        "d3_vendor_isolation_verified": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
