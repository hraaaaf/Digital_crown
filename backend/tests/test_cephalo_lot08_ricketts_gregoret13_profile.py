import json
from pathlib import Path

from backend.services.cephalo_measure_registry import canonical_measurement


PROFILE = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "audits"
    / "schemas"
    / "ortho_lot08_ricketts_gregoret13_protocol_profile_v1.json"
)


def test_gregoret13_profile_has_exactly_13_unique_measurements_in_order():
    data = json.loads(PROFILE.read_text(encoding="utf-8"))
    rows = data["measurements"]
    assert len(rows) == 13
    assert [row["order"] for row in rows] == list(range(1, 14))
    ids = [row["measurement_id"] for row in rows]
    assert len(ids) == len(set(ids))


def test_gregoret13_every_measurement_is_registered_canonically():
    data = json.loads(PROFILE.read_text(encoding="utf-8"))
    missing = [
        row["measurement_id"]
        for row in data["measurements"]
        if canonical_measurement(row["measurement_id"]) is None
    ]
    assert missing == []


def test_gregoret13_does_not_relabel_tweed_mandibular_plane():
    data = json.loads(PROFILE.read_text(encoding="utf-8"))
    ids = {row["measurement_id"] for row in data["measurements"]}
    assert "M_RICKETTS_MANDIBULAR_PLANE_FH_DEG_V1" in ids
    assert "M_FH_GOME_DEG_V1" not in ids


def test_gregoret13_keeps_incisal_edge_apog_variant_explicit():
    data = json.loads(PROFILE.read_text(encoding="utf-8"))
    ids = {row["measurement_id"] for row in data["measurements"]}
    assert "M_L1_EDGE_APOG_MM_V1" in ids
    assert "M_L1_FACIAL_SURFACE_APOG_MM_V1" not in ids


def test_gregoret13_normative_classification_stays_disabled():
    data = json.loads(PROFILE.read_text(encoding="utf-8"))
    assert data["normative_state"]["universal_classification"] is False
    assert data["normative_state"]["vert_enabled"] is False
    assert data["rules"]["historical_norms_reference_only"] is True


def test_gregoret13_mandibular_plane_is_conditional_and_not_tweed_alias():
    data = json.loads(PROFILE.read_text(encoding="utf-8"))
    row = next(
        item for item in data["measurements"]
        if item["measurement_id"] == "M_RICKETTS_MANDIBULAR_PLANE_FH_DEG_V1"
    )
    assert row["state"] == "CONDITIONAL_EXECUTABLE"
    assert row["gate"] == "EXPLICIT_SUBGO_RICKETTS_AND_ME_TANGENT_CONSTRUCTION_REQUIRED"
    assert row["measurement_id"] != "M_FH_GOME_DEG_V1"
