# V1-05 Ortho Journey — F3 Longitudinal Comparison

Status: **STARTED — BEFORE VISUAL BASELINE FIRST**

## Trailer

F3 lets the practitioner compare two orthodontic timepoints (for example T0 vs T1) side by side.

It presents:
- the selected timepoints and dates
- canonical evidence attached to each timepoint
- overlapping certified cephalometric measurements
- raw numeric values and numeric deltas only

It must never automatically say that treatment improved, succeeded, failed, normalized, worsened, or reached a clinical objective.

## Goal

Create one focused longitudinal comparison surface in the patient Overview, backed by canonical F2 timepoints/evidence.

## Success

A practitioner can:
1. choose two existing timepoints
2. see both dates and evidence inventory
3. see side-by-side canonical evidence summaries
4. see common certified numeric cephalometric measurements and their arithmetic delta
5. navigate to the canonical source where applicable
6. use the experience on 390×844, 768×1024 and 1280×900 without horizontal overflow

## BEFORE finding

The current Patient Journey can receive F2 `ortho_timepoint` events, but:
- `PHASE_ORDER` has no `ortho` phase
- `SOURCE_LABELS` has no `ortho_timepoint`
- `SOURCE_ICONS` has no `ortho_timepoint`
- there is no T0/T1 comparison surface

Therefore F3 should not overload the generic timeline. It should add a dedicated longitudinal comparison surface above the timeline while keeping Patient Journey factual and generic.

## Scientific guardrails

Longitudinal cephalometric differences are measurement differences, not automatic treatment-effect judgments.

Published work documents non-zero method/landmark error and variable longitudinal reproducibility. F3 therefore:
- shows values and deltas without qualitative labels
- preserves calibration/provenance
- does not apply thresholds for improvement/worsening
- does not infer treatment success
- does not implement superimposition (F5)

## UI/UX protocol

Mandatory sequence:
1. BEFORE exact merged F2 baseline
2. written Goal
3. mockup/reference aligned to current PatientDetails visual language
4. implementation
5. AFTER at identical viewports: 390×844 / 768×1024 / 1280×900
6. pixel/layout comparison + tests + severe visual score

## Initial layout direction

Patient Overview / Vue d’ensemble:
- compact header: “Comparaison orthodontique”
- two balanced timepoint selectors/cards: T0 and T1
- evidence lane under each side
- compact measurement table below, responsive to stacked cards on mobile
- neutral delta column using signed numeric values only
- explicit caption: “Variation numérique — interprétation clinique par le praticien”

## Out of scope

- automatic improvement/success/progress labels
- normative severity thresholds
- automatic treatment recommendation
- cephalometric superimposition
- F4 full orthodontic cockpit
