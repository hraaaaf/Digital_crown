# V1-05 F4 — Ortho Cockpit Data Contract + Visual Goal

Status: PRE-IMPLEMENTATION CONTRACT

## Goal
Create one compact practitioner cockpit at the top of Patient Details → Vue d’ensemble that exposes the current orthodontic state in seconds, using canonical persisted sources only.

## Placement
Order on Overview:
1. F4 Ortho Cockpit
2. F3 Longitudinal Compare
3. Patient Journey

The cockpit is orthodontic-only. Patient Journey remains the generic chronology and already owns the generic “Prochaine action” surface.

## Aggregation endpoint decision
A dedicated read-only aggregation endpoint is justified.

Proposed route:
`GET /patients/{patient_id}/ortho-cockpit`

Why:
- F4 needs OrthoCase + latest OrthoControl + latest OrthoTimepoint/evidence + next canonical Appointment.
- Coordinating these independently in the client would duplicate selection rules and increase inconsistent empty/error states.
- No new persistence is required.
- The endpoint returns references/summaries only; source tables remain authoritative.

## Field contract

### case
- `case_id` ← OrthoCase.id
- `started_at` ← OrthoCase.started_at
- `lifecycle_status` ← OrthoCase.lifecycle_status
- `current_phase_key` ← OrthoCase.current_phase_key
- `closed_at` ← OrthoCase.closed_at
- `controls_count` ← COUNT(OrthoControl) scoped to same patient/case/employer

Absent case:
- response may be 200 with `case: null` and all ortho sections null/empty, or 404 only if existing API convention requires it.
- UI must not fabricate zeros beyond an explicit count attached to an existing case.

### latest_control
Canonical source: newest OrthoControl by `occurred_at DESC, id DESC`.
- id
- occurred_at
- phase_key
- notable_event
- next_planned_step
- next_control_at
- appointment_id

Absent:
- `latest_control: null`
- UI label: “Aucun contrôle structuré enregistré”
- never “0 jour” / “aucun problème”.

### next_appointment
Canonical source: Appointment.
Selection rule must reuse the same factual policy already used by Patient Journey:
- same patient
- future `datetime_start`
- status in PREVU / EN_SALLE_ATTENTE / EN_FAUTEUIL / CONFIRME
- earliest datetime
- tenant-scoped
- non-deleted

Fields:
- id
- datetime_start
- status
- motif

Critical distinction:
`next_control_at` is a planned orthodontic control date, not a confirmed appointment.
They must appear as two distinct facts if both exist.

### latest_timepoint
Canonical source: newest OrthoTimepoint by ordinal/occurred_at policy explicitly defined in service.
Preferred for F4: highest ordinal, tie-break by occurred_at then id.
Fields:
- id
- ordinal
- occurred_at
- note
- evidence_count

Absent:
- `latest_timepoint: null`
- factual attention item allowed: “Aucun timepoint enregistré”.

### latest evidence
Evidence ownership remains OrthoTimepointEvidence → canonical referenced entities.

Return at most the latest usable reference for each type:
- `latest_cephalo`: CephaloAnalysis reference
- `latest_panoramic`: PanoramicAnalysis reference
- `latest_clinical_asset`: ClinicalAsset reference only when linked canonically through OrthoTimepointEvidence

Fields:
- kind
- ref_id
- recorded_at
- label
- timepoint_ordinal

No copied media payload. No inferred photo classification.

### attention
Server may return factual flags only:
- TREATMENT_INTERRUPTED
- NO_TIMEPOINT
- LATEST_TIMEPOINT_WITHOUT_EVIDENCE
- NO_NEXT_CONTROL_DATE
- NEXT_PLANNED_STEP_PRESENT

No severity, risk, progress, success/failure, improvement/worsening or recommendation.

## Navigation contract
- Case/control summary → stays on Overview; no duplicate editor introduced.
- F3 action → existing longitudinal compare below / anchored target.
- Cephalo → `?tab=radiology&radioTab=cephalo`
- Panoramic → `?tab=radiology&radioTab=panoramic`
- ClinicalAsset → `?tab=radiology&radioTab=media`
- Appointment → `/agenda`

## UI visual goal
The first viewport should communicate:
1. treatment state,
2. last structured control,
3. what is planned next,
4. latest evidence,
without becoming an analytics dashboard.

### 390×844
Single-column cockpit.
Top line: lifecycle + phase.
Then 3 compact rows/blocks:
- traitement
- dernier contrôle
- suite planifiée
Evidence becomes a horizontal/stacked compact strip.
F3 remains below the fold but immediately after F4.

### 768×1024
2-column grid:
- left: current state + latest control
- right: next dates + latest evidence
Attention facts span full width only when present.

### 1280×900
One compact premium surface:
- header/state strip
- 3 columns: current state / latest control / next & evidence
- max one concise attention row
No card-within-card wall.

## Empty / unavailable semantics
- loading: local section loader only
- endpoint error: neutral “Cockpit orthodontique indisponible”
- no ortho case: hide cockpit or show one compact activation-neutral state according to existing product behavior
- missing field: “Non renseigné”, never zero
- no next appointment: “Aucun rendez-vous futur enregistré”
- no next_control_at: “Date de contrôle non renseignée”

## No-duplication proof
Patient Journey:
- remains generic chronology, milestones and generic next action.
F3:
- remains the dedicated two-timepoint comparator.
Media Core:
- remains sole media registry.
F4:
- only current-state synthesis + source links.

## Safety
Forbidden:
- diagnosis
- treatment recommendation
- automatic phase classification
- treatment progress score
- success/failure
- improved/worsened
- normative interpretation of deltas
- F5 superimposition

## Success proof
F4 is valid only after:
- exact BEFORE at 390/768/1280
- mockup/reference recorded
- source-mapping tests
- tenant-scope tests
- absent-vs-zero tests
- runtime/overflow/accessibility checks
- exact-head AFTER at same viewports
- severe visual scoring
- human visual gate before merge
