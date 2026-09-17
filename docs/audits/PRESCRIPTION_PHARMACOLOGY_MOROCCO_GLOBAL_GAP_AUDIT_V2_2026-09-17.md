# Morocco prescription + oral-care global gap audit V2 — 2026-09-17

Status: SOURCE DISPOSITION COMPLETE FOR ENUMERATED INVENTORY — COMPLETENESS NOT CERTIFIED — TAXONOMY NOT CLOSED — CLINICAL ACTIVATION NO

## Goal
Give every enumerated inventory source row an explicit canonical disposition without erasing clinically meaningful form, strength, indication, regulatory or protocol distinctions.

## Observable success criterion for this pass
1. Every one of the 170 historical source rows has exactly one disposition row.
2. Every one of the 8 subsequent addendum rows has exactly one disposition row.
3. Every structural gap identified by the historical mapping has an explicit canonical extension target.
4. No mapped row is clinically activated.

## Verified result

### Historical base inventory
- Source rows: 170.
- Unique historical IDs mapped: 170.
- Disposition coverage: 170/170 = 100% for the enumerated historical base.
- `clinical_activation != NO`: 0.

Base disposition counts:
- `IDENTITY_RETAINED`: 61
- `MAP_FAMILY_WITH_REQUIRED_ATTRIBUTE`: 38
- `MAP_EXACT`: 17
- `DISTINCT_CANONICAL_GAP`: 20
- `ACTIVE_OVERLAP`: 9
- `ACTIVE_INDICATION_OVERLAP`: 6
- `FORM_CONTEXT_OVERLAP`: 3
- `MAP_SPLIT_FAMILY`: 3
- `ADJACENT_MEDICAL_BOUNDARY`: 3
- `PROTOCOL_CONTEXT_OVERLAP`: 2
- `EXACT_OR_QUASI_DUPLICATE`: 2
- `EXACT_DUPLICATE`: 2
- `QUASI_DUPLICATE`: 2
- `MEDICINE_BOUNDARY`: 1
- `MARKET_ONLY_CANONICAL_GAP`: 1

### Structural gap resolution
The 21 historical rows carrying a gap disposition reduce to 20 unique structural gap targets because the low-abrasivity and strontium concepts each have overlapping historical representations.

- Unique structural gap targets: 20.
- Canonical extension rows created for those targets: 20/20.
- These rows are taxonomy/evidence placeholders only. They do not constitute Morocco market validation, regulatory validation or clinical recommendation.
- All extension rows remain `clinical_activation=NO`.

### Subsequent addenda
- Addendum V1 rows: 4.
- Addendum V2 rows: 4.
- Addendum disposition coverage: 8/8.
- Combined enumerated source rows now dispositioned: 178/178.
- The gingival-antimicrobial toothpaste addendum is represented as a product-specific canonical alias requiring the exact active/material, concentration and product; it is not a generic treatment recommendation.

## Important interpretation
`178/178 dispositioned` means the currently enumerated source universe has no unmapped row. It does **not** prove that the inventory contains every medicine, OTC product or dental para that could be relevant in Morocco.

Likewise, converting structural gaps into explicit canonical rows closes silent-loss risk, not evidence risk. Many canonical rows still require Morocco product localization, regulatory evidence, clinical evidence review, or product-specific safety review.

## Safety invariants retained
- `clinical_activation=NO` throughout.
- Market presence is not treated as medicine authorization.
- Foreign regulatory evidence is not treated as Morocco regulatory evidence.
- Family-level evidence is not treated as exact product/form/concentration evidence.
- Duplicate and overlap rows remain traceable; no unsafe automatic merge is authorized.
- No AMMPS contact was made.

## Remaining critical path
1. Run canonical-target integrity checks: every mapping target must resolve to a base canonical row, canonical extension, retained medicine identity, documented overlap entity, or explicit adjacent-care boundary.
2. Resolve remaining Morocco localization gaps for priority clinical/product families.
3. Perform deterministic fail-closed tests against consumer/activation logic.
4. Perform independent clinical/regulatory review before any activation claim.
5. Reconcile the branch with current `master` only after the evidence/data layer is internally coherent.

## Verdict V2
- `ENUMERATED_SOURCE_DISPOSITION = 178/178`
- `HISTORICAL_MAPPING_COMPLETION = 100%`
- `STRUCTURAL_GAP_TARGET_ASSIGNMENT = 20/20`
- `COMPLETENESS_CERTIFIED = NO`
- `TAXONOMY_CLOSED = NO`
- `CLINICAL_ACTIVATION = NO`
