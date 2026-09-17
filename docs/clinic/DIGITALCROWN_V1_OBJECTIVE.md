# Digital Crown — V1 objective

Status: FROZEN OBJECTIVE — execution roadmap locked — candidate SHA not yet selected

## Execution authority

The sole authorized execution roadmap until V1 is operational is:

`docs/clinic/DIGITALCROWN_V1_CANONICAL_ROADMAP.md`

Its lot order is mandatory. No workstream outside the currently unlocked lot is authorized. Other roadmap/plan/handover documents are supporting or historical evidence only and cannot alter scope, sequencing or unlock a later lot.

## Goal

Produce the first managed cabinet update from canonical V0 (`76547ed178b98b4d8cf14c0fdc691ff3f787076e`) to one exact future candidate SHA, while preserving the existing cabinet database, patients, appointments, actes, payments, document archives, media/files, and historical PK/FK relationships.

V1 is not defined as "latest master". V1 is the first exact SHA that is proven installable from V0 under the managed update contract **after completion of the mandatory canonical roadmap through LOT V1-09**.

## Success criteria

V1 is achieved only when all of the following are proven:

1. All mandatory lots preceding candidate freeze in `DIGITALCROWN_V1_CANONICAL_ROADMAP.md` are closed in order with their required proofs.
2. Exact candidate SHA is locked in LOT V1-10.
3. Candidate CI/certification required for its scope is green.
4. Fresh PREUPDATE evidence is captured from the real V0 cabinet immediately before rehearsal/update.
5. Verified PostgreSQL dump and verified media/document backup exist.
6. The exact candidate SHA is rehearsed on an isolated clone restored from that fresh PREUPDATE state.
7. Alembic migration from the cabinet's current revision to the candidate target head succeeds.
8. All historical rows are preserved.
9. Historical PK definitions are preserved.
10. Historical FK relationships are preserved and no new orphans are introduced.
11. Document archives remain resolvable.
12. Media/file manifest is unchanged by migration.
13. A second Alembic upgrade is a no-op.
14. The candidate application starts successfully on the migrated clone.
15. `/api/health` and critical cabinet smoke tests pass.
16. Candidate is explicitly marked `INSTALLABLE_CERTIFIED`.
17. The real cabinet update is performed from the same locked candidate identity, with writes frozen and backups revalidated, and only after explicit human authorization.
18. Post-update integrity, startup, and critical smoke tests pass on the real cabinet.
19. `V1_OPERATIONAL` is recorded in the canonical roadmap with the installed SHA and proof references.

Only then may the installed cabinet baseline be promoted from V0 to V1.

## Proof required

The V1 closeout must preserve:

- V0 SHA
- candidate/V1 SHA
- source Alembic revision
- target Alembic revision
- PREUPDATE fingerprints
- POSTUPDATE fingerprints
- backup verification evidence
- rehearsal report/result
- CI/run identifiers relevant to the candidate
- post-update health/smoke evidence
- rollback point identity
- canonical roadmap lot closeouts V1-00 through V1-12

## Scope lock

V1 now requires completion of the exact mandatory lot sequence defined in `DIGITALCROWN_V1_CANONICAL_ROADMAP.md`.

Until `V1_OPERATIONAL`:

- no unrelated chantier may be started;
- no later lot may be advanced before its predecessor closes;
- an open historical PR does not authorize work or merge outside its assigned lot;
- fixes discovered by the active lot are permitted only when strictly necessary to make that active lot pass its gates.

V1 does not authorize:

- recreating or reseeding the cabinet DB
- replacing the persistent cabinet data root
- silently repairing schema at runtime
- destructive live downgrade as rollback
- treating a moving branch name as the install identity
- mutating the real cabinet before LOT V1-12 and explicit human authorization

## Candidate selection rule

Until LOT V1-10 is reached and a specific SHA is intentionally chosen for installation, V1 has **no candidate SHA**.

When chosen, the candidate must be recorded here and in `DIGITALCROWN_V1_CANONICAL_ROADMAP.md` and remain immutable throughout rehearsal and real installation. If that SHA changes for any reason, certification restarts for the new SHA.

## Rollback rule

Before the real cabinet update, rollback must be executable by restoring the verified PREUPDATE PostgreSQL + media/document snapshot together with the previous V0 application identity when necessary.

## Current state

- Canonical V0: `76547ed178b98b4d8cf14c0fdc691ff3f787076e`
- sole roadmap: `docs/clinic/DIGITALCROWN_V1_CANONICAL_ROADMAP.md`
- active lot: `V1-00 — CI / Windows / dependency contract`
- V1 candidate SHA: NOT SELECTED
- V1 status: EXECUTION LOCKED / NOT OPERATIONAL
