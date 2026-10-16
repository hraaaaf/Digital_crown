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
