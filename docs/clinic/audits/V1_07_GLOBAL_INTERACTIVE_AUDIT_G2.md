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
