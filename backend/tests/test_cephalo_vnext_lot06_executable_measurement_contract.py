import importlib
import json
from pathlib import Path

from backend.services.cephalo_measure_registry import CANONICAL_MEASUREMENTS

ROOT=Path(__file__).resolve().parents[2]
CONTRACT=ROOT/"docs"/"audits"/"schemas"/"cephalo_vnext_lot06_executable_measurement_contract_v1.json"

def load_contract():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))

def test_lot06_contract_entries_bind_existing_canonical_measurements():
    data=load_contract()
    assert data["schema_version"]=="CEPHALO_LOT06_EXECUTABLE_MEASUREMENT_CONTRACT_V1"
    assert data["clinical_interpretation"] is False
    ids=[m["measurement_id"] for m in data["measurements"]]
    assert len(ids)==len(set(ids))
    for entry in data["measurements"]:
        canonical=CANONICAL_MEASUREMENTS[entry["measurement_id"]]
        assert canonical.source_status.startswith("GEOMETRY_COVERED")
        assert canonical.unit==entry["unit"]
        assert entry["required_landmarks"]
        assert entry["source_contracts"]
        assert entry["availability_gate"]

def test_lot06_contract_implementation_symbols_are_importable_and_callable():
    for entry in load_contract()["measurements"]:
        module_name,symbol=entry["implementation"].split(":",1)
        module=importlib.import_module(module_name)
        assert callable(getattr(module,symbol))

def test_lot06_contract_keeps_ambiguous_identities_explicit():
    by_id={m["measurement_id"]:m for m in load_contract()["measurements"]}
    assert "Gn_anatomic" in by_id["M_SN_GOGN_DEG_V1"]["required_landmarks"]
    assert "Gn_anatomic" in by_id["M_CO_GN_ANATOMIC_MM_V1"]["required_landmarks"]
    assert "Po_anatomic" in by_id["M_FH_GOME_DEG_V1"]["required_landmarks"]
    assert "Po_anatomic" in by_id["M_FMIA_L1_FH_DEG_V1"]["required_landmarks"]
    assert "Po_anatomic" in by_id["M_B_NPERP_MM_V1"]["required_landmarks"]
    assert "Po_anatomic" in by_id["M_AB_PRIME_FH_MM_V1"]["required_landmarks"]

def test_lot06_contract_requires_calibration_for_every_mm_measurement():
    for entry in load_contract()["measurements"]:
        if entry["unit"]=="mm":
            assert entry["requires_calibration"] is True


def test_lot06_contract_construction_ids_exist_in_canonical_registry():
    registry=(ROOT/"docs"/"CEPHALO_CONSTRUCTION_REGISTRY.md").read_text(encoding="utf-8")
    for entry in load_contract()["measurements"]:
        for construction_id in entry["required_constructions"]:
            assert f"`{construction_id}`" in registry

def test_lot06_contract_uses_analysis_specific_mandibular_constructions():
    by_id={m["measurement_id"]:m for m in load_contract()["measurements"]}
    assert by_id["M_SN_GOGN_DEG_V1"]["required_constructions"]==["STEINER_MP_GO_GN_V1"]
    assert by_id["M_FH_GOME_DEG_V1"]["required_constructions"]==["FH_PO_OR_V1","TWEED_DC_MP_GO_ME_V1"]
    assert by_id["M_IMPA_GOME_DEG_V1"]["required_constructions"]==["TWEED_DC_MP_GO_ME_V1"]
    assert by_id["M_B_NPERP_MM_V1"]["required_constructions"]==["FH_PO_OR_V1","NASION_VERTICAL_FH_V1"]


def test_lot06_contract_exhausts_every_geometry_covered_registry_entry():
    data=load_contract()
    promoted={m["measurement_id"] for m in data["measurements"]}
    non_promoted={m["measurement_id"] for m in data["non_promoted_geometry_covered"]}
    covered={k for k,v in CANONICAL_MEASUREMENTS.items() if "GEOMETRY_COVERED" in v.source_status}
    assert promoted.isdisjoint(non_promoted)
    assert promoted | non_promoted == covered

def test_lot06_non_promoted_entries_are_explicitly_fail_closed():
    data=load_contract()
    reasons={m["measurement_id"]:m["reason"] for m in data["non_promoted_geometry_covered"]}
    assert reasons == {}
    promoted={m["measurement_id"] for m in data["measurements"]}
    assert "M_FACIAL_AXIS_RICKETTS_DEG_V1" in promoted
    assert "M_MAXILLARY_CONVEXITY_A_NPOG_MM_V1" in promoted
    assert "M_LI_EPLANE_MM_V1" in promoted
    assert "M_LS_EPLANE_MM_V1" in promoted
    assert "M_DOWNS_FACIAL_ANGLE_NPOG_FH_ACUTE_DEG_V1" in promoted
    assert "M_RICKETTS_FACIAL_DEPTH_NPOG_FH_POSTERIOR_DEG_V1" in promoted


def test_lot06_explicit_identity_gates_remain_fail_closed():
    data=load_contract()
    for entry in data["measurements"]:
        canonical=CANONICAL_MEASUREMENTS[entry["measurement_id"]]
        if canonical.source_status != "GEOMETRY_COVERED":
            assert "EXPLICIT" in canonical.source_status or "REQUIRED" in canonical.source_status
            assert any(token in entry["availability_gate"] for token in ("EXPLICIT","EXACT","VERIFIED"))
