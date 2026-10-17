# DIGITAL CROWN — LOT06-P / Request for genuinely independent re-review

**Independent reviewers only.** This document is a request, **not** a review
and **not** a claim of CONVERGED. Never ask the original implementer to
self-certify as an external reviewer.

## Mission and constraints

Independently inspect **PR #909** against parent PR #901 in
`hraaaaf/Digital_crown`. Before reviewing, read the current HEAD
directly from GitHub; cite its **complete 40-character SHA**, base SHA,
the exact code/line, the tests and the workflow run/job URLs. Re-evaluate
from scratch; do not accept prior internal scores. The user postponed
all remote/local PC and hardware tests to **LOT10** because that PC is
offline. No clinical device, real patient data, merge, release, install,
server deployment or UI patient auto-attachment is authorized.

Original external adverse result: **FAIL / LOT06-P OPEN** with **five MAJOR**:
F01 Windows junction/path escape and TOCTOU, F02 FastAPI lifespan cleanup,
F03 duplicated reads/decrypt, F04 OS-blocked thread/shutdown, F05 magic-only
media accepted. Old scores **security 4.5/10, reliability 4/10**.
All remain audit items; green synthetic CI does not establish closure.

## Review 1 — independent SECURITY reviewer

Prove or disprove:
- Native Windows `NtCreateFile RootDirectory` source + `.ready` reads,
  `NtSetInformationFile` relative spool create/rename/read, collision
  refusal and handle-based cleanup under directory substitutions/reparse.
- SQLite VFS `sqlite3.connect` **still opens by path**. Verify the
  new Windows no-`FILE_SHARE_DELETE` directory/main-DB HANDLE lifetime,
  including a real **second-process** main-file rename denial and rename
  succeeding after close. The test is narrow: actively try a same-user
  in-place write, unpinned WAL/SHM/journal replacement, first-bootstrap
  name creation race, hardlink/symlink/reparse, and path-identity ABA race.
  Examine whether native APIs/handle lifetimes interfere with SQLite's
  own WAL checkpoint/close. State exactly what is and is not stopped by
  filesystem sharing; do not mistake no-rename for full ACL isolation.
  Can an adversary win TOCTOU between checks and SQLite open/commit?
- SQLite WAL/SHM/journal plus checkpoint/rollback, temp SQLite files and
  named external attaches: any paths escaping private root, PHI or secrets?
- Windows DACL installer contract is unimplemented; explicitly state that
  protected service SID/ACL is **NOT CERTIFIED**. Key in environment is
  acceptable only for disposable LAB, not production.
- Security of Win32 ctypes structures/NT API permissions, races at handle
  ownership transfer, possible fail-open error swallowing.
- Product invariant: no patient auto-association, no server receipt, no
  production flag, zero real-device inputs.

## Review 2 — independent RELIABILITY/Windows reviewer

Prove or disprove:
- `FastAPI lifespan` exception/shutdown and tests on real entrypoint.
- `Windows Job Object KILL_ON_JOB_CLOSE`, GO gate before scanning, real
  parent disappearance, OS child release/reap; Linux PDEATHSIG equivalent.
- Single-process ownership with multi-Uvicorn worker or restart after crash.
- WAL FULL durability, checkpoint/recovery, out-of-space, SQLite busy locks,
  stale sidecars, database identity reuse after legitimate restarts;
  assess Windows per-connection ancestry/main-DB no-delete-sharing for
  lock-order inversion, denied checkpoint/unlink, handle leaks, concurrent
  worker contention, normal shutdown, and restart.
- Encryption/nonce/AAD/isolated lab, no duplicate replay, source unchanged,
  actual protocol/media format fail-closed.
- Windows package/service and ACL gate remains **NOT TESTED / DEFERRED LOT10**.

## Mandatory report

For EACH F01-F05: `CLOSED BY PROOF`, `MITIGATED/OPEN` or `BLOCKER`,
severity, file:line, realistic exploit or regression, reproduction,
test executed vs CI-only vs not run and proposed minimal correction.
Separate score A/B severe /10, two perspectives where applicable, plus
original independent review relation. Confirm no extra application visible
and no live hardware. List each referenced workflow run URL and HEAD.

Decision must be **FAIL / OPEN** if any MAJOR persists; do not use
`CONVERGED` unless there are two actually independent clean reviews
on the **same HEAD**, tests executed, clean confirmation, user authorization
and no significant issues. No PR merge or production install.

Current LAB suite for the reviewer:
`python -m unittest discover -s tools/imaging_gateway/tests -v`;
`python -m pytest backend/tests/test_imaging_bridge_lifespan_v15.py -q`;
`python -m pytest backend/tests/test_imaging_acquisition_preflight_v15.py backend/tests/test_media_core_ingestion_api.py tools/imaging_gateway/tests/test_qa_visual_runtime.py -q`.

All machine/hardware experiments are **LOT10, NOT NOW**.
