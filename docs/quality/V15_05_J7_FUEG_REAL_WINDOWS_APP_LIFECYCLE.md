# Digital Crown LOT05 J7 — FUE-G réelle Windows, application source et restauration (LAB)

**Decision:** Owner GO 2026-11-09 for step 1 of LOT05 after J1–J7 lab success. **Scope strictly GitHub-hosted Windows 2022 VM + fake SQLCipher/Media + real source app `run.py`, not a packaged signed EXE or a live cabinet workstation.** Do not interpret green CI as clinical use permission.

## GOAL

Prove that the existing product backup/restore implementation can safely restart an actual Digital Crown backend process and pass real `/health` with `db=ok`, after a real native SQLCipher/WAL backup and media restore, and recover following a genuine failed application boot. This closes the specific limitation of [J7 native FUE](V15_05_J7_REAL_SQLCIPHER_WAL_MEDIA_RESTORE_LAB.md), which mocks process launch and health.

## Execution (separate disposable Windows runner only)

- A new virgin directory under `RUNNER_TEMP` is mandatory; inherited DATABASE_URL, cabinet appdata, cabinet env file, master/SQLCipher keys or media paths make the job fail **before opening any database**.
- A fully synthetic encrypted SQLCipher database is generated using the repository's real Alembic schema with separate one-run random cryptographic keys. The source app `run.py` is started as a real child process using the project startup policy `restore03_rehearsal`, proper DB fingerprint attestation, disabled telemetry and HTTP bound to 127.0.0.1.
- The test checks genuine loopback HTTP `GET /health` with status 200, `status=ok`, `db=ok`; synthetic SQLCipher WAL is committed in a separate process terminating via `os._exit(0)`. A real on-disk encrypted backup and verified clone are produced through `BackupService`.
- Construct an encrypted GuidedRestore archive with an actual SQLCipher snapshot and two synthetic media files. Call actual `GuidedRestoreService.preflight_file/prepare`, stop the real parent process, and run actual `GuidedRestoreWorker.run` to restore DB/media and restart the genuine `run.py` process. Check HTTP, integrity and fake data.
- Repeat with a different synthetic candidate. Cause the genuine first restart to **refuse boot** using an invalid startup secret. The real HTTP smoke check must fail; the actual worker must roll back DB + media and start the healthy `run.py` again. Verify restoration of the prior synthetic marker, media bytes, failed media absence, and job terminal `rolled_back`.
- Only the launcher invocation `_launch_app` is adapted to start `python run.py` because the real frozen executable is unavailable until independently `INSTALLABLE_CERTIFIED`. The health probe itself is real; its timeout is shortened for the negative case, not faked.
- After the job, **all fake DBs, WAL files, media, generated secrets, logs and child processes are deleted**. GitHub artifacts contain only a non-PHI JSON verdict and exact HEAD.

## SUCCESS and proof contract

Required: exact PR HEAD; Windows 2022 only; a real process launch/kill; real HTTP health; native SQLCipher+WAL crash commit; actual BackupService encrypted clone; actual GuidedRestoreWorker success and HTTP-restart; actual GuidedRestoreWorker health-failure rollback and restart, with matching synthetic DB/media invariants. Failure of ANY assertion => RED, no certificate. See `scripts/lot05_j7_fueg_real_windows_lifecycle.py`, workflow `.github/workflows/lot05-j7-fueg-windows-real-lifecycle.yml`, and its GitHub job logs/artifact.

**Current execution status:** do not mark GREEN before the exact-head GitHub Actions run finishes and an actual log/artifact has been checked. A workflow running or skipped is **not** proof.

## Explicit exclusions and human gates

- No frozen/packaged signed Windows EXE, no installer, no desktop GUI screenshots, no physical power-cut, USB/NAS/SMB or cross-machine migration.
- No clinical data, no real cabinet machine, no patient records, no Firebase credentials or production encryption keys, no real source vendor import, no live user authentication.
- `GuidedRestoreService.request_apply` is deliberately **not** invoked: that endpoint is frozen-cabinet-only and must remain fail-closed. The FUE manually schedules a preflighted synthetic job in a private directory to test the actual worker.
- No modification to product routers, runtime database schema, or release policy. No production deployment or activation. The separate owner/clinical/physical gate remains **NO-GO**.

**NEXT after green:** capture run ID, exact SHA, job logs, artifact checksum and negative proof, then request a separate decision for any signed executable/physical cabinet test. The lab test itself cannot authorize deployment.
