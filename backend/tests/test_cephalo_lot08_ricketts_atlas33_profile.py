import json
from pathlib import Path

from backend.services.cephalo_measure_registry import canonical_measurement

ROOT = Path(__file__).resolve().parents[2]
PROFILE = ROOT / "docs/audits/schemas/ortho_lot08_ricketts_atlas2009_complete33_protocol_profile_v1.json"
COMPAT = ROOT / "docs/audits/schemas/ortho_lot08_facad_ricketts_compatibility_targets_v1.json"
COMPOSITION = ROOT / "docs/audits/CEPHALO_LOT08_RICKETTS_ATLAS2009_COMPLETE33_COMPOSITION_LOCK.md"


def test_atlas2009_profile_contains_exactly_33_unique_ordered_rows():
    data = json.loads(PROFILE.read_text(encoding="utf-8"))
    rows = data["measurements"]
    assert len(rows) == 33
    assert [row["order"] for row in rows] == list(range(1, 34))
    non_null = [row["measurement_id"] for row in rows if row["measurement_id"]]
    assert len(non_null) == len(set(non_null))


def test_atlas2009_wave_a_rows_are_source_specific_and_fail_closed():
    data = json.loads(PROFILE.read_text(encoding="utf-8"))
    rows = {row["order"]: row for row in data["measurements"]}
    assert rows[1]["measurement_id"] == "M_RICKETTS_MOLAR_RELATION_FOP_MM_V1"
    assert rows[2]["measurement_id"] == "M_RICKETTS_CANINE_RELATION_FOP_MM_V1"
    assert rows[3]["measurement_id"] == "M_RICKETTS_OVERJET_FOP_MM_V1"
    assert rows[4]["measurement_id"] == "M_RICKETTS_OVERBITE_FOP_MM_V1"
    assert rows[4]["state"] == "CONDITIONAL_EXECUTABLE"
    assert rows[4]["gate"] == "VERSIONED_IMAGE_ORIENTATION_EVIDENCE_REQUIRED"
    assert rows[10]["measurement_id"] == "M_L1_EDGE_APOG_MM_V1"
    assert rows[10]["state"] == "EXECUTABLE"
    assert "PERPENDICULAR_APOG__ANTERIOR_POSITIVE" in rows[10]["gate"]
    assert rows[11]["measurement_id"] == "M_RICKETTS_U1_APOG_PROTRUSION_MM_V1"
    assert rows[11]["state"] == "EXECUTABLE"
    assert "PERPENDICULAR_APOG__ANTERIOR_POSITIVE" in rows[11]["gate"]
    assert rows[13]["measurement_id"] == "M_RICKETTS_U1_APOG_INCLINATION_DEG_V1"


def test_atlas2009_every_non_null_measurement_is_registered():
    data = json.loads(PROFILE.read_text(encoding="utf-8"))
    missing = [
        row["measurement_id"]
        for row in data["measurements"]
        if row["measurement_id"] and canonical_measurement(row["measurement_id"]) is None
    ]
    assert missing == []


def test_atlas2009_factor_29_conflict_resolution_is_explicit_and_auditable():
    data = json.loads(PROFILE.read_text(encoding="utf-8"))
    row = data["measurements"][28]
    assert row["order"] == 29
    assert row["measurement_id"] == "M_RICKETTS_TOTAL_FACIAL_HEIGHT_BAN_XIPM_DEG_V1"
    assert row["state"] == "CONDITIONAL_EXECUTABLE"
    assert "SOURCE_LABEL_CONFLICT_RESOLVED_AS_TOTAL_FACIAL_HEIGHT" in row["gate"]
    text = COMPOSITION.read_text(encoding="utf-8")
    assert "Factor 29 conflict — resolved" in text
    assert "Total Facial Height" in text


def test_facad_targets_remain_parity_only_and_not_scientific_equivalence():
    data = json.loads(COMPAT.read_text(encoding="utf-8"))
    assert data["status"] == "PARITY_TARGETS_ONLY__MEMBERSHIP_NOT_DIRECTLY_OBSERVED"
    assert {item["vendor_label"] for item in data["targets"]} == {"Ricketts (32 F)", "Ricketts (13 F)"}
    assert all(item["scientific_profile_equivalence"] is False for item in data["targets"])


def test_atlas2009_normative_classification_stays_disabled():
    data = json.loads(PROFILE.read_text(encoding="utf-8"))
    assert data["normative_state"]["universal_classification"] is False
    assert data["normative_state"]["vert_enabled"] is False
    assert data["rules"]["historical_norms_reference_only"] is True


def test_atlas2009_wave_b_rows_are_locked_and_fail_closed():
    data = json.loads(PROFILE.read_text(encoding="utf-8"))
    rows = {row["order"]: row for row in data["measurements"]}

    assert rows[14]["measurement_id"] == "M_RICKETTS_OCCLUSAL_PLANE_XI_MM_V1"
    assert rows[14]["state"] == "CONDITIONAL_EXECUTABLE"
    assert rows[14]["gate"] == "VERSIONED_IMAGE_ORIENTATION_EVIDENCE_REQUIRED"
    assert rows[15]["measurement_id"] == "M_RICKETTS_OCCLUSAL_PLANE_XIPM_DEG_V1"
    assert rows[15]["state"] == "CONDITIONAL_EXECUTABLE"
    assert rows[17]["measurement_id"] == "M_RICKETTS_UPPER_LIP_LENGTH_ANS_COMMISSURE_MM_V1"
    assert rows[17]["state"] == "CONDITIONAL_EXECUTABLE"
    assert rows[18]["measurement_id"] == "M_RICKETTS_COMMISSURE_FOP_MM_V1"
    assert rows[18]["state"] == "CONDITIONAL_EXECUTABLE"
    assert rows[18]["gate"] == "VERSIONED_IMAGE_ORIENTATION_EVIDENCE_REQUIRED"
    assert rows[21]["measurement_id"] == "M_RICKETTS_FACIAL_TAPER_NPOG_MP_DEG_V1"
    assert rows[23]["measurement_id"] == "M_RICKETTS_MAXILLARY_HEIGHT_NCFA_DEG_V1"
    assert rows[24]["measurement_id"] == "M_RICKETTS_PALATAL_PLANE_FH_DEG_V1"
    assert all(rows[index]["state"] == "CONDITIONAL_EXECUTABLE" for index in (21, 23))
    assert rows[24]["state"] == "CONDITIONAL_EXECUTABLE"
    assert rows[24]["gate"] == "VERSIONED_IMAGE_ORIENTATION_EVIDENCE_REQUIRED"


def test_atlas2009_wave_b_new_ids_are_registered():
    data = json.loads(PROFILE.read_text(encoding="utf-8"))
    ids = [
        row["measurement_id"]
        for row in data["measurements"]
        if row["order"] in {14, 15, 17, 18, 21, 23, 24}
    ]
    assert all(measurement_id is not None for measurement_id in ids)
    assert all(canonical_measurement(measurement_id) is not None for measurement_id in ids)


def test_atlas2009_wave_c_rows_close_remaining_new_canonicals():
    data = json.loads(PROFILE.read_text(encoding="utf-8"))
    rows = {row["order"]: row for row in data["measurements"]}
    expected = {
        26: "M_RICKETTS_CRANIAL_DEFLECTION_FH_BAN_DEG_V1",
        27: "M_RICKETTS_ANTERIOR_CRANIAL_LENGTH_CC_N_MM_V1",
        28: "M_RICKETTS_POSTERIOR_FACIAL_HEIGHT_GO_CF_MM_V1",
        29: "M_RICKETTS_TOTAL_FACIAL_HEIGHT_BAN_XIPM_DEG_V1",
        30: "M_RICKETTS_RAMUS_POSITION_FH_CFXI_DEG_V1",
        31: "M_RICKETTS_PORION_LOCATION_PTV_MM_V1",
        32: "M_RICKETTS_MANDIBULAR_ARC_DCXI_XIPM_DEG_V1",
        33: "M_RICKETTS_CORPUS_LENGTH_XI_PM_MM_V1",
    }
    assert {index: rows[index]["measurement_id"] for index in expected} == expected
    assert rows[26]["state"] == "EXECUTABLE"
    assert all(rows[index]["state"] == "CONDITIONAL_EXECUTABLE" for index in range(27, 34))
    assert all(canonical_measurement(measurement_id) is not None for measurement_id in expected.values())
    assert not any(row["state"] == "NEW_CANONICAL_REQUIRED" for row in data["measurements"])


def test_atlas2009_factor29_is_total_facial_height_after_source_conflict_resolution():
    data = json.loads(PROFILE.read_text(encoding="utf-8"))
    row = data["measurements"][28]
    assert row["order"] == 29
    assert row["measurement_id"] == "M_RICKETTS_TOTAL_FACIAL_HEIGHT_BAN_XIPM_DEG_V1"
    assert row["state"] == "CONDITIONAL_EXECUTABLE"
    assert "SOURCE_LABEL_CONFLICT_RESOLVED_AS_TOTAL_FACIAL_HEIGHT" in row["gate"]


def test_atlas2009_complete_profile_has_no_unmapped_contract_rows():
    data = json.loads(PROFILE.read_text(encoding="utf-8"))
    rows = data["measurements"]
    assert data["status"] == "COMPOSITION_AND_EXECUTION_CONTRACTS_SOURCE_LOCKED__ALL_33_EXECUTABLE_OR_CONDITIONAL"
    assert all(row["measurement_id"] is not None for row in rows)
    assert not any(row["state"] in {"NEW_CANONICAL_REQUIRED", "SOURCE_LABEL_CONFLICT_BLOCKED"} for row in rows)
    states = [row["state"] for row in rows]
    assert states.count("EXECUTABLE") == 10
    assert states.count("CONDITIONAL_EXECUTABLE") == 23
    assert states.count("SOURCE_LOCKED_BLOCKED") == 0
