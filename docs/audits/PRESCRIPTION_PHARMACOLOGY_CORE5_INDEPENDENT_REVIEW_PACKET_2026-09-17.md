# Prescription Pharmacology — Core-5 Independent Review Packet — 2026-09-17

Status: READY_FOR_INDEPENDENT_REVIEW
Clinical activation: NO

## Goal
Provide a bounded, traceable package for an independent dentist/pharmacist/clinical reviewer to assess the five Core-5 medicine candidates before any automatic prescription activation.

## Scope
- MED-PAIN-001 — paracetamol
- MED-PAIN-002 — ibuprofen
- MED-ABX-003 — phenoxymethylpenicillin / penicillin V
- MED-ABX-001 — amoxicillin
- MED-ABX-004 — metronidazole

## Required inputs
1. `PRESCRIPTION_PHARMACOLOGY_MOROCCO_CLINICAL_PASS1_CORE_2026-09-16.csv`
2. `PRESCRIPTION_PHARMACOLOGY_CORE5_MOROCCO_REGULATORY_PASS_2026-09-17.md`
3. `PRESCRIPTION_PHARMACOLOGY_CORE5_SAFETY_EVIDENCE_INDEX_2026-09-17.csv`
4. `PRESCRIPTION_PHARMACOLOGY_CORE5_SOURCE_REVALIDATION_2026-09-18.md`
5. Current deterministic fail-closed validator and tests.

## Reviewer decisions required for each Core-5 row
The reviewer must explicitly mark each dimension PASS / FAIL / NEEDS_CORRECTION:
- dental indication boundary
- adult regimen evidence
- pediatric regimen evidence / age boundary
- maximum dose or treatment limit
- duration / review interval
- contraindications and precautions coverage
- interaction coverage
- renal/hepatic adjustment boundary where applicable
- Morocco exact product/form/strength/presentation suitability
- consistency between source evidence, backend representation, UI/PDF wording

## Mandatory fail-closed rules
- `clinical_activation` remains `NO` unless every required dimension is explicitly accepted by the independent reviewer.
- Official Moroccan product/catalogue presence does not equal dental indication validation.
- Commercial status does not equal regulatory status.
- A molecule-level AMM/database match does not close an exact product/form/strength automation target.
- Any unresolved interaction, contraindication, age/weight boundary, renal/hepatic boundary, formulation mismatch, or source conflict keeps activation at `NO`.

## Reviewer output contract
For every reviewed medicine, record:
- reviewer identity and professional role
- review date
- source set reviewed
- PASS / FAIL / NEEDS_CORRECTION for every required dimension
- exact correction requested when not PASS
- final recommendation limited to `ELIGIBLE_FOR_TECHNICAL_ACTIVATION_REVIEW` or `KEEP_FAIL_CLOSED`

The independent review does not itself activate a medicine. Technical activation requires a subsequent code/data change, deterministic tests, exact-HEAD CI, and final integration review.

## Current state before independent review
- Morocco molecule/product evidence: indexed for Core-5.
- Safety evidence domains: revalidated against current public authoritative sources on 2026-09-18.
- Exact AMMPS product/presentation revalidation on 2026-09-18: NOT REPRODUCED FROM PUBLIC SEARCH; historical direct AMMPS capture retained, exact automation target still PENDING.
- Deterministic fail-closed baseline: established.
- Automatic clinical activation: 0/5.
- Independent clinical/scientific review: NOT YET PERFORMED.
