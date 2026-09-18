# Digital Crown — Ordonnance Core-5 V1 Handover — 2026-09-18

Status: TECHNICALLY_FAIL_CLOSED / QUALIFIED_HUMAN_REVIEW_REQUIRED

## Goal
Close the residual Core-5 pharmacology evidence gap on top of the certified V1-03 audit-only reconstruction without reintroducing stale #565 history or authorizing prescribing automation.

## Base
- repository: hraaaaf/Digital_crown
- base master: d6ba162f14545be521279c2dd38226161633287a
- branch: feat/v1-ordonnance-core5-certification
- PR: #594 DRAFT
- stale source PR #565: evidence source only; never merge as-is
- divergent audit PR #572: evidence source only; never merge as-is

## Core-5 scope
- MED-PAIN-001 — paracetamol
- MED-PAIN-002 — ibuprofen
- MED-ABX-003 — phenoxymethylpenicillin / penicillin V
- MED-ABX-001 — amoxicillin
- MED-ABX-004 — metronidazole

## Verified technical state
- V1-03 baseline remains audit-only and fail-closed.
- Current 68-row medicine projection retains clinical_activation=NO for all medicines.
- Core-5 safety evidence index contains exactly the five expected medicines and requires independent review.
- Core-5 review packet is tied to the current projection and current source revalidation.
- Historical unreviewed detailed regimen CSV is intentionally not restored into the V1 activation path.
- Qualified review form starts all dimensions at NOT_REVIEWED, final recommendation KEEP_FAIL_CLOSED, clinical activation NO.
- Exact Morocco automation product/form/strength/presentation closure remains PENDING for all 5.

## Current source boundary
Safety evidence was rechecked on 2026-09-18 against current public authoritative sources including SDCEP, DailyMed and emc.

The direct AMMPS observations from 2026-09-17 are retained as historical primary-source capture. Public search on 2026-09-18 did not independently reproduce every exact presentation-level AMMPS record, so no fresh exact-product regulatory closure is claimed.

## Deterministic proof
Pharmacology Deterministic Scientific Safety Gate run 35358243923 completed SUCCESS on candidate HEAD 82e95c16af89841af52b4c1bdf3ba43dd2b95e7f:
- targeted pharmacology documentary tests: SUCCESS
- reconstructed reference validator: SUCCESS
- deterministic medicine gap audit: SUCCESS
- deterministic scientific safety oracle: SUCCESS

The temporary branch push trigger used to materialize the gate was removed afterward. Final exact-HEAD recertification is therefore required on the final PR head before technical closeout.

## Human gate
A qualified independent dentist/pharmacist/clinical reviewer must review the five medicines using:
1. PRESCRIPTION_PHARMACOLOGY_MOROCCO_MEDICINE_CURRENT_STATUS_PROJECTION_V1_2026-09-17.csv
2. PRESCRIPTION_PHARMACOLOGY_CORE5_MOROCCO_REGULATORY_PASS_2026-09-17.md
3. PRESCRIPTION_PHARMACOLOGY_CORE5_SAFETY_EVIDENCE_INDEX_2026-09-17.csv
4. PRESCRIPTION_PHARMACOLOGY_CORE5_SOURCE_REVALIDATION_2026-09-18.md
5. PRESCRIPTION_PHARMACOLOGY_CORE5_QUALIFIED_REVIEW_FORM_2026-09-18.md
6. current primary clinical references

The qualified review must explicitly decide each required dimension for each medicine. Any FAIL, NEEDS_CORRECTION, NOT_REVIEWED, unresolved product/formulation question or source conflict keeps that medicine fail-closed.

## Prohibited conclusions
- do not call Core-5 clinically certified before qualified review;
- do not set clinical_activation=YES from this evidence package;
- do not infer exact Moroccan product suitability from molecule-level presence;
- do not restore historical dosing data as an automatic prescribing source;
- do not merge #565 or #572 wholesale.

## Next exact
1. obtain final exact-HEAD deterministic pharmacology gate on the final PR head;
2. record that technical proof here if green;
3. execute qualified independent clinical/scientific review using the review form;
4. correct and re-review any failed dimension;
5. only if qualified review clears a medicine, create a separate technical activation change with deterministic negative tests and exact-HEAD CI;
6. merge/closeout only within the canonical V1 roadmap rules.

No clinical activation is authorized by this handover.
