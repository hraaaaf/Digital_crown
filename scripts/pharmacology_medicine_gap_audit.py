import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECTION = ROOT / "docs/audits/PRESCRIPTION_PHARMACOLOGY_MOROCCO_MEDICINE_CURRENT_STATUS_PROJECTION_V1_2026-09-17.csv"

DIMENSIONS = [
    "morocco_market_status",
    "regulatory_status",
    "clinical_evidence_status",
    "adult_regimen_status",
    "pediatric_regimen_status",
    "max_dose_limit_status",
    "duration_status",
    "contraindications_precautions_status",
    "interactions_status",
    "specialist_protocol_boundary",
    "evidence_layer",
    "clinical_activation",
]

PENDING_TOKENS = (
    "TO_VERIFY", "TO_VALIDATE", "TO_RECONCILE", "NOT_PROVEN", "NOT_SEPARATELY_PROVEN",
    "NOT_NORMALIZED", "NOT_LOCKED", "PENDING", "NOT_CERTIFIED", "UNRESOLVED",
)


def main():
    with PROJECTION.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    report = {"total_medicines": len(rows), "dimensions": {}}
    for field in DIMENSIONS:
        counts = Counter(row[field] for row in rows)
        unresolved = sum(n for value, n in counts.items() if any(token in value for token in PENDING_TOKENS))
        report["dimensions"][field] = {
            "unresolved": unresolved,
            "resolved_or_bounded": len(rows) - unresolved,
            "statuses": dict(sorted(counts.items())),
        }
    report["rows_with_any_pending_token"] = sum(
        any(any(token in row[field] for token in PENDING_TOKENS) for field in DIMENSIONS[:-1])
        for row in rows
    )
    report["clinical_activation_no"] = sum(row["clinical_activation"] == "NO" for row in rows)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
