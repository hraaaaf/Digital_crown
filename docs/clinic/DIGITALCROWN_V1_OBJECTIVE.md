# Digital Crown — V1 objective

Status: CANONICAL OBJECTIVE — V1-07 PRE-FREEZE TRIPLE-CHECK IN PROGRESS — candidate SHA not yet selected

## Execution authority

The sole authorized execution roadmap until V1 is operational is:

`docs/clinic/DIGITALCROWN_V1_CONSOLIDATED_ROADMAP.md`

Its lot order is mandatory. No workstream outside the currently unlocked lot is authorized. Other roadmap/plan/handover documents are supporting or historical evidence only and cannot alter scope, sequencing or unlock a later lot.

## Goal

Produce the first managed cabinet update from canonical V0 (`76547ed178b98b4d8cf14c0fdc691ff3f787076e`) to one exact future candidate SHA, while preserving the existing cabinet database, patients, appointments, actes, payments, document archives, media/files, and historical PK/FK relationships.

V1 is not defined as "latest master". V1 is the first exact SHA that completes the mandatory consolidated roadmap, is proven installable from V0 under the managed update contract, and is then installed and verified on the real cabinet after explicit human authorization.

## Success criteria

V1 is achieved only when all of the following are proven:

1. All mandatory lots preceding candidate freeze in `DIGITALCROWN_V1_CONSOLIDATED_ROADMAP.md` are closed in order with their required proofs.
2. One exact candidate SHA is intentionally locked at the freeze lot.
3. Candidate CI/certification required for its scope is green.
4. Fresh PREUPDATE evidence is captured from the real V0 cabinet immediately before rehearsal/update.
5. Verified PostgreSQL dump and verified media/document backup exist.
6. The exact candidate SHA is rehearsed on an isolated clone restored from that fresh PREUPDATE state.
7. Alembic migration from the cabinet's current revision to the candidate target head succeeds.
8. Historical rows, PK definitions and FK relationships are preserved and no new orphans are introduced.
9. Document archives remain resolvable and media/file manifest is preserved.
10. A second Alembic upgrade is a no-op.
11. The candidate application starts successfully on the migrated clone.
12. `/api/health` and critical cabinet smoke tests pass.
13. Candidate is explicitly marked `INSTALLABLE_CERTIFIED`.
14. The real cabinet update is performed from the same locked candidate identity, with writes frozen and backups revalidated, and only after explicit human authorization.
15. Post-update integrity, startup, and critical smoke tests pass on the real cabinet.
16. `V1_OPERATIONAL` is recorded in the consolidated roadmap with the installed SHA and proof references.

Only then may the installed cabinet baseline be promoted from V0 to V1.

## Proof required

The V1 closeout must preserve V0 SHA, candidate/V1 SHA, source/target Alembic revisions, PREUPDATE/POSTUPDATE fingerprints, backup verification, rehearsal result, relevant CI/run IDs, post-update health/smoke evidence, rollback identity, and every mandatory lot closeout from the consolidated roadmap.

## Scope lock

Until `V1_OPERATIONAL`:

- no unrelated chantier may be started;
- no later lot may be advanced before its predecessor closes;
- an open historical PR does not authorize work or merge outside its assigned lot;
- fixes discovered by the active lot are permitted only when strictly necessary to make that active lot pass its gates;
- no competing V1 roadmap may be created or used.

V1 does not authorize recreating/reseeding the cabinet DB, replacing the persistent cabinet data root, silently repairing schema at runtime, destructive live downgrade as rollback, treating a moving branch name as install identity, or mutating the real cabinet before the final cabinet-update lot and explicit human authorization.

## Candidate selection rule

Until the freeze lot is reached and a specific SHA is intentionally chosen, V1 has **no candidate SHA**. If that SHA changes after freeze, certification restarts for the new SHA.

## Rollback rule

Before the real cabinet update, rollback must be executable by restoring the verified PREUPDATE PostgreSQL + media/document snapshot together with the previous V0 application identity when necessary.

## Current state

- Canonical V0: `76547ed178b98b4d8cf14c0fdc691ff3f787076e`
- sole roadmap: `docs/clinic/DIGITALCROWN_V1_CONSOLIDATED_ROADMAP.md`
- active lot: **V1-07 — Master stabilization / mandatory pre-freeze triple-check**
- audit base: `master@ceae1624c5f1311eb7ffcf512785b8a30fe438fc`
- V1-08 freeze: **BLOCKED** until all V1 BLOCKER/MUST-FIX findings are remediated and re-certified
- V1 candidate SHA: **NOT SELECTED**
- installability status: **NOT CERTIFIED**
- V1 status: **EXECUTION LOCKED / NOT OPERATIONAL**
- production/cabinet mutation: **NOT AUTHORIZED**
- Vercel deployment: **NOT AUTHORIZED**
- audit: `docs/clinic/audits/V1_07_PREFREEZE_TRIPLE_CHECK.md`

## Current next exact

Complete Pass 1 remediation, Pass 2 evidence double-check and Pass 3 adversarial re-audit on one exact HEAD. Only after all V1 BLOCKER/MUST-FIX findings are green may V1-07 close and V1-08 select an immutable candidate SHA.
