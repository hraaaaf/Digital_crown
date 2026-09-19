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


## Behavioral proof added

1. `DocumentStudioShell.g4Interactive.test.tsx`
   - all document tabs;
   - preview/save/print contracts;
   - direct-print confirmation.

2. `PrescriptionForm.g4Interactive.test.tsx`
   - quick protocols;
   - medication fields;
   - pharmaceutical form/package;
   - add/remove medication;
   - explicit suggestion apply;
   - validation/safety warnings.

3. `CertificateLibre.g4Interactive.test.tsx`
   - certificate type/content/duration/start-date;
   - free-document metadata/header/format/alignment;
   - formatting controls and validation.

4. `InstallmentStudio.g4Interactive.test.tsx`
   - exact balanced allocation;
   - save after ACK;
   - draft add/remove;
   - explicit payment collection;
   - refusal non-mutation;
   - WhatsApp reminder.

5. `Honoraires.g4Interactive.test.tsx`
   - honorarium line editing/order/removal/total;
   - treasury status/mode/accounting;
   - partial-payment guard;
   - unique/global billing and planned installments.

6. `DevisOdontogram.g4Interactive.test.tsx`
   - adult/pediatric and odontogram modes;
   - tooth treatment to priced devis line;
   - quick tooth groups and grouped treatment;
   - catalog-price precedence;
   - phase organization.

7. `DocumentGeneration.g4Interactive.test.tsx`
   - real honorarium archive/PDF pipeline;
   - refusal preserves accounting state;
   - duplicate force retry;
   - ordonnance generation payload;
   - invalid prescription blocked before backend mutation.

Status remains IN PROGRESS. Imaging and final deep-control reconciliation remain.
