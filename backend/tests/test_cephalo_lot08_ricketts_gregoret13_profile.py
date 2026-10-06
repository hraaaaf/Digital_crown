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
MANDIBULAR_ARC_CONTRACT = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "audits"
    / "schemas"
    / "ortho_lot08_ricketts_mandibular_arc_identity_contract_v1.json"
)
FOP_MP_SOURCE_LOCK = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "audits"
    / "CEPHALO_LOT08_RICKETTS_FOP_MANDIBULAR_PLANE_SOURCE_LOCK.md"
)
CONSTRUCTION_REGISTRY = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "CEPHALO_CONSTRUCTION_REGISTRY.md"
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


def test_gregoret13_mandibular_plane_is_conditional_on_explicit_ricketts_identity():
    data = json.loads(PROFILE.read_text(encoding="utf-8"))
    row = next(
        item for item in data["measurements"]
        if item["measurement_id"] == "M_RICKETTS_MANDIBULAR_PLANE_FH_DEG_V1"
    )
    assert row["state"] == "CONDITIONAL_EXECUTABLE"
    assert row["gate"] == "EXPLICIT_RICKETTS_INFERIOR_ANGLE_POINT_AND_ANATOMICAL_FRANKFORT_REQUIRED"
    assert "M_FH_GOME_DEG_V1" not in {
        item["measurement_id"] for item in data["measurements"]
    }


def test_gregoret13_mandibular_plane_registry_requires_explicit_ricketts_angle_point():
    item = canonical_measurement("M_RICKETTS_MANDIBULAR_PLANE_FH_DEG_V1")
    assert item is not None
    assert item.source_status == "GEOMETRY_COVERED_EXPLICIT_RICKETTS_ANGLE_POINT_REQUIRED"


def test_gregoret13_l1_occlusal_extrusion_is_conditional_and_fail_closed_without_evidence():
    data = json.loads(PROFILE.read_text(encoding="utf-8"))
    row = next(
        item for item in data["measurements"]
        if item["measurement_id"] == "M_RICKETTS_L1_OCCLUSAL_EXTRUSION_MM_V1"
    )
    assert row["state"] == "CONDITIONAL_EXECUTABLE"
    assert row["gate"] == "EXPLICIT_RICKETTS_FOP_PREMOLAR_MOLAR_ANCHORS_L1_AXIS_AND_VERIFIED_CALIBRATION_REQUIRED"


def test_gregoret13_does_not_substitute_steiner_occlusal_plane_for_ricketts_functional_plane():
    data = json.loads(PROFILE.read_text(encoding="utf-8"))
    ids = {item["measurement_id"] for item in data["measurements"]}
    assert "M_RICKETTS_L1_OCCLUSAL_EXTRUSION_MM_V1" in ids
    assert "M_OCCLUSAL_PLANE_SN_DEG_V1" not in ids


def test_gregoret13_l1_occlusal_extrusion_registry_is_source_locked_and_conditional():
    item = canonical_measurement("M_RICKETTS_L1_OCCLUSAL_EXTRUSION_MM_V1")
    assert item is not None
    assert item.source_status == "GEOMETRY_COVERED_SOURCE_LOCKED_FOP_CROWNWARD_SIGN__EXPLICIT_ANCHORS_L1_AXIS_REQUIRED"


def test_gregoret13_mandibular_arc_identity_contract_is_fail_closed():
    data = json.loads(MANDIBULAR_ARC_CONTRACT.read_text(encoding="utf-8"))
    assert data["measurement_id"] == "M_RICKETTS_MANDIBULAR_ARC_DCXI_XIPM_DEG_V1"
    assert data["state"] == "SOURCE_LOCKED_GEOMETRY_CONDITIONAL_EXECUTION"
    assert data["construction"]["condylar_axis"] == "DC_Ricketts-Xi_Ricketts"
    assert data["scientific_identities"]["DC_Ricketts"]["runtime_authority"] == "MANUAL_OR_MANUAL_CORRECTED_REQUIRED"
    assert data["construction"]["corpus_axis"] == "Xi_Ricketts-Pm_Ricketts"
    assert data["construction"]["runtime_binding"] == "RICKETTS_MANDIBULAR_ARC_CANONICAL_DEG_V2"
    assert data["construction"]["fail_closed"] is True
    assert data["normative_state"]["age_adjustment_status"] == "QUARANTINED_CONFLICTING_TRANSCRIPTION"
    assert data["normative_state"]["universal_classification"] is False


def test_gregoret13_mandibular_arc_forbids_legacy_aliases():
    data = json.loads(MANDIBULAR_ARC_CONTRACT.read_text(encoding="utf-8"))
    identities = data["scientific_identities"]
    assert set(identities["DC_Ricketts"]["forbidden_aliases"]) == {"DC", "Co", "Co_anatomic", "D_point"}
    assert set(identities["Xi_Ricketts"]["forbidden_aliases"]) == {"Xi", "Go", "Ar", "PT_point"}
    assert set(identities["Pm_Ricketts"]["forbidden_aliases"]) == {"Pm", "Pog", "Pog_hard", "B", "Me"}
    assert data["rules"]["generic_labels_require_validated_bridge"] is True


def test_gregoret13_mandibular_arc_profile_and_registry_are_conditional():
    data = json.loads(PROFILE.read_text(encoding="utf-8"))
    row = next(
        item for item in data["measurements"]
        if item["measurement_id"] == "M_RICKETTS_MANDIBULAR_ARC_DCXI_XIPM_DEG_V1"
    )
    assert row["state"] == "CONDITIONAL_EXECUTABLE"
    assert row["gate"] == "MANUAL_DC_RICKETTS_SOURCE_LOCKED_XI_MANUAL_PM_RICKETTS_REQUIRED"
    item = canonical_measurement("M_RICKETTS_MANDIBULAR_ARC_DCXI_XIPM_DEG_V1")
    assert item is not None
    assert item.source_status == "GEOMETRY_COVERED_MANUAL_DC_CONSTRUCTED_XI_MANUAL_PM_REQUIRED"


def test_gregoret13_lower_facial_height_is_conditional_on_source_locked_xi_pm():
    data = json.loads(PROFILE.read_text(encoding="utf-8"))
    row = next(
        item for item in data["measurements"]
        if item["measurement_id"] == "M_ORAL_GNOMON_ANS_XI_PM_DEG_V1"
    )
    assert row["state"] == "CONDITIONAL_EXECUTABLE"
    assert row["gate"] == "MANUAL_R1_R4_RICKETTS_AND_ANATOMICAL_FRANKFORT_FOR_XI_PLUS_MANUAL_PM_RICKETTS_REQUIRED"


def test_gregoret13_profile_links_the_ricketts_plane_source_lock():
    data = json.loads(PROFILE.read_text(encoding="utf-8"))
    expected = "docs/audits/CEPHALO_LOT08_RICKETTS_FOP_MANDIBULAR_PLANE_SOURCE_LOCK.md"
    assert expected in data["source_contracts"]
    text = FOP_MP_SOURCE_LOCK.read_text(encoding="utf-8")
    assert "RICKETTS_FUNCTIONAL_OCCLUSAL_PLANE_BICUSPID_MOLAR_V1" in text
    assert "RICKETTS_MANDIBULAR_PLANE_ANGLE_MENTON_V1" in text
    assert "CROWNWARD_POSITIVE_SIGN_V1" in text


def test_gregoret13_registry_contains_both_ricketts_plane_constructions():
    text = CONSTRUCTION_REGISTRY.read_text(encoding="utf-8")
    assert "## RICKETTS_FUNCTIONAL_OCCLUSAL_PLANE_BICUSPID_MOLAR_V1" in text
    assert "## RICKETTS_MANDIBULAR_PLANE_ANGLE_MENTON_V1" in text
    assert "M_RICKETTS_L1_OCCLUSAL_EXTRUSION_MM_V1" in text
    assert "M_RICKETTS_MANDIBULAR_PLANE_FH_DEG_V1" in text


def test_gregoret13_profile_links_xi_pm_source_lock():
    data = json.loads(PROFILE.read_text(encoding="utf-8"))
    expected = "docs/audits/CEPHALO_LOT08_RICKETTS_XI_PM_SOURCE_LOCK.md"
    assert expected in data["source_contracts"]
    text = (Path(__file__).resolve().parents[2] / expected).read_text(encoding="utf-8")
    assert "RICKETTS_XI_RAMAL_RECTANGLE_R1_R4_FH_V1" in text
    assert "Pm_Ricketts" in text
    assert "M_ORAL_GNOMON_ANS_XI_PM_DEG_V1" in text


def test_gregoret13_profile_links_dc_mandibular_arc_source_lock():
    data = json.loads(PROFILE.read_text(encoding="utf-8"))
    expected = "docs/audits/CEPHALO_LOT08_RICKETTS_DC_MANDIBULAR_ARC_SOURCE_LOCK.md"
    assert expected in data["source_contracts"]
    text = (Path(__file__).resolve().parents[2] / expected).read_text(encoding="utf-8")
    assert "DC_Ricketts" in text
    assert "RICKETTS_MANDIBULAR_ARC_CANONICAL_DEG_V2" in text
    assert "posterior corpus extension" in text


def test_gregoret13_construction_registry_marks_mandibular_arc_conditional():
    text = CONSTRUCTION_REGISTRY.read_text(encoding="utf-8")
    assert "M_RICKETTS_MANDIBULAR_ARC_DCXI_XIPM_DEG_V1" in text
    assert "CONDITIONAL_EXECUTABLE" in text
    assert "manual/manual-corrected `DC_Ricketts`" in text
