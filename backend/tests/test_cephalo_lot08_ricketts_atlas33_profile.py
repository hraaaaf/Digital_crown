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
    assert rows[4]["state"] == "SOURCE_LOCKED_BLOCKED"
    assert rows[10]["measurement_id"] == "M_L1_EDGE_APOG_MM_V1"
    assert rows[10]["state"] == "SOURCE_LOCKED_BLOCKED"
    assert rows[10]["gate"] == "L1_INCISAL_EDGE_AND_A_POG_LOCKED__DISTANCE_DIRECTION_UNRESOLVED"
    assert rows[11]["measurement_id"] == "M_RICKETTS_U1_APOG_PROTRUSION_MM_V1"
    assert rows[11]["state"] == "SOURCE_LOCKED_BLOCKED"
    assert rows[11]["gate"] == "U1_INCISAL_EDGE_AND_A_POG_LOCKED__DISTANCE_DIRECTION_UNRESOLVED"
    assert rows[13]["measurement_id"] == "M_RICKETTS_U1_APOG_INCLINATION_DEG_V1"


def test_atlas2009_every_non_null_measurement_is_registered():
    data = json.loads(PROFILE.read_text(encoding="utf-8"))
    missing = [
        row["measurement_id"]
        for row in data["measurements"]
        if row["measurement_id"] and canonical_measurement(row["measurement_id"]) is None
    ]
    assert missing == []


def test_atlas2009_factor_29_conflict_is_not_silently_normalized():
    data = json.loads(PROFILE.read_text(encoding="utf-8"))
    row = data["measurements"][28]
    assert row["order"] == 29
    assert row["measurement_id"] is None
    assert row["state"] == "SOURCE_LABEL_CONFLICT_BLOCKED"
    text = COMPOSITION.read_text(encoding="utf-8")
    assert "Source-label conflict quarantined" in text
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
    assert rows[14]["state"] == "SOURCE_LOCKED_BLOCKED"
    assert rows[15]["measurement_id"] == "M_RICKETTS_OCCLUSAL_PLANE_XIPM_DEG_V1"
    assert rows[15]["state"] == "CONDITIONAL_EXECUTABLE"
    assert rows[17]["measurement_id"] == "M_RICKETTS_UPPER_LIP_LENGTH_ANS_COMMISSURE_MM_V1"
    assert rows[17]["state"] == "CONDITIONAL_EXECUTABLE"
    assert rows[18]["measurement_id"] == "M_RICKETTS_COMMISSURE_FOP_MM_V1"
    assert rows[18]["state"] == "SOURCE_LOCKED_BLOCKED"
    assert rows[21]["measurement_id"] == "M_RICKETTS_FACIAL_TAPER_NPOG_MP_DEG_V1"
    assert rows[23]["measurement_id"] == "M_RICKETTS_MAXILLARY_HEIGHT_NCFA_DEG_V1"
    assert rows[24]["measurement_id"] == "M_RICKETTS_PALATAL_PLANE_FH_DEG_V1"
    assert all(rows[index]["state"] == "CONDITIONAL_EXECUTABLE" for index in (21, 23))
    assert rows[24]["state"] == "SOURCE_LOCKED_BLOCKED"
    assert rows[24]["gate"] == "PALATAL_PLANE_IDENTITIES_LOCKED__SIGNED_ANGLE_ORIENTATION_UNRESOLVED"


def test_atlas2009_wave_b_new_ids_are_registered():
    data = json.loads(PROFILE.read_text(encoding="utf-8"))
    ids = [
        row["measurement_id"]
        for row in data["measurements"]
        if row["order"] in {14, 15, 17, 18, 21, 23, 24}
    ]
    assert all(measurement_id is not None for measurement_id in ids)
    assert all(canonical_measurement(measurement_id) is not None for measurement_id in ids)
