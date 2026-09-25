# Digital Crown V1-07 — Global Interactive Audit — G2

Status: IN PROGRESS

## Goal
Certify the interactive behavior of Dashboard, Patients, and Patient dossier surfaces exposed by G0, without depending on G1 certification.

## Success
- Dashboard critical controls have behavioral proof.
- Patient list critical controls have behavioral proof.
- Patient create/edit flows have success, refusal/error, and non-mutation proof where applicable.
- Patient dossier tab/navigation/permission boundaries have behavioral proof.
- Exact-head frontend tests and build are green before G2 certification.

## Current verified inventory

### Dashboard
Verified source: `frontend/src/pages/Dashboard.tsx`.

Interactive surfaces include:
- patient search and patient navigation;
- quick actions;
- waiting-room refresh/status changes;
- proactive alerts: navigate, snooze, mark-read;
- management panel expand/collapse;
- mobile security dialog open/close and keyboard behavior;
- patient discharge ghost-action checklist;
- permission-gated patient, agenda, accounting and admin surfaces.

### Patient list
Verified source: `frontend/src/features/patients/PatientList.tsx`.

Critical controls include:
- Import CSV modal;
- Create patient;
- search;
- sort;
- table/grid mode persistence;
- row/card keyboard and pointer navigation;
- edit;
- delete dialog;
- exact-name delete confirmation;
- cancel/close non-mutation;
- empty-state create;
- no-result create with query prefill.

Delete business rule:
- delete action only executes when entered confirmation text exactly matches the patient display name after trim;
- API mutation: `DELETE /patients/:id`;
- local/cache removal happens only after API success;
- failure does not remove the patient locally.

### Patient create/edit
Verified sources:
- `frontend/src/features/patients/AddPatientForm.tsx`
- `frontend/src/features/patients/EditPatientForm.tsx`

Critical boundaries include:
- identity validation;
- dossier-number availability;
- duplicate pre-check before create;
- duplicate backend 409 handling;
- explicit forced create path;
- create success navigation;
- edit fetch truth / fetch failure retry;
- edit success;
- edit conflict/refusal handling.

### Patient dossier
Verified source: `frontend/src/features/patients/PatientDetailsInner.tsx`.

Critical boundaries include:
- patient fetch/loading/error;
- dossier tabs;
- radiology sub-tabs;
- permission-gated clinical / panoramic / cephalo / finance access;
- invalid/forbidden tab fallback;
- payment modal;
- contextual patient navigation and document handoff.

## Reuse — existing evidence
Existing tests identified in the patient domain include:
- `PatientDetailsFlowHandoff.test.ts`
- `PatientDossierResponsiveUX.ux1.test.ts`
- `PatientIdentityContract.p6.test.ts`
- `PatientIndicatorsExplainable.test.ts`
- `PatientMediaTimeline.c5.test.tsx`
- `PatientMediaTimeline.c7.test.tsx`
- `PatientP3ClinicalAssistantBoundary.test.ts`
- `PatientP4ImagingTruth.test.ts`
- `PatientP6PaymentContract.test.ts`
- `PatientP6Truth.test.ts`
- `patientDocumentBoundary.test.ts`

These are reusable evidence, not automatic proof for every G2 interactive control.

## G2 certification gate
Do not certify G2 until:
1. missing critical behavioral matrices are added;
2. exact-head frontend test suite passes;
3. exact-head frontend build passes;
4. G2 evidence is recorded here and in Notion.

G1 may remain pending independently while G2 work proceeds.


## Behavioral proof added

1. `frontend/src/features/patients/PatientList.g2Interactive.test.tsx`
   - patient navigation/edit;
   - exact-name delete confirmation;
   - backend-delete ACK before local/cache removal;
   - delete failure preserves patient;
   - CSV import open;
   - search-driven create;
   - table/grid persistence.

2. `frontend/src/features/patients/AddPatientForm.g2Interactive.test.tsx`
   - identity validation + duplicate pre-check;
   - duplicate-check outage fails closed;
   - duplicate detected = no automatic creation;
   - explicit force-create;
   - open existing dossier;
   - cancel non-mutating.

3. `frontend/src/features/patients/EditPatientForm.g2Interactive.test.tsx`
   - backend truth hydration;
   - read failure + retry;
   - save then navigate only after ACK;
   - 409 conflict stays on form;
   - generic save failure has no false success.

4. `frontend/src/features/patients/PatientDetails.g2Interactive.test.tsx`
   - owner/admin tab access;
   - forbidden clinical / finance / companion deep-links normalize to tracking;
   - forbidden cephalo/panoramic deep-link fails closed to RVG;
   - ortho activation unlocks cephalo only after backend ACK;
   - activation failure remains locked;
   - Modifier / RDV / Document quick actions.

5. `frontend/src/features/dashboard/DashboardInteractions.g2Interactive.test.tsx`
   - patient search;
   - quick-add menu;
   - permission-hidden controls;
   - waiting-room refresh and state transitions;
   - unavailable vs truthful empty waiting room;
   - proactive-alert navigation/snooze/read;
   - marketplace visibility/navigation.

6. `frontend/src/features/dashboard/DashboardPage.g2Interactive.test.tsx`
   - management panel toggle;
   - mobile security dialog open/close;
   - post-appointment Ghost Action lifecycle.

Status remains IN PROGRESS until exact-head tests + build are green.


## Additional G2 behavioral proof

7. `frontend/src/features/patients/CsvImportModal.g2Interactive.test.tsx`
   - file required;
   - multipart upload;
   - created/duplicate/error result truth;
   - backend refusal has no false success;
   - close resets transient state.

8. `frontend/src/features/patients/PatientListSearchSort.g2Interactive.test.tsx`
   - patient-name and dossier-number filtering;
   - A→Z / Z→A sort;
   - keyboard row activation.

9. `frontend/src/features/patients/AddPatientVariants.g2Interactive.test.tsx`
   - extra phone numbers;
   - private insurance;
   - complementary insurance;
   - orthodontic activation propagated to create payload.

10. `frontend/src/features/patients/EditPatientVariants.g2Interactive.test.tsx`
    - extra phone numbers and insurance variants propagated to update payload.

11. `frontend/src/features/patients/PatientDossierNumber.g2Interactive.test.tsx`
    - dossier number taken;
    - dossier number available;
    - availability verification unavailable.

12. `frontend/src/features/patients/PatientDetails.g2Interactive.test.tsx` extended
    - patient-load error + retry;
    - Documents create/history boundary.

G2 functional implementation work is now substantially covered. Certification still requires exact-head tests + build to pass.


## Browser escalation
G2 is no longer certifiable from component matrices + CI alone. Dashboard, Patients and Patient dossier controls must be enumerated and exercised in real Chromium. The shared G1→G7 browser factory supplies the runtime denominator; a G2 Playwright action pass must reconcile Dashboard/Patients controls to observable navigation, mutation ACK/refusal and non-mutation outcomes before certification.


## Deep browser reconciliation completed — 2026-09-23

The G2 Chromium gate now proves the visible contracts through their real consequences, not click/state alone.

### Dashboard
- waiting-room chain: PRÉVU -> EN_S_ATTENTE -> EN_FAUTEUIL -> TERMINÉ with fixture ACK/refetch after every mutation;
- Ghost Action checklist appears only after completion and disappears only after all actions are completed;
- proactive alerts: snooze/read remove only the targeted alert after ACK; patient alert navigation reaches the exact dossier;
- Mobile Security: dialog focus ownership, pairing payload/ACK, revoke refusal keeps pairing, revoke ACK clears pairing, Escape closes and restores focus;
- management/quick actions remain permission-gated.

### Patient list
- deterministic A→Z / Z→A sort consumer proof and keyboard row activation;
- CSV file gate, multipart ACK result truth, backend refusal with modal retained;
- delete wrong-confirmation blocked, cancel non-mutating, backend refusal preserves the row, ACK removes locally, hard reload proves the isolated real fixture was never deleted;
- no-result add-patient handoff preserves search identity in the create route.

### Add / Edit patient
- duplicate-check outage fails closed;
- detected duplicate never creates automatically;
- open-existing path is non-mutating;
- force-create only mutates after explicit user choice;
- create cancel is non-mutating;
- edit read failure is fail-closed + Retry;
- edit 409 conflict/refusal never navigates as success;
- create/edit success ACK paths verify payload and navigation while Playwright interception prevents mutation of the real T2 patient fixture.

### Patient dossier
- tab controls verify both URL state and rendered `data-flow-patient-surface`;
- Documents create/history round-trip;
- Modifier and RDV quick actions reach their actual destinations, with RDV preserving `prefillPatientId`;
- patient-load failure + Retry;
- ortho activation refusal stays locked; ACK unlocks the cephalometry consumer.

### Permission boundary
A real product defect was found and remediated:
- `/patients*` routes had backend permission enforcement but no equivalent React route guard;
- `/settings` and the Header Settings entry had the same frontend exposure gap.

The isolated restricted employee fixture (`agenda=true`, `patients/settings/accounting/admin=false`) now proves:
- patient/settings navigation and privileged Dashboard controls are hidden;
- Nouveau RDV remains available while Nouveau Patient is hidden;
- direct `/patients` and `/settings` deep-links fail closed to Dashboard.

`CsvImportModal` also gained dialog semantics and a named close control during this reconciliation.

Functional deep-check status: COMPLETE IN HARNESS. G2 remains NOT CERTIFIED until the exact-head browser/CI gates are green.
