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
