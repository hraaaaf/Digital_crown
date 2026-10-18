# Digital Crown — Technical Doubts / Open Evidence

## LOT06-P / P2 — Windows SCM Service Identity, NTFS DACL & SQLite WAL (2026-10-18)

**Status:** OPEN; not a certification, not a waiver, not production-ready. Working PR: https://github.com/hraaaaf/Digital_crown/pull/909. Source audited at `0e98237774bcd7d299335826b12c39a2cabc9393`; preparatory ADR and tests committed at `d5e696aeb29ffecadf805e2540f3a0e327c152ec`. See `docs/quality/LOT06_P_P2_WINDOWS_SCM_IDENTITY_WAL_MIGRATION_ADR.md`.

### TD-P2-01 — Windows security principal, BLOCKER
- **Unproved:** Actual SCM service process token, stable virtual service account, service SID and attributes, Session 0, SCM object permissions, binary protection and minimum privileges. The current TEST bridge child inherits its parent token. A peer using the same interactive SID can write SQLite DB/WAL/SHM in place.
- **Required proof:** Authorize a *separate* synthetic Windows SCM laboratory setup, then inspect the real token and try actual positive service reads/writes plus forbidden interactive-user writes. Service installation or account changes require explicit owner approval, including in a lab. **Status: NOT TESTED**.

### TD-P2-02 — NTFS effective permissions and SQLite sidecars, MAJOR
- **Unproved:** Protected DACL/owner/OWNER RIGHTS on the root and newly created WAL/SHM/journal leaves; WRITE_DAC, WRITE_OWNER, DELETE_CHILD, hardlink/reparse/rename/replace and path-based VFS races. A successful standard-user cross-SID LAB alone does not establish SCM isolation.
- **Required proof:** Dynamic Windows native W01–W12 scenarios in the P2 ADR with correctly denied write access and simultaneously permitted service transactions/backup/restore. **Status: NOT TESTED under SCM**.

### TD-P2-03 — Clinical runtime, compatibility and recoverability, BLOCKER for installation
- **Unproved:** Frozen `run.py` split into headless Session 0 + interactive UI, Windows APPDATA and cabinet .env access, SQLCipher key continuity, media/TLS/licence vault, Firebase/FTS/scheduler, guided restore, install/upgrade/uninstall and usable rollback. The original runtime launches browser/Tk and a user-context restore worker.
- **Required proof:** Full profile/path census, isolated signed-package rehearsal, encrypted backup and *successful detached restore*, API/login parity, exact data invariants, staged rollback, no silent new clinical DB. Separate approval before any actual profile, ACL, key or clinical-data migration. **Status: NOT TESTED**.

### TD-P2-04 — Exact-HEAD CI and independent convergence, OPEN
- **At checkpoint:** `d5e696aeb29ffecadf805e2540f3a0e327c152ec` had workflows 06-A (39128419807), 06-B (39128419805), F01 EXP (39128419799), Scope (39128419840), Portability (39128419798), Settings (39128419827), Staff (39128419858) still **QUEUED**, with M6-I SKIPPED/HORS SCOPE. No invented PASS. This document commit requires CI/review again at its new SHA.
- **Direct proof, narrower scope:** Four disposable stdlib SQLite WAL semantics tests executed locally Linux, 4/4 PASS, Git blob of executed file matches repo test `d6769d2abd052af4a556b01a65dfed7bb47eea21`. Does not attest Windows SCM, DACL or SQLCipher.
- **Required proof:** exact final HEAD CI and test counts, two *genuinely independent* clean reviewer reports on the same HEAD plus clean confirmation. Internal adversarial perspectives are not independent reviewers.

**Gate:** GO for documentation and purely synthetic, reversible tests. NO-GO for SCM registration/install (even laboratory VM), changing effective backend identity, data/key/path/ACL migration, real patient data, merge or deployment. Next: P2 native SCM proof only after separate explicit authorization. Effort: EXTRA HIGH.


## 2026-10-18 P2-F01 — native SCM activation blocked, NOT TESTED

**Explicit scope:** User authorized only a disposable GitHub-hosted Windows SCM laboratory on synthetic data, not the LOT10 client PC or real Digital Crown installer, keys, data, migrations, merge or deploy.

**Prepared, unexecuted WIP in PR #909:** tools/imaging_gateway/windows/p2_scm_synthetic_service.cs and tools/imaging_gateway/windows/p2_scm_virtual_account_wal_lab.ps1. Proposed true virtual NT SERVICE account, SCM Session 0 token proof, protected NTFS acquisition-private directory, Windows SQLite WAL/SHM, user-token denials and service positive transactions/recovery. No Windows compilation, service start, service stop or cleanup occurred during this assistant turn. All of those are NOT TESTED. Neither file belongs in a commercial installer.

**ACTIVATION BLOCKER:** Creating the automated Windows SCM experiment workflow was explicitly blocked by OpenAI tool security controls. No native SCM workflow was committed; no native SCM run was launched, and there is no run URL for it. Do not route around this control with another tool or host. The owner's approval is not a bypass of a tool safety gate.

**CI evidence:** Older exact HEAD 468f8f6082640718c82500e90a88e30555ca7a1b had all seven applicable CI SUCCESS; F01 only cross-standard-user and SCM_SERVICE_SID=NOT_TESTED. Subsequent lab preparation head 1fe45f6f6e53d366d6039537b63e140847a3d6c0 had 06-A/06-B IN_PROGRESS when checked, five applicable others SUCCESS, and M6-I SKIPPED/HORS SCOPE. This documentation edit creates a new HEAD requiring fresh checks. No automatic green carryover.

**Unresolved critical proof:** virtual account logon and real SID token, Windows winsqlite3 availability, runtime CSharp compilation, owner/OWNER RIGHTS effective WRITE_DAC, in-place writes and recreated WAL/SHM, hardened service binary/SCM object, peer user launch, guaranteed SCM/account/files cleanup, complete native W01–W12, clinical SQLCipher/profile/restore and true reviewer independence (0/2).

**Gate:** GO static design/CI as safely available. NO-GO claiming actual SCM isolation or running the blocked workflow. SCM NOT TESTED, P2 NOT CONVERGED; no migration, merge, production install or deployment. Next effort EXTRA HIGH.
