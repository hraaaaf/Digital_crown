# Prescription / Pharmacology Morocco — Medicine Current Status Projection V1

Date: 2026-09-17
Branch: `docs/pharmacology-m1-handover-20260915`
Input HEAD: `b6318d342267bd0762a535139f35e4d1765b3602`
Status: CURRENT-STATUS PROJECTION / FAIL-CLOSED
Clinical activation: NO

## Goal

Create the current row-level medicine closure view without treating stale `TO_VERIFY_MA` / `TO_VALIDATE` fields in the early master inventory as current truth.

## Success / proof contract

Success requires every medicine inventory row to be projected against later dedicated clinical and Morocco-localization passes before any global completion percentage is certified.

This V1 establishes the projection rules and verified deltas visible in the current evidence set. It does not infer missing evidence and does not authorize clinical activation.

## Source precedence

For a medicine row, use the newest dedicated evidence layer that names the same medicine/entity before the historical master inventory:

1. dedicated medicine family pass (analgesics/AINS/opioids; antifungal/antiviral; secondary anti-infectives; mucosal; local anaesthesia; emergencies; remaining medicines);
2. clinical pass with explicit regimen/safety fields;
3. Morocco availability/localization evidence pass;
4. master inventory only as the historical denominator and identity registry.

Market presence, regulatory authorization/form status, clinical evidence and clinical activation are separate dimensions.

## Projection schema

The normalized row-level registry must carry at minimum:

`historical_id | canonical_medicine | dental_role | exact_form_strength_target | morocco_market_status | regulatory_status | clinical_evidence_status | adult_regimen_status | pediatric_regimen_status | max_dose_limit_status | duration_status | contraindications_precautions_status | interactions_status | specialist_protocol_boundary | unresolved_critical_fields | evidence_layer | clinical_activation`

`clinical_activation` defaults to `NO` and cannot be promoted by this projection.

## Verified current deltas from inspected evidence

### Core clinical pass

The dedicated core clinical pass supersedes historical `TO_VALIDATE` for the following rows at the clinical-evidence dimension only:

- MED-PAIN-001 paracetamol → `CROSS_VALIDATED_CORE`;
- MED-PAIN-002 ibuprofen → `CROSS_VALIDATED_CORE`;
- MED-ABX-003 penicillin V → `CROSS_VALIDATED_CORE`;
- MED-ABX-001 amoxicillin → `CROSS_VALIDATED_CORE`;
- MED-ABX-004 metronidazole → `CROSS_VALIDATED_CORE`;
- MED-ABX-006 clarithromycin → `CROSS_VALIDATED_WITH_CAUTION`;
- MED-ABX-005 clindamycin → `CROSS_VALIDATED_WITH_CAUTION`;
- MED-ABX-002 amoxicillin/clavulanate → `NOT_ROUTINE_DENTAL_ABSCESS`.

These statuses do not upgrade Morocco regulatory proof and do not authorize automatic prescribing.

### Analgesics / NSAIDs / opioids pass

- MED-PAIN-003 naproxen → clinical `CLINICAL_SUPPORTED`; Morocco `PARTIAL_VERIFIED_MA`; formulation/regimen remains to validate.
- MED-PAIN-004 diclofenac → clinical `CLINICAL_SUPPORTED_NONDEFAULT`; Morocco `PARTIAL_VERIFIED_MA`; regimen remains to validate.
- MED-PAIN-005 ketoprofen → clinical `TO_VALIDATE`; Morocco `TO_VERIFY_MA`.
- MED-PAIN-006 dexketoprofen → clinical `TO_VALIDATE`; Morocco `TO_VERIFY_MA`.
- MED-PAIN-007 paracetamol + codeine → `SPECIALIST_OR_EXCEPTION`; Morocco presence verified; `NO_AUTOMATIC_REGIMEN`.
- MED-PAIN-008 tramadol → `SPECIALIST_OR_EXCEPTION`; Morocco presence verified; `NO_AUTOMATIC_REGIMEN`.

All remain `clinical_activation=NO`.

### Remaining-medicines pass

The later pass establishes these current deltas without converting them into routine dental prescriptions:

- hydrocortisone buccal: adult reference captured; pediatric age-restricted; Morocco still `TO_VERIFY_MA`;
- triamcinolone oral paste, dexamethasone topical/rinse, prednisolone topical/rinse: specialist/exception boundaries remain; formulation-specific evidence incomplete;
- tranexamic acid: not routine primary-care dental prescription;
- pilocarpine: reference captured but specialist/exception; Morocco still unclosed;
- cevimeline: reference captured but Morocco availability/authorization unproven;
- nitrous oxide + oxygen: protocol/competence/monitoring boundary required; Morocco unclosed;
- midazolam: Morocco partially verified, references captured, but no automatic dental protocol;
- diazepam: Morocco market presence verified but dental indication/regimen not thereby established;
- hydroxyzine: Morocco/form status remains unresolved.

## Fail-closed reconciliation rules

1. A newer clinical status may replace historical `TO_VALIDATE` only for the clinical-evidence dimension explicitly covered by that pass.
2. A Morocco market-presence finding never upgrades `regulatory_status` unless the evidence explicitly proves the regulatory/form claim.
3. A form/strength mismatch remains unresolved even if the same DCI is present in Morocco.
4. `SPECIALIST_OR_EXCEPTION`, `NON_ROUTINE`, `PROTOCOL_REQUIRED`, `NO_AUTOMATIC_REGIMEN`, `TO_VALIDATE` and equivalent boundaries cannot be silently promoted.
5. Missing pediatric, maximum-dose, duration, contraindication/precaution or interaction evidence remains an unresolved clinical field.
6. No row may become clinically active from aggregation or projection alone.

## Current closure conclusion

The historical medicine inventory is demonstrably stale for several rows because later passes contain stronger, more specific statuses. Therefore raw counts of `TO_VERIFY_MA` / `TO_VALIDATE` in the master inventory are not a valid current denominator.

At the same time, the inspected later passes still contain explicit unresolved Morocco, formulation, regimen, pediatric, interaction and specialist/protocol boundaries. Consequently medicine closure is not yet certified and no global Ordonnance completion percentage is emitted by V1.

## Next exact

Materialize the projection as a row-level CSV covering every `MED-*` row in the master inventory, reconciling all dedicated later passes by historical ID/canonical entity. Any field not explicitly supported remains pending and `clinical_activation=NO`.

After the full row-level projection exists, compute unresolved counts by dimension and prioritize the safety-critical gaps before independent scientific review.

## Safety boundary

This document is a normalization/provenance artifact, not scientific or clinical approval. Independent scientific review and clinician review remain required. No deployment is authorized.
