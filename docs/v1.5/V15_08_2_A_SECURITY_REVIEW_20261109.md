# LOT08.2-A — Security review and direct Windows evidence (2026-11-09)

**State: DRAFT / Security source reviewed / Physical bootstrap NOT RUN / No merge.**

## Scope
Local-first Queue Core first-admin bootstrapping, local login sessions and offline recovery, isolated from clinical data. Owner GO: 08.2-A implementation and review only. No web endpoints, Firebase, patient data, actual installed service or production enrollment.

## Source and reviewers
- PR [#1238](https://github.com/hraaaaf/Digital_crown/pull/1238), branch `feat/v15-08-2-a-local-admin-bootstrap-20261108`, base master `edf26bb7ff70904b802069891f31ef3b4dc7691d`.
- Independent Codex generic initial review `58e3b5e7`: no initial findings, but a separate adversarial SEC/OPS review of that same SHA identified **P1 spoofed ACL/attacker-owned existing directory** and **P2 dangling link/reparse handling**. Both were corrected in `e3513ac9` using atomic Win32 security-descriptor creation and owner/ACE verification, lstat and reparse-safe create.
- Independent Codex read-only review on `e3513ac9`: no P1/P2; **P3 status path created an auth directory on an uninitialized server**. Corrected on `09f3d40e` with no-create behavior and a negative test.
- Independent Codex read-only review on `09f3d40e`: **P2 expired session digests persisted indefinitely**, risking unbounded database growth. Fixed on source **`44bc6fc639332796f064dbf18a59a4f8b5c3333f`** with transactional removal on every login attempt and a negative test.
- Independent Codex read-only **delta review** of `44bc6fc6` relative to previously reviewed `09f3d40e`: **“I found no actionable defect in the diff.”** This is an independent AI agent's code review, *not human approval* or physical-operability certification. Review raw transcripts remain on the owner-authorized workstation, outside the Git repository.

## Verified direct Windows evidence
- DESKTOP-3MAJEEH, Python 3.12. `python -m pytest -q queue_core/tests`: **53/53 PASS** at source SHA `44bc6fc6`, exit 0. Existing Queue Core 08.1 regressions included. `python -m compileall -q queue_core/security` exit 0. Git clean on reviewed source commit.
- Direct command `python -m queue_core.security.windows_cli status` from Remote Desktop Commander: **refused `INTERACTIVE_CONSOLE_REQUIRED` (exit 2)**; ProgramData identity SQLite file **absent before and after**.
- Windows `advapi32!ConvertStringSecurityDescriptorToSecurityDescriptorW` successfully parsed both **directory and file SDDL** in memory; **no filesystem writes**. Static PowerShell ACL scripts parsed without errors.
- Local tests used temporary synthetic SQLite files and injected fake physical-console guard. **No actual local admin or recovery token created**, no real patient/clinical data or migrations, no GitHub Actions Queue tests deliberately launched. Green legacy runs are not evidence for this new SHA.

## Mandatory unexecuted acceptance / no-go
- Positive **physically local elevated Windows console** path (initial `issue` → `enroll` → encrypted/offline recovery, ACL owner/SYSTEM+Administrators actual), full signed service/installer and isolated physical Windows LAB **NOT_RUN**. RDP and redirected shells are intentionally denied. Passing mocks and SDDL parsing do not substitute for this real gate.
- If not separately proven, **NO-GO to merge/close 08.2-A, install in cabinet or begin 08.2-B**. G2/tenant RBAC, kiosk/wall pairing, single-use QR, distributed API/webhooks, local backup/restore and patient-level security remain downstream. The actual source implementation contains no patient data.

## NEXT
1. Prepare an authorized **isolated physical Windows LAB** (not a real patient workstation) with elevated local console.
2. Demonstrate first Admin, local file ACL from actual security descriptors, one-time offline recovery, invalidation and restoration failure modes; store recovery secret offline only, **never in test logs**.
3. Reverify source SHA, use direct Windows evidence, independent security recheck if code changes, owner merge gate, post-merge verification.
