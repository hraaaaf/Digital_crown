# LOT06-P / P2-F01 — Internal adversarial review A+B (2026-10-18)

**Evidence freeze before fix:** repository `hraaaaf/Digital_crown`, PR #909, HEAD `5faadfc19750311a030253ef37775a3e2e23bdb1`, base `373ced67385a444996ba290755bdfcdd255440bf`. This is **one assistant, two INTERNAL review perspectives**, not two independently executed BLIND reviewers. Never report 2/2 BLIND. Both follow the frozen A/B prompts at `docs/quality/LOT06_P_P2_F01_BLIND_A_B_PROMPTS.md`.

**Scope and proof separation.** [FUE-A and FUE-B workflow #39170261828](https://github.com/hraaaaf/Digital_crown/actions/runs/39170261828) succeeded with two distinct disposable Windows runner jobs (A: 33/33 peer denials plus 6/6 WRITE_DAC/WRITE_OWNER, B: 14/14 backup/SQLite recovery tests), and CI [06-B #39170261704](https://github.com/hraaaaf/Digital_crown/actions/runs/39170261704) was green. Those runs did **not** start the prototype service. Source syntax/compilation on Windows does not establish SCM token, Session 0, service DACL, privileged API compatibility, service crash/restart, or real Windows headless backup/restore. Executing the blocked privileged SCM setup is **not authorized**.

## A — Windows token and NTFS isolation, internal security perspective

**Score: 4/10, BLOCKER remains.**

- **A-BLOCKER-01 — Actual service identity/effective permissions not tested.** `tools/imaging_gateway/windows/p2_scm_virtual_account_wal_lab.ps1` lines 126–165 *contain* `sc create`, `sidtype`, `Win32_Service`, SID/Session0/PID comparisons but the tested P2 gate compiles/parses source only and prints `P2_FIXTURE_NATIVE_SCM_TOKEN=NOT_TESTED`. FUE-A runs `f01_cross_sid_acl_lab.ps1` with **ordinary** user SIDs. Runtime SCM actual token privileges, effective DACL, service object DACL (`sc sdshow`), service SID restrictions and object ownership are **UNKNOWN**; never infer them from config.
- **A-MAJOR-02 — ACL allow-list lacks effective-rights oracle.** The `Ace` function in the same PowerShell script, lines 25–33, admits any `Allow` ACE with an allow-listed SID and does not validate file access masks, OWNER RIGHTS interaction, owner identity, service-object DACL, effective rights or reparse/replace escapes. It can print `P2_SCM_CONFIG_AND_PROTECTED_ACL=PASS` after checking only private-root protected inheritance and allow-list identities. This is **not** proof of the intended effective rights.
- **A-MAJOR-03 — Peer execution/guard mismatch not exercised.** The Peer requires `CI`, `GITHUB_ACTIONS`, `P2_RUNNER_ENVIRONMENT`, `GITHUB_REPOSITORY` and `P2_SCM_OWNER_GO`; Harness uses `Start-Process -Credential` without a demonstrated environment transfer to the separate logon. A runnable negative oracle is not established; do not patch it to bypass previously denied SCM execution.
- **A-MAJOR-04 — Coverage gaps, not disproven isolation.** No permissible proof of service-object CHANGE_CONFIG/WRITE_DAC, file/dir renames and replacement, junctions/hardlinks, inherited permissions on sidecars or compromised service principal. A hostile Administrator, SYSTEM or backup operator is explicitly outside the local standard-user threat model, but effective low-privilege isolation still needs native proof.

No change to privileged SCM harness is proposed here because previously blocked SCM execution must not be enabled by a source workaround.

## B — SQLite WAL, process lifecycle and recoverability, internal reliability perspective

**Score: 3/10 for SCM certification; source MAJOR resolved only subject to exact-HEAD tests.**

- **B-MAJOR-01 — checkpoint false-positive: FIXED IN SOURCE in accompanying change.** `tools/imaging_gateway/windows/p2_scm_synthetic_service.cs` calls `Sql(db, "PRAGMA wal_checkpoint(PASSIVE);")` before emitting both `service.ready` and `service.after`. `sqlite3_exec` returns SQLITE_OK even when a reader pins WAL pages and the checkpoint result has fewer checkpointed frames than log frames. Therefore `SQLITE_COMMIT=PASS`/after markers previously did not establish completed checkpoint. Fix calls `RequireCompleteCheckpoint` to read `busy`, `logFrames`, `checkpointedFrames` and fail closed if busy/nonvalid/incomplete before either proof marker. **No native service was executed.** A new pure Python SQLite test establishes the relevant semantics: holding an older read snapshot can yield `(0, log, checkpointed)` with `checkpointed < log`, then catch up after the reader exits.
- **B-MAJOR-02 — stop and close remain unproven.** `OnStop` at end of C# calls `worker.Join(7000)` but does not check its boolean result; `Close(db)` return code is ignored. Nothing here proves that a real service stop drained writes or observed close errors. Do not describe successful `ServiceBase.Run` startup as evidence of SCM-safe shutdown.
- **B-BLOCKER-03 — no native SCM WAL recovery after kill/restart/restore.** `test_p2_sqlite_recovery_semantics.py` tests crash-replay in a plain Python subprocess and consistent online snapshots in disposable directories. `p2_backup_lab.py` and FUE-B cover synthetic DB/spool/key restore but not a running SCM process, packaging, Windows service identity, SQLCipher, clinical key escrow or migration. The B02 snapshot explicitly warns it is not a durability guarantee against power loss. **W01–W12 native contract NOT_TESTED**.
- **B-MAJOR-04 — backup assumptions.** `snapshot_quiescent_lab` protects only cooperating LAB owner lock, checks ledger/spool in a staged tree and publishes via rename. It does not prove an uncooperative same-SID writer cannot race between checks and publication, or crash-durable publication on real NTFS.

## Decision / next gate

Review A **OPEN 4/10**; Review B **OPEN 3/10 (one source defect addressed)**. These two assessments are **not independently BLIND**; count `0/2` external reviews on the final HEAD. Source fix requires **new exact-HEAD CI (06-A Windows+Ubuntu; P2 C# compile syntax Windows; 06-B), FUE A+B and an internal recheck**, otherwise even static improvement is NOT VALIDATED. No merge, deployment, customer device, actual SCM service registration, bypass of security controls, migration or LOT10. Retain every unproven item in `techdoubt.md`.

## Internal continuation — shutdown/close source hardening, same P2-F01 scope

B-MAJOR-02 has an additional **source-only** mitigation: `sqlite3_close` now checks return status and writes a class-only `service.error`; `OnStop` fails when the worker does not join within seven seconds or when a worker/close error marker exists. The new HEAD requires Windows C# compilation, 06-A static regression tests, 06-B and both FUE jobs. Until exact-HEAD runs finish, status is UNVERIFIED; even GREEN is not a true SCM service shutdown or restart proof. Independent BLIND remains 0/2.

## Internal re-review — worker error marker can fail to write

The prior `OnStop()` failure guard depended on an on-disk `service.error` that is best effort (its write exceptions are swallowed). Under a full disk / denial, the guard could miss a failed `sqlite3_close()` and falsely report a clean stop. Latest follow-on source patch adds an in-process `volatile workerFailed` flag, set before marker writes by either Work catch or close failure and checked after join by OnStop. A fresh exact-HEAD CI must pass; this remains internal source hardening, NOT a native service lifecycle proof.
