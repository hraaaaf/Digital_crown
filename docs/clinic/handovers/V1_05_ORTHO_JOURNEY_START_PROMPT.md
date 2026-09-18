# START PROMPT — Digital Crown V1 / LOT V1-05 — Orthalis benchmark reconciliation + Ortho Journey

Repository: `hraaaaf/Digital_crown`

Canonical roadmap:
`docs/clinic/DIGITALCROWN_V1_CONSOLIDATED_ROADMAP.md`

Historical competitive canonical:
`docs/audits/COMPETITIVE_ROADMAP_POST_MEDIA.md`

Previous lot:
**V1-04 — Céphalométrie scientific re-baseline**

Verified merge:
- PR #592 — MERGED
- merge SHA: `aea5da874ad53bf53d16eff45845794e63982134`
- V1-04 product result: signed overjet preserved frontend/backend; R18 concordance extended with Surplomb/Recouvrement; no new diagnosis, severity, indication or treatment inference activated.
- V1-04 exact-head pre-merge CI/R18/T2/R15/R15bis/A5 were green.
- V1-04 post-merge certification must be re-checked before declaring V1-05 formally unlocked.

Current master after V1-05 roadmap preparation:
`b2b5f669ef38d47a74f7fd3ba809463ea8a89f39`

Do not assume this SHA is still current. On entry, verify current `master`, PR state and relevant Actions before changing product code.

---

## Goal

Resume the historical competitive chantier at the correct point instead of restarting a generic Orthalis benchmark from zero.

V1-05 = **Orthalis benchmark reconciliation + Lot F — Ortho Journey**.

Build only the missing longitudinal orthodontic workflow around capabilities Digital Crown already owns.

### Success

V1-05 is successful when:

1. the historical competitive roadmap is reconciled against current master;
2. already-built Lot D Patient Companion and Lot E Connect Hub are not rebuilt;
3. Patient Journey, Media Core and Céphalométrie are reused rather than duplicated;
4. F0 proves the minimum non-duplicative Ortho Case architecture;
5. only genuine current-master gaps from F1–F4 are implemented;
6. longitudinal orthodontic chronology and evidence are traceable to canonical data;
7. no unsourced diagnosis, treatment recommendation, severity or “treatment success” inference is introduced;
8. applicable migrations/tests/security/runtime/UI evidence are green;
9. exact-head CI, merge, post-merge certification and canonical closeout are complete.

### Proof

- current-master anti-duplication audit;
- historical competitive reconciliation;
- current primary Orthalis sources only where external claims are used;
- schema/code/tests/observed behavior;
- Media Core integration proof;
- longitudinal ordering/integrity tests;
- tenant/patient isolation tests where applicable;
- mandatory UI BEFORE → Goal → implementation → AFTER at 390×844 / 768×1024 / 1280×900 → comparison/tests → severe visual score;
- severe dual review;
- exact PR/HEAD/run/artifact/digest/merge/post-merge evidence in canonical docs.

---

## Historical competitive state — do not recreate it

Canonical:
`docs/audits/COMPETITIVE_ROADMAP_POST_MEDIA.md`

Verified historical progression:

- **Lot C — Media Core:** CLOSED.
- **Lot D — Patient Companion:** implemented through D0/D1/D2; final continuation handover merged.
- **Lot E — Connect Hub:** MERGED via PR #557.
- Lot E merge commit: `7c175bdd37b2f53afb7b05fd8cf21aaf4bda2164`.

Therefore the next historical competitive lot is:

**Lot F — Ortho Journey**

Do not restart Lots C/D/E unless current master proves a real regression.

---

## Existing product boundary to preserve

Digital Crown already has a general Patient Journey.

Relevant existing design:
`docs/TREATMENT_JOURNEY_DESIGN.md`

That design already established:

- Patient is the aggregation root;
- Patient Journey fuses dated events from canonical sources;
- JourneyMilestone exists for explicit manual milestones;
- Acte can be linked to TreatmentPlanStep;
- Appointment / TreatmentPlanStep / DocumentArchive / PanoramicAnalysis / CephaloAnalysis / Acte / Payment / Installment / LabJob are canonical sources;
- generic Tracking/Patient Journey must not be duplicated.

Therefore **Ortho Journey is NOT another generic patient timeline**.

It is a specialized longitudinal orthodontic layer that references canonical events and evidence.

---

# V1-05 execution structure

## F0 — Current-state audit + Ortho Case model

Goal:
Map current master before implementation and define the minimum additive Ortho Case boundary.

Inspect at minimum:
- Patient Journey;
- JourneyMilestone;
- TreatmentPlanStep;
- CephaloAnalysis;
- PanoramicAnalysis;
- Media Core;
- appointments;
- existing orthodontic stores/routes/screens;
- current treatment-plan links;
- current patient/tenant authorization.

Required output:
- exact current capability map;
- anti-duplication matrix;
- existing-vs-missing contracts;
- data model decision;
- bounded F1–F4 implementation plan.

Hard rule:
Do not create a second Patient Journey, media store or cephalo engine.

If no new Ortho Case persistence is required, do not invent one.

---

## F1 — Orthodontic phases + structured controls

Goal:
Represent an orthodontic treatment as a real longitudinal chronology.

Target conceptual flow:
`T0 Diagnostic → Préparation → Appareillage → Alignement → Finition → Contention → Clôture`

Do not hard-code those labels as universal clinical truth if current product workflows require a configurable phase model.

In scope:
- treatment start;
- current phase;
- phase history;
- structured orthodontic controls;
- control date;
- phase at control;
- practitioner observations;
- appliance/device context when explicitly entered;
- notable event;
- next planned step;
- interruption/abandon/closure explicitly recorded;
- controls surfaced into existing Patient Journey.

Out of scope:
- automatic diagnosis;
- automatic treatment plan;
- automatic phase determination from measurements;
- unsourced severity/classification inference.

Success:
A practitioner can reconstruct the chronological orthodontic course without relying on free-text archaeology.

---

## F2 — T0 / T1 / T2 / Tn + Media Core

Goal:
Bind meaningful orthodontic study timepoints to canonical evidence.

Each timepoint may reference existing canonical objects:
- panoramic imaging;
- cephalometric analysis;
- clinical photo series;
- scan/impression only if a canonical source exists;
- certified measurements;
- source date/provenance.

Rules:
- all media remain in Media Core;
- Ortho Journey stores references/relationships, never duplicate files;
- historical media must not be silently relabeled as T0/T1/T2 without explicit provenance;
- no derived clinical conclusion without source-backed rules.

Success:
A practitioner can identify exactly what evidence belongs to each treatment timepoint.

---

## F3 — Longitudinal Compare

Goal:
Compare treatment timepoints using only valid canonical evidence.

In scope:
- side-by-side T0/T1/T2/Tn;
- before/after visual comparison;
- evolution of measurements already certified by current Céphalo contracts;
- exact date and provenance per value;
- missing/unavailable values fail closed.

Example of permitted display:
`ANB: 6.1° → 4.8° → 3.9°`

Not permitted without a separate source-locked rule:
- “improved”;
- “normalized”;
- “successful treatment”;
- diagnosis;
- severity;
- treatment recommendation.

Success:
The user can observe longitudinal change without the software inventing clinical interpretation.

---

## F4 — Ortho Cockpit

Goal:
Provide one compact practitioner-facing orthodontic control surface.

Target summary:
- treatment start;
- current phase;
- number of controls;
- last control;
- next appointment;
- latest cephalometric timepoint;
- progress photo series count;
- unresolved longitudinal items/events.

UX rules:
- reuse current patient/ortho navigation patterns;
- do not create a competing Patient Journey;
- BEFORE and AFTER must use the same deterministic case and canonical viewports;
- mobile density/readability must be explicitly checked.

Success:
The practitioner can understand the current orthodontic state in seconds and drill down to canonical source records.

---

## F5 — Scientific Superimposition

Status:
**SEPARATE SCIENTIFIC GATE — NOT AUTHORIZED FOR IMPLEMENTATION BY THIS START PROMPT**

Goal:
Assess whether Digital Crown can implement a clinically defensible cephalometric superimposition method.

Before any implementation:
- dedicated scientific literature review;
- exact superimposition method;
- reference structures/landmarks;
- modality requirements;
- stability assumptions;
- reproducibility/error evidence;
- explicit distinction between visual overlay and clinical inference.

Hard rules:
- no homemade geometric superimposition;
- no “treatment success” claims from an overlay;
- no automatic interpretation;
- if evidence is insufficient, F5 remains deferred.

---

## Orthalis use inside V1-05

Orthalis is a comparison source, not the roadmap owner.

Use current official Orthalis sources to answer only:
- what longitudinal orthodontic capabilities they currently claim;
- what integrations/workflows they expose;
- whether a claimed gap is still absent on current Digital Crown master.

Do not:
- inherit historical scores blindly;
- copy features solely because Orthalis has them;
- convert marketing claims into verified technical facts;
- build external integrations without a demonstrated V1 need.

---

## Safety / scientific boundary

Preserve all V1-04 boundaries:

- signed measurements stay signed;
- unavailable measurements fail closed;
- `LEGACY_TO_AUDIT` remains non-authoritative;
- no new cephalometric norm without source-lock;
- no diagnosis/treatment/severity inference without evidence and required review;
- no production/cabinet data mutation unless explicitly authorized;
- no Vercel deployment without explicit authorization.

---

## Mandatory UI doctrine

For every V1-05 visual change:

1. BEFORE capture;
2. written visual Goal;
3. mockup/reference when useful;
4. implementation;
5. AFTER at the same viewports;
6. side-by-side comparison;
7. automated visual/runtime tests;
8. severe visual score;
9. second severe independent/expert-style review;
10. human review before merge authorization.

Canonical viewports:
- 390×844
- 768×1024
- 1280×900

Never fabricate screenshots.

---

## Start protocol in this new window

Execute in this order:

1. Read:
   - `docs/clinic/DIGITALCROWN_V1_CONSOLIDATED_ROADMAP.md`
   - `docs/audits/COMPETITIVE_ROADMAP_POST_MEDIA.md`
   - `docs/TREATMENT_JOURNEY_DESIGN.md`
2. Verify current `master` SHA.
3. Verify V1-04 PR #592 merge and post-merge CI/PostgreSQL/scientific evidence.
4. If V1-04 post-merge is green, formally unlock V1-05 in the canonical roadmap.
5. If post-merge is still pending, continue only read-only F0 audit work; do not start product code.
6. Perform F0 current-master anti-duplication audit.
7. Produce exact existing-vs-missing matrix.
8. Decide whether any new Ortho Case persistence is actually needed.
9. Define bounded F1–F4 implementation sequence from proven gaps only.
10. Implement the first proven gap without asking for confirmation unless a real human gate exists.
11. Validate, correct, continue.
12. Merge only after explicit human merge authorization.
13. Post-merge certify.
14. Update canonical closeout before declaring V1-05 closed.

If a CI run is pending:
- check once;
- do all independent work;
- never idle/poll;
- if no independent work remains and the result is indispensable, record:
  `BLOQUÉ ASYNCHRONE — CI EN COURS`
  with exact run/state/Next.

---

## Expected first deliverable

The first deliverable of V1-05 is **not code**.

It is:

**F0 — CURRENT MASTER ORTHO JOURNEY GAP MATRIX**

For each capability:
- EXISTING / PARTIAL / MISSING;
- canonical source;
- user-visible behavior;
- duplication risk;
- V1 relevance;
- required implementation, if any;
- proof.

Only after this matrix may F1–F4 product changes begin.

---

## Repères at handover creation

- chantier: Digital Crown V1
- next lot: V1-05 — Orthalis benchmark reconciliation + Ortho Journey
- previous lot: V1-04 Céphalométrie
- V1-04 PR: #592 MERGED
- V1-04 merge SHA: `aea5da874ad53bf53d16eff45845794e63982134`
- current known master after roadmap update: `b2b5f669ef38d47a74f7fd3ba809463ea8a89f39`
- competitive canonical: `docs/audits/COMPETITIVE_ROADMAP_POST_MEDIA.md`
- V1 canonical: `docs/clinic/DIGITALCROWN_V1_CONSOLIDATED_ROADMAP.md`
- next exact: verify V1-04 post-merge, then F0 audit
- deployment: NOT AUTHORIZED

End of start prompt.
