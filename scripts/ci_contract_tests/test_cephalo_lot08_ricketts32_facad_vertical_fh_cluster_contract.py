import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "docs/audits/schemas/ortho_lot08_ricketts32_facad_vertical_fh_cluster_resolution_v1.json"
BACKLOG = ROOT / "docs/audits/schemas/ortho_lot08_facad_dc_unmapped_backlog_v1.json"


def _schema():
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def _backlog():
    return json.loads(BACKLOG.read_text(encoding="utf-8"))


def test_vertical_fh_cluster_has_exact_five_rows_and_no_direct_aliases():
    data = _schema()
    assert set(data["resolutions"]) == {"LFH", "Max depth", "Max hgh", "NL/FH", "CBL/FH"}
    assert all(row["dc"]["direct_alias_allowed"] is False for row in data["resolutions"].values())
    assert data["safety_rules"]["no_runtime_activation"] is True


def test_lfh_is_same_vertex_geometry_but_numeric_presentation_stays_gated():
    row = _schema()["resolutions"]["LFH"]
    assert row["facad"]["calc_type"] == "Angle3p"
    assert row["facad"]["refs"] == ["Xi", "ANS", "PM"]
    assert row["dc"]["measurement_id"] == "M_ORAL_GNOMON_ANS_XI_PM_DEG_V1"
    assert "PRESENTATION_PARITY_GATED" in row["dc"]["status"]


def test_maxillary_depth_uses_anatomical_frankfort_and_na_but_not_direct_alias():
    row = _schema()["resolutions"]["Max depth"]
    assert row["facad"]["refs"] == ["A", "N", "P", "Or"]
    assert row["dc"]["measurement_id"] == "M_RICKETTS_MAXILLARY_DEPTH_NA_FH_DEG_V1"
    assert "PRESENTATION_PARITY_GATED" in row["dc"]["status"]


def test_maxillary_height_keeps_cf_ptv_anchor_identity_gate():
    data = _schema()
    row = data["resolutions"]["Max hgh"]
    assert row["facad"]["refs"] == ["CF", "N", "A"]
    assert data["facad_constructions"]["CF"]["refs"] == ["FH", "PtV"]
    assert data["facad_constructions"]["PtV"]["refs"] == ["FH", "Pt"]
    assert "CF_PTV_ANCHOR_IDENTITY_GATED" in row["dc"]["status"]
    assert data["safety_rules"]["max_height_cf_anchor_identity_must_remain_explicit"] is True


def test_palatal_plane_same_lines_but_signed_orientation_is_not_inferred():
    data = _schema()
    row = data["resolutions"]["NL/FH"]
    assert data["facad_constructions"]["FH"]["refs"] == ["P", "Or"]
    assert data["facad_constructions"]["NL"]["refs"] == ["PNS", "ANS"]
    assert row["dc"]["measurement_id"] == "M_RICKETTS_PALATAL_PLANE_FH_DEG_V1"
    assert "SIGNED_ORIENTATION_PARITY_GATED" in row["dc"]["status"]
    assert data["safety_rules"]["palatal_plane_signed_orientation_requires_versioned_evidence"] is True


def test_cranial_deflection_preserves_reversed_line_equivalence_but_gates_presentation():
    row = _schema()["resolutions"]["CBL/FH"]
    assert row["facad"]["refs"] == ["N", "Ba", "Or", "P"]
    assert row["dc"]["measurement_id"] == "M_RICKETTS_CRANIAL_DEFLECTION_FH_BAN_DEG_V1"
    assert "PRESENTATION_PARITY_GATED" in row["dc"]["status"]


def test_vertical_fh_cluster_stays_resolved_in_current_final_backlog():
    data = _backlog()
    profile = data["profiles"]["Ricketts (32 F)"]
    unresolved = set(profile["unmapped"])
    resolved = {row["facad_label"] for row in profile["resolved_items"]}
    moved = {"LFH", "Max depth", "Max hgh", "NL/FH", "CBL/FH"}
    assert moved.isdisjoint(unresolved)
    assert moved.issubset(resolved)
    assert data["totals"]["unmapped_items"] == 0
    assert data["high_review_progress"]["Ricketts (32 F)"]["remaining_unmapped"] == 0
    assert data["high_review_progress"]["Ricketts (32 F)"]["resolved_total"] == 26
