import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "docs/audits/PRESCRIPTION_PHARMACOLOGY_CORE5_SAFETY_EVIDENCE_INDEX_2026-09-17.csv"
EXPECTED_IDS = {
    "MED-PAIN-001",
    "MED-PAIN-002",
    "MED-ABX-003",
    "MED-ABX-001",
    "MED-ABX-004",
}


def test_core5_safety_evidence_index_is_complete_and_fail_closed():
    with INDEX.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 5
    assert {row["historical_id"] for row in rows} == EXPECTED_IDS
    assert all(row["evidence_status"] == "EVIDENCE_INDEXED" for row in rows)
    assert all(row["clinical_activation"] == "NO" for row in rows)
    assert all(row["review_gate"] == "INDEPENDENT_REVIEW_REQUIRED" for row in rows)
    assert all(row["safety_review_domains"].strip() for row in rows)
    assert all(row["source_1"].startswith("https://") for row in rows)
    assert all(row["source_2"].startswith("https://") for row in rows)
    assert all(row["source_1"] != row["source_2"] for row in rows)
