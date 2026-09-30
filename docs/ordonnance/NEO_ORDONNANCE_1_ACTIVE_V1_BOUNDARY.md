# NEO-ORDONNANCE 1 — Active V1 boundary correction

Date: 2026-09-30
Status: BLOCKED_BY_DESIGN

## Critical correction after active-studio trace
The active `PrescriptionAgenticStudioV1.tsx` explicitly declares:
- `data-clinical-rule-status="blocked"`
- `data-safety-status="blocked"`

It renders `DrugRow` with `assessment={null}`, empty safety suggestions/checks, and no active pharmacology normalization call. The existing `PrescriptionIntelligenceV1.boundary.test.ts` intentionally asserts that legacy automatic prescription mechanisms and the uncertified legacy safety engine remain outside the active V1 studio.

Therefore the pharmacology engines audited in the companion document are implemented/tested foundations, but they are NOT proven to be active in the current V1 ordonnance line-editing runtime. This distinction is mandatory.

## Additional context gap
`PatientClinicalContextPanel` actively captures weight, medication allergies, penicillin allergy, endocarditis cardiac-risk category, renal context and hepatic context. It does not currently expose pregnancy or breastfeeding fields. `PrescriptionPharmacologyPipeline` supports pregnancy/breastfeeding if supplied by structured assessment data, but the active V1 studio currently passes `assessment={null}` to its drug rows.

## Revised NEO-ORDONNANCE 1 goal
Do not merely harden a supposedly active safety engine. First design and prove a safe activation boundary:
1. active V1 studio -> structured patient context;
2. medication identity/DCI -> deterministic pharmacology arbitration;
3. missing/unsafe/interaction-sensitive context -> fail closed / practitioner review;
4. no automatic therapeutic substitution;
5. no automatic overwrite of explicit practitioner dosage/posology;
6. audit trail of rule/evidence/version used.

## Gate
NEO-ORDONNANCE 1 remains OPEN. Current active V1 safety automation is intentionally blocked. Activation requires implementation + targeted tests + observed runtime evidence; existing engine unit tests alone are insufficient.

Strict current score for active V1 safety integration: 5.5/10.
Underlying pharmacology foundation: 8.2/10.
