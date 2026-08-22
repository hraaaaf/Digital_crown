# Digital Crown — Portability & Launcher Windows + macOS

Status: **CANONICAL / VALIDATED / P0 CLOSED / P1 NOT STARTED**

This document is the canonical compass for the Portability & Launcher chantier. Product implementation must not start merely because this file exists. The roadmap was validated by product, and P0 was later executed as a documentation/audit-only lot on baseline `a25893c7c1c3bb5bbecd6fb8ff54a0d81ab440a0`.

Canonical P0 evidence: `docs/portability/PORTABILITY_P0_BASELINE.md`.

## Global goal

Deliver **one Digital Crown product** with one shared product core, installable and operable on Windows and macOS, with reliable startup, portable cabinet data, safe update/recovery, and an explicitly certified hardware compatibility matrix.

## Global success

A clean installation on Windows and macOS can launch Digital Crown, operate the same critical cabinet workflows, restart safely, back up/restore, update, and recover without undocumented functional divergence.

## Final proof

End-to-end certification on real Windows and macOS machines, including Windows → macOS and macOS → Windows cabinet migration.

## Non-negotiable architecture rule

**No functional Windows/macOS fork.** Business, clinical, document, data and scientific semantics belong to the shared core. Only genuinely OS-dependent integration belongs to platform adapters.

## Effort scale

Effort Points (EP) are relative complexity units, not hours.

- 1 EP — micro change
- 3 EP — small lot
- 5 EP — medium lot
- 8 EP — substantial lot
- 13 EP — heavy/transversal lot
- 21 EP — very heavy/high uncertainty

Total roadmap: **162 EP**.

---

## P0 — Baseline & portability contract — 5 EP — CLOSED

### Goal
Lock the current portability boundary and the Windows/macOS parity contract before architecture changes.

### Scope
1. Inventory Windows-specific dependencies.
2. Inventory filesystem/config/log/data paths.
3. Inventory processes, ports and browser-launch behavior.
4. Inventory installation/uninstallation/autostart mechanisms.
5. Inventory secrets and licensing storage.
6. Inventory native/scientific dependencies.
7. Inventory direct hardware/driver/SDK integrations visible in the repository.
8. Define behavior that must remain identical across OSes.
9. Define acceptable OS-specific differences.
10. Establish the initial certification matrix.
11. Record the current test/CI evidence boundary.
12. Record the BEFORE architecture.

### Success
Known OS dependencies are explicit and mapped to a later lot; unknown hardware/vendor support is explicitly tracked rather than silently assumed.

### Proof
`docs/portability/PORTABILITY_P0_BASELINE.md` on the exact audited baseline.

---

## P1 — OS abstraction layer — 13 EP

### Goal
Remove direct OS-specific integration from the shared product core.

### Steps
1. Centralize OS detection.
2. Define one platform contract for user-data/config/log/runtime paths.
3. Implement Windows paths.
4. Implement native macOS paths (`~/Library/Application Support/...` and related locations as selected).
5. Isolate autostart integration.
6. Abstract browser/application opening.
7. Abstract process and OS-command execution where needed.
8. Normalize filesystem permissions and atomic-file behavior.
9. Keep business/clinical code free of Windows/macOS branching.
10. Add Windows/macOS adapter unit tests.
11. Add static guards against unmanaged OS-specific dependencies.
12. Re-run existing Windows regression gates.

### Success
The shared core no longer directly depends on Windows-only paths or commands.

### Proof
Static dependency guard + adapter tests + Windows regression proof.

---

## P2 — Runtime Supervisor / Launcher V2 — 13 EP

### Goal
Create one authoritative cross-platform lifecycle supervisor.

### Steps
1. Keep a single launch authority.
2. Establish one canonical host/port source.
3. Add single-instance locking.
4. Load and validate configuration before service start.
5. Initialize/validate the local database safely.
6. Start the backend under supervisor control.
7. Replace fixed-delay browser launch with a real readiness/health contract.
8. Open the UI only after READY.
9. Define controlled startup timeout.
10. Handle clean shutdown.
11. Handle backend crash and restart policy explicitly.
12. Persist launcher/runtime logs.
13. Expose actionable error states/codes.
14. Provide recovery hooks for the future launcher UX.
15. Test launch/stop/restart/crash/port-conflict scenarios.

### Current P0 correction
The previous historical audit found duplicate browser-opening logic. On P0 baseline `a25893c...`, backend `main.py` no longer contains that second opener; `run.py` remains the launcher authority but still uses a fixed two-second delay. P2 must solve the current problem, not revive a deleted one.

### Success
No competing runtime instance and no user UI opened against a backend that has not reached READY.

### Proof
Runtime tests with injected startup and crash failures.

---

## P3 — Cabinet data portability — 13 EP

### Goal
Make the cabinet portable independently of the computer and OS.

### Steps
1. Define the canonical Cabinet Bundle format.
2. Include SQLCipher database data as applicable.
3. Include media/radiographs/documents covered by the cabinet contract.
4. Include portable settings only.
5. Add bundle metadata and schema version.
6. Add manifest and integrity checksums.
7. Implement controlled export.
8. Implement controlled import/preflight.
9. Validate schema compatibility before mutation.
10. Support schema migration where required.
11. Reject incompatible/corrupt bundles fail-closed.
12. Create a verified rescue point before restore.
13. Roll back failed restore.
14. Certify Windows → Windows.
15. Certify macOS → macOS.
16. Certify Windows → macOS.
17. Certify macOS → Windows.
18. Explicitly exclude machine-local secrets from naive cabinet copying.

### Success
A cabinet can move between supported machines without loss of clinical integrity.

### Proof
Cross-platform restore with data-integrity comparison.

---

## P4 — Licence & local secrets cross-platform — 8 EP

### Goal
Keep licensing and local secrets secure on both OSes without coupling clinical data to one machine.

### P0 correction
The current `LicenseStore` no longer uses the historical hardware fingerprint/DPAPI design. It stores `license.dat` plus a local Fernet secret under `AppPaths`. Therefore this lot must first preserve the current verified model and only introduce device identity if a real licensing requirement proves it necessary.

### Steps
1. Freeze the current licence and local-secret contract.
2. Classify each secret as cabinet-portable, machine-local, or regenerable.
3. Define Windows secure local-storage semantics.
4. Define macOS secure local-storage semantics.
5. Decide whether OS-native key stores are required from a threat-model proof, not preference.
6. Define migration/re-activation behavior when moving a cabinet to a new machine.
7. Validate licence signature/activation behavior on both OSes.
8. Validate offline behavior where supported.
9. Test reboot and Digital Crown update.
10. Test failed/corrupt local secret storage.
11. Ensure licensing failure never destroys or strands recoverable clinical data.

### Success
Licensing remains fail-closed where required while cabinet recovery remains possible and explicit.

### Proof
Windows/macOS licence + secret migration scenario matrix.

---

## P5 — Scientific runtime & native dependencies on macOS — 13 EP

### Goal
Prove real scientific/runtime parity, especially on Apple Silicon.

### Steps
Certify, where actually used:
1. Python runtime.
2. SQLCipher/native SQLite crypto stack.
3. OpenCV.
4. ONNX Runtime.
5. TensorFlow and/or PyTorch only where reachable.
6. Pillow/image stack.
7. PDF stack including ReportLab/PyMuPDF/WeasyPrint as reachable.
8. Cryptography stack.
9. Cephalometric models.
10. Panoramic models.
11. Frozen/bundled resource loading.
12. Apple Silicon arm64.
13. Memory behavior.
14. Model startup.
15. Real inference.
16. Windows/macOS numerical comparison with predefined tolerances.
17. Remove or quarantine unreachable native dependencies rather than certifying dead weight.

### Success
Reachable scientific functions produce equivalent acceptable results on Windows and Apple Silicon.

### Proof
Golden datasets on both OSes with declared tolerances.

### Gate A — CORE PORTABLE
P0–P5 must be closed before claiming the core portable.

---

## P6 — Industrialized Windows packaging — 8 EP

### Goal
Make Windows distribution deterministic and production-grade.

### Steps
1. Reproducible Windows build.
2. Clean PyInstaller configuration or approved successor.
3. Controlled resource/model bundling.
4. Canonical version source.
5. Installer build.
6. Start Menu/desktop integration.
7. Autostart only if product decision retains it.
8. Explicit uninstall semantics.
9. Preserve cabinet data intentionally.
10. Upgrade over existing installation.
11. Clean install.
12. Installer/runtime logs.
13. Windows code signing as required for distribution policy.
14. Clean-Windows certification.

### Success
Install/upgrade/uninstall are deterministic and preserve intended data.

### Proof
Exact signed/releasable artifact installed on a clean Windows machine.

---

## P7 — Native macOS packaging — 13 EP

### Goal
Deliver a normal macOS application without Terminal or Gatekeeper bypasses.

### Steps
1. Produce `Digital Crown.app`.
2. Target Apple Silicon arm64 first.
3. Bundle the shared backend/runtime.
4. Bundle frontend/resources/models.
5. Use native macOS app/config/data locations.
6. Provide correct `.icns` and bundle metadata.
7. Handle filesystem/network permissions explicitly.
8. Integrate lifecycle/autostart only as approved.
9. Choose DMG or PKG based on install requirements.
10. Configure Developer ID signing.
11. Configure hardened runtime/entitlements as required.
12. Notarize with Apple.
13. Staple notarization ticket where applicable.
14. Validate Gatekeeper.
15. Clean install.
16. Upgrade from previous version.
17. Document uninstall and retained-data behavior.
18. Decide Intel Mac support separately from Apple Silicon based on product need/evidence.

### Success
A normal Mac user installs and launches Digital Crown without command-line workarounds.

### Proof
Clean-Mac installation of the exact signed/notarized artifact.

---

## P8 — Hardware & peripheral compatibility — 21 EP

### Goal
Know and prove what clinical/peripheral hardware is actually supported on each OS.

### Steps
Build a canonical matrix: `Peripheral | Windows | macOS | Driver | SDK | Mode | Evidence`.

Qualify as relevant:
1. RVG sensors.
2. Direct radiographic acquisition.
3. Import from manufacturer software.
4. USB devices.
5. Relevant scanners.
6. Printers.
7. PDF printing.
8. Cameras if used.
9. Network peripherals.
10. macOS privacy/USB/network permissions.
11. Apple Silicon availability of vendor SDKs.
12. File-import fallback where direct acquisition is unavailable.
13. Classify every item `SUPPORTED`, `LIMITED`, `FILE-IMPORT`, or `UNSUPPORTED`.
14. Separate vendor claim from Digital Crown tested proof.

### Success
No hardware compatibility is implied without an explicit support classification.

### Proof
Real-device tests where available; authoritative vendor evidence where physical testing is unavailable, labelled accordingly.

---

## P9 — Backup, Recovery & Disaster Recovery — 8 EP

### Goal
Make machine loss or runtime failure recoverable without losing the cabinet.

### Steps
1. Canonical automatic backup.
2. Manual backup.
3. Rotation/retention.
4. Integrity verification.
5. Encryption/key-management contract.
6. Restore preflight.
7. Corruption simulation.
8. Insufficient-disk simulation.
9. Interrupted backup.
10. Interrupted restore.
11. Old-format migration.
12. New-machine recovery.
13. Windows → macOS recovery.
14. macOS → Windows recovery.
15. Cabinet recovery runbook.

### Success
Loss of one computer does not imply loss of the cabinet.

### Proof
Documented disaster-recovery drill.

---

## P10 — Cross-platform Update Engine — 13 EP

### Goal
Make updates authenticated, verifiable and automatically recoverable.

### Steps
1. Canonical versioning.
2. Update manifest.
3. Authenticity/signature verification.
4. Download and checksum verification.
5. Pre-update backup/rescue point.
6. Preflight compatibility checks.
7. Controlled runtime stop.
8. Apply Windows update.
9. Apply macOS update.
10. Run DB/schema migration if required.
11. Restart.
12. Health/readiness validation.
13. Confirm effective version.
14. Automatic rollback on failure.
15. Protect against incompatible downgrade.
16. Persist update logs/audit.
17. Test interrupted network/download.
18. Test corrupted package.
19. Test failed migration/startup.

### Success
An update is not considered successful until the new runtime is healthy.

### Proof
N → N+1 plus injected failure and rollback on both OSes.

### Gate B — PRODUCT PORTABLE
P0–P10 must be closed before claiming the distributed product portable.

---

## P11 — Launcher & Recovery UX — 8 EP

### Goal
Make startup/update/recovery understandable without exposing technical internals.

### Mandatory visual protocol
BEFORE captures → written Goal → mockup/reference → implementation → AFTER same viewports → BEFORE/mockup/AFTER validation → visual score.

### States to design
1. Starting.
2. Preparing/migrating.
3. Updating.
4. Restoring.
5. Recoverable error.
6. Critical error.
7. Ready.

### Steps
1. Create BEFORE on both OSes.
2. Define user-facing state/message contract.
3. Produce mockup.
4. Implement shared state machine UI.
5. Expose progress only when backed by real state.
6. Add retry/recovery actions.
7. Keep technical logs accessible but not dominant.
8. Validate accessibility.
9. Validate Windows/macOS consistency.
10. Capture AFTER on same targets.
11. Score visual result.

### Success
Common startup/recovery failures are understandable and actionable without Terminal/console use.

### Proof
UX tests + BEFORE/mockup/AFTER + score.

---

## P12 — CI & certification matrix — 13 EP

### Goal
Prevent one OS from silently breaking when shared code changes.

### Matrix
At minimum:
`Core | Backend | Frontend | SQLCipher | Launcher | Scientific runtime | Backup | Restore | Packaging | Upgrade | Recovery`
against `Windows` and `macOS arm64`.

### Steps
1. Unit tests.
2. Integration tests.
3. Runtime startup tests.
4. Frozen/bundled builds.
5. Packaging artifacts.
6. Installation smoke tests where CI/runner allows.
7. Scientific golden tests.
8. Backup/restore tests.
9. Update/rollback tests.
10. OS-specific static guards.
11. Artifact retention and provenance.
12. Exact-HEAD certification reports.
13. Keep expensive native/hardware tests separated from ordinary PR feedback where needed.

### Success
Shared changes cannot silently remove Windows/macOS support without a failing gate or explicit unsupported classification.

### Proof
Green exact-HEAD certification matrix plus native-machine evidence where CI runners are insufficient.

---

## P13 — Real cabinet certification — 13 EP

### Goal
Certify the complete critical cabinet story on real supported machines.

### Windows journey
Install → activate/authenticate → cabinet → patient → radiography/import → scientific workflow → document → backup → restart.

### macOS journey
Same critical functional journey.

### Migration journeys
1. Windows → bundle/backup → macOS → restore → integrity check.
2. macOS → bundle/backup → Windows → restore → integrity check.

### Failure drills
1. Backend crash.
2. Controlled DB corruption/invalid restore artifact.
3. Interrupted update.
4. Network/auth service unavailable.
5. Missing/corrupt model.
6. Insufficient disk.
7. Port conflict/single-instance case.

### Success
Critical cabinet workflows are equivalent on both supported platforms within explicit documented exceptions.

### Proof
Reproducible certification dossier tied to exact artifacts/commits.

### Gate C — CABINET CERTIFIED
Only after P13 may the chantier claim Windows + macOS cabinet certification.

---

## P14 — Closeout & permanent compass — 5 EP

### Goal
Make cross-platform support maintainable after the chantier ends.

### Steps
1. Update README.
2. Final architecture document.
3. Final roadmap state.
4. OS support matrix.
5. Hardware support matrix.
6. Backup/recovery runbook.
7. Windows install guide.
8. macOS install guide.
9. Troubleshooting guide.
10. Release/update process.
11. Dependency/OS governance rules.
12. Remove superseded launcher/packaging legacy only after proof.
13. Check docs ↔ code consistency.
14. Final certification record.
15. Git closeout/post-merge verification.

### Success
A future contributor can preserve Windows/macOS compatibility without reconstructing the architecture from archaeology.

### Proof
Canonical docs consistent with the final certified HEAD.

---

## Execution order

`P0 → P1 → P2 → P3 → P4 → P5 → (P6 + P7 + P8 where independent) → P9 → P10 → P11 → P12 → P13 → P14`

The three gates are mandatory:
- **Gate A after P5 — CORE PORTABLE**
- **Gate B after P10 — PRODUCT PORTABLE**
- **Gate C after P13 — CABINET CERTIFIED**

## Progress accounting

Roadmap weight = 162 EP. A lot contributes only after its Success and Proof criteria are actually met. Partial work inside an unclosed lot is not automatically credited as completed EP.

Current credited state after the documentation-only P0: **5 / 162 EP = 3.1%**.

## Deployment rule

No Vercel deployment is part of this roadmap without explicit product authorization.
