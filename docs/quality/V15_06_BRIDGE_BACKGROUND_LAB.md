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
