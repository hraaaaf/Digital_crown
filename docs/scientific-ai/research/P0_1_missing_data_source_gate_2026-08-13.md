# P0-1 — Missing clinical data source gate — 2026-08-13

## Question
Can Digital Crown safely synthesize age/weight or infer weight from age when a prescription-support rule depends on those inputs?

## Intended implementation target
`P0-1 — PRESCRIPTION-MISSING-DATA-FAIL-CLOSED`

Target behavior under review:
- a missing clinical input remains unknown;
- no patient-specific calculation is produced from a synthetic default;
- the UI asks for the missing input or marks the rule non-evaluable;
- no invented value is persisted, printed, or learned as a practitioner habit.

## Verified candidate sources

### AAPD — Useful Medications for Oral Conditions
- Organization: American Academy of Pediatric Dentistry
- Reference Manual: 2025-2026
- Latest revision shown by source: 2025
- Jurisdiction: United States
- Source type: professional society guidance
- Candidate claim supported: pediatric medication guidance uses explicit pediatric dose logic and states that pediatric dosage should not exceed adult dosage.
- Limitation: does not by itself establish Moroccan product availability or approve any specific Digital Crown dosing rule.
- Status: candidate only; no human approval assigned.
- URL: https://www.aapd.org/research/oral-health-policies--recommendations/useful-medications-for-oral-conditions/

### AAPD — Use of Local Anesthesia for Pediatric Dental Patients
- Organization: American Academy of Pediatric Dentistry
- Reference Manual: 2026-2027 page listing
- Latest revision shown by source: 2023
- Jurisdiction: United States
- Source type: professional society best practice
- Candidate claim supported: medication safety considerations include patient medical history, developmental status, age and weight; dose administered should be documented.
- Limitation: local-anesthesia scope; not a universal drug-dose table.
- Status: candidate only; no human approval assigned.
- URL: https://www.aapd.org/research/oral-health-policies--recommendations/use-of-local-anesthesia-for-pediatric-dental-patients/

### AAPD — Policy on Patient Safety
- Organization: American Academy of Pediatric Dentistry
- Reference Manual: 2026-2027 page listing
- Latest revision shown by source: 2025
- Jurisdiction: United States
- Source type: professional society policy
- Candidate claim supported: medication ordering/administration should include review of current medications, allergies, drug interactions, indication and correct dosage calculation.
- Limitation: safety policy, not a product-specific prescribing monograph.
- Status: candidate only; no human approval assigned.
- URL: https://www.aapd.org/research/oral-health-policies--recommendations/patient-safety/

## Rejected use
- No source was used to approve any specific drug, concentration, mg/kg constant, maximum dose, duration, product presentation, or Moroccan market status.
- No source was used to justify estimating a real patient's weight from age.

## Engineering conclusion supported for review
The current synthetic-default pattern is not suitable as authoritative patient context. The safe implementation direction is fail-closed: when an input required by a patient-specific rule is unavailable, the rule is non-evaluable until the explicit input is available.

## Governance status
`candidate-only`

This research record does not activate or approve a scientific rule. Human clinician approval remains required by `.claude/skills/implement-scientific-rule/SKILL.md` before modifying active scientific logic.

## Recommended reviewer
Human clinician reviewer with responsibility for Digital Crown prescription governance.
