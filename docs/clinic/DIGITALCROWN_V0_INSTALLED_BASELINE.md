# Digital Crown — V0 installed cabinet baseline

Status: CANONICAL SOFTWARE BASELINE — locally verified installed worktree

## Goal

Freeze the exact software version currently installed in the cabinet's principal worktree as **V0**, so the next installable SHA is treated as a controlled migration without replacing or recreating cabinet data.

## Canonical V0 identity

Fresh local proof from the cabinet PC established:

- Principal worktree branch: `test/local-validation-76547ed`
- Principal worktree HEAD: `76547ed178b98b4d8cf14c0fdc691ff3f787076e`
- Canonical V0 SHA: `76547ed178b98b4d8cf14c0fdc691ff3f787076e`
- GitHub reference: `release/v0-installed-cabinet`
- GitHub commit verified: yes
- Commit message: `Merge PR #387: polish P4 mobile density`

A separate rehearsal worktree was also observed:

- Rehearsal branch: `fix/boot-schema-explicit-migrations`
- Rehearsal HEAD: `49eff48185029658030245fa1bbbea1e8203217a`

The rehearsal worktree is **not** the installed cabinet V0 and must never be used as the source version for a real cabinet update.

## Data rule

V0 freezes the **software/schema origin**, not the living patient dataset.

The following remain persistent across updates:

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

Before touching the installed cabinet, the update agent MUST collect and persist a fresh PREUPDATE manifest containing at minimum:

1. `git rev-parse HEAD` from the principal cabinet worktree and proof that it is canonical V0 (`76547ed178b98b4d8cf14c0fdc691ff3f787076e`)
2. working-tree status; any local modification must be classified/preserved before update
3. `/api/health` version/build identifier
4. active backend/frontend processes and their working-directory paths
5. Python/runtime version and launch mode
6. environment and resolved DB engine/host/database name, secrets masked
7. current Alembic revision and target Alembic head from the candidate SHA
8. PostgreSQL version
9. current table count plus row/content/PK fingerprints for all historical tables
10. FK/orphan fingerprint
11. current document archive count and archive-resolution proof
12. current media manifest: file count, total bytes, deterministic fingerprint
13. sufficient free disk space
14. verified PostgreSQL dump
15. verified media/document backup or immutable copy
16. exact candidate package/SHA identity and integrity proof

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

Rollback must be planned before update. Because schema migrations can be irreversible, rollback means restoring the verified PREUPDATE DB/media snapshot together with the V0 application code when necessary; never blindly run destructive Alembic downgrades against the live cabinet.

## First managed update contract

When the next SHA is ready to install, treat it as a **V1 candidate** only after:

- exact SHA locked
- CI/certification green
- fresh PREUPDATE snapshot from the cabinet
- isolated representative rehearsal PASS
- backup verification PASS
- explicit install package identity

Then perform the real V0 -> candidate update using the sequence above.

## Canonical decision

**V0 is frozen at `76547ed178b98b4d8cf14c0fdc691ff3f787076e`.**

The branch name of the principal cabinet worktree (`test/local-validation-76547ed`) is incidental; the immutable SHA is the authoritative software baseline.
