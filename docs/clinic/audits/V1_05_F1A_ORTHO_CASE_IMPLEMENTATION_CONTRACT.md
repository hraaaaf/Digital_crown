# V1-05 / F1A — ORTHO CASE IMPLEMENTATION CONTRACT

Date: 2026-09-18  
Status: **DESIGN READY / PRODUCT IMPLEMENTATION BLOCKED UNTIL V1-04 POST-MERGE CERTIFICATION IS PROVEN**

## Goal

Define the smallest safe persistence/runtime slice needed to represent one longitudinal orthodontic treatment without duplicating Patient Journey, Treatment Plan, Media Core, Céphalo, Panoramique or Agenda.

## Success

F1A is implementation-ready when the exact model boundary, tenant/patient authorization, lifecycle semantics, migration strategy and test matrix are fixed before any product code is written.

## Current-master constraints

Verified on current master:
- `PatientJourney` already aggregates 9 canonical sources.
- `JourneyMilestone` already carries `employer_id`, patient scope, audit, soft-delete and duplicate protection.
- `TreatmentMasterPlan / TreatmentPlanStep` are generic; step date remains a free-form `date_str`.
- `DossierClinique.is_ortho_active` exists but is only a boolean context flag.
- `Acte` currently has no `treatment_plan_step_id`.
- Media Core already owns clinical media storage/provenance and `T0..T999` labels.
- Céphalo/Panoramique remain canonical imaging/scientific sources.
- Appointment remains the scheduling authority.

## Scope F1A

F1A includes only:
1. one durable Ortho Case per active longitudinal treatment;
2. explicit lifecycle state;
3. current phase key;
4. append-only phase/lifecycle event history;
5. tenant + patient isolation;
6. API read/create/transition primitives;
7. targeted PostgreSQL/SQLite-compatible additive migration;
8. tests and Journey integration contract tests where applicable.

F1A does **not** include:
- structured control details (F1B);
- T0/T1/Tn evidence grouping (F2);
- longitudinal comparison (F3);
- cockpit UI (F4);
- scientific superimposition (F5);
- automatic diagnosis, phase assignment, severity, treatment recommendation;
- backfill or inference from old free text.

---

## Persistence decision

### `OrthoCase`

Required fields:

- `id` primary key
- `employer_id` FK users.id, non-null, indexed
- `patient_id` FK patients.id, non-null, indexed
- `started_at` datetime, non-null
- `lifecycle_status` string/enum-like constrained value
- `current_phase_key` nullable string
- `closed_at` nullable datetime
- `created_by` FK users.id SET NULL
- `created_at`
- `updated_at`

Recommended lifecycle values:
- `ACTIVE`
- `INTERRUPTED`
- `ABANDONED`
- `CLOSED`

Hard rule:
- lifecycle values describe practitioner-recorded workflow state only;
- they do not imply treatment quality, success or failure.

### Uniqueness

Default V1 contract:
- at most one non-terminal Ortho Case per tenant + patient;
- historical closed/abandoned cases may coexist later if future product need is proven.

Implementation should enforce the active-case invariant transactionally and, where portable, with a database constraint/index appropriate to PostgreSQL without inventing unsafe SQLite-only behavior.

### `OrthoPhaseEvent`

Required fields:

- `id`
- `ortho_case_id` FK `ortho_cases.id`, non-null
- `employer_id` non-null
- `patient_id` non-null
- `event_type`
- `phase_key` nullable
- `effective_at` datetime, non-null
- `note` nullable
- `created_by` nullable FK user
- `created_at`

Allowed event types:
- `START`
- `ENTER_PHASE`
- `INTERRUPT`
- `RESUME`
- `ABANDON`
- `CLOSE`

No destructive update of historical events in F1A.

---

## Phase contract

Phase labels are practitioner workflow metadata, not scientific truth.

Default selectable set may be:
- `DIAGNOSTIC`
- `PREPARATION`
- `APPAREILLAGE`
- `ALIGNEMENT`
- `FINITION`
- `CONTENTION`
- `CLOTURE`

But:
- no automatic transition;
- no inference from cephalometric values, appointments, acts, media or dates;
- a future configurable phase catalogue remains possible;
- persistence must not encode numeric “progress %” from phase position.

---

## Authorization / isolation

Every Ortho Case operation must:

1. resolve tenant from `current_user.get_employer_id()`;
2. call/reuse `assert_patient_access(patient_id, current_user, db)`;
3. query `OrthoCase` by **id + patient_id + employer_id**;
4. reject cross-tenant object access even when an id exists;
5. validate `created_by` belongs to the tenant when used;
6. never trust `employer_id` supplied by a client payload.

Creation/transition permission:
- require existing clinical/patient permission path;
- mutation should be practitioner/admin only unless current product permission model proves another safe role;
- no patient-facing mutation route in F1A.

---

## Transaction / concurrency rules

Creation:
- lock the patient row using the same PostgreSQL `SELECT ... FOR UPDATE` pattern already used by JourneyMilestone;
- verify no active case exists;
- create `OrthoCase`;
- create matching `START` phase event in the same transaction.

Transition:
- lock the Ortho Case row;
- validate legal lifecycle transition;
- append one `OrthoPhaseEvent`;
- update `current_phase_key` / lifecycle state atomically.

Never:
- create a phase event without the corresponding case state mutation;
- silently repair contradictory history;
- infer missing historical events.

---

## Lifecycle state machine

Allowed baseline transitions:

- CREATE → `ACTIVE`
- `ACTIVE` → `ACTIVE` with `ENTER_PHASE`
- `ACTIVE` → `INTERRUPTED`
- `INTERRUPTED` → `ACTIVE` with `RESUME`
- `ACTIVE` or `INTERRUPTED` → `ABANDONED`
- `ACTIVE` or `INTERRUPTED` → `CLOSED`

Terminal in F1A:
- `ABANDONED`
- `CLOSED`

No transition out of a terminal state in F1A.

---

## Journey integration contract

Patient Journey remains the canonical generic chronology.

F1A must add Ortho lifecycle events to the existing Journey aggregation **without creating another timeline**.

New Journey event source:
- `ortho_phase_event`

Suggested mapping:
- START → title “Traitement orthodontique démarré”
- ENTER_PHASE → factual phase label only
- INTERRUPT → “Traitement orthodontique interrompu”
- RESUME → “Traitement orthodontique repris”
- ABANDON → “Traitement orthodontique arrêté”
- CLOSE → “Traitement orthodontique clôturé”

No words such as:
- improved
- normalized
- successful
- failed
unless literally entered by the practitioner as free text and clearly shown as practitioner-authored content.

---

## API boundary

Minimum F1A endpoints:

### GET
`GET /patients/{patient_id}/ortho-case`
- returns active/current case and ordered phase history;
- 404 or explicit `null` contract when absent;
- no inferred case from `is_ortho_active`.

### POST create
`POST /patients/{patient_id}/ortho-case`
Payload:
- started_at
- optional initial_phase_key

Server:
- derives employer/user;
- creates case + START event atomically.

### POST transition
`POST /patients/{patient_id}/ortho-case/{case_id}/transitions`
Payload:
- event_type
- effective_at
- phase_key where required
- note optional

Server:
- validates state machine;
- appends history + updates case atomically.

No DELETE endpoint in F1A.

---

## Migration strategy

Use one additive Alembic revision chained from the actual current head verified at implementation time.

Migration:
- CREATE `ortho_cases`
- CREATE `ortho_phase_events`
- indexes for:
  - tenant/patient lookup;
  - case/history chronological lookup;
  - active-case lookup.

No:
- DROP;
- destructive ALTER;
- patient backfill;
- derivation from `DossierClinique.is_ortho_active`;
- production/cabinet DB mutation during development.

Because current Digital Crown also has historical self-healing schema behavior, implementation must explicitly decide whether these new tables are fully covered by `Base.metadata.create_all()` for legacy installs or require a bounded startup schema assertion. Do not add ad-hoc duplicate ALTER logic if Alembic + create_all already covers fresh additive tables.

---

## Targeted test matrix

### Model / persistence
- create one active case;
- duplicate active case rejected;
- closed case history retained;
- START event created atomically;
- chronological event order deterministic;
- terminal case rejects new transition.

### State machine
- ACTIVE → ENTER_PHASE;
- ACTIVE → INTERRUPTED;
- INTERRUPTED → RESUME;
- ACTIVE/INTERRUPTED → CLOSED;
- ACTIVE/INTERRUPTED → ABANDONED;
- invalid transitions rejected;
- terminal reopen rejected.

### Tenant / patient isolation
- own tenant + own patient succeeds;
- foreign tenant patient rejected;
- forged case id from another tenant rejected;
- forged employer_id payload impossible/ignored;
- deleted/archived patient behavior follows existing patient access contract.

### Concurrency
- concurrent create cannot yield two active cases;
- concurrent conflicting transition cannot produce mismatched case/event state on PostgreSQL.

### Journey
- new factual events appear once;
- no existing Journey source duplicated;
- date ordering stable;
- 12-month window/full-history cap behavior preserved;
- no clinical inference wording generated.

### Migration
- fresh PostgreSQL schema;
- upgrade from current certified head;
- second upgrade no-op;
- one coherent Alembic head;
- SQLite test schema remains usable where supported.

---

## Runtime proof before UI

Before F1B/UI work:
- boot backend against isolated test/rehearsal DB;
- create patient fixture;
- create Ortho Case;
- transition through at least two factual events;
- fetch case;
- fetch Patient Journey;
- prove same canonical event ids/state are returned;
- prove foreign tenant cannot read/mutate.

No cabinet/production data.

---

## UI doctrine

F1A can remain backend-only if no UI is added.

If a product surface is added in F1A despite this contract:
- capture BEFORE;
- write exact visual Goal;
- implement;
- capture AFTER at 390×844 / 768×1024 / 1280×900;
- compare;
- run visual/runtime tests;
- severe score + independent severe review;
- human review before merge.

---

## External competitor evidence verified 2026-09-18

Official Orthalis/Orqual sources support only the bounded competitive observations used by F0:
- Orthalis training explicitly teaches clinical comments, next appointment and treatment-plan/diagnostic/objective forms.
- Imaging training explicitly includes photo import, viewers and comparator.
- Kitview official material describes Wi-Fi/smartphone acquisition/import into the patient library.
- Ceph official material advertises superposition of cephalometric tracings, radiographs and photos.

These are vendor capability claims, not independent scientific validation.

Sources:
- https://www.orthalis.com/nos-formations/client/
- https://www.orthalis.com/kitview/
- https://www.orthalis.com/ceph/
- https://www.orthalis.com/wp-content/uploads/2023/11/KITVIEW-SMARTPHONE-1.pdf

## Gate

F1A product implementation starts only when V1-04 post-merge certification is proven.

Next exact after gate:
**create clean F1A implementation branch from then-current certified master → models + migration + schemas/service/routes + isolation/state-machine tests → runtime proof → Journey integration → exact-head CI.**
