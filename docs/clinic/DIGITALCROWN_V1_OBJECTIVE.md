# Digital Crown — V1 objective

Status: FROZEN OBJECTIVE — candidate SHA not yet selected

## Goal

Produce the first managed cabinet update from canonical V0 (`76547ed178b98b4d8cf14c0fdc691ff3f787076e`) to one exact future candidate SHA, while preserving the existing cabinet database, patients, appointments, actes, payments, document archives, media/files, and historical PK/FK relationships.

V1 is not defined as "latest master". V1 is the first exact SHA that is proven installable from V0 under the managed update contract.

## Success criteria

V1 is achieved only when all of the following are proven:

1. Exact candidate SHA is locked.
2. Candidate CI/certification required for its scope is green.
3. Fresh PREUPDATE evidence is captured from the real V0 cabinet immediately before rehearsal/update.
4. Verified PostgreSQL dump and verified media/document backup exist.
5. The exact candidate SHA is rehearsed on an isolated clone restored from that fresh PREUPDATE state.
6. Alembic migration from the cabinet's current revision to the candidate target head succeeds.
7. All historical rows are preserved.
8. Historical PK definitions are preserved.
9. Historical FK relationships are preserved and no new orphans are introduced.
10. Document archives remain resolvable.
11. Media/file manifest is unchanged by migration.
12. A second Alembic upgrade is a no-op.
13. The candidate application starts successfully on the migrated clone.
14. `/api/health` and critical cabinet smoke tests pass.
15. Candidate is explicitly marked `INSTALLABLE_CERTIFIED`.
16. The real cabinet update is performed from the same locked candidate identity, with writes frozen and backups revalidated.
17. Post-update integrity, startup, and critical smoke tests pass on the real cabinet.

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

## Non-goals

V1 does not require a particular feature set, number of merged PRs, or current `master` state. Functional changes included in the candidate are whatever has independently passed their own lot gates before the candidate SHA is locked.

V1 does not authorize:

- recreating or reseeding the cabinet DB
- replacing the persistent cabinet data root
- silently repairing schema at runtime
- destructive live downgrade as rollback
- treating a moving branch name as the install identity

## Candidate selection rule

Until a specific SHA is intentionally chosen for installation, V1 has **no candidate SHA**.

When chosen, the candidate must be recorded here and remain immutable throughout rehearsal and real installation. If that SHA changes for any reason, certification restarts for the new SHA.

## Rollback rule

Before the real cabinet update, rollback must be executable by restoring the verified PREUPDATE PostgreSQL + media/document snapshot together with the previous V0 application identity when necessary.

## Current state

- Canonical V0: `76547ed178b98b4d8cf14c0fdc691ff3f787076e`
- V1 candidate SHA: NOT SELECTED
- V1 status: OBJECTIVE FROZEN / NOT STARTED
