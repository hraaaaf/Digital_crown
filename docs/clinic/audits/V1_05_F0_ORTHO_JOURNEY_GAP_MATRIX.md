# V1-05 / F0 — CURRENT MASTER ORTHO JOURNEY GAP MATRIX

Date: 2026-09-18  
Repository: `hraaaaf/Digital_crown`  
Audit base: `master@d6ba162f14545be521279c2dd38226161633287a`  
Status: **READ-ONLY PRODUCT AUDIT COMPLETE / PRODUCT CODE STILL BLOCKED BY V1-04 POST-MERGE CERTIFICATION**

## Goal

Prove the minimum non-duplicative Ortho Journey boundary on current master before any F1–F4 implementation.

## Success

F0 succeeds only if:
- current Patient Journey, Media Core, Céphalo, Panoramique and treatment-plan capabilities are mapped;
- duplicate stores/timelines/media engines are excluded;
- genuine missing longitudinal orthodontic contracts are isolated;
- a bounded F1–F4 sequence is derived from current-master evidence.

## Evidence boundary

This audit uses:
- current master code at `d6ba162f14545be521279c2dd38226161633287a`;
- canonical `docs/TREATMENT_JOURNEY_DESIGN.md`;
- canonical `docs/audits/COMPETITIVE_ROADMAP_POST_MEDIA.md`;
- current V1 handover `docs/clinic/handovers/V1_05_ORTHO_JOURNEY_START_PROMPT.md`;
- current official Orthalis/Orqual product pages only for externally claimed competitor capabilities.

No clinical conclusion is inferred from competitor marketing.

## V1-04 gate

Verified:
- PR #592 is merged.
- Merge commit: `aea5da874ad53bf53d16eff45845794e63982134`.
- Current master contains the merge and later documentation commits.

Not yet independently proven through the available Actions connector:
- exact post-merge master CI;
- exact post-merge PostgreSQL certification;
- exact post-merge scientific gate.

Therefore:
- F0 documentation/audit may proceed;
- **no V1-05 product code or migration is authorized yet**;
- canonical V1-05 status remains blocked until post-merge evidence is recovered.

---

## Current-master gap matrix

| Capability | State | Canonical source / proof | User-visible behavior | Duplication risk | V1 relevance | Required implementation |
|---|---|---|---|---|---|---|
| General Patient Journey | **EXISTING** | `backend/services/patient_journey_service.py`; `GET /patients/{id}/journey`; `PatientJourney.tsx` | Existing patient chronology already aggregates canonical clinical/admin events | **CRITICAL** if rebuilt | High | Reuse only. Ortho must surface into this Journey, not replace it |
| JourneyMilestone | **EXISTING** | `JourneyMilestone` model + create/delete routes; types DIAGNOSTIC / DEVIS_VALIDE / CONTROLE / CLOTURE; audit + auth + soft-delete | Practitioner can explicitly record factual milestones | High | High | Reuse for generic milestones; do not create `OrthoMilestone` clone |
| TreatmentMasterPlan / TreatmentPlanStep | **PARTIAL** | `backend/models.py`; current step = title / assistant / status / date_str / order_index | Generic treatment-plan steps exist | Medium | High | Extend only if necessary for ortho linkage; do not turn generic steps into a second Ortho timeline |
| Acte → TreatmentPlanStep relational link | **MISSING** | Current `Acte` has `document_archive_id` but no `treatment_plan_step_id`; historical design proposed it but current master does not contain it | New performed acts cannot be reliably traced to the originating plan step | Low duplication / high traceability gap | Medium-High | Candidate additive nullable FK only if F1 chronology needs it; no historical backfill |
| Ortho activation flag | **EXISTING BUT MINIMAL** | `DossierClinique.is_ortho_active` | Flags orthodontic context only | Low | Medium | Reuse as eligibility/context signal; not sufficient as longitudinal model |
| Dedicated Ortho Case persistence | **MISSING** | No current Ortho Case model found; existing ortho frontend store is cephalo-session state, not longitudinal treatment persistence | No canonical treatment start/current phase/closure object | Medium | **High** | Add one bounded Ortho Case aggregate **only because phase lifecycle needs durable state** |
| Ortho phase history | **MISSING** | No current-master phase/history commit or model found | Practitioner cannot reconstruct phase transitions | Low | **High** | Add durable configurable phase/current-phase + phase history |
| Structured orthodontic controls | **MISSING** | No dedicated longitudinal control entity found; generic Journey CONTROLE milestone lacks phase/device/observation/next-step structure | Controls require free-text archaeology | Low | **High** | Add structured Ortho Control linked to Ortho Case and patient, with practitioner-entered factual fields only |
| Interruption / abandon / closure state | **PARTIAL** | Generic CLOTURE milestone exists; no Ortho treatment lifecycle state | Closure can be noted, but orthodontic treatment state is not reconstructable | Medium | High | Store explicit lifecycle state/history in Ortho Case; optionally mirror factual events into Patient Journey |
| Appointment integration | **EXISTING** | `Appointment`, tenant scoped, patient scoped, resource-aware | Next appointment and completed sessions already exist | High | High | Reference existing appointments; never duplicate scheduling |
| Céphalométrie canonical evidence | **EXISTING** | `CephaloAnalysis`, V1-04 signed-measurement boundary, fail-closed scientific core | Current analyses and certified raw measurements exist | **CRITICAL** | High | Reference analyses only; no second cephalo engine / no reinterpretation |
| Panoramic canonical evidence | **EXISTING** | `PanoramicAnalysis` + current imaging routes | Panoramic studies already exist | Critical | High | Reference only |
| Media Core / ClinicalAsset | **EXISTING** | `backend/models_media_core.py`; tenant + patient scoped; provenance; encrypted storage binding | Canonical clinical media library | **CRITICAL** | **High** | Reuse only |
| Media timepoint T0/T1/T2/Tn | **EXISTING FOUNDATION** | `ClinicalAsset.timepoint`; invariant accepts `T0..T999`; `captured_at`; `source_ref`; provenance | Media can already carry longitudinal labels | Critical | **High** | Do not create another timepoint media table. Add explicit Ortho-study/timepoint relationships only where one logical study must bind heterogeneous canonical evidence |
| Media timeline/viewer | **EXISTING** | Competitive Media C4 closed on master; authenticated patient media timeline | Existing patient-facing/practitioner media chronology | High | Medium | Reuse |
| Media compare/search/filters | **EXISTING** | Competitive Media C5 closed on master | Existing compare/search/filter foundation | High | **High for F3** | Reuse visual comparison foundation |
| Smartphone clinical capture | **EXISTING** | Media C6 routes capture into `ClinicalAsset PHOTO / DEVICE_CAPTURE` | Clinical photos can enter canonical Media Core | High | Medium | Reuse |
| Media volumetric / tenant / responsive certification | **EXISTING** | Media C7 closed | Media foundation already certified for scale/isolation/responsive behavior | High | Medium | Reuse |
| Ortho study timepoint as a coherent bundle | **MISSING / PARTIAL** | Media assets can have T-labels, but no proven current canonical object binds cephalo + pano + photo series + provenance into one orthodontic study point | User cannot reliably say “this complete evidence set is T1” across heterogeneous sources | Medium | **High** | Candidate small `OrthoTimepoint` relation/aggregate; references canonical objects, duplicates no files/results |
| Longitudinal cephalo measurement compare | **MISSING AS ORTHO WORKFLOW** | Individual analyses exist; Media compare exists; no proven T0→Tn certified-measure series surface | No dedicated factual evolution view | Low | **High** | F3 reads certified canonical measurements by selected timepoints, exact date/provenance, missing values fail closed |
| Automatic clinical interpretation of change | **INTENTIONALLY ABSENT** | Scientific-core fail-closed doctrine | Product does not autonomously infer success/normalization/treatment recommendation | N/A | Safety-critical | Keep absent |
| Ortho Cockpit | **MISSING** | No current compact longitudinal ortho summary found | Practitioner lacks one treatment-state surface | Low | High | F4 composition over Ortho Case + canonical appointments/media/cephalo; no duplicated source of truth |
| Scientific superimposition | **NOT AUTHORIZED** | V1-05 handover F5 separate gate | No clinically defended superimposition claimed in V1-05 | High scientific risk | Deferred | Separate scientific review before any implementation |

---

## Anti-duplication decisions

### 1. Patient Journey remains the only generic chronological patient timeline
Ortho Journey must publish/reference factual orthodontic events into the existing Patient Journey. A second generic timeline is prohibited.

### 2. Media Core remains the only clinical media registry
No OrthoPhoto, OrthoMedia, OrthoFile or duplicate blob store.

### 3. Céphalo and Panoramique remain canonical scientific/imaging records
Ortho longitudinal objects store references only.

### 4. T0/T1/T2 labels already exist at Media Core level
F2 is not “build timepoints from zero”. The actual missing contract is grouping heterogeneous evidence into a clinically explicit, practitioner-selected orthodontic study point.

### 5. Generic JourneyMilestone is not sufficient for orthodontic controls
It records factual milestones but does not provide phase, appliance/device context, structured observation, notable event, next step or treatment lifecycle history. Extending it into a large ortho-specific polymorphic object would pollute the generic Patient Journey contract. A bounded Ortho Control entity is cleaner.

---

## Data-model decision

### Decision: a minimal new Ortho persistence layer **is required**

A zero-persistence solution is rejected because current master has no durable source for:
- orthodontic treatment start;
- current phase;
- phase transition history;
- structured orthodontic controls;
- explicit interruption/abandon/orthodontic closure;
- coherent cross-source study timepoints.

### Minimum additive model proposed for implementation after V1-04 unlock

1. `OrthoCase`
   - patient_id
   - employer_id
   - started_at
   - lifecycle_status
   - current_phase_key
   - closed_at nullable
   - created_by / timestamps

2. `OrthoPhaseEvent`
   - ortho_case_id
   - phase_key
   - effective_at
   - event_type (ENTER / EXIT / INTERRUPT / RESUME / CLOSE)
   - practitioner_note nullable
   - created_by

3. `OrthoControl`
   - ortho_case_id
   - control_date
   - phase_key snapshot
   - observations
   - device_context nullable
   - notable_event nullable
   - next_planned_step nullable
   - appointment_id nullable reference
   - created_by

4. `OrthoTimepoint`
   - ortho_case_id
   - label (`T0..T999`, validated)
   - observed_at
   - practitioner_note nullable
   - explicit provenance metadata
   - references to canonical evidence through relation rows or typed references

5. `OrthoTimepointEvidence`
   - ortho_timepoint_id
   - evidence_type
   - canonical_id
   - no copied clinical values/files

No separate Ortho Patient Journey table.

### Phase labels

Default UI may offer:
`T0 Diagnostic → Préparation → Appareillage → Alignement → Finition → Contention → Clôture`

But persistence should use configurable/stable keys rather than asserting that sequence as universal clinical truth. The practitioner remains authoritative for phase assignment.

---

## Competitor reconciliation — bounded current claims

Current Orthalis/Orqual official material confirms:
- Kitview centralizes clinical digital data and provides image presentation/comparison;
- Kitview supports acquisition/import including smartphone;
- Ceph advertises cephalometric tracing and trace/radio/photo superposition;
- Orthalis training material explicitly includes clinical comments, next appointment and treatment-plan/diagnostic/objective form workflows.

These are competitor capability claims only. They do not define Digital Crown clinical truth or authorize copying diagnostic automation.

Official sources checked:
- https://www.orthalis.com/kitview/
- https://www.orthalis.com/ceph/
- https://www.orthalis.com/orthalis/
- https://www.orthalis.com/nos-formations/client/

---

## Bounded F1–F4 sequence from proven gaps

### F1A — Ortho Case + lifecycle persistence
Implement only durable case start/current state/phase history with tenant/patient isolation.

### F1B — Structured controls
Add factual practitioner-entered controls and surface them into existing Patient Journey.

### F1C — Optional Acte→TreatmentPlanStep link
Implement only if the flow needs plan-step traceability after the Ortho Case/control contracts are proven. Additive nullable FK, no backfill.

### F2 — Ortho study timepoints
Create only the thin cross-source binding layer. Reuse `ClinicalAsset.timepoint`, Media Core, Céphalo and Panoramique.

### F3 — Longitudinal Compare
Compose existing Media C5 compare foundation with certified cephalo values. Exact dates/provenance; missing values fail closed. No “improved/normalized/successful”.

### F4 — Ortho Cockpit
Read-only composition:
- treatment start;
- current phase;
- control count;
- last control;
- next canonical appointment;
- latest cephalo timepoint;
- progress-photo series count;
- unresolved factual longitudinal items/events.

---

## First implementation gate

Do **not** start F1 product code until V1-04 post-merge certification is independently proven.

When unlocked, first code slice should be:
**F1A — minimal OrthoCase + OrthoPhaseEvent persistence + isolation tests**, with no UI change in the same first slice unless required for observed runtime proof.

Any UI change later follows mandatory:
BEFORE → Goal → reference/mockup → implementation → AFTER same 390×844 / 768×1024 / 1280×900 → comparison/tests → severe dual visual review → human merge gate.

## F0 conclusion

F0 proves that V1-05 is **not** a generic Journey rebuild and **not** a Media/Céphalo rebuild.

The genuine V1 gaps are narrow:
1. durable orthodontic case/lifecycle;
2. structured controls;
3. coherent cross-source study timepoints;
4. factual longitudinal comparison;
5. compact Ortho Cockpit.

F5 superimposition stays outside this authorization.
