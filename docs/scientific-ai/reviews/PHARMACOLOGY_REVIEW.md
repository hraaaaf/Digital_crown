# Pharmacology review

## Verdict

The V2 architecture is safe, but Digital Crown pharmacology data and active rules are not scientifically cleared. No dose was approved or changed.

| Decision | Status | Review |
|---|---|---|
| WHO INN/DCI for substance identity | VALID | Keep substance separate from product and brand |
| Brand implies strength/concentration | BLOCKING_GAP | Forbidden; presentation must be explicit |
| Moroccan authorization/market status | BLOCKING_GAP | AMMPS authority verified, reusable official structured product source not verified |
| ATC/DDD as utilization metadata | VALID | WHO defines DDD as a technical utilization unit |
| DDD as patient dose | BLOCKING_GAP | Explicitly prohibited |
| Typed amount/frequency/duration/route/maximum | VALID | Structured in V2 |
| mg to mL conversion | VALID | Requires explicit concentration and dimensional tests |
| LLM dose calculation | BLOCKING_GAP | Explicitly prohibited |
| Pediatric/pregnancy/renal/hepatic contexts | NEEDS_CHANGE | Must be structured inputs with no fallback |
| Antibiotic stewardship | VALID | Candidate jurisdiction-specific sources identified |

## Existing risks documented, not fixed

REPO_MAP identifies hard-coded prophylaxis and pediatric dose values in backend/services/clinical_rules_engine.py. backend/data/medications_ma.json contains 4,234 records whose provenance, update cadence, Moroccan authorization status and reuse license are not established. Both are P1 blockers before pharmacology activation.

## Correct strategy

Use INN for substance identity. Use only a verified AMMPS/official or licensed product feed for Moroccan authorization and presentations. Version product information per presentation. Never infer concentration from brand. Store every patient-specific rule with explicit inputs, units, maximum, safety context, missing-data refusal, version and tests.

WHO, SDCEP, ADA, AAPD and AHA sources are accessible candidates. EMA product information does not prove Moroccan availability. No public reusable AMMPS catalogue/API was verified.

