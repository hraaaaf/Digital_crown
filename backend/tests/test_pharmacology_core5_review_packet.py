from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDITS = ROOT / "docs" / "audits"
PACKET = AUDITS / "PRESCRIPTION_PHARMACOLOGY_CORE5_INDEPENDENT_REVIEW_PACKET_2026-09-17.md"
REQUIRED = [
    "PRESCRIPTION_PHARMACOLOGY_MOROCCO_CLINICAL_PASS1_CORE_2026-09-16.csv",
    "PRESCRIPTION_PHARMACOLOGY_CORE5_MOROCCO_REGULATORY_PASS_2026-09-17.md",
    "PRESCRIPTION_PHARMACOLOGY_CORE5_SAFETY_EVIDENCE_INDEX_2026-09-17.csv",
]


def test_core5_review_packet_references_existing_inputs_and_stays_fail_closed():
    text = PACKET.read_text(encoding="utf-8")
    for name in REQUIRED:
        assert name in text
        assert (AUDITS / name).is_file()
    assert "Clinical activation: NO" in text
    assert "Independent clinical/scientific review: NOT YET PERFORMED." in text
