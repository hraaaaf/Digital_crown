import json
from pathlib import Path


AUDIT_DIR = Path(__file__).resolve().parents[2] / "docs" / "audits"
MATRIX_PATH = AUDIT_DIR / "PRESCRIPTION_PHARMACOLOGY_MOROCCO_M0_MATRIX.json"
EVIDENCE_PATH = AUDIT_DIR / "PRESCRIPTION_PHARMACOLOGY_MOROCCO_M0_EVIDENCE.json"
INDICATIONS_PATH = AUDIT_DIR / "PRESCRIPTION_PHARMACOLOGY_MOROCCO_M0_INDICATIONS.json"

ALLOWED_TIERS = {
    "AUTO_OK_MAROC",
    "PROPOSE_CONFIRM",
    "REVIEW_ONLY",
    "NOT_SUPPORTED",
}
ALLOWED_EVIDENCE_STATES = {"CROSS_CHECKED", "PRIMARY_ONLY"}


def load_matrix():
    return json.loads(MATRIX_PATH.read_text(encoding="utf-8"))


def load_evidence():
    return json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))


def load_indications():
    return json.loads(INDICATIONS_PATH.read_text(encoding="utf-8"))


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


def test_morocco_m0_evidence_ledger_is_unique_and_references_known_rows():
    matrix = load_matrix()
    evidence = load_evidence()
    known_rows = {row["id"] for row in matrix["rows"]}
    evidence_ids = [entry["evidence_id"] for entry in evidence["entries"]]

    assert evidence["schema_version"] == "m0-evidence.1"
    assert evidence["verified_at"] == "2026-09-15"
    assert len(evidence_ids) == len(set(evidence_ids))

    for entry in evidence["entries"]:
        assert entry["verification_state"] in ALLOWED_EVIDENCE_STATES, entry["evidence_id"]
        assert entry.get("primary_sources"), entry["evidence_id"]
        assert entry["clinical_regimen_proven"] is False, entry["evidence_id"]

        for row_id in entry.get("matrix_ids", []):
            assert row_id in known_rows, f"{entry['evidence_id']}: unknown matrix row {row_id}"

        if entry["verification_state"] == "CROSS_CHECKED":
            assert entry.get("cross_checks"), entry["evidence_id"]


def test_morocco_m0_negative_search_is_not_encoded_as_absence():
    evidence = load_evidence()
    assert "NEGATIVE_SEARCH_NOT_ABSENCE" in evidence["rules"]

    for row in load_matrix()["rows"]:
        assert row.get("market_state") != "ABSENT_BY_SEARCH_ONLY", row["id"]


def test_morocco_m0_indication_universe_is_parseable_unique_and_non_runtime():
    indications = load_indications()
    rows = indications["rows"]
    ids = [row["id"] for row in rows]

    assert indications["schema_version"] == "m0-indications.1"
    assert indications["runtime_behavior_change"] is False
    assert indications["verified_at"] == "2026-09-15"
    assert len(rows) == 22
    assert len(ids) == len(set(ids)) == 22


def test_morocco_m0_indications_are_fail_closed_and_link_only_known_molecules():
    matrix = load_matrix()
    known_matrix_rows = {row["id"] for row in matrix["rows"]}

    for indication in load_indications()["rows"]:
        assert indication["m0_tier"] in ALLOWED_TIERS, indication["id"]
        assert indication["m0_tier"] != "AUTO_OK_MAROC", indication["id"]
        assert indication.get("gap", "").strip(), indication["id"]
        assert indication.get("indication", "").strip(), indication["id"]
        assert indication.get("care_scope", "").strip(), indication["id"]
        assert indication.get("drug_role", "").strip(), indication["id"]
        assert isinstance(indication.get("local_measures_first"), bool), indication["id"]

        for row_id in indication.get("linked_matrix_ids", []):
            assert row_id in known_matrix_rows, f"{indication['id']}: unknown matrix row {row_id}"


def test_morocco_m0_never_turns_localised_abscess_or_red_flags_into_auto_antibiotics():
    indications = {row["id"]: row for row in load_indications()["rows"]}

    localised = indications["infection.dental_abscess_localised"]
    assert localised["drug_role"] == "NO_ROUTINE_ANTIBIOTIC"
    assert localised["m0_tier"] == "REVIEW_ONLY"

    severe = indications["infection.dental_abscess_severe_red_flags"]
    assert severe["care_scope"] == "EMERGENCY_REFERRAL"
    assert severe["m0_tier"] == "NOT_SUPPORTED"

    emergency = indications["emergency.chairside_medication_set"]
    assert emergency["care_scope"] == "EMERGENCY_CHAIRSIDE"
    assert emergency["m0_tier"] == "NOT_SUPPORTED"
