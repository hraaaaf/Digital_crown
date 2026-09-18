import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "docs/audits/PRESCRIPTION_PHARMACOLOGY_MOROCCO_MASTER_INVENTORY_2026-09-16.csv"
PROJECTION = ROOT / "docs/audits/PRESCRIPTION_PHARMACOLOGY_MOROCCO_MEDICINE_CURRENT_STATUS_PROJECTION_V1_2026-09-17.csv"


def _rows(path: Path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_medicine_projection_exactly_covers_master_medicine_denominator():
    master_ids = [row["id"] for row in _rows(MASTER) if row["id"].startswith("MED-")]
    projection_ids = [row["historical_id"] for row in _rows(PROJECTION)]

    assert len(master_ids) == 68
    assert len(master_ids) == len(set(master_ids))
    assert len(projection_ids) == len(set(projection_ids))
    assert set(projection_ids) == set(master_ids)


def test_medicine_projection_remains_fail_closed():
    rows = _rows(PROJECTION)
    assert rows
    assert all(row["clinical_activation"] == "NO" for row in rows)
