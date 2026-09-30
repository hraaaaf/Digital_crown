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
DiagnosticEngine.ts still contains automatic therapeutic substitutions from free-text antecedents:
- amoxicillin -> clindamycin/macrolide when penicillin allergy text is detected;
- NSAID -> corticosteroids when NSAID allergy text is detected.

This directly conflicts with the current pharmacology contract documented in DENTAL_PHARMACOLOGY_COVERAGE.md and DENTAL_PHARMACOLOGY_SOURCES.md, which prohibit automatic allergy substitution.

## Gate decision
NEO-ORDONNANCE 1 cannot be certified while it is unproven that DiagnosticEngine.ts is unreachable from the active prescription runtime. The safe next action is to trace every import/call path to this engine, then either remove/quarantine the legacy substitution path or prove it is outside the ordonnance runtime with regression tests.

## Evidence targets for closeout
1. Active runtime call graph documented.
2. No active path can auto-substitute therapy because of free-text allergy detection.
3. Regression test proves allergy context yields block/review, never automatic replacement.
4. Existing paediatric weight fail-closed tests remain green.
5. Full targeted ordonnance/pharmacology test suite green.

## Current strict score
Safety architecture: 8.5/10.
Runtime coherence: 6.5/10 until the legacy path is resolved.
NEO-ORDONNANCE 1 gate: NOT PASSED.
