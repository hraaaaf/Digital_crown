# Digital Crown — V0 installed cabinet baseline

Status: CANDIDATE ONLY — NOT CANONICAL UNTIL LOCAL PC VERIFICATION

## Goal

Identify and then freeze the exact software version currently installed on the cabinet PC as V0, so the next installable SHA can be treated as a controlled migration without replacing or recreating cabinet data.

## Current candidate — UNVERIFIED

The SHA below comes from an earlier local observation and is **not yet accepted as V0**:

- Historical candidate commit: `76547ed178b98b4d8cf14c0fdc691ff3f787076e`
- Existing convenience branch: `release/v0-installed-cabinet`
- GitHub commit verified: yes
- Commit message: `Merge PR #387: polish P4 mobile density`

The branch name above is historical and MUST NOT be interpreted as proof of the currently installed cabinet version.

## Mandatory local Codex verification before V0 freeze

An agent with direct access to the cabinet PC must provide fresh evidence from the machine that is actually running Digital Crown:

1. Exact repository/runtime path used to launch Digital Crown.
2. `git rev-parse HEAD` from that exact path.
3. `git status --short`.
4. Current branch/ref.
5. `/api/health` version/build identifier.
6. Active backend/frontend processes with executable and working-directory paths.
7. Current Alembic revision.
8. PostgreSQL version plus resolved host/database name, credentials masked.
9. Current user/media data root.
10. Whether the running installation is a packaged runtime or the development repository.

Only when those signals agree may the installed SHA be frozen as canonical **V0**.

If the live PC SHA differs from `76547ed178b98b4d8cf14c0fdc691ff3f787076e`, the live PC SHA wins and this historical candidate remains non-canonical.

## Data rule

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

## Mandatory PREUPDATE capture for the first managed update

Before touching the installed cabinet, the update agent MUST collect and persist a PREUPDATE manifest containing at minimum:

1. locally verified canonical V0 SHA
2. working-tree status
3. `/api/health` version
4. Python/runtime version and launch mode
5. environment and resolved DB engine/host/database name, secrets masked
6. current Alembic revision and target Alembic head from the candidate SHA
7. PostgreSQL version
8. current table count plus row/content/PK fingerprints for all historical tables
9. FK/orphan fingerprint
10. current document archive count and archive-resolution proof
11. current media manifest: file count, total bytes, deterministic fingerprint
12. sufficient free disk space
13. verified PostgreSQL dump
14. verified media/document backup or immutable copy
15. candidate package/SHA identity and integrity proof

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

Rollback must be planned before update. Because schema migrations can be irreversible, rollback means restoring the verified PREUPDATE DB/media snapshot together with the previous application code when necessary; never blindly run destructive Alembic downgrades against the live cabinet.

## Current decision

**No V0 is frozen yet.** The next action is local machine verification by Codex (or another agent with direct PC access). Only after receiving that evidence may this document be promoted from `CANDIDATE ONLY` to `CANONICAL SOFTWARE BASELINE`.
