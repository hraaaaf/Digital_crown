#!/usr/bin/env python3
"""DC-CEPH-02E: independent analytic oracles for four still-BLOCKED CRANIOM geometries.

Only synthetic point tuples. File-based loading runs the exact source functions,
not the whole backend. This tests arithmetic, not clinical equivalence,
canonical identity authorization, deployment readiness, or numerical vendor parity.
"""
from __future__ import annotations

import ast
import copy
import importlib.util
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/audits/DC_CEPH02E_INDEPENDENT_GEOMETRY_EVIDENCE_V1.json"
CONTRACT = ROOT / "docs/audits/schemas/cephalo_vnext_lot06_executable_measurement_contract_v1.json"
BRIDGE = ROOT / "backend/services/cephalo_canonical_method_bridge.py"

EXPECTED = {
    "M_AB_PRIME_FH_MM_V1": {
        "method": "CRANIOM_AB_PRIME_MM_V1",
        "implementation": "backend.services.cephalo_constructions:craniom_ab_prime_mm_v1",
        "landmarks": ["A", "B", "Po_anatomic", "Or"],
        "constructions": ["FH_PO_OR_V1", "CRANIOM_AB_PRIME_V1"],
        "operation": "SIGNED_FH_PROJECTION_A_MINUS_B", "unit": "mm",
        "literature": ("https://pubmed.ncbi.nlm.nih.gov/2639735/",),
    },
    "M_B_NPERP_MM_V1": {
        "method": "CRANIOM_SITUATION_B_MM_V1",
        "implementation": "backend.services.cephalo_constructions:nasion_vertical_offset_mm_v1",
        "landmarks": ["B", "N", "Po_anatomic", "Or"],
        "constructions": ["FH_PO_OR_V1", "NASION_VERTICAL_FH_V1"],
        "operation": "SIGNED_FH_PROJECTION_B_MINUS_N", "unit": "mm",
        "literature": ("https://pmc.ncbi.nlm.nih.gov/articles/PMC4436328/",),
    },
    "M_COM_S_NPERP_DEPTH_MM_V1": {
        "method": "CRANIOM_FACIAL_DEPTH_MM_V1",
        "implementation": "backend.services.cephalo_constructions:craniom_facial_depth_mm_v1",
        "landmarks": ["S", "N", "Po_anatomic", "Or"],
        "constructions": ["FH_PO_OR_V1", "NASION_VERTICAL_FH_V1", "CRANIOM_S_TO_N_VERTICAL_DEPTH_V1"],
        "operation": "ABSOLUTE_FH_PROJECTION_S_MINUS_N", "unit": "mm",
        "literature": ("https://www.ncbi.nlm.nih.gov/sites/books/NBK594272/table/article-131913.table2/",),
    },
    "M_U1_FH_DEG_V1": {
        "method": "CRANIOM_U1_FRANKFORT_DEG_V1",
        "implementation": "backend.services.cephalo_craniom_angular:craniom_u1_frankfort_deg_v1",
        "landmarks": ["U1_apex", "U1_incisal", "Po_anatomic", "Or"],
        "constructions": ["FH_PO_OR_V1"],
        "operation": "SUPPLEMENT_180_MINUS_ACOS_U1_APEX_TO_INCISAL_VS_PO_TO_OR", "unit": "°",
        "literature": (
            "https://pmc.ncbi.nlm.nih.gov/articles/PMC3059215/",
            "https://www.mdpi.com/2075-4418/15/12/1553",
        ),
    },
}


class GateError(ValueError):
    pass


def check(condition: bool, code: str) -> None:
    if not condition:
        raise GateError(code)


def parsed_bridge():
    tree = ast.parse(BRIDGE.read_text(encoding="utf-8"))
    rows = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_b":
            if len(node.args) == 4 and all(isinstance(a, ast.Constant) for a in node.args):
                method, canonical, state, reason = (x.value for x in node.args)
                if method in rows:
                    raise GateError("DUPLICATE_BRIDGE_METHOD")
                rows[method] = (canonical, state, reason)
    return rows


def validate(manifest: dict, registry: dict, bridge: dict) -> dict:
    check(manifest.get("schema") == "DC_CEPH02E_INDEPENDENT_GEOMETRY_EVIDENCE_V1", "SCHEMA")
    check(manifest.get("version") == 1, "VERSION")
    check(manifest.get("based_on_head") == "caa436da9b105ee2d26c176d47bab255c6da21ac", "SOURCE_HEAD")
    check(manifest.get("intent") == "DIAGNOSTIC_GEOMETRY_ORACLES_ONLY", "INTENT")
    check(manifest.get("literature_role") == "SUPPORTS_GENERIC_GEOMETRY_NOT_SOURCE_LOCKED_IDENTITY_PARITY",
          "LITERATURE_LIMIT")
    check(manifest.get("decision") == "ALL_FOUR_BLOCKED_PENDING_ANATOMICAL_LINEAGE_AND_CLINICAL_ADJUDICATION",
          "DECISION")
    for key in ("patient_data_used", "vendor_executed", "clinical_unblock_allowed",
                "clinical_norms_added", "formula_runtime_modified"):
        check(manifest.get(key) is False, "NO_PRODUCTION_OR_CLINICAL_PROMOTION_" + key.upper())
    check(manifest.get("requires_external_orthodontist_review") is True, "EXTERNAL_CLINICAL_REVIEW")
    recs = manifest.get("methods", [])
    check(isinstance(recs, list) and len(recs) == 4, "FOUR_ONLY")
    check({x.get("canonical_id") for x in recs} == set(EXPECTED), "EXACT_IDENTITIES")
    contract = {x["measurement_id"]: x for x in registry.get("measurements", [])}
    check(len(contract) == 38 and len(registry["measurements"]) == 38, "SOURCE_REGISTRY")
    modules = set()
    for rec in recs:
        key = rec["canonical_id"]
        definition = EXPECTED[key]
        source = contract[key]
        check(rec.get("legacy_method_id") == definition["method"], "LEGACY_IDENT_" + key)
        check(rec.get("function") == definition["implementation"] ==
              source.get("implementation"), "SOURCE_FUNCTION_" + key)
        check(rec.get("points") == definition["landmarks"] ==
              source.get("required_landmarks"), "ANATOMIC_POINTS_" + key)
        check(rec.get("construction_ids") == definition["constructions"] ==
              source.get("required_constructions"), "CONSTRUCTION_IDS_" + key)
        check(rec.get("unit") == definition["unit"] == source.get("unit"), "UNIT_" + key)
        check(rec.get("operation") == definition["operation"], "SIGNED_CONVENTION_" + key)
        check(rec.get("calibration_required") is (definition["unit"] == "mm"), "CALIBRATION_" + key)
        check(source.get("requires_calibration") is rec.get("calibration_required"),
              "SOURCE_CALIBRATION_" + key)
        check(rec.get("runtime_state") == "BLOCKED" and
              rec.get("runtime_reason") == "LEGACY_LANDMARK_IDENTITY_BRIDGE_REQUIRED",
              "FAIL_CLOSED_STATE_" + key)
        check(bridge.get(definition["method"]) ==
              (None, "BLOCKED", "LEGACY_LANDMARK_IDENTITY_BRIDGE_REQUIRED"),
              "SOURCE_BRIDGE_" + key)
        for lock in ("clinical_activation_allowed", "scientific_authority_certified",
                     "facad_numeric_parity_certified"):
            check(rec.get(lock) is False, "NO_AUTHORITY_" + key + lock)
        check(isinstance(rec.get("missing_evidence"), list)
              and "ORTHODONTIST_SIGNOFF" in rec["missing_evidence"]
              and "NUMERIC_SAME_TRACE_ADJUDICATION" in rec["missing_evidence"],
              "OPEN_EVIDENCE_" + key)
        check(isinstance(rec.get("source_internal"), list)
              and set(rec["source_internal"]) == {
                  "docs/CEPHALO_CONSTRUCTION_REGISTRY.md",
                  "docs/audits/CEPHALO_GEOMETRIC_MEASUREMENT_CONTRACTS.md",
              }, "INTERNAL_PROVENANCE_" + key)
        check(all((ROOT / p).is_file() for p in rec["source_internal"]), "MISSING_INTERNAL_SOURCE")
        references = rec.get("literature")
        check(isinstance(references, list) and tuple(x.get("url") for x in references)
              == definition["literature"], "LITERATURE_SCOPE_" + key)
        check(all(isinstance(x.get("scope"), str) and "NOT" in x["scope"]
                  and len(x["scope"]) >= 24 for x in references), "NO_UNBOUNDED_LITERATURE_CLAIMS_" + key)
        check(isinstance(rec.get("source_identity_proof"), str)
              and "PROVEN" not in rec["source_identity_proof"]
              and "CERTIFIED" not in rec["source_identity_proof"], "IDENTITY_UNPROVEN_" + key)
        module_name, func_name = definition["implementation"].split(":")
        path = ROOT / (module_name.replace(".", "/") + ".py")
        check(path.is_file(), "SOURCE_MODULE_MISSING_" + key)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        check(any(isinstance(node, ast.FunctionDef) and node.name == func_name
                  for node in tree.body), "SOURCE_FUNCTION_MISSING_" + key)
        modules.add(module_name)
    return {"source_rows": len(recs), "implementation_modules": len(modules)}


def oracle_linear(args, signed=True):
    # Independent analytic definition, not a call into production's axis helpers.
    target, origin, po, orbitale, ratio = args
    if any(p is None for p in (target, origin, po, orbitale)):
        return None
    if ratio is None or not math.isfinite(ratio) or ratio <= 0:
        return None
    delta = (orbitale[0] - po[0], orbitale[1] - po[1])
    magnitude = math.hypot(*delta)
    if not math.isfinite(magnitude) or magnitude <= 1e-12:
        return None
    scalar = ((target[0] - origin[0]) * delta[0] +
              (target[1] - origin[1]) * delta[1]) / magnitude
    value = scalar * ratio if signed else abs(scalar) * ratio
    return value if math.isfinite(value) else None


def oracle_angle(args):
    apex, incisal, po, orbitale = args
    if any(p is None for p in (apex, incisal, po, orbitale)):
        return None
    u = (incisal[0] - apex[0], incisal[1] - apex[1])
    h = (orbitale[0] - po[0], orbitale[1] - po[1])
    lengths = (math.hypot(*u), math.hypot(*h))
    if not all(math.isfinite(q) and q > 1e-12 for q in lengths):
        return None
    dot = (u[0] * h[0] + u[1] * h[1]) / (lengths[0] * lengths[1])
    raw = math.degrees(math.acos(max(-1.0, min(1.0, dot))))
    value = 180.0 - raw
    return value if math.isfinite(value) else None


def close(actual, expected, code):
    if expected is None:
        check(actual is None, code + "_FAIL_CLOSED")
    else:
        check(actual is not None and math.isfinite(actual)
              and math.isclose(actual, expected, rel_tol=1e-11, abs_tol=1e-9), code + "_WRONG_VALUE")


def geometry_suite():
    # No backend/package import: load the existing production function files directly.
    funcs = {}
    for mid, config in EXPECTED.items():
        module, symbol = config["implementation"].split(":")
        if module not in funcs:
            path = ROOT / (module.replace(".", "/") + ".py")
            spec = importlib.util.spec_from_file_location("dc_ceph02e_" + module.rsplit(".", 1)[-1], path)
            check(spec is not None and spec.loader is not None, "MODULE_LOADER")
            obj = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(obj)
            funcs[module] = obj
    samples = {
        "M_AB_PRIME_FH_MM_V1": ((6.,4.), (2.,-1.), (0.,0.), (10.,0.), 0.5),
        "M_B_NPERP_MM_V1": ((4.,3.), (1.,9.), (0.,0.), (10.,0.), 0.5),
        "M_COM_S_NPERP_DEPTH_MM_V1": ((-4.,7.), (1.,9.), (0.,0.), (10.,0.), 0.5),
        "M_U1_FH_DEG_V1": ((0.,0.), (3.,4.), (0.,0.), (10.,0.)),
    }
    num = 0
    def compare(fn, oracle, args, label):
        nonlocal num
        close(fn(*args), oracle(args), label)
        num += 1
    def translated(args):
        return tuple((x+27., y-18.) for x,y in args[:4]) + args[4:]
    def rotated(args):
        t = math.radians(39)
        c, s = math.cos(t), math.sin(t)
        return tuple((c*x-s*y, s*x+c*y) for x,y in args[:4]) + args[4:]
    def scaled(args):
        points = tuple((3*x,3*y) for x,y in args[:4])
        return points + (args[4] / 3.,) if len(args) == 5 else points
    for mid, cfg in EXPECTED.items():
        module, symbol = cfg["implementation"].split(":")
        fn = getattr(funcs[module], symbol)
        args = samples[mid]
        oracle = oracle_angle if cfg["unit"] == "°" else (
            (lambda a: oracle_linear(a, signed=False)) if mid == "M_COM_S_NPERP_DEPTH_MM_V1"
            else (lambda a: oracle_linear(a, signed=True))
        )
        for transform, label in ((lambda x: x,"baseline"),(translated,"translation"),
                                 (rotated,"rigid_rotation"),(scaled,"scale_compensated")):
            compare(fn,oracle,transform(args),mid+"_"+label)
        # Deliberate vector reversal: signed distances invert, magnitude does not.
        reversed_fh = args[:2] + (args[3], args[2]) + args[4:]
        compare(fn,oracle,reversed_fh,mid+"_fh_reversal")
        if len(args) == 5:
            for invalid in (None, 0., -2., float("nan"), float("inf")):
                compare(fn, oracle, args[:4] + (invalid,), mid+"_invalid_ratio")
        for i in (0, 2, 3):
            bad = list(args)
            bad[i] = None
            compare(fn,oracle,tuple(bad),mid+"_missing_point_"+str(i))
        # Construct fully degenerate Frankfort and ensure no stale output.
        compare(fn,oracle,args[:3]+(args[2],)+args[4:],mid+"_zero_fh")
        if len(args) == 4:
            # A zero upper-incisor long axis must be unavailable.
            compare(fn,oracle,(args[0],args[0],args[2],args[3]),mid+"_zero_incisor_axis")
        # One manifest-defined sign/magnitude convention on easily audited axes.
        base_value = fn(*args)
        if mid == "M_AB_PRIME_FH_MM_V1":
            close(base_value,2.0,mid+"_sign")
        elif mid == "M_B_NPERP_MM_V1":
            close(base_value,1.5,mid+"_sign")
        elif mid == "M_COM_S_NPERP_DEPTH_MM_V1":
            close(base_value,2.5,mid+"_nonnegative")
        elif mid == "M_U1_FH_DEG_V1":
            close(base_value,180.0-math.degrees(math.atan2(4.,3.)),mid+"_supplement")
        num += 1
    return num


def negative_controls(manifest, registry, bridge):
    tests = [
        lambda x: x.update(clinical_unblock_allowed=True),
        lambda x: x.update(clinical_norms_added=True),
        lambda x: x.update(formula_runtime_modified=True),
        lambda x: x.update(requires_external_orthodontist_review=False),
        lambda x: x.update(based_on_head="0"*40),
        lambda x: x["methods"][0].update(runtime_state="MAPPED"),
        lambda x: x["methods"][1].update(points=["Pog_hard", "N", "Po_anatomic", "Or"]),
        lambda x: x["methods"][0].update(operation="WITS_OCCLUSAL_PLANE_DISTANCE"),
        lambda x: x["methods"][2].update(source_identity_proof="CERTIFIED_BY_FACAD"),
        lambda x: x["methods"][3].update(scientific_authority_certified=True),
        lambda x: x["methods"][0]["literature"].clear(),
        lambda x: x["methods"][0].update(missing_evidence=[]),
        lambda x: x["methods"][3].update(function="backend.services.cephalo_craniom_angular:craniom_l1_downs_deg_v1"),
    ]
    for n, mutate in enumerate(tests):
        trial = copy.deepcopy(manifest)
        mutate(trial)
        try:
            validate(trial,registry,bridge)
        except GateError:
            continue
        raise GateError("FAIL_OPEN_MUTATION_"+str(n))
    return len(tests)


def main():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    registry = json.loads(CONTRACT.read_text(encoding="utf-8"))
    bridge = parsed_bridge()
    source_check = validate(manifest,registry,bridge)
    checks = geometry_suite()
    mutations = negative_controls(manifest,registry,bridge)
    check(source_check["source_rows"] == 4 and source_check["implementation_modules"] == 2,
          "FOUR_ORACLES_TWO_REAL_SOURCE_MODULES")
    check(checks >= 30 and mutations == 13, "COVERAGE_FLOOR")
    print(json.dumps({
        "schema":"DC_CEPH02E_SAFE_SOURCE_ORACLE_REPORT_V1",
        "verdict":"FOUR_PRIMITIVES_CHECKED__FOUR_IDENTITY_GATES_STILL_BLOCKED",
        "contract_rows_verified":source_check["source_rows"],
        "real_geometry_modules":source_check["implementation_modules"],
        "independent_synthetic_oracles_executed":checks,
        "fail_closed_contract_mutations_rejected":mutations,
        "clinical_unblocks":0,
        "facad_executions":0,
        "clinical_source_equivalence_proved":False,
        "external_orthodontist_review_completed":False,
        "numeric_same_trace_vendor_parity_proved":False,
        "patient_data_accessed":False,
        "production_modified":False,
    },sort_keys=True,separators=(",",":")))


if __name__=="__main__":
    main()
