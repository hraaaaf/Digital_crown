# P10 — Cross-platform Update Engine

**Status:** ACTIVE — secure-core + Windows production wiring + real packaged lifecycle candidate + interruption recovery under certification. **0 EP credited.**

## Goal

Install only an authentic, fresh, strictly newer Digital Crown release, with a verified rescue point before mutation and automatic post-update health/rollback once the P6/P7 distribution artifacts are certified.

## Secure-core contract

P10 does not treat HTTPS or a SHA-256 alone as update authentication.

A release manifest is a detached Ed25519-signed envelope. The client:

1. verifies the signature against the configured production public key;
2. requires a monotonic positive `sequence`;
3. remembers the highest accepted sequence + canonical signed-metadata hash;
4. rejects lower sequence (`UPDATE_ROLLBACK_BLOCKED`);
5. permits an exact retry of the same sequence only for identical signed metadata;
6. rejects same-sequence conflicting metadata (`UPDATE_REPLAY_CONFLICT`);
7. requires timezone-aware issuance/expiration and rejects expired metadata;
8. persists a monotonic `last_trusted_time` so a local clock rollback cannot move trust time backwards;
9. selects exactly one OS/architecture target;
10. requires HTTPS and verifies exact artifact size + SHA-256 before promotion from `.partial`;
11. creates and verifies a local encrypted DB rescue point, then copies that rescue inside the immutable update job before it can become `prepared`;
12. stages the artifact under the filename signed by the manifest;
13. persists only non-secret update state atomically.

The production **private key is never committed, bundled, downloaded by the client, or persisted by this service**. Only its Ed25519 public key is trusted by the client. Production public-key pinning plus rotation/revocation remain P10 closure gates.

## Post-install truth contract

P10 has a platform-independent verification boundary for the package after an installer has run.

The verifier cross-checks two independent truths:

1. the installed executable runs its existing `--package-self-test`, which reads the root canonical `VERSION` bundled by `DigitalCrown.spec`; the self-test must prove the **exact manifest version**, a frozen executable, no missing/forbidden assets, no unqualified scientific weights and `FAIL_CLOSED_NO_WEIGHTS`;
2. only after package truth passes, the verifier accepts the loopback `/health` endpoint when both runtime and DB report `ok`.

The HTTP health gate is restricted to loopback. Git metadata, installer display labels and remote HTTP endpoints are not accepted as the installed-version source of truth.

## Windows production apply + external worker contract

The Windows candidate is wired into production apply, but only behind a fail-closed boundary: frozen `cabinet` runtime, Windows platform, exact admin confirmation, staged worker hash verification and a real Authenticode `Valid` signature with timestamp certificate. `apply_certified=true` is written only after these checks.

The current P6 distribution evidence remains `P6_AUTHENTICODE=NOT_CONFIGURED`. Therefore the existing unsigned P6 artifact cannot cross this production mutation gate. Wiring exists; production signed distribution certification does not yet exist.

### Native shell requirement

The worker targets **Windows PowerShell 5.1 (`powershell.exe`)**, the Windows-integrated shell, and does not require separately installed PowerShell 7 (`pwsh.exe`). The worker source is constrained to the Windows PowerShell 5.1/.NET Framework-compatible surface. CI routes the core child-worker drills through the native `powershell.exe`, asserts the reported runtime is 5.1, and rejects a regression back to `#requires -Version 7.0` or `Path.IsPathFullyQualified`.

The benchmark-validated mutation/rollback implementation remains isolated in `windows_update_worker_core.ps1`. The public `windows_update_worker.ps1` is a narrow orchestrator around that core, while `windows_update_worker_entry.ps1` owns detached execution and direct-wrapper process waiting.

Before the installer can mutate anything, the core must:

1. require `platform=windows`, `worker_contract=windows-inno-v1`, `status=scheduled` and `apply_certified=true`;
2. verify the signed installer's exact staged size + SHA-256;
3. verify the staged encrypted DB rescue SHA-256;
4. wait for the parent Digital Crown process to exit;
5. run the current packaged `--package-self-test` against the exact current version;
6. reject install trees containing reparse points;
7. create a verified **program snapshot** with file/directory integrity manifests;
8. export the matching per-user **uninstall registry** metadata and verify its current `DisplayVersion`.

Only then may it run the silent Inno installer into the already-attested install directory.

After install it requires:

- exact target package self-test;
- uninstall metadata `DisplayVersion` equal to the target version;
- a loopback `/health` response with both runtime and DB `ok`.

On post-apply failure, the core stops the failed runtime, restores the exact program snapshot, imports the previous uninstall registry metadata, proves the old package version again, relaunches it and accepts rollback only if `/health` is healthy. A successful package rollback explicitly records `database_rollback=not_needed`.

## Interrupted apply recovery

A frozen cabinet startup inspects only recoverable update states and may launch the staged `windows_update_recovery.ps1` worker after verifying its SHA-256. Recovery never performs a blind installer re-apply.

- `scheduled` before mutation is reset to `prepared` and certification is cleared;
- `health_pending` rechecks exact target package truth + `/health` before finalization, otherwise rolls back;
- `applying` / `rolling_back` restore the old package from the verified program snapshot + uninstall registry;
- `database_rolling_back` or the exact package-rollback health failure may resume the old-package DB rescue path;
- worker ownership is serialized by `worker.lock`.

The real packaged interruption drill remains a closure gate until it completes green with inspected artifact proof. P10 #37 exposed a Windows PowerShell path-separator type bug in this recovery worker after the ordinary current→next and rollback paths had already produced valid proof; that defect must be re-certified by a subsequent real packaged run before any closure claim.

## Last-resort database rollback bridge

Database restore is deliberately **not** a generic response to rollback failure. The orchestrator may cross this boundary only when the core has already restored the exact old program and uninstall metadata, but the old runtime still fails health with the exact reason `UPDATE_WINDOWS_PACKAGE_ROLLBACK_HEALTH_FAILED`.

Only in that state:

1. the orchestrator marks `database_rollback=running`;
2. it invokes the restored **old packaged executable** with `--update-db-rollback-worker <job.json>`;
3. PowerShell never receives the backup key and never decrypts cabinet data;
4. the old executable loads the existing cabinet environment before any first-boot secret generation;
5. the bridge accepts only the staged `.db.enc` rescue whose SHA-256 matches the immutable job;
6. the existing `backup.key` is mandatory and is never generated by rollback;
7. PostgreSQL / `.sql.enc` restores fail closed because local file replacement is not a substitute for `pg_restore` semantics;
8. the decrypted rescue remains a SQLCipher database and must pass SQLCipher `integrity_check` before replacement;
9. the current DB/WAL/SHM family is copied and hash-verified into the private job rescue quarantine;
10. the canonical `clinical_vault.db` is replaced atomically, stale WAL/SHM sidecars are removed, and the restored DB must pass SQLCipher verification again;
11. if post-replacement verification fails, the pre-rollback DB family is restored;
12. only after the bridge exits successfully does the orchestrator relaunch the old package and require loopback `/health` with runtime and DB both `ok`.

A registry failure, program snapshot failure, old package self-test failure, missing key, checksum mismatch, PostgreSQL database, invalid SQLCipher rescue or DB-worker failure never broadens the fallback. Those paths remain `rollback_failed` and fail closed.

## Verified Windows evidence to date

The targeted Windows contracts already prove uncertified apply rejection, healthy target transition to `health_pending`, exact package rollback, DB fallback ownership by the old executable and finalization truth. Real packaged benchmarks have also demonstrated current `1.0.0` → target `1.0.1`, target package self-test + `/health`, package rollback and SQLCipher DB rescue. The interruption-recovery path is not credited until its corrected real packaged drill and artifact are green.

## Packaging boundary

P6/P7 own the exact signed installers/packages and their platform distribution semantics.

- Windows production wiring is implemented and fail-closed.
- `UpdateApplyService` can set `apply_certified=true` only after the real Windows Authenticode signature is `Valid` and a timestamp certificate is present.
- The current P6 artifact is unsigned, so automatic production apply remains blocked despite the wiring and benchmark harness.
- P7 signed/notarized macOS packaging remains required before a real macOS update lifecycle can be certified.

A secure updater must not turn an uncertified distribution artifact into an automatic production mutation.

## Remaining gates before P10 closure

- corrected real packaged Windows interruption recovery drill green + inspected artifact proof;
- signed/timestamped P6 Windows production artifact and real production apply current → next proof;
- P7 exact signed/notarized macOS package certified and wired to update apply;
- production public-key pinning plus signing-key rotation/revocation procedure;
- Windows + macOS clean-machine certification.

The first real package used as an auto-update source must already contain the DB rollback worker CLI, so its restored old executable owns rescue decryption and SQLCipher validation.

No Vercel.
