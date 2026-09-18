# V1-05 F1A — ORTHO CASE CLOSEOUT

Status: **IMPLEMENTED — FINAL FULL BACKEND CERTIFICATION PENDING**

Repository: `hraaaaf/Digital_crown`
PR: #596
Exact product HEAD at closeout preparation: `cf9662812a4bbeb9a8433bd96fa555b258d59420`

## Goal

Create the smallest durable longitudinal orthodontic lifecycle layer without duplicating Patient Journey, Media Core, cephalometry, or introducing clinical inference.

## Implemented

- durable `OrthoCase`
- append-only `OrthoPhaseEvent`
- lifecycle states: ACTIVE / INTERRUPTED / ABANDONED / CLOSED
- explicit practitioner-selected phase key
- START / ENTER_PHASE / INTERRUPT / RESUME / ABANDON / CLOSE event history
- patient + tenant isolation
- practitioner/admin-only mutations
- explicit chronological transition guard
- one non-terminal OrthoCase per tenant+patient enforced at DB level
- DB CHECK constraints for lifecycle/event/phase domains
- concurrent create normalized to HTTP 409
- factual OrthoPhaseEvent reuse inside existing Patient Journey
- explicit Alembic migration `ojf1a000006`
- runtime schema gate advanced to `ojf1a000006`
- targeted F1A lifecycle/isolation/RBAC/Journey/invariant tests

## Explicitly not implemented

- structured orthodontic controls (F1B)
- Acte linkage unless separately justified
- study timepoints/media binding (F2)
- longitudinal compare (F3)
- Ortho cockpit/UI (F4)
- scientific superimposition (F5)
- automatic diagnosis, phase, severity, prognosis, treatment recommendation, success/progress inference

## V1-04 prerequisite proof

V1-04 was recertified before F1A product work:
- CI Full Backend run `35359641815` — SUCCESS
- PostgreSQL Alembic run `35359641879` — SUCCESS
- R18 Scientific Concordance run `35359642082` — SUCCESS
- T2 Runtime Browser run `35359641897` — SUCCESS
- Agenda A5 run `35359641824` — SUCCESS
- temporary recertification PR #595 closed without merge

## Current F1A proof

On exact product HEAD `cf9662812a4bbeb9a8433bd96fa555b258d59420`:
- PR #596 mergeable
- CI `35378447229` — SUCCESS, but Full backend regression job was SKIPPED
- PostgreSQL Alembic Schema Certification `35378436623` — SUCCESS
- T2 `35378447397` — SUCCESS
- Agenda A5 `35378447186` — SUCCESS
- Patient P7 `35378436654` — SUCCESS

Therefore F1A is **not yet declared certified**.

A temporary product-equivalent certification PR #604 was created from exact product HEAD `cf9662812a4bbeb9a8433bd96fa555b258d59420`.
Its only intended semantic change is to allow the generic Full backend regression job on that temporary PR. It MUST NOT be merged.

## Certification gate

F1A becomes certifiable only when:
1. PR #604 Full backend regression completes SUCCESS;
2. no product changes exist between `cf966281...` and the certification candidate beyond the temporary CI condition;
3. PR #604 is closed without merge;
4. exact run/job evidence is recorded here;
5. PR #596 remains the product PR.

## Next after certification

Prepare and implement F1B only:
structured orthodontic controls linked to OrthoCase, with explicit practitioner-entered facts and Patient Journey reuse.

No UI or F2 work belongs to F1B.
