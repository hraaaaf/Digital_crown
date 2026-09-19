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


8. `frontend/src/features/patients/components/ClinicalHubCore.g4Interactive.test.tsx`
   - clinical odontogram dirty/save boundary;
   - optimistic revision persistence;
   - 409 conflict/reload;
   - explicit practitioner conclusion;
   - 403 conclusion refusal;
   - treatment-plan status/delete persistence and refusal preservation.

9. `frontend/src/features/panoramic/PanoramicStudio.g4Interactive.test.tsx`
   - upload/refusal;
   - practitioner findings;
   - report generation/refusal;
   - preview/download/edit;
   - history/comparison;
   - filters/manual annotations;
   - evolution unavailable truth.

10. `frontend/src/features/ortho/CephaloWorkspace.g4Interactive.test.tsx`
    - patient truth gate;
    - four-step navigation;
    - save boundary;
    - history hydration/refusal.

11. `frontend/src/features/patients/components/RvgDeep.g4Interactive.test.tsx`
    - upload + metadata;
    - upload refusal;
    - open/download authenticated blob;
    - explicit delete confirmation;
    - delete refusal preserves card.

Imaging and clinical-authoritative boundaries are now covered. Remaining work is G4-G reconciliation against all deep controls exposed by G0 and exact-head CI.


12. `frontend/src/features/patients/components/Payments.g4Interactive.test.tsx`
    - QuickPay amount/method gate;
    - all four payment methods;
    - exact payment payload;
    - accounting-context reset only after ACK;
    - refusal keeps modal/state;
    - act-specific partial payment with acte_id;
    - act-payment refusal without false paid callback.

Remaining G4-G reconciliation focus:
- structured clinical assistant wizards;
- any PatientFinances deep controls not already proved by payment/installment matrices;
- final G0 ↔ G4 control reconciliation;
- exact-head CI/test/build.


13. `frontend/src/features/patients/components/wizards/ClinicalWizards.g4Interactive.test.tsx`
    - all nine structured clinical assistants;
    - cancel without conclusion;
    - backward navigation;
    - Examen complet triage return;
    - explicit option-driven completion;
    - completion returns structured proposal only.

G4-G reconciliation now focuses on verifying that every deep module exposed by G0 maps to one of the behavioral matrices above, then exact-head tests/build.


## G4-G reconciliation — inspected deep modules

| Deep module | Behavioral proof |
| --- | --- |
| Document Studio shell / tabs / preview / print | `DocumentStudioShell.g4Interactive.test.tsx` |
| Ordonnance / prescription | `PrescriptionForm.g4Interactive.test.tsx`, `DocumentGeneration.g4Interactive.test.tsx` |
| Certificates / libre docs | `CertificateLibre.g4Interactive.test.tsx` |
| Honoraires / treasury | `Honoraires.g4Interactive.test.tsx`, `DocumentGeneration.g4Interactive.test.tsx` |
| Devis / odontogram accounting | `DevisOdontogram.g4Interactive.test.tsx` |
| Installments | `InstallmentStudio.g4Interactive.test.tsx` |
| Direct patient payments | `Payments.g4Interactive.test.tsx` |
| Patient finance screen | `PatientFinances.g4Interactive.test.tsx` |
| Clinical odontogram / conclusions / master plan | `ClinicalHubCore.g4Interactive.test.tsx` |
| Structured clinical assistants | `ClinicalWizards.g4Interactive.test.tsx` |
| RVG | `RvgDeep.g4Interactive.test.tsx` |
| Panoramic | `PanoramicStudio.g4Interactive.test.tsx` |
| Cephalometry | `CephaloWorkspace.g4Interactive.test.tsx` |

Based on the inspected G4 surfaces, no known deep module is currently left without a behavioral proof file. This is not certification yet: exact-head frontend tests/build must still pass, and any CI failure must be resolved before G4 can be marked certified.


## Functional reconciliation
Observed G4 behavioral matrices now cover:
- Document Studio shell/navigation/generation;
- Prescription;
- Certificate/Libre;
- Honorarium/accounting;
- Installments;
- Devis + accounting odontogram;
- Patient finance screen;
- global and act-specific payments;
- clinical authoritative odontogram;
- practitioner conclusions;
- treatment-plan mutations;
- 9 structured clinical wizards;
- RVG;
- panoramic;
- cephalometry.

No additional independent G4 deep-control gap is currently known from the reconciled source inventory.

Status: FUNCTIONALLY RECONCILED — CERTIFICATION PENDING EXACT-HEAD TESTS + BUILD.
