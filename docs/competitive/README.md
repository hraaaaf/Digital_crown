# Competitive Evidence Harness

Entry point: `LOT_B_EVIDENCE_HARNESS.md`.

Artifacts:

- `digital_crown_inventory.json` — exact benchmark-relevant module/route inventory at pinned Digital Crown baseline;
- `capabilities.json` — 12 cross-product benchmark capabilities and evidence status;
- `orthalis_sources.json` — dated official Orthalis/Orqual vendor sources;
- `scenarios.json` — symmetric benchmark scenarios and measurement slots;
- `synthetic_dataset.json` — synthetic-only fixture contract, forbidden on cabinet databases.

Validation:

```bash
python scripts/validate_competitive_evidence.py
python -m pytest \
  backend/tests/test_competitive_evidence_harness.py \
  backend/tests/test_competitive_evidence_repo_paths.py \
  backend/tests/test_competitive_inventory.py -q
```

Rules:

- `VERIFIED_REPO` requires direct repo evidence.
- `VENDOR_CLAIM_VERIFIED` means an official vendor claim, not independent runtime proof.
- `NOT_PROVEN` is not equivalent to absent.
- Non-measured performance fields stay `null`.
- No real patient data belongs in this harness.
