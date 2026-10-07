#!/usr/bin/env python3
import json
from pathlib import Path

from backend.services.cephalo_measure_registry import CANONICAL_MEASUREMENTS

ROOT = Path(__file__).resolve().parents[1]

BACKEND_PROFILE = ROOT / "backend/data/cephalometry/steiner_protocol_profile_v1.json"
DOCS_PROFILE = ROOT / "docs/audits/schemas/ortho_lot08_steiner_protocol_profile_v1.json"
RESOLUTION = ROOT / "docs/audits/schemas/ortho_lot08_facad_dc_steiner_gap_resolution_v1.json"
MAPPING = ROOT / "docs/audits/schemas/ortho_lot08_facad_dc_existing_protocol_mapping_v1.json"
BACKLOG = ROOT / "docs/audits/schemas/ortho_lot08_facad_dc_unmapped_backlog_v1.json"
EXECUTABLE = ROOT / "docs/audits/schemas/cephalo_vnext_lot06_executable_measurement_contract_v1.json"
CANONICAL_MD = ROOT / "docs/audits/CEPHALO_CANONICAL_MEASUREMENT_REGISTRY.md"

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

def fail(message):
    raise SystemExit(message)

def main():
    backend = load(BACKEND_PROFILE)
    docs = load(DOCS_PROFILE)
    resolution = load(RESOLUTION)
    mapping = load(MAPPING)
    backlog = load(BACKLOG)
    executable = load(EXECUTABLE)
    canonical = CANONICAL_MD.read_text(encoding="utf-8")

    if backend != docs:
        fail("Steiner backend/docs profiles diverge")

    sources = {item.get("id"): item for item in backend.get("sources", []) if isinstance(item, dict)}
    vendor_source = sources.get("FACAD_314_STEINER_CPH")
    if not isinstance(vendor_source, dict) or vendor_source.get("scientific_authority") is not False:
        fail("Facad Steiner CPH must remain vendor compatibility evidence only")
    secondary_source = sources.get("PMID_38909276_STEINER_SLINE")
    if not isinstance(secondary_source, dict) or secondary_source.get("primary_historical_authority") is not False:
        fail("Steiner S-line secondary source must not become primary historical authority")

    rels = backend["layers"]["STEINER_1959_EXTENSION"]["derived_relationships"]
    rel = next((x for x in rels if x.get("relationship_id") == "STEINER_L1_NB_VS_POG_NB_V1"), None)
    if rel is None:
        fail("Missing Steiner L1-NB vs Pog-NB relationship")
    compat = rel.get("facad_compatibility") or {}
    if compat.get("facad_label") != "Ii-Pog // NB":
        fail("Facad relationship label mismatch")
    if compat.get("calc_type") != "Sub":
        fail("Facad relationship calc type mismatch")
    if compat.get("ordered_inputs") != ["M_L1_NB_MM_V1", "M_POG_NB_MM_V1"]:
        fail("Facad relationship ordered inputs mismatch")
    if compat.get("runtime_numeric_presentation") != "NOT_EXPOSED":
        fail("Facad relationship must remain non-exposed")

    identities = backend.get("explicit_manual_or_constructed_identities") or {}
    ms = identities.get("MS_Steiner", "")
    for forbidden in ("Cm", "Sn_soft", "Prn"):
        if forbidden not in ms:
            fail(f"MS_Steiner guard missing forbidden alias {forbidden}")

    sline = backend.get("separate_profiles", {}).get("STEINER_SLINE_COMPATIBILITY_V1")
    if not isinstance(sline, dict):
        fail("Missing Steiner S-line compatibility profile")
    if "BLOCKED_EXACT_MS_STEINER" not in sline.get("status", ""):
        fail("S-line profile must remain blocked on exact MS_Steiner")
    if sline.get("facad_reference_values_runtime_authority") is not False:
        fail("Facad S-line reference values must not gain runtime authority")
    if sline.get("same_trace_numeric_parity_observed") is not False:
        fail("S-line same-trace parity must remain unobserved")

    decisions = resolution.get("decisions") or {}
    if decisions.get("Ii-Pog // NB", {}).get("decision") != "EXISTING_DERIVED_RELATIONSHIP":
        fail("Ii-Pog relationship resolution mismatch")
    for label in ("Ls-SL", "Li-SL"):
        item = decisions.get(label) or {}
        if item.get("decision") != "BLOCKED_EXACT_LANDMARK_AND_HISTORICAL_PRIMARY_AUTHORITY":
            fail(f"{label} resolution mismatch")
        if item.get("dc_missing_exact_identity") != "MS_Steiner":
            fail(f"{label} missing identity mismatch")
        if set(item.get("forbidden_aliases") or []) != {"Cm", "Sn_soft", "Prn"}:
            fail(f"{label} forbidden alias set mismatch")

    steiner_map = mapping["profiles"]["Steiner"]["mappings"]
    expected_labels = {
        "SNA","SNB","ANB","OL/NSL","ML/NSL","Is-NA","ILs/NA","Ii-NB",
        "ILi/NB","InterIncisal","Pog-NB","Ii-Pog // NB","Ls-SL","Li-SL"
    }
    if set(steiner_map) != expected_labels:
        fail("Steiner Facad mapping is not exhaustive")
    if steiner_map["Ii-Pog // NB"].get("dc_relationship_id") != "STEINER_L1_NB_VS_POG_NB_V1":
        fail("Steiner derived relationship mapping mismatch")
    for label in ("Ls-SL", "Li-SL"):
        item = steiner_map[label]
        if item.get("status") != "BLOCKED_EXACT_LANDMARK" or item.get("required_identity") != "MS_Steiner":
            fail(f"{label} blocked mapping mismatch")

    steiner_backlog = backlog["profiles"]["Steiner"]
    if steiner_backlog.get("unmapped") != []:
        fail("Steiner backlog still has unmapped rows")
    if backlog.get("totals", {}).get("unmapped_items") != 39:
        fail("Global unmapped count must be 39 after Steiner resolution")

    executable_ids = {x.get("measurement_id") for x in executable.get("measurements", [])}
    blocked_ids = {"M_LS_STEINER_SLINE_MM_V1", "M_LI_STEINER_SLINE_MM_V1"}
    if executable_ids & blocked_ids:
        fail("Blocked Steiner S-line measurements leaked into executable contract")
    for measurement_id in blocked_ids:
        if measurement_id not in canonical:
            fail(f"Canonical registry markdown missing {measurement_id}")
        item = CANONICAL_MEASUREMENTS.get(measurement_id)
        if item is None:
            fail(f"Runtime canonical registry missing {measurement_id}")
        if item.unit != "mm":
            fail(f"Runtime canonical unit mismatch for {measurement_id}")
        if item.source_status != "BLOCKED_LANDMARK_MS_STEINER+FACAD_SAME_TRACE_SIGN_PARITY_PENDING":
            fail(f"Runtime canonical blocked status mismatch for {measurement_id}")

    guards = resolution.get("runtime_guards") or {}
    if guards.get("primary_historical_authority_for_sline_locked") is not False:
        fail("S-line primary historical authority must remain unlocked")
    if guards.get("facad_same_trace_numeric_parity_observed") is not False:
        fail("Facad same-trace parity must remain false")

    print("STEINER_FACAD_GAP_RESOLUTION=PASS")
    print("STEINER_UNMAPPED=0")
    print("STEINER_EXISTING_RELATIONSHIP=1")
    print("STEINER_BLOCKED_EXACT_LANDMARK=2")

if __name__ == "__main__":
    main()
