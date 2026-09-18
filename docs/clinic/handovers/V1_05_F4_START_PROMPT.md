# START PROMPT — Digital Crown V1-05 / F4 — Ortho Cockpit

Repository: `hraaaaf/Digital_crown`

Parent chantier:
**V1-05 — Ortho Journey**

Previous completed lot:
**F3 — Longitudinal Compare**

## Functional trailer

- F1A: durable orthodontic case lifecycle
- F1B: structured orthodontic controls
- F2: canonical T0/T1/T2/Tn evidence binding
- F3: factual longitudinal comparison with raw numeric deltas
- **F4: compact practitioner cockpit for current orthodontic state**
- F5: scientific superimposition — separate scientific gate, not authorized here

---

## Goal

Give the practitioner one compact, high-signal orthodontic control surface inside the patient record.

The cockpit must answer, in seconds:

- when treatment started
- current phase
- current lifecycle status
- number of structured controls
- last control
- next planned step
- next control / next appointment
- latest orthodontic timepoint
- latest canonical cephalometric/panoramic/media evidence
- unresolved or recent longitudinal events that require attention

It must drill down to canonical sources instead of duplicating them.

---

## Success

F4 succeeds only if:

1. the cockpit reuses F1/F2/F3 canonical data;
2. it does not create a second Patient Journey;
3. it does not create a second media registry;
4. it does not infer diagnosis, treatment success, improvement, severity or treatment recommendation;
5. every displayed current-state fact has a canonical source;
6. missing data fail closed and are clearly distinguished from zero/none;
7. the practitioner can navigate from summary cards to canonical evidence;
8. mobile/tablet/desktop remain readable with no horizontal overflow;
9. BEFORE → Goal → mockup/reference → implementation → AFTER is completed on the canonical viewports;
10. exact-head CI and post-merge certification are green.

---

## Canonical inputs already available

### F1A — OrthoCase

Use the durable orthodontic case as the source of truth for:

- treatment start
- lifecycle status
- current practitioner-selected phase
- interruption/resume
- abandonment/closure
- append-only phase/lifecycle history

Do not infer phase from cephalometric measurements or media.

### F1B — OrthoControl

Use structured controls for:

- control date
- phase at control
- observations
- appliance/device context
- notable event
- next planned step
- next_control_at

Do not replace structured fields with free-text summarization.

### F2 — OrthoTimepoint

Use timepoints for:

- T0/T1/T2/Tn chronology
- canonical evidence inventory
- latest timepoint
- linked ClinicalAsset / CephaloAnalysis / PanoramicAnalysis

Media remain owned by Media Core.

### F3 — Longitudinal Compare

F3 remains a focused comparator.

F4 may link to F3 or reuse factual summary information, but must not duplicate the full comparison surface.

---

## F4 cockpit content

Target compact summary:

### Current state
- treatment start date
- lifecycle status
- current phase
- elapsed treatment duration if computed purely from dates
- number of structured controls

### Latest control
- date
- phase
- notable event
- next planned step
- next_control_at

### Next scheduled care
- next appointment, if canonical appointment data exists
- never invent a next appointment from next_control_at

### Latest evidence
- latest orthodontic timepoint
- latest cephalometric evidence
- latest panoramic evidence
- latest Media Core orthodontic/progress-photo evidence when reliably classifiable from canonical metadata

### Longitudinal attention
Only factual unresolved/recent items.

Examples permitted:
- no future control date recorded
- treatment marked interrupted
- latest control has a next planned step
- no timepoint recorded yet
- latest timepoint has no linked evidence

Do not label these as clinical risk, failure or poor progress.

---

## UI doctrine

F4 is a premium practitioner cockpit, not an ERP dashboard.

Target qualities:

- compact
- calm
- clinically readable
- strong visual hierarchy
- minimal scrolling
- no dense analytics wall
- source-first
- responsive

Reuse PatientDetails design language:
- `bg-card-bg`
- `border-border-main`
- rounded cards
- restrained primary accents
- slate typography
- no semantic red/green treatment-outcome coloring

Canonical viewports:
- 390×844
- 768×1024
- 1280×900

Mandatory sequence:

1. capture exact F3 merged baseline BEFORE;
2. write visual Goal;
3. create mockup/reference;
4. implement;
5. capture AFTER at the same three viewports;
6. compare BEFORE vs AFTER;
7. runtime/overflow/accessibility checks;
8. severe visual score;
9. human visual validation before merge.

---

## Placement decision to validate during F4

Preferred direction:

Patient Details → Vue d’ensemble

F4 should become the main orthodontic summary surface above the generic Patient Journey.

F3 remains reachable from the cockpit or immediately below it depending on final density.

Do not stack multiple large orthodontic cards if one cockpit can summarize them coherently.

---

## Backend strategy

Prefer a read-only aggregation endpoint if current APIs would otherwise require many uncoordinated calls.

A valid F4 aggregation endpoint may combine references to:

- OrthoCase
- OrthoControl
- OrthoTimepoint
- Appointment
- canonical evidence summaries

Rules:

- no new persistence unless a proven gap requires it;
- no caching layer unless proven necessary;
- no cross-tenant leakage;
- no mutation;
- no copied media;
- no duplicate clinical truth.

---

## Safety boundaries

Forbidden:

- automatic diagnosis
- automatic treatment recommendation
- automatic phase classification
- treatment progress score
- treatment success/failure
- "improved/worsened"
- normative interpretation of cephalometric deltas
- F5 superimposition

F4 presents factual state only.

---

## Mandatory first step in the new window

Before coding:

1. read `docs/clinic/handovers/V1_05_F3_CLOSEOUT.md`;
2. verify F3 merge SHA and post-merge proof;
3. inspect current master;
4. audit current PatientDetails placement/density;
5. audit existing endpoints for case/controls/timepoints/appointments/media;
6. produce a bounded F4 data contract;
7. capture BEFORE;
8. write Goal + mockup;
9. only then implement.

If F3 post-merge is not green, F4 product code is not authorized yet; only read-only audit/preparation may proceed.

---

## Expected first deliverable

**F4 — ORTHO COCKPIT DATA CONTRACT + VISUAL GOAL**

It must state:

- exact canonical source for every displayed field;
- unavailable-vs-empty behavior;
- navigation target for each drill-down;
- whether a new aggregation endpoint is justified;
- responsive structure at 390 / 768 / 1280;
- no-duplication proof against Patient Journey and F3.

End of start prompt.
