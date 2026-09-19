# Digital Crown V1-07 — Global Interactive Audit — G4

Status: IN PROGRESS

## Goal
Exhaustively certify deep clinical/business interactions inside the patient dossier: documents, prescriptions, certificates, accounting/honorarium flows, payments, treatment planning, odontogram, panoramic/RVG/cephalometry and related archives.

## Success
For every applicable deep module:
- every visible interactive control is inventoried;
- success path is behaviorally proved;
- refusal/error path is proved for mutations;
- no false success or unintended mutation is allowed;
- persistence/result truth is verified where applicable;
- permission and disabled states are covered;
- exact-head frontend tests + build are green before G4 certification.

## Doctrine
Opening a tab or rendering a button is not proof.
A control counts as covered only when its expected business result is asserted.

## G4 workstreams

### G4-A — Document Studio shell and navigation
- document tabs;
- create/history transitions;
- author selection;
- preview/print/download where exposed;
- dirty-state/reset/close boundaries.

### G4-B — Prescription / Ordonnance
- medication rows;
- add/remove/edit;
- dosage/form/frequency/duration/quantity;
- guide/safety panels;
- validation;
- preview/generation;
- save/print/PDF;
- pharmacology refusal/safety states.

### G4-C — Certificates / Libre documents
- all form controls;
- validation;
- preview;
- generation;
- print/export;
- dirty-state handling.

### G4-D — Honorarium / accounting / payment
- treatment/act lines;
- price editing;
- phases/bundles;
- totals;
- payment recording;
- installments;
- conversions;
- quick actions;
- note/honorarium generation and resulting documents.

### G4-E — Odontogram / treatment planning
- tooth selection;
- act/treatment selection;
- state changes;
- pricing coupling;
- plan conversion;
- save/refusal;
- source-of-truth boundaries.

### G4-F — Imaging
- RVG;
- panoramic;
- cephalometry;
- upload/select/history;
- calibration/analysis controls where interactive;
- archive/report actions;
- permission/refusal states.

### G4-G — Reconciliation
- compare G0 deep-control inventory against G4-A→F;
- zero known untested critical deep control before certification.

## Existing reusable evidence
Existing tests in DocumentStudio, odontogram, panoramic and ortho may be reused only when they prove the same user-visible business result. Static/policy tests alone do not automatically cover a UI control.

## Certification gate
Do not certify G4 until:
1. every applicable deep control is reconciled;
2. critical mutations have success + refusal/non-mutation proof;
3. exact-head frontend tests + build pass;
4. evidence is recorded here and in Notion.
