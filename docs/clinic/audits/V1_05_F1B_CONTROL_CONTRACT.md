> Historical design/audit record extracted during V1-06 pre-freeze reconciliation on 2026-09-19. Status/gates inside this document describe the state at authorship time; subsequent product implementation and certification are recorded in the V1-05 closeouts and consolidated roadmap.

# V1-05 F1B — Structured Orthodontic Controls Contract

Status: **DESIGN READY — PRODUCT CODE BLOCKED ON F1A POST-MERGE CERTIFICATION**

## Trailer

F1B turns each orthodontic follow-up visit into a real structured clinical control record:
date, phase, observations, appliance context, notable event, and next planned step.

It does **not** create another Patient Journey and does **not** interpret the treatment automatically.

## Proven gap

Existing objects do not replace this need:

- `JourneyMilestone.CONTROLE`: generic milestone only; no structured ortho control fields.
- `Appointment`: scheduling/attendance source; not the clinical control record.
- `TreatmentPlanStep`: plan/workflow step; not an observed follow-up visit.
- `OrthoPhaseEvent`: lifecycle/phase history from F1A; not the content of a control.
- Patient Journey: read-only aggregation layer; not a persistence source.

No existing dedicated `OrthoControl` / orthodontic control persistence was found during the F1B audit.

## Goal

Persist one factual practitioner-entered orthodontic control linked to one `OrthoCase`.

## Minimal persistence

Additive table: `ortho_controls`

Required fields:
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

## Semantics

All values are factual/practitioner-entered.

No field may encode:
- diagnosis
- severity
- prognosis
- automatic phase inference
- automatic progress/success
- treatment recommendation

`phase_key` is the phase recorded for that control. If copied from current `OrthoCase.current_phase_key`, the API must make that behavior explicit and deterministic; no inference from measurements/media is allowed.

## Lifecycle constraints

Control creation:
- case must belong to exact tenant + patient
- case must be non-terminal (ACTIVE or INTERRUPTED)
- control_at must be >= case.started_at
- controls are returned in deterministic chronological order
- no delete in F1B
- no patch/update in initial slice unless audit proves a real need

Terminal cases:
- new controls rejected on ABANDONED/CLOSED
- historical records remain readable

## Security

Read:
- patient permission + tenant/patient access

Mutation:
- DENTISTE / ADMIN only
- employer_id never accepted from client
- every case lookup constrained by employer_id + patient_id + case_id
- cross-tenant case existence must not leak

## API

Target endpoints:

- `GET /patients/{patient_id}/ortho-case/{case_id}/controls`
- `POST /patients/{patient_id}/ortho-case/{case_id}/controls`

POST payload:
- control_at
- phase_key optional
- observations optional
- appliance_context optional
- notable_event optional
- next_planned_step optional

No DELETE.

## Patient Journey reuse

`OrthoControl` becomes one more factual canonical source in the existing Patient Journey.

Suggested factual rendering:
- source: `ortho_control`
- type: `control`
- date: control_at
- title: `Contrôle orthodontique`
- phase_hint: phase_key.lower() if present, otherwise `ortho`
- navigation: INLINE for F1B

Do not display free-text observations as synthesized conclusions.

## Database and migration

- one additive Alembic revision from current unique head `ojf1a000006`
- update `CURRENT_ALEMBIC_HEAD` in same implementation
- preserve explicit migration-only upgrade contract
- no startup migration
- employer FK preserves clinical history
- patient/case delete behavior must match F1A lifecycle retention policy

## Required tests

1. create/read structured control
2. chronological ordering
3. reject control before case start
4. reject control on CLOSED case
5. reject control on ABANDONED case
6. case/patient mismatch blocked
7. cross-tenant read/mutation blocked
8. secretary same-tenant read allowed, mutation forbidden
9. Journey contains factual `ortho_control` event
10. schema runtime head sync
11. fresh PostgreSQL Alembic upgrade
12. full backend regression

## Out of scope

- UI/cockpit
- media/timepoints
- cephalometric comparison
- superimposition
- Acte billing linkage
- automatic interpretation

## Entry gate

Product implementation starts only after F1A merged baseline `c41f47d2eb7708d6494fd32c97814d7a968ed5e0` has successful post-merge-equivalent Full Backend certification and the temporary certification PR is closed without merge.
