import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TRIAGE = ROOT / "docs/audits/PRESCRIPTION_PHARMACOLOGY_CORE8_ACTIVATION_TRIAGE_2026-09-17.csv"
EXPECTED_IDS = {
    "MED-PAIN-001", "MED-PAIN-002", "MED-ABX-003", "MED-ABX-001",
    "MED-ABX-004", "MED-ABX-006", "MED-ABX-005", "MED-ABX-002",
}


def test_core8_triage_is_complete_and_fail_closed():
    with TRIAGE.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 8
    assert {row["historical_id"] for row in rows} == EXPECTED_IDS
    assert all(row["activation_status"] == "NO" for row in rows)
    assert all(row["regulatory_gap_morocco"] == "OPEN" for row in rows)
    assert Counter(row["triage_class"] for row in rows) == {
        "CANDIDATE_AFTER_CERTIFICATION": 5,
        "RESTRICTED": 2,
        "NON_ROUTINE": 1,
    }
    assert sum(row["automatic_prescription_candidate"] == "YES_AFTER_CERTIFICATION" for row in rows) == 5
