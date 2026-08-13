# P0-1 — Prescription Missing-Data Audit

Date: 2026-08-13
Baseline: `master@c8669527c6eb9c5232afa4277b5cd4c387a862fd`
Mode: **read-only audit** under `.claude/skills/audit-prescription-flow/SKILL.md`.

## Verdict

**BLOCKED — P0 CONFIRMED**

The prescription flow does not fail closed when required patient context is missing. Synthetic defaults and estimated values can participate in dosage guidance, propagate to the active prescription UI, reach document generation, and be learned as practitioner habits.

No production code, rule, test, fixture, database or patient data was modified during this audit.

## Route map

`DocumentHub` → active `PrescriptionAgenticStudio` → prescription assessment/suggestion endpoints → `PrescriptionService` → `ClinicalRulesEngine` → UI drug fields → `useDocumentGenerator` → documents API → ordonnance PDF → optional archive → prescription habit recording.

The active ordonnance UI is `PrescriptionAgenticStudio`. `PrescriptionForm` remains present as a parallel/legacy implementation and should not be treated as the current primary path without a separate wiring change.

## Blocking findings

### B1 — Synthetic patient weight in backend

`PrescriptionService.resolve_smart_prescription()` supplies a fixed weight when no measured weight exists. `ClinicalRulesEngine.analyze_case()` contains a second independent age/weight fallback.

The patient model currently has no structured weight field. Therefore the safe correction is not to substitute another guessed value: weight-dependent logic must become non-evaluable until an authoritative measurement exists.

### B2 — Synthetic/estimated weight in frontend

`PrescriptionAgenticStudio` initializes age/weight defaults and the frontend clinical-rules module can estimate weight from age when actual weight is unavailable. That estimated weight can feed pediatric dosing guidance.

This is an independent clinical authority outside the backend and can diverge from backend behavior.

### B3 — Unknown clinical context can be presented as cleared

Nullable medical-history data is collapsed into an empty string in the backend suggestion path. The agentic assessment can then report that no risk was detected even though the relevant history may simply be undocumented.

Unknown must remain unknown; absence of documented evidence is not evidence of absence.

### B4 — Duplicate clinical rule authorities

Substantial medication/dosing/contraindication logic exists both in backend `ClinicalRulesEngine` and frontend `clinical_rules.ts`, plus legacy quick-prescription logic. This violates the backend-authority direction and creates divergence/provenance risk.

### B5 — Unsupported values can propagate to PDF and habits

The ordonnance PDF renderer prints the medication fields it receives; it does not independently establish the clinical provenance of those fields. After non-preview generation, medication usage can be recorded into practitioner habits. Therefore a synthetic or unsupported suggestion can become persistent learned preference data.

### B6 — Missing-data safety is not covered by tests

Current tests cover authentication, DDI examples, cross-checks and happy paths, but do not demonstrate:

- child + unknown weight → no automatic weight-dependent dose;
- unknown history → explicit incomplete/unknown state;
- no age/weight fallback in direct engine calls;
- assessment/API/UI parity for patient context;
- frontend never deriving a clinical dose from estimated weight;
- PDF/habit persistence cannot promote an unsupported value.

## High findings / adjacent scope

- The patient model has a required date of birth in normal persisted flow, but direct rule-engine fallbacks still synthesize age on incomplete calls.
- The prescription safety route tenant guard remains a separate P0 (`P0-5`) and is not fixed in this audit.
- Agentic design accepts client-provided assessment/context and requires a separate trust-boundary review during implementation.
- Appointment motives / recent act labels can influence prescription context without an explicit diagnostic-state contract; this should be cross-reviewed under the diagnosis-flow skill.
- Medication/dosing constants require traceable scientific provenance before they can be treated as authoritative. Tests alone are not scientific validation.

## Evidence gaps

Before authoritative dose/rule changes:

1. define the source of an actual current patient weight;
2. distinguish undocumented history from documented absence;
3. establish authoritative source records for dosing/contraindication constants;
4. define server-side context/provenance returned to the UI;
5. define which frontend rule code must become renderer-only or be removed.

## Required implementation acceptance criteria

A future implementation lot must prove at minimum:

- no fabricated or age-estimated patient weight is used for clinical dosing;
- missing required context produces an explicit non-evaluable/incomplete state;
- backend is the sole clinical authority for prescription safety/dosing decisions;
- UI displays provenance/uncertainty and does not reconstruct dosing authority;
- unknown history cannot be rendered as “no risk detected”;
- generated/archived documents cannot silently promote unsupported auto-generated values;
- unsupported values are not learned as practitioner habits;
- new targeted tests cover missing-data paths and UI/API/PDF parity;
- scientific review is independent from implementation review where required by project rules.

## Handoff

Recommended next sequence:

1. **LOT 1B — structural fail-closed implementation**: remove synthetic defaults/estimated-weight clinical use and introduce explicit incomplete states, without inventing new medical constants.
2. **LOT 1C — scientific source certification**: use `scientific-source-research` for any dosage/contraindication rule that is intended to remain authoritative.
3. targeted tests + broader regression;
4. independent scientific review;
5. canonical closeout and exact-head certification.
