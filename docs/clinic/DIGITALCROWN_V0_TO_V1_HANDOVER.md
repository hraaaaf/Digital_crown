# HANDOVER — Digital Crown cabinet update V0 -> V1

Status: READY FOR NEW WINDOW

## Goal

Prepare the first controlled cabinet update from the real installed V0 to one exact future V1 candidate SHA while preserving all cabinet data.

## Canonical V0

- Installed software SHA: `76547ed178b98b4d8cf14c0fdc691ff3f787076e`
- Principal local worktree branch observed on cabinet PC: `test/local-validation-76547ed`
- GitHub reference: `release/v0-installed-cabinet`
- Source-of-truth file: `docs/clinic/DIGITALCROWN_V0_INSTALLED_BASELINE.md`

This V0 identity is locally verified and is the only valid software origin for the first managed cabinet update.

## Separate rehearsal worktree — do not confuse with V0

- Branch: `fix/boot-schema-explicit-migrations`
- HEAD: `49eff48185029658030245fa1bbbea1e8203217a`

This worktree was used for migration rehearsal/certification only. It is not the installed cabinet baseline.

## Current repository state

At handover preparation time:

- Repository: `hraaaaf/Digital_crown`
- `master`: `039df96eb76c11f6e8f05c10a35eca2ef0c230b1`
- Latest relevant master commit: `docs: freeze V1 update objective`
- V1 objective file: `docs/clinic/DIGITALCROWN_V1_OBJECTIVE.md`

Master may advance after this handover. A new window must re-check current master/HEAD/PR/CI before acting.

## V1 state

- V1 candidate SHA: NOT SELECTED
- V1 status: OBJECTIVE FROZEN / NOT STARTED
- V1 is NOT "latest master".
- V1 becomes real only when one exact SHA is intentionally selected and remains immutable through rehearsal and installation.

## Managed-update contract

The first real cabinet update must follow exactly:

`V0 -> fresh PREUPDATE capture -> verified DB/media backup -> isolated clone restore -> exact candidate migration -> integrity comparison -> second migration no-op -> app startup -> health/smoke tests -> INSTALLABLE_CERTIFIED -> real cabinet update -> post-update integrity proof`

No shortcut turns CODE_CERTIFIED into INSTALLABLE_CERTIFIED.

## Mandatory PREUPDATE evidence from the real cabinet

Before any real update or rehearsal based on current cabinet state, collect fresh evidence from the actual principal worktree/runtime:

1. exact `git rev-parse HEAD`
2. branch/ref
3. `git status --short`
4. `/api/health` version/build
5. active backend/frontend processes and working directories
6. Python/runtime version and launch mode
7. current Alembic revision
8. PostgreSQL version + host/database name, secrets masked
9. current table/row/content/PK fingerprints
10. FK/orphan fingerprint
11. document archive resolution proof
12. media/file count, bytes, deterministic fingerprint
13. free disk space
14. verified PostgreSQL dump
15. verified media/document backup or immutable copy
16. exact candidate SHA/package identity

Any missing critical proof => `BLOCKED — DO NOT UPDATE`.

## Data-preservation invariant

Must preserve across update:

- PostgreSQL cabinet database
- patients
- appointments
- actes
- payments
- documents/document archives
- media/files
- historical rows
- historical PK definitions
- historical FK relationships
- no new orphans

Application code may change. Persistent cabinet data must never be recreated, reseeded, silently repaired, or replaced.

## Rollback rule

Rollback must be planned before update. If the candidate fails migration/integrity/startup/smoke checks, rollback means restoring the verified PREUPDATE PostgreSQL + media/document snapshot together with the previous V0 application identity when needed. Do not rely on destructive live Alembic downgrade.

## First action in the next window

Read in order:

1. `docs/clinic/DIGITALCROWN_V0_INSTALLED_BASELINE.md`
2. `docs/clinic/DIGITALCROWN_V1_OBJECTIVE.md`
3. `docs/clinic/DIGITALCROWN_V0_TO_V1_HANDOVER.md`
4. `docs/clinic/CABINET_UPGRADE_COMPATIBILITY_GATE.md`

Then verify:

- current `master` SHA
- any candidate SHA proposed for installation
- open PRs/CI relevant to that candidate
- that the local cabinet still reports V0 until a managed update is actually performed

## Next exact

Do nothing to the real cabinet until an exact V1 candidate SHA is intentionally selected.

When a candidate SHA is selected:

1. lock the candidate SHA
2. verify candidate CI/certification
3. capture fresh PREUPDATE state from the real V0 cabinet
4. create/verify backups
5. rehearse on isolated clone
6. compare all integrity fingerprints
7. certify `INSTALLABLE_CERTIFIED` only if all gates pass
8. perform the real V0 -> V1 update
9. run post-update health/integrity/smoke proof
10. promote the installed baseline to V1 only after proof

## Sequence remaining

`candidate selection -> exact-SHA lock -> CI/certification -> PREUPDATE -> backup -> isolated rehearsal -> integrity/no-op/startup/smoke -> INSTALLABLE_CERTIFIED -> real update -> post-update proof -> V1 baseline closeout`

## Real blocker

No technical blocker. The intentional V1 candidate SHA has not yet been selected.

## Canonical files

- `docs/clinic/DIGITALCROWN_V0_INSTALLED_BASELINE.md` — installed V0 source of truth
- `docs/clinic/DIGITALCROWN_V1_OBJECTIVE.md` — frozen V1 objective
- `docs/clinic/DIGITALCROWN_V0_TO_V1_HANDOVER.md` — restart/handover file
- `docs/clinic/CABINET_UPGRADE_COMPATIBILITY_GATE.md` — migration compatibility/certification gate
