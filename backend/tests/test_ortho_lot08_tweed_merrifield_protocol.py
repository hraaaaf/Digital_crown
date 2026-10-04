import json
from pathlib import Path

from backend.services.cephalo_measure_registry import CANONICAL_MEASUREMENTS
from backend.services.cephalo_protocol_projection import project_tweed_merrifield_protocol

ROOT = Path(__file__).resolve().parents[2]
PROFILE = ROOT / "docs/audits/schemas/ortho_lot08_tweed_merrifield_protocol_profile_v1.json"


def _profile():
    return json.loads(PROFILE.read_text(encoding="utf-8"))


def _canonical(cid, value, status="AVAILABLE"):
    return {
        "canonical_measurement_id": cid,
        "value": value if status == "AVAILABLE" else None,
        "unit": "deg",
        "availability_status": status,
        "measurement_refs": [f"m:{cid}"],
        "value_authority_method_id": f"METHOD:{cid}",
    }


def test_profile_source_locked_and_lot06_authoritative():
    p = _profile()
    assert p["status"] == "SOURCE_LOCKED"
    assert p["scientific_authority"] == "LOT06_CANONICAL_MEASUREMENT_REGISTRY"
    assert p["pre_code_gate"]["status"] == "SATISFIED"
    assert p["final_gate"]["status"] == "OPEN"
    assert p["execution_policy"]["parallel_formula_outside_LOT06"] == "FORBIDDEN"


def test_every_required_identity_is_canonical():
    p = _profile()
    ids = []
    for section in p["profiles"].values():
        ids += section.get("required_measurement_ids", [])
        ids += section.get("context_measurement_ids", [])
    assert sorted(set(ids) - set(CANONICAL_MEASUREMENTS)) == []


def test_selected_dc_variant_resolves_product_geometry_without_claiming_strict_1954_equivalence():
    p = _profile()
    historical = p["historical_geometry_resolution"]["TWEED_1954_STRICT_EAR_ROD_FH"]
    selected = p["historical_geometry_resolution"]["TWEED_DC_MP_GO_ME_V1"]
    assert historical["status"] == "HISTORICAL_NOT_SELECTED"
    assert historical["equivalence_claim"] == "FORBIDDEN"
    assert selected["status"] == "SELECTED_DC_CONTRACT"
    assert p["scope_resolutions"]["STRICT_TWEED_1954_GEOMETRY"].endswith("NOT_A_PRODUCT_BLOCKER")


def test_historical_context_cannot_classify_or_generate_runtime_delta():
    p = _profile()
    for reference in p["reference_contexts"]:
        assert reference["classification_authority"] is False
        assert reference["runtime_delta_authority"] is False
    assert p["scope_resolutions"]["AUTONOMOUS_TREATMENT"] == "FORBIDDEN"
    assert p["scope_resolutions"]["EXTRACTION_NON_EXTRACTION"] == "CLINICIAN_ONLY"


def test_projection_has_four_fail_closed_raw_rows_without_fake_norm_delta():
    rows = [
        _canonical("M_FH_GOME_DEG_V1", 24.5),
        _canonical("M_IMPA_GOME_DEG_V1", 89.0),
        _canonical("M_FMIA_L1_FH_DEG_V1", 66.5),
        _canonical("M_MERRIFIELD_Z_FH_DEG_V1", 79.0),
    ]
    out = project_tweed_merrifield_protocol(rows)
    assert out["protocol_profile_id"] == "TWEED_MERRIFIELD_DC_PROTOCOL_PROFILE_V1"
    assert out["source_lock_gate"]["status"] == "SATISFIED"
    assert len(out["rows"]) == 4
    assert {row["value"] for row in out["rows"]} == {24.5, 89.0, 66.5, 79.0}
    assert all(row["classification_authority"] is False for row in out["rows"])
    assert all(row["reference_authority"] == "CONTEXT_ONLY_NO_RUNTIME_DELTA" for row in out["rows"])


def test_projection_missing_measurements_fail_closed():
    out = project_tweed_merrifield_protocol([])
    assert len(out["rows"]) == 4
    assert all(row["availability_status"] == "NOT_COMPUTABLE" for row in out["rows"])
    assert all(row["value"] is None for row in out["rows"])


def test_runtime_profile_copy_matches_frozen_audit_profile():
    runtime = ROOT / "backend/data/cephalometry/tweed_merrifield_protocol_profile_v1.json"
    assert runtime.read_bytes() == PROFILE.read_bytes()


def test_primary_source_manifest_and_applicability_are_explicit():
    p = _profile()
    sources = {item["id"]: item for item in p["sources"]}
    assert sources["TWEED_1946_FMA"]["doi"] == "10.1016/0096-6347(46)90001-4"
    assert "tweedortho.com" in sources["TWEED_1954_FMIA"]["url"]
    assert sources["TWEED_1969_TRIANGLE"]["doi"] == "10.1016/0002-9416(69)90041-4"
    assert sources["MERRIFIELD_1966_PROFILE_LINE"]["doi"] == "10.1016/0002-9416(66)90250-8"
    strict = p["historical_geometry_resolution"]["TWEED_1954_STRICT_EAR_ROD_FH"]
    assert "4.5 mm" in strict["definition"]
    merrifield = next(item for item in p["reference_contexts"] if item["reference_id"] == "MERRIFIELD_1966_Z_CONTEXT_V1")
    assert merrifield["adult_reference_deg"] == 80.0
    assert merrifield["age_11_15_reference_deg"] == 78.0
    assert "NOT_AUTO_PROVEN" in merrifield["applicability_condition"]
