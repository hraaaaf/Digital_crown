# LOT06 — Imaging Bridge background integration (isolated LAB prototype)

## Goal
One Digital Crown installation, no second user-facing app. Exercise a synthetic imaging receiver via the existing FastAPI backend lifespan, in the background. This does **not** install, activate, or certify a real Windows service, vendor driver, Wi-Fi camera, RVG device, DICOM node, or any clinical association.

## Scope
- The existing backend lifespan starts a coroutine **only** when explicitly selected for an isolated test; it joins that coroutine during shutdown. Blocking filesystem scans execute off the API event loop.
- Disabled by default: all three environment gates must hold: ENVIRONMENT=test, DIGITALCROWN_ISOLATED_RUNTIME=true, DC_V15_06_BRIDGE_LAB=1.
- Only watch an explicitly prepared fixture within the OS temporary directory. Require an incoming directory, the sentinel .digitalcrown-imaging-lab-only containing DIGITALCROWN_IMAGING_LAB_ONLY_V1, and a synthetic 256-bit lab key via DC_V15_06_BRIDGE_LAB_KEY_HEX. Accepted files additionally require a producer `.ready` sidecar with size+SHA-256 matching completed contents; an ordinary Wi-Fi camera will need an adapter that safely emits this marker.
- Valid simulated photos remain locally PENDING_CONFIRMATION, invalid media QUARANTINED. No upload, server receipt, patient identity inference, clinical asset, device credentials or real device IO.
- Do not modify DigitalCrown.spec, Inno Setup, mobile packaging, Windows services or production startup activation.

## Evidence and negative cases
Default-off; cabinet/non-isolated or backend-settings mismatch denial; fixture sentinel/path/key failures; incomplete/mismatched image cannot stage; completed encrypted synthetic image without patient ID; quarantine unknown content; background worker starts/stops, exceptions do not leak sensitive filenames. Existing LOT06-A GitHub Actions Windows/Ubuntu matrix discovers and executes these unittest cases.

## Gates still open
Native Windows background process/service lifecycle and INSTALLABLE_CERTIFIED packaging, multi-poste ownership, Wi-Fi/RVG/DICOM/TWAIN/proprietary SDK hardware, certified patient binding and atomic receipt, product/mobile UI, RPG-X separate process actors and RPG-P physical tests. Tests here do not certify any device or claim clinical interoperability.

This is a lab-only prototype on a draft stacked PR. No clinical installation without separate certified release, rehearsal and explicit human approval.

## CI separation
The existing 06-A imaging matrix has only lightweight spool/cryptography dependencies. This LAB worker lives in `tools.imaging_gateway.bridge_background_lab` and is imported from the product's FastAPI lifespan; the synthetic suite therefore does not import `backend.__init__` or require SQLAlchemy. The 06-B operational route check supports both first-level PRs (preflight 0 -> 1) and stacked descendant PRs (preflight 1 -> 1), retaining strict multiset equality for all other routes.

The optional LAB module import in `backend.main.lifespan` is guarded by the explicit `DC_V15_06_BRIDGE_LAB=1` switch; ordinary installed startup must never require the optional imaging gateway package at boot. A source-level regression asserts this property in the lightweight CI.

### CI repair 2026-10-16
Both Python 3.11 OS runners use `unittest` without `pytest`; route-registry regression tests are now `unittest.TestCase` tests collected and executed on both. The isolated root guard retains strict canonical equality and OS temp containment while normalizing Windows path casing (with a Windows-only case-alias test). The import-scope AST negative test counts only direct guarded imports, not nested `If` duplicates. None of these changes enable acquisition in a cabinet.

### CI repair follow-up — filesystem identity
The earlier normalization-only Windows fix remained red. LAB confinement now validates TEMP ancestry using `Path.samefile` (true directory identity) instead of lexical `commonpath`, and explicitly rejects any supplied component with symlink or Windows reparse-point attributes. The startup AST test checks both valid imports independently: `start_if_enabled` guarded by the explicit LAB flag and `stop_bridge_lab` guarded by an existing worker handle. Neither test is skipped or weakened.

## FastAPI lifespan end-to-end synthetic proof
`backend/tests/test_imaging_bridge_lifespan_v15.py` uses the **real** `backend.main.app` and FastAPI lifespan through `TestClient`. The test explicitly enables a TEMP-marked LAB fixture with a synthetic, SHA-256-completed PNG, waits for its local `PENDING_CONFIRMATION` state, verifies zero additional ClinicalAsset records, exits the real FastAPI lifespan, and asserts the Bridge worker was joined and the tempfile safely removed. A second test leaves the LAB switch absent and asserts the real app does **not** start a Bridge. Unrelated Firebase, indexing, scheduler and panorama side effects are patched (the app's lifespan is **not patched**). Runner: heavy-dependency existing 06-B isolated Ubuntu job. This is not a test of installed Windows service/real hardware or actual product launch package.

## Independent audit (external) — 2026-10-17: FAIL; remediation scope

An independent adversarial review rejected closure of LOT06-P (FAIL, 5 MAJOR;
security 4.5/10, reliability 4.0/10). The earlier green CI established only
nominal LAB tests and should not be described as certification. Corrections
on PR #909 since `a6483264`:

- **F01 (NTFS junction escape) — mitigated, OPEN pending native retest/review.**
  Detect Windows reparse points at incoming/private, watch/private/spool and
  ancestor level; check canonical roots and per-scan directory identities.
  Windows CI includes actual `mklink /J` attacks for both LAB subdirectories
  (creation is mandatory, not silently skipped) and a post-init root swap test.
  A TOCTOU replacement between checking and opening a file remains possible
  without Windows anchored handles and ACL/process isolation.
- **F02 (FastAPI shutdown absent on exceptional exit) — corrected in code,
  CI proof pending.** The actual `yield` is now inside a `try` with a
  `finally` that stops the LAB handle and cancels/joins pre-existing async
  tasks. The startup logger does not stringify the exception. A test raises
  inside the actual FastAPI `lifespan(app)` and asserts the Bridge stops.
- **F03 (re-reading all already received files) — optimized manifest mode,
  CI proof pending.** Look up completed source signatures and producer SHA
  in the durable indexed SQLite ledger, check bounded spool metadata, skip
  repeated input read, hash and AES-GCM decrypt. The first capture still
  checks source bytes and SHA; `read_verified()` reauthenticates on use.
  The older no-manifest mode remains unchanged; periodic spool scrub and
  high-volume soak profiling are NOT implemented.
- **F04 (blocked OS I/O prevents shutdown) — partially mitigated, MAJOR
  OPEN.** The LAB API shutdown wait is bounded and explicitly returns False
  with a generic warning if a thread is stuck. Python `to_thread` CANNOT
  forcibly terminate an in-flight OS read. A supervised process with native
  Windows cancellation/kill/reap is required for real devices before
  clinical release. No claim of true resource disposal after a timeout.
- **F05 (magic-only media accepted) — conservative fail-closed correction,
  CI proof pending.** Only structurally parsed 8-bit non-interlaced PNG can
  reach PENDING_CONFIRMATION in this LAB: chunk lengths and CRC, critical
  chunks, IHDR size/pixel cap, bounded decompression and row filter checks.
  JPEG/WebP/PDF (and DICOM) are QUARANTINED until their own validators exist.
  This is an intentional functional limitation, not clinical image decoding
  certification.

Gates: new exact-SHA Windows/Ubuntu CI, preflight+lifespan CI, two fresh
independent external reviews on the SAME final HEAD, installer/ACL confinement,
real-device compatibility and explicit patient linking are **OPEN**.
PR #909 is DRAFT; no merge, no install, no clinical activation.

## F01/F04 second hardening batch — supervised LAB child and Windows scan handles

- **F01:** the synthetic scan now enters `pin_directories`, taking `CreateFileW` directory handles with `FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT` and **without** `FILE_SHARE_DELETE` for the watch, private, spool and their parents during each scan. After pins are acquired, the existing directory identities/reparse checks run again. New native Windows test demands that a watched directory cannot be renamed while the handle is held; it can be renamed after the context closes. This reduces a live Windows rename/junction TOCTOU window, but is **not** proof of complete path confinement, file-level reparse protection, a secure ACL policy, or kernel-anchored per-file opens.
- **F04:** the real backend `start_if_enabled` no longer uses `asyncio.to_thread(scan_once)`; it launches a **hidden**, LAB-only, same-package subprocess via `sys.executable -m tools.imaging_gateway.process_lab`. The child runs with a minimal environment (no other backend credentials), validates the same marker and TEST isolation, monitors a parent-owned stdin channel and gracefully stops at a safe polling boundary. On stop deadline the parent kills and **reaps** the child, returning **False**, never a false success. Tests prove a real child stages a fake PNG and is reaped on normal shutdown, and inject an uncooperative synthetic subprocess that is killed and reaped after timeout on Windows/Ubuntu. No second application is installed or visible.
- The original in-process `poll_lab_collector` is retained only for direct test compatibility, **not used** in FastAPI. This is laboratory process supervision, **not** a production-certified Windows Job Object/service: parent crash orphan handling, process multi-instance locks, ACL hardening, packaged executable, malicious local administrator and real-device drivers remain OPEN. No patient binding, server receipt, transport or clinical upload.
- CI for the exact new HEAD must pass before treating these corrections as verified. The independent 5-MAJOR FAIL is **not** overturned by this internal implementation, and a fresh independent reviewer must reassess F01/F04.


## F01 native Windows proof correction — 2026-10-17
The first native Windows CI [run #39013786582](https://github.com/hraaaaf/Digital_crown/actions/runs/39013786582) demonstrated that a watched directory **could be renamed despite a handle opened without FILE_SHARE_DELETE**. That initial handle-pin idea was **not** a valid confinement proof. We therefore **revert the pin abstraction instead of hiding or skipping the failing test**. `scan_once` performs strict identity/reparse checks again immediately **after reading** and around spool writes; a new test performs an actual mid-read watch-folder replacement and requires fail-closed without a DB item. This detects several races but is **not full Windows kernel-level confinement**. F01 remains MAJOR/OPEN until directory-relative handle-based opens and ACL isolation are independently reviewed and tested. The old claim in the preceding experimental-batch paragraph is superseded by this correction.
