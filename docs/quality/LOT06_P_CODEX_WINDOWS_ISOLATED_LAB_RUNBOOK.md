# Digital Crown — LOT06-P: Codex Windows isolated Bridge LAB rehearsal

> **Scope**: validate **only** the synthetic Imaging Bridge on the owner's
> authorized Windows computer after GitHub CI is green. This is not the
> installation or activation of Digital Crown's commercial clinical product.

## Explicit non-negotiable boundaries

- Work only in a new, uniquely named folder **inside the current user's
  Windows %TEMP%**. Never use existing clinic folders, Desktop, Documents,
  downloads from actual imaging equipment, shared drives, patient files,
  program folders, or existing application data.
- Do **not** request administrator rights or modify Windows services,
  scheduled tasks, registry, PATH, startup items, system policies,
  antivirus, firewall, or existing Digital Crown installations.
- Do **not** connect to RVG/cameras, TWAIN/DICOM/PACS, clinic backend,
  patient API, Firebase, or production. Do not run the full cabinet app.
- Never use existing environment secrets, bank/medical credentials, or a
  user's real patient IDs. Never print or upload the 256-bit ephemeral LAB key.
- Only synthetic fixtures, e.g. the embedded 2x2 PNG in the repository tests.
  No imaging data sourced from the owner or patient.
- Pin and verify the exact reviewed PR #909 commit before downloading or
  executing it, and record the exact SHA in the final report.
- Do not merge PRs, push changes, release an installer or register a service.
- If safety conditions are not satisfied, **ABORT** and report the blocker.

## Local setup (Python 3.11, isolated, no global installation)

1. Verify OS is Windows, interpreter is Python 3.11 x64, Git is available,
   the user's precise TEMP root, and the sandbox does not exist already.
2. With explicit local user approval to run a temporary rehearsal, create a
   uniquely named LAB workspace beneath `$env:TEMP`, and `git clone
   --filter=blob:none --no-checkout` the trusted
   `https://github.com/hraaaaf/Digital_crown.git` into a child folder.
3. Configure sparse checkout to contain **only**
   `tools/imaging_gateway/**` and read-only `backend/main.py` if needed by
   the AST guard test. Do NOT install backend, frontend, node or extra services.
4. Checkout the **exact SHA** supplied with this handoff; verify
   `git rev-parse HEAD` and `git status --porcelain` before running tests.
5. Create a Python venv inside that new TEMP sandbox. Install only
   `cryptography>=42,<48` there and no other package unless a reproducible
   existing dependency in the Bridge needs it. Compile and run the repository's
   independent unit tests (below). Stop if unexpected imports require clinic
   backend, external connectivity or user data.

## Required safe tests and evidence

- `python -m compileall -q tools/imaging_gateway`.
- `python -m unittest discover -s tools/imaging_gateway/tests -v`.
  Capture exact run/skip/failure totals, specifically tests of native
  Windows junctions `incoming/private`, swapped watched root, swapped spool
  root, same-handle collision-safe ciphertext publish, `PENDING_CONFIRMATION`
  for a valid synthetic PNG, no patient ID, NO plain PNG in the encrypted
  spool, versioned crypto compatibility and bounded force kill/reap.
- Build a disposable isolated TEMP fixture with
  `.digitalcrown-imaging-lab-only` holding the exact expected marker string,
  an `incoming` directory, a new key generated using `secrets.token_hex(32)`,
  and process-local ONLY:
  `DC_V15_06_BRIDGE_LAB=1`, `ENVIRONMENT=test`,
  `DIGITALCROWN_ISOLATED_RUNTIME=true`,
  `DC_V15_06_BRIDGE_LAB_ROOT=<TEMP fixture>`,
  `DC_V15_06_BRIDGE_LAB_KEY_HEX=<ephemeral secret>`.
  Put the repository's genuine 2x2 PNG fixture and its SHA-256 `.ready`
  manifest into the `incoming` directory.
- Exercise `start_if_enabled(trusted_environment="test")` in a disposable
  Python script or subprocess with `asyncio.run`; verify exactly one
  `PENDING_CONFIRMATION` synthetic item and that source bytes are preserved,
  no patient linkage or server upload. Call `stop_bridge_lab`; require the
  child process exits, is reaped and temporary SQLite handles are closed.
- Negative tests (inside the TEMP sandbox only): no opt-in = no collector;
  invalid marker/paths/manifest = rejected; malformed PNG quarantined;
  native Windows NTFS junction attacks and swapping spool/watch directories =
  fail closed/no unauthorized writes; fake blocked child is forcibly killed
  and reaped. For parent-death tests, terminate **only a disposable LAB harness
  PID** created by Codex, never an existing backend or installed application.
- Inspect Windows file permissions of the fresh sandbox **read-only**; do
  not change existing system ACLs. Record observed ACL limitations honestly.
- If any test fails or shows a file written outside the LAB fixture,
  **STOP**. Report the precise safe failure, without leaking any key/path/PHI.

## Local proof and final verdict

Provide Windows build, Python version, exact SHA, venv/package list, the
commands actually executed and test totals, a concise redacted file inventory
of the disposable fixture, evidence of forced child termination, and the
negative-path outcomes. Label every missing test **NON EXÉCUTÉ**.

After verification, close processes/handles, show the exact sandbox target
before cleanup, and remove **only the sandbox created by this rehearsal**
with the user's permission. No collateral files should be deleted.

Verdict levels: `LAB PASS` only if all run tests pass and no unexpected side
effects; otherwise `LAB FAIL/OPEN`. Never claim `INSTALLABLE_CERTIFIED`,
clinical approval, F01 full closure, or merge readiness. F01 remains open
because actual SQLite/WAL and commercial ACL/installer boundaries are
not kernel-handle-contained and validated. F04 Windows parent process
crash on a real installed package remains a separate proof.

Return findings to the developer for fixes/review. The external adverse audit
must be re-run on the exact final HEAD before any merge decision.
