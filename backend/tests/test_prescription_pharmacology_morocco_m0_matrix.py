import json
from pathlib import Path


MATRIX_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "audits"
    / "PRESCRIPTION_PHARMACOLOGY_MOROCCO_M0_MATRIX.json"
)

ALLOWED_TIERS = {
    "AUTO_OK_MAROC",
    "PROPOSE_CONFIRM",
    "REVIEW_ONLY",
    "NOT_SUPPORTED",
}


def load_matrix():
    return json.loads(MATRIX_PATH.read_text(encoding="utf-8"))


def test_morocco_m0_matrix_is_parseable_and_non_runtime():
    matrix = load_matrix()
    assert matrix["schema_version"] == "m0.1"
    assert matrix["runtime_behavior_change"] is False
    assert matrix["verified_at"] == "2026-09-15"


def test_morocco_m0_matrix_has_exactly_50_unique_rows():
    matrix = load_matrix()
    rows = matrix["rows"]
    ids = [row["id"] for row in rows]

    assert len(rows) == 50
    assert len(ids) == len(set(ids)) == 50


def test_morocco_m0_rows_are_fail_closed_and_traceable():
    matrix = load_matrix()
    source_registry = matrix["source_registry"]

    assert set(matrix["automation_tiers"]) == ALLOWED_TIERS

    for row in matrix["rows"]:
        assert row["m0_tier"] in ALLOWED_TIERS, row["id"]
        assert row.get("gap", "").strip(), row["id"]
        assert row.get("domain", "").strip(), row["id"]
        assert row.get("entity", "").strip(), row["id"]
        assert row.get("care_scope", "").strip(), row["id"]
        assert row.get("market_state", "").strip(), row["id"]
        assert row.get("rcp_state", "").strip(), row["id"]

        for source_id in row.get("source_ids", []):
            assert source_id in source_registry, f"{row['id']}: unknown source {source_id}"


def test_morocco_m0_does_not_grant_new_auto_ok_rules():
    matrix = load_matrix()
    auto_rows = [row["id"] for row in matrix["rows"] if row["m0_tier"] == "AUTO_OK_MAROC"]

    assert auto_rows == [], f"M0 must not activate AUTO_OK_MAROC rows: {auto_rows}"


def test_morocco_m0_keeps_high_risk_contexts_out_of_automatic_prescription():
    matrix = load_matrix()
    rows = {row["id"]: row for row in matrix["rows"]}

    for row_id in (
        "pain.tramadol",
        "anxiety.diazepam",
        "facial_pain.tmd_diazepam",
        "facial_pain.neuropathic",
        "emergency.adrenaline",
        "emergency.midazolam",
    ):
        assert rows[row_id]["m0_tier"] in {"REVIEW_ONLY", "NOT_SUPPORTED"}
