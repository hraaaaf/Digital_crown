import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "docs/audits/schemas/ortho_lot08_ricketts32_facad_final_seven_cluster_resolution_v1.json"
BACKLOG = ROOT / "docs/audits/schemas/ortho_lot08_facad_dc_unmapped_backlog_v1.json"


def _schema():
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def _backlog():
    return json.loads(BACKLOG.read_text(encoding="utf-8"))


def test_final_cluster_has_exact_seven_rows_and_no_direct_aliases():
    data = _schema()
    assert set(data["resolutions"]) == {
        "Xi-OL", "Xi-PM/OL", "Upper lip len", "STi-OL",
        "Facial cone angle", "Mand arc", "Mand len",
    }
    assert all(row["dc"]["direct_alias_allowed"] is False for row in data["resolutions"].values())
    assert data["safety_rules"]["no_runtime_activation"] is True


def test_xi_ol_and_xi_pm_ol_keep_vendor_occlusal_line_boundary():
    data = _schema()
    assert data["facad_constructions"]["OLa"]["refs"] == ["Is", "Ii"]
    assert data["facad_constructions"]["OL"]["refs"] == ["OLp", "OLa"]
    assert "STRICT_EQUIVALENCE_FORBIDDEN" in data["resolutions"]["Xi-OL"]["dc"]["status"]
    assert "OCCLUSAL_LINE_VARIANT" in data["resolutions"]["Xi-PM/OL"]["dc"]["status"]
    assert data["safety_rules"]["facad_ol_must_not_alias_ricketts_functional_occlusal_plane"] is True


def test_upper_lip_length_stomion_is_not_atlas_commissure():
    data = _schema()
    row = data["resolutions"]["Upper lip len"]
    assert row["facad"]["refs"] == ["ANS", "STs"]
    assert data["facad_markers"]["STs"] == "Stomion superior"
    assert row["dc"]["nearest_measurement_id"] == "M_RICKETTS_UPPER_LIP_LENGTH_ANS_COMMISSURE_MM_V1"
    assert "STRICT_EQUIVALENCE_FORBIDDEN" in row["dc"]["status"]
    assert data["safety_rules"]["facad_sts_must_not_alias_labial_commissure_ricketts"] is True


def test_sti_ol_has_both_landmark_and_plane_mismatch():
    data = _schema()
    row = data["resolutions"]["STi-OL"]
    assert row["facad"]["refs"] == ["OL", "STi"]
    assert row["facad"]["changeRightLeft"] is True
    assert data["facad_markers"]["STi"] == "Stomion inferior"
    assert row["dc"]["nearest_measurement_id"] == "M_RICKETTS_COMMISSURE_FOP_MM_V1"
    assert "STRICT_EQUIVALENCE_FORBIDDEN" in row["dc"]["status"]


def test_facial_cone_forbids_generic_go_me_as_ricketts_mandibular_plane():
    data = _schema()
    row = data["resolutions"]["Facial cone angle"]
    assert row["facad"]["refs"] == ["Go", "Me", "N", "Pog"]
    assert row["dc"]["nearest_measurement_id"] == "M_RICKETTS_FACIAL_TAPER_NPOG_MP_DEG_V1"
    assert "STRICT_EQUIVALENCE_FORBIDDEN" in row["dc"]["status"]
    assert data["safety_rules"]["facad_generic_go_me_must_not_alias_ricketts_mandibular_plane"] is True


def test_mandibular_arc_is_geometry_family_only_until_landmark_authority_and_presentation_parity():
    data = _schema()
    row = data["resolutions"]["Mand arc"]
    assert row["facad"]["refs"] == ["Xi", "PM", "DC", "Xi"]
    assert data["facad_markers"]["DC"] == "Centre of condyle"
    assert row["dc"]["nearest_measurement_id"] == "M_RICKETTS_MANDIBULAR_ARC_DCXI_XIPM_DEG_V1"
    assert "AUTHORITY_AND_ANGLE_PRESENTATION_GATED" in row["dc"]["status"]
    assert data["safety_rules"]["facad_dc_must_not_alias_dc_ricketts_without_identity_proof"] is True


def test_mandibular_length_pm_prime_is_distinct_constructed_endpoint():
    data = _schema()
    row = data["resolutions"]["Mand len"]
    assert row["facad"]["refs"] == ["Xi", "PM'"]
    assert data["facad_constructions"]["PM'"]["refs"] == ["Xi", "PM", "A", "Pog"]
    assert row["dc"]["nearest_measurement_id"] == "M_RICKETTS_CORPUS_LENGTH_XI_PM_MM_V1"
    assert "STRICT_EQUIVALENCE_FORBIDDEN" in row["dc"]["status"]
    assert data["safety_rules"]["facad_pm_prime_must_not_alias_pm_ricketts"] is True


def test_backlog_is_empty_after_final_seven_dispositions():
    data = _backlog()
    assert data["profiles"]["Ricketts (32 F)"]["unmapped"] == []
    assert data["totals"]["unmapped_items"] == 0
    progress = data["high_review_progress"]["Ricketts (32 F)"]
    assert progress["resolved_total"] == 26
    assert progress["remaining_unmapped"] == 0
