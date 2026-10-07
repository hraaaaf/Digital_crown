import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "docs/audits/schemas/ortho_lot08_ricketts32_facad_ptv_cranial_cluster_resolution_v1.json"
BACKLOG = ROOT / "docs/audits/schemas/ortho_lot08_facad_dc_unmapped_backlog_v1.json"


def _schema():
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def _backlog():
    return json.loads(BACKLOG.read_text(encoding="utf-8"))


def test_ptv_cranial_cluster_has_exact_five_rows_and_no_direct_aliases():
    data = _schema()
    assert set(data["resolutions"]) == {
        "Ms-PtV", "Cranium ant len", "PFH", "Ramus Xi pos", "Porion pos"
    }
    assert all(row["dc"]["direct_alias_allowed"] is False for row in data["resolutions"].values())
    assert data["safety_rules"]["no_runtime_activation"] is True


def test_ms_ptv_forbids_vendor_pt_and_generic_molar_aliases():
    data = _schema()
    row = data["resolutions"]["Ms-PtV"]
    assert row["facad"]["refs"] == ["FH", "Pt", "Ms-d"]
    assert row["dc"]["nearest_measurement_id"] == "M_U6_PTV_MM_V1"
    assert "STRICT_EQUIVALENCE_FORBIDDEN" in row["dc"]["status"]
    assert data["safety_rules"]["facad_pt_must_not_alias_dc_pr_ricketts_ptv"] is True
    assert data["safety_rules"]["facad_ms_d_must_not_alias_dc_ricketts_a6"] is True


def test_anterior_cranial_length_keeps_cc_pt_and_gn_identity_gate():
    data = _schema()
    row = data["resolutions"]["Cranium ant len"]
    assert row["facad"]["refs"] == ["CC", "N"]
    assert data["facad_constructions"]["CC"]["refs"] == ["N", "Ba", "Pt", "Gn"]
    assert row["dc"]["nearest_measurement_id"] == "M_RICKETTS_ANTERIOR_CRANIAL_LENGTH_CC_N_MM_V1"
    assert "CC_PT_AND_GN_IDENTITY_GATED" in row["dc"]["status"]
    assert data["safety_rules"]["facad_direct_gn_must_not_alias_dc_constructed_gn"] is True


def test_pfh_keeps_cf_ptv_and_go_identity_gate():
    data = _schema()
    row = data["resolutions"]["PFH"]
    assert row["facad"]["refs"] == ["CF", "Go"]
    assert data["facad_constructions"]["CF"]["refs"] == ["FH", "PtV"]
    assert data["facad_constructions"]["PtV"]["refs"] == ["FH", "Pt"]
    assert row["dc"]["nearest_measurement_id"] == "M_RICKETTS_POSTERIOR_FACIAL_HEIGHT_GO_CF_MM_V1"
    assert "CF_PTV_AND_GO_IDENTITY_GATED" in row["dc"]["status"]
    assert data["safety_rules"]["facad_generic_go_must_not_alias_dc_go_ricketts_pfh"] is True


def test_ramus_position_matches_line_family_but_keeps_cf_and_presentation_gates():
    row = _schema()["resolutions"]["Ramus Xi pos"]
    assert row["facad"]["refs"] == ["CF", "Xi", "P"]
    assert row["dc"]["nearest_measurement_id"] == "M_RICKETTS_RAMUS_POSITION_FH_CFXI_DEG_V1"
    assert "CF_PTV_ANCHOR_AND_ANGLE_PRESENTATION_GATED" in row["dc"]["status"]


def test_porion_position_keeps_ptv_anchor_and_signed_parity_gate():
    row = _schema()["resolutions"]["Porion pos"]
    assert row["facad"]["refs"] == ["PtV", "P"]
    assert row["facad"]["changeRightLeft"] is True
    assert row["dc"]["nearest_measurement_id"] == "M_RICKETTS_PORION_LOCATION_PTV_MM_V1"
    assert "PTV_ANCHOR_AND_SIGN_PARITY_GATED" in row["dc"]["status"]


def test_backlog_moves_only_ptv_cranial_cluster_and_reaches_seven():
    data = _backlog()
    unresolved = set(data["profiles"]["Ricketts (32 F)"]["unmapped"])
    moved = {"Ms-PtV", "Cranium ant len", "PFH", "Ramus Xi pos", "Porion pos"}
    assert moved.isdisjoint(unresolved)
    assert len(unresolved) == 7
    assert data["totals"]["unmapped_items"] == 7
    assert data["high_review_progress"]["Ricketts (32 F)"]["remaining_unmapped"] == 7
