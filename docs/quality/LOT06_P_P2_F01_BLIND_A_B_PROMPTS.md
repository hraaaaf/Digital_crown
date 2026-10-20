# LOT06-P / P2-F01 — Blind-first review prompts A+B (2026-10-18)

**Repository**: `hraaaaf/Digital_crown`. **PR**: https://github.com/hraaaaf/Digital_crown/pull/909. **Scope**: disposable Windows SCM / NTFS / SQLite WAL synthetic LAB only. Never operate on an actual clinic workstation, medical data, installable release, LOT10 or deployed environment. Do not run/register a privileged SCM service using a route blocked by tool safety controls. Do not merge/deploy.

**Freeze the HEAD before every run** from GitHub; do not rely on a SHA printed in this document. The examiner must specify the exact SHA and base, its own execution environment, exact sources/line ranges, commands/log URLs, negative evidence, and skips. Every new commit invalidates earlier reviews. A GitHub Actions GREEN status is not evidence of true SCM isolation unless the real service actually ran with its own verified token.

### Review A — independent first-time Windows security examiner

You are an offensive Windows security engineer, encountering the code for the first time, **without seeing Review B or another reviewer’s conclusions**. Your objective is to falsify the claim that a normal interactive user cannot read, write, replace, take ownership of, or change DACLs of the service-private DB/WAL/SHM/spool/key and cannot modify the service binary or service object.

1. Inventory the exact SCM service account configuration, *runtime primary token*, service SID and group/privilege attributes, session ID, owner, DACL/OWNER RIGHTS, inherited ACEs, file/object reparse and alias paths. Explicitly distinguish code constructs, syntax-only CI, ordinary two-user tests and genuine SCM service evidence.
2. Attack each DB, WAL, SHM, journal, private directory, spool, key, binary and service DACL using a genuinely separate standard-user SID: direct open, in-place same-byte write, delete/delete-child, rename/replacement, WRITE_DAC, WRITE_OWNER, reparse/hardlink, forged proof reports, environment guards and peer token inheritance. Expect no permissions change. Verify source hash and SDDL before/after if a permitted executable experiment exists.
3. Look for false positives: permissive effective rights despite an allow-list; implicit owner permissions; SCM config mistaken for runtime token; evidence flags accepted without native execution; cleanup weakness, ambiguous error classification, wrong test fixture; fail-open behavior. Never create a synthetic success marker.
4. Produce **BLOCKER / MAJOR / MINOR** defects with line-level support, repeatable reproduction only if permitted, severity /10 (10 is best), exact status of A-01/A-02 and W01–W12, and next permitted fixes. Mark NOT_TESTED where needed. If the required privileged experiment is blocked, state so and STOP; do not bypass it.

### Review B — independent first-time SQLite WAL reliability examiner

You are a Windows service reliability engineer and SQLite concurrency/recovery specialist, encountering the code for the first time, **without seeing Review A or another reviewer’s conclusions**. Your objective is to falsify committed-data durability, integrity, startup/shutdown, and recoverability claims for a real headless Windows SCM process.

1. Inventory process lifetime, startup/stop completion, joins/errors, SQLite opening and PRAGMA readbacks, journal mode, WAL/SHM checkpoint, lock coordination, busy handling, rollback, connection close, and proof gating. Distinguish synthetic Python process crash from real SCM stop/kill/restart.
2. Inspect snapshot boundaries and backup/restore: SQLite online backup API, schema, spool, continuity marker, ciphertext/key, publication atomicity, race/TOCTOU, interruption at every stage, wrong/missing keys, SQLCipher and migration compatibility. Require complete positive and negative scenarios rather than `PRAGMA integrity_check` alone.
3. Seek false positives: WAL fallback reported as success, checkpoint busy silently ignored, committed but unsynced records, service stop while worker remains active, partial spool restore, account/profile differences, claims extrapolated from standard-user subprocess tests, and stale exact-SHA CI.
4. Deliver **BLOCKER / MAJOR / MINOR**, grounded file/line location, exact proof/run labels, score /10, fault model, safe remediation within LAB, and explicit NOT_TESTED SCM W01–W12. Stop on blocked privileged operation, without workaround.

### Non-fabrication and convergence protocol

Each A/B report must be captured and frozen **in genuinely separate agent contexts** with no exchange of evidence or reports before both submissions, then reconciled. A single assistant performing two passes is **two internal perspectives, NOT independent BLIND A+B**. Tool availability/connection must be independently demonstrated. If no separate execution mechanism is available, publish these prompts, a clearly labeled internal review, and keep BLIND gate OPEN (0/2). A and B must both report zero BLOCKER and MAJOR **on the identical final HEAD**, CI/tests must be executed on that SHA, and genuine native SCM proofs remain separate mandatory gates. Never declare CONVERGED because documentation or synthetic CI is GREEN.
