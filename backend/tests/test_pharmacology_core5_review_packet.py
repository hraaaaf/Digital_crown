import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDITS = ROOT / "docs" / "audits"
PACKET = AUDITS / "PRESCRIPTION_PHARMACOLOGY_CORE5_INDEPENDENT_REVIEW_PACKET_2026-09-17.md"
PROJECTION = AUDITS / "PRESCRIPTION_PHARMACOLOGY_MOROCCO_MEDICINE_CURRENT_STATUS_PROJECTION_V1_2026-09-17.csv"
EXPECTED_IDS = {
    "MED-PAIN-001",
    "MED-PAIN-002",
    "MED-ABX-003",
    "MED-ABX-001",
    "MED-ABX-004",
}
REQUIRED = [
    "PRESCRIPTION_PHARMACOLOGY_MOROCCO_CLINICAL_PASS1_CORE_2026-09-16.csv",
    "PRESCRIPTION_PHARMACOLOGY_CORE5_MOROCCO_REGULATORY_PASS_2026-09-17.md",
    "PRESCRIPTION_PHARMACOLOGY_CORE5_SAFETY_EVIDENCE_INDEX_2026-09-17.csv",
    "PRESCRIPTION_PHARMACOLOGY_CORE5_SOURCE_REVALIDATION_2026-09-18.md",
]


def test_core5_review_packet_references_existing_inputs_and_stays_fail_closed():
    text = PACKET.read_text(encoding="utf-8")
    for name in REQUIRED:
        assert name in text
        assert (AUDITS / name).is_file()
    assert "Clinical activation: NO" in text
    assert "Automatic clinical activation: 0/5." in text
    assert "Independent clinical/scientific review: NOT YET PERFORMED." in text


def test_core5_projection_remains_explicitly_fail_closed_until_review():
    with PROJECTION.open(encoding="utf-8", newline="") as handle:
        rows = {row["historical_id"]: row for row in csv.DictReader(handle)}

    assert EXPECTED_IDS <= set(rows)
    for medicine_id in EXPECTED_IDS:
        row = rows[medicine_id]
        assert row["clinical_activation"] == "NO"
        assert row["unresolved_critical_fields"].strip()
