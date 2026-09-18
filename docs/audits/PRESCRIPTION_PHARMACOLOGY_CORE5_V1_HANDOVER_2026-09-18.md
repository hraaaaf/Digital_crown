# Digital Crown — Ordonnance Core-5 V1 Handover — 2026-09-18

Status: CLOSED_AS_FAIL_CLOSED_EVIDENCE_PACKAGE / NO_CLINICAL_ACTIVATION

## Goal
Close the residual Core-5 pharmacology evidence gap on top of the certified V1-03 audit-only reconstruction without reintroducing stale #565 history or authorizing prescribing automation.

## Base
- repository: hraaaaf/Digital_crown
- base master: d6ba162f14545be521279c2dd38226161633287a
- merged branch: feat/v1-ordonnance-core5-certification
- PR #594: MERGED
- merge SHA: 2304003a4757ed8442f0b3f2ec121aa3dce6dac2
- stale source PR #565: CLOSED WITHOUT MERGE
- divergent audit PR #572: CLOSED WITHOUT MERGE

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
Final PR exact-head proof on `689e6c7af7a548ca25f008887b7ce95b8af73eda`:
- Pharmacology Deterministic Scientific Safety Gate `35358582607`: SUCCESS
- CI `35358582688`: SUCCESS
- T2 Runtime Browser Certification `35358582593`: SUCCESS
- Agenda A5 Visual Evidence `35358582692`: SUCCESS
- UI Human Visual Approval `35358579137`: SUCCESS

The earlier candidate gate `35358243923` also completed SUCCESS and established:
- targeted pharmacology documentary tests: SUCCESS
- reconstructed reference validator: SUCCESS
- deterministic medicine gap audit: SUCCESS
- deterministic scientific safety oracle: SUCCESS

The temporary branch push trigger used during development was removed before merge. Final exact-head recertification is complete.

## Scientific pre-review and activation boundary
Automated adversarial scientific pre-review run `35359075923` completed SUCCESS on immutable target `689e6c7...` with decision `approve_for_human_review_with_reservations`, 0 blocking findings, `clinical_activation_authorized=false`, and `human_clinical_review_required=true`.

Product-owner decision on 2026-09-18: exact Morocco product/form/strength/presentation closure and qualified human review are not required to merge this documentation/evidence package because all five medicines remain fail-closed. They remain required before any future clinical activation is considered.

If future activation is requested, a qualified independent dentist/pharmacist/clinical reviewer must review the five medicines using:
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

## Closeout
The residual Core-5 evidence package is merged and closed as fail-closed documentation. No medicine is clinically activated by this work.

## Next exact
No Core-5 action is required for the current V1 path while `clinical_activation=NO` remains unchanged. If future activation is requested, reopen a separate activation lot beginning with qualified clinical/scientific review, exact Morocco product/form/strength/presentation closure where relevant, deterministic negative tests, and exact-head CI.

No clinical activation is authorized by this handover.
