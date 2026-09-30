# NEO-ORDONNANCE 1 — Runtime Safety Audit

Date: 2026-09-30
Status: CHANGES_REQUIRED

## Goal
Establish the exact active prescription safety path before adding any new clinical automation.

## Verified active safety foundations
- Structured patient context exists for medication allergies and penicillin/amoxicillin allergy.
- Pharmacology pipeline preserves unknown paediatric weight; it does not synthesize weight from age.
- Amoxicillin severe-infection rules fail closed when weight/context is insufficient and require practitioner review in ambiguous adolescent cases.
- A post-arbitration weight safety gate exists for ibuprofen and does not invent replacement doses.
- Pharmacology documentation explicitly forbids automatic allergy substitution and local force-allergy bypass.

## Critical finding — legacy contradiction
`DiagnosticEngine.ts` still contains automatic therapeutic substitutions from free-text antecedents:
- amoxicillin -> clindamycin/macrolide when penicillin allergy text is detected;
- NSAID -> corticosteroids when NSAID allergy text is detected.

This directly conflicts with the current pharmacology contract documented in `DENTAL_PHARMACOLOGY_COVERAGE.md` and `DENTAL_PHARMACOLOGY_SOURCES.md`, which prohibit automatic allergy substitution.

## Runtime trace — verified
Repository search shows `DiagnosticEngine.ts` is imported only by `SafeDiagnosticEngine.ts`. The UI caller (`HouseWizard.tsx`) imports the safe wrapper, not the legacy engine directly. The safe wrapper invokes the legacy evaluator with `medicalHistory: ''`, preventing its free-text allergy substitution branch from firing, then emits warning-only review signals from the actual history.

Therefore the suspected automatic allergy substitution is currently quarantined from the observed UI call path. The unsafe code still exists and remains technical/clinical debt; direct future import would re-open the hazard.

## Test evidence
Targeted Vitest run: 5 files passed, 39/39 tests passed:
- DiagnosticEngine.p5p0.test.ts
- PrescriptionPharmacologyPipeline.test.ts
- PrescriptionAmoxicillinSevereSafety.test.ts
- normalizeMedicationForPatient.test.ts
- PrescriptionSafetyState.test.ts

## Coverage inventory — first pass
- Pregnancy: structured field reaches the arbiter; explicit ibuprofen review gate exists. Broad medication coverage is not yet demonstrated.
- Renal: structured UI context exists; severe amoxicillin path fails closed. Broad medication coverage is not yet demonstrated.
- Hepatic: structured UI context exists and pipeline carries a hepatic flag, but no broad executable hepatic safety rule was found in this first pass.
- Interactions: documentation marks clarithromycin, miconazole and fluconazole as requiring interaction review, but this first pass did not find a comprehensive executable drug-drug interaction engine in the ordonnance module.

## Priority gaps
P0: make legacy unsafe substitution structurally impossible to call directly.
P0: prove or implement a deterministic interaction gate for the medications whose source contract requires interaction review.
P1: expand structured pregnancy/renal/hepatic gates molecule-by-molecule from source-backed rules; do not infer missing facts.

## Gate decision
PARTIAL PASS for the runtime boundary. NEO-ORDONNANCE 1 is not closed.

Strict score after trace: 8.2/10 runtime safety boundary.

## Evidence targets for closeout
1. Active runtime call graph documented.
2. No active path can auto-substitute therapy because of free-text allergy detection.
3. Regression test proves allergy context yields block/review, never automatic replacement.
4. Existing paediatric weight fail-closed tests remain green.
5. Deterministic interaction gate proven for source-declared interaction-sensitive medications.
6. Full targeted ordonnance/pharmacology test suite green.
