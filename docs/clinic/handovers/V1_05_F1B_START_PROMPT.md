# START PROMPT — Digital Crown V1-05 / F1B — Structured Orthodontic Controls

Repository: `hraaaaf/Digital_crown`
Parent product PR: #596 — V1-05 F1A OrthoCase
Parent product HEAD at preparation: `cf9662812a4bbeb9a8433bd96fa555b258d59420`

## Entry gate

Do not start F1B product code until F1A Full Backend exact-product-equivalent certification is SUCCESS and temporary certification PR #604 is closed without merge.

## Goal

Add the smallest durable structured orthodontic control record linked to `OrthoCase` so a practitioner can reconstruct controls chronologically without free-text archaeology.

## Success

A control can be explicitly recorded with:
- OrthoCase identity
- patient/tenant identity
- control date/time
- phase at control, explicitly entered or copied from current case state with clear provenance
- practitioner observations
- appliance/device context only when explicitly entered
- notable event only when explicitly entered
- next planned step only when explicitly entered
- creator + timestamps

The control must surface factually into the existing Patient Journey without creating another timeline.

## Hard boundaries

Do NOT implement:
- automatic diagnosis
- automatic severity/classification
- automatic phase inference
- treatment recommendation
- progress/success scoring
- cephalometric interpretation beyond already certified canonical data
- F2 timepoints/media binding
- F3 compare
- F4 cockpit/UI
- F5 superimposition
- duplicate generic Journey or Media storage

## Recommended persistence

Add one additive table `ortho_controls` linked to `ortho_cases`:
- id
- ortho_case_id
- employer_id
- patient_id
- control_at
- phase_key nullable
- observations nullable
- appliance_context nullable
- notable_event nullable
- next_planned_step nullable
- created_by nullable
- created_at
- updated_at

Keep all fields factual/practitioner-entered.

## API target

Patient-scoped routes under the existing patient/ortho boundary:
- GET controls for a case
- POST control
- optionally PATCH only if current audit proves editing is needed and auditability is preserved

No DELETE unless a soft-delete/audit contract is explicitly justified.

## Security

- reuse `assert_patient_access`
- never accept employer_id from client
- mutation only dentist/admin
- every case lookup scoped by employer_id + patient_id + case_id
- no cross-tenant existence leak

## Transaction/integrity

- verify OrthoCase belongs to the patient+tenant
- reject creation on a terminal case unless product semantics explicitly justify historical entry
- preserve chronological factual ordering
- additive Alembic revision from current unique head
- advance `CURRENT_ALEMBIC_HEAD` in same implementation
- no startup migration/self-healing

## Patient Journey

Add `OrthoControl` as a factual canonical source in the existing Patient Journey.
Do not synthesize clinical meaning from the observation text.

## Tests required

At minimum:
- create/read control
- tenant isolation
- secretary read vs mutation restriction
- wrong case/patient pairing blocked
- terminal-case behavior
- chronology
- Journey reuse
- schema head sync
- PostgreSQL Alembic fresh-db certification
- full backend regression

## UI

No F1B UI unless separately authorized by proven product need.
If any visual change is introduced, mandatory BEFORE → Goal → implementation → AFTER at 390×844 / 768×1024 / 1280×900 → comparison/tests → severe visual score.

## Next exact

After F1A certification, create a dedicated F1B branch from the certified/merged product baseline and implement this contract without widening scope.
