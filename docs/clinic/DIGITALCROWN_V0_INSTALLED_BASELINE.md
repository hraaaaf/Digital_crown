# Digital Crown — V0 installed cabinet baseline

Status: CANONICAL SOFTWARE BASELINE — local revalidation required before first managed update

## Goal

Freeze the currently known cabinet software installation as **V0** so that the next installable SHA is treated as a controlled migration from V0, without replacing or recreating cabinet data.

## V0 software identity

- Canonical V0 commit: `76547ed178b98b4d8cf14c0fdc691ff3f787076e`
- Convenience immutable-origin branch: `release/v0-installed-cabinet`
- GitHub commit verified: yes
- Commit message: `Merge PR #387: polish P4 mobile density`
- Last verified local repository path: `C:\Users\lenovo\Documents\Cabinet\DigitalCrown`
- Last verified runtime: FastAPI on port `8005`, Vite on port `5173`
- `/api/health` reported version prefix: `76547ed1`
- No separate `DigitalCrown-Runtime` release was proven active at this capture; the active installation was the development repository runtime.

## V0 database/runtime identity

Last verified local state:

- Environment: `cabinet`
- DB engine: PostgreSQL 18.2
- DB endpoint: `localhost/digitalcrown_db`
- Alembic revision: `f7a8b9c0d1e2`
- User/media data root: `%APPDATA%\DigitalCrown`

Historical observation at the V0 capture point (informational only, **not** an update invariant):

- 81 tables
- 296 patients
- 149 appointments
- 283 actes
- 214 payments
- 402 documents

These counts are expected to change during normal cabinet use. A future update MUST compare against a fresh PREUPDATE snapshot, never against these historical counts.

## What V0 means

V0 freezes the **software/schema origin**, not the living patient dataset.

The following must remain persistent across updates:

- PostgreSQL cabinet database
- patient records
- appointments
- actes
- payments
- document archives
- media/files
- PK/FK relationships and historical rows

Application files may be replaced. Cabinet data must not be recreated, reseeded, or overwritten.

## Mandatory preflight before the first V0 -> next-SHA update

Before touching the installed cabinet, the update agent MUST collect and persist a PREUPDATE manifest containing at minimum:

1. `git rev-parse HEAD` and proof that the installed origin is V0 (`76547ed178b98b4d8cf14c0fdc691ff3f787076e`).
2. Working-tree status; any local modification blocks automatic update until classified/preserved.
3. `/api/health` version.
4. Python/runtime version and launch mode.
5. `ENVIRONMENT` and resolved DB engine/host/database name, with secrets masked.
6. Current Alembic revision and target Alembic head from the candidate SHA.
7. PostgreSQL version.
8. Current table count plus row/content/PK fingerprints for all historical tables.
9. FK/orphan fingerprint.
10. Current document archive count and proof that every referenced archive resolves.
11. Current media manifest: file count, total bytes, and deterministic hash/fingerprint.
12. Free disk space sufficient for dump + media copy + candidate package.
13. Verified PostgreSQL dump produced before migration.
14. Verified media/document backup or immutable copy before migration.
15. Candidate package/SHA identity and integrity proof.

If any mandatory item cannot be proven, status is **BLOCKED — DO NOT UPDATE**.

## Required rehearsal before touching the cabinet

The exact candidate SHA must first pass on an isolated clone of the fresh PREUPDATE cabinet state:

`PREUPDATE dump/media copy -> isolated restore -> Alembic upgrade -> preservation comparison -> second upgrade no-op -> app startup -> health/smoke tests -> PASS`

Required preservation proof:

- all historical table rows preserved
- historical PK definitions preserved
- historical FK relationships preserved
- no new orphans
- document archives still resolvable
- media manifest unchanged
- second Alembic upgrade is a no-op
- application starts successfully on the migrated clone

Only after this rehearsal passes can the candidate become `INSTALLABLE_CERTIFIED`.

## Real cabinet update sequence

1. Freeze writes / close the application cleanly.
2. Re-run PREUPDATE capture against the real cabinet.
3. Create and verify PostgreSQL + media/document backups.
4. Verify candidate SHA/package signature/hash.
5. Install application files only; do not replace the cabinet data root.
6. Run Alembic migration against the existing cabinet DB.
7. Re-run integrity/fingerprint checks.
8. Start the application.
9. Verify `/api/health` and critical cabinet smoke tests.
10. Mark update successful only after all gates are green.

Failure at migration, integrity, startup, or smoke-test stage is fail-closed. Do not silently recreate schema or data.

## Rollback rule

Rollback must be planned before update. Because schema migrations can be irreversible, rollback means restoring the verified PREUPDATE DB/media snapshot together with the previous V0 application code when necessary; never blindly run destructive Alembic downgrades against the live cabinet.

## First managed update contract

When the next SHA is ready to install, treat it as **V1 candidate** only after:

- exact SHA locked
- CI/certification green
- fresh PREUPDATE snapshot from the cabinet
- isolated representative rehearsal PASS
- backup verification PASS
- explicit install package identity

Then perform the real V0 -> candidate update using the sequence above.

## Revalidation caveat

This V0 identity is based on the last verified local installation state. Before the first managed update, the local agent must re-prove the current PC still matches the V0 software identity. If it does not, update this manifest with the actually installed origin before proceeding.
