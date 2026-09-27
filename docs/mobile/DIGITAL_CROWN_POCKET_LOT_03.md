# Digital Crown Pocket — LOT 03 Business Experience

Status: **remediation in progress after two independent CHANGES_REQUIRED reviews on isolated PR #696**  
Dependency lock: **do not merge Pocket and do not run final repo-wide certification until PR #699 is merged**.

## Goal

Turn the existing mobile shell into a role-aware chairside companion without recreating the desktop product.

Success criteria:

- Today is role-aware for DENTISTE / ADMIN versus SECRETAIRE.
- Practitioner sees the next operational patient and can open that patient cockpit directly.
- Assistant sees operational shortcuts for waiting room, frontdesk and alerts.
- Waiting-room state round-trips as EN_ATTENTE instead of collapsing to PLANIFIE.
- Patient cockpit can show the consultation context and latest clinical note only when the paired user has clinical permission.
- No patient identifier is added to the browser URL.
- Financial information remains read-only and only appears when existing permissions allow it.
- Mobile payment writes remain out of Pocket.

## Implemented in this lot

### Today

PocketTodayOverview uses the encrypted mobile snapshot already returned by /api/mobile/snapshot.

Practitioner surface:
- today appointment count;
- waiting-room count;
- completed count;
- next operational patient;
- direct patient cockpit action;
- waiting-room and alerts shortcuts.

Assistant surface:
- today appointment count;
- waiting-room count;
- remaining operational count;
- waiting-room, frontdesk and alerts shortcuts;
- no practitioner patient shortcut.

### Waiting room

The mobile/backend status mapping now preserves the real waiting-room state:

- EN_ATTENTE ↔ AppointmentStatus.EN_SALLE_ATTENTE.

This also makes existing Agenda → Waiting Room transitions server-valid instead of returning 422.

### Direct patient cockpit

The Today patient shortcut passes an in-memory initialSelectedId to the Patients view. It does **not** serialize patient_id into the route or query string.

The cockpit continues to load data through tenant-scoped, encrypted mobile APIs and opens resource contexts through the existing opaque device-bound context mechanism.

### Clinical context

/api/mobile/patient-cockpit/{patient_id} now exposes clinical_context only when has_permission(user, 'clinical') is true.

Read-only fields:
- patient consultation motif;
- latest clinical act label/type/date;
- latest notes_cliniques.

No clinical context is returned to a paired user without the clinical permission.

## Targeted tests added/updated

- backend/tests/test_mobile_pocket_status_mapping.py
  - waiting-room round-trip;
  - existing planned/chairside states preserved.
- backend/tests/test_mobile_patient_cockpit.py
  - clinical context permission gate;
  - most recent clinical note selection.
- PocketTodayOverview.test.tsx
  - practitioner next-patient action;
  - assistant operational surface.
- MobilePatientsView.test.tsx
  - clinical-context rendering;
  - direct patient selection through cockpit API;
  - no patient_id in browser URL.

These are targeted LOT 03 tests. Their presence does not constitute final certification.

## Out of scope in this checkpoint

- LOT 04 voice memo.
- merge of PR #696.
- Vercel deployment.
- final repo-wide certification.
- final AFTER visual certification.

## Required sequence after PR #699

1. Verify PR #699 is merged to master and record its merge SHA.
2. Resynchronize feat/mobile-team-cockpit-20260927 / PR #696 onto current master.
3. Resolve conflicts without reintroducing retired mobile modules or contextual bridge destinations.
4. Run Pocket targeted tests on the resynchronized exact HEAD.
5. Run the final repo-wide exact-head certification only then.
6. Perform AFTER visual evidence on the agreed mobile viewports and compare against the approved Pocket direction.
7. Double check, triple check, independent internal review.
8. Only after evidence is green may PR #696 become eligible for merge; merge still requires explicit project authorization.

## Independent review checkpoint — rejected predecessor

Rejected reviewed HEAD: `2cdb49ece774d1604d4052653f3e9aba486191c9`.

Two independent reviewers both returned `CHANGES_REQUIRED`.
The rejected HEAD is not certifiable and its earlier internal 9.2/8.8 pseudo-double-check scores are invalidated.

Convergent findings:
- Pocket mobile JWT could authenticate against generic desktop/API dependencies.
- secretary `patients` permission could cross into clinical context/write paths.
- mobile document authoring could mutate financial/accounting state.
- agenda snapshot cache was not scoped to selected date.
- next-patient selection was time-naive.
- extended backend appointment statuses could silently become PLANIFIE.
- latest clinical note semantics were too broad.

## Remediation now implemented — evidence pending

Current remediation branch code now:
- rejects `type=mobile` JWTs from generic desktop `get_current_user()`;
- keeps mobile authentication under explicit `/api/mobile/*` dependencies;
- no longer copies the Pocket JWT into desktop `localStorage.token`;
- routes Pocket patient/RDV creation through mobile-scoped adapters that reuse canonical backend creation logic;
- requires `clinical` for opaque patient clinical contexts and patient-context photo/scan writes;
- hides medical-alert details and clinical actions when clinical permission is absent;
- removes financial document authoring from the patient cockpit;
- scopes cached snapshots to cabinet + device + selected date and never labels cached hydration as fresh;
- ranks Today patients by operational state (EN_COURS → EN_ATTENTE → upcoming PLANIFIE), skips missing patient IDs and does not invent a next patient for a past day;
- explicitly maps CONFIRME as planned and refuses to silently project request/rejected/expired/absent statuses as PLANIFIE;
- selects the latest non-empty, non-future clinical note;
- makes header date wording truthful outside today and labels previous/next date controls.

Targeted negative tests were added for:
- generic desktop/financial API rejection of mobile JWTs;
- secretary clinical-context denial;
- clinical-action fail-closed rendering;
- operational next-patient ranking;
- explicit status projection;
- latest relevant clinical note behavior.

**Important:** these changes are not yet declared validated. The new exact-head CI is automatic and must turn green before this remediation can be considered technically proven. Final repo-wide certification remains blocked by PR #699.
