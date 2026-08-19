# Digital Crown — Portability & Launcher Windows + macOS

Status: **CANONICAL / VALIDATED / NOT STARTED**

This document is the canonical compass for the future Portability & Launcher chantier. It is intentionally recorded before execution and must not be interpreted as authorization to start implementation.

## Global goal

Deliver **one Digital Crown product** with a shared core, installable and operable on Windows and macOS, with reliable startup, portable cabinet data, safe update/recovery, and an explicitly certified hardware compatibility matrix.

## Global success criteria

A clean installation on Windows and macOS can launch Digital Crown, operate a cabinet, restart safely, back up/restore, and update without undocumented functional divergence.

## Final proof

End-to-end certification on real Windows and macOS machines, including cross-platform cabinet migration.

## Effort scale

Effort Points (EP) are relative complexity units, not hours.

- 1 EP: micro-change
- 3 EP: small lot
- 5 EP: medium lot
- 8 EP: substantial lot
- 13 EP: heavy/transversal lot
- 21 EP: very heavy / high uncertainty

---

## P0 — Baseline & portability contract — 5 EP

### Goal
Lock the target and the complete portability boundary before architecture changes.

### Scope
1. Final inventory of Windows dependencies.
2. Inventory of filesystem paths.
3. Inventory of processes, ports and browser-opening behavior.
4. Inventory of installation/uninstallation mechanisms.
5. Inventory of secrets, licensing and machine identity.
6. Inventory of AI/native model dependencies.
7. Inventory of peripherals, drivers and SDKs.
8. Define behavior that must be identical on Windows/macOS.
9. Define acceptable OS-specific differences.
10. Create the initial certification matrix.
11. Record current test baseline.
12. Record BEFORE architecture documentation.

### Success
No known OS dependency remains implicitly hidden in the shared core.

### Proof
Exhaustive code/dependency/OS/action matrix.

---

## P1 — OS abstraction layer — 13 EP

### Goal
Remove direct Windows knowledge from the shared product core.

### Scope
Create a single platform contract covering paths, runtime, process control, browser/app opening, autostart, filesystem, device identity and platform metadata, with Windows and macOS implementations.

1. Centralize OS detection.
2. Extract APPDATA/LOCALAPPDATA handling.
3. Define macOS data/config/log/runtime locations.
4. Centralize config, logs, cache, runtime and cabinet data paths.
5. Remove Windows paths from business logic.
6. Isolate Windows autostart.
7. Add macOS autostart adapter capability.
8. Abstract browser/application opening.
9. Abstract OS process/command execution.
10. Normalize filesystem permissions.
11. Add adapter unit tests.
12. Add guards against unmanaged OS-specific dependencies.

### Success
Digital Crown core no longer directly depends on Windows-specific APIs or paths.

### Proof
Tests + static search + Windows regression proof.

---

## P2 — Runtime Supervisor / Launcher V2 — 13 EP

### Goal
Create one authoritative, cross-platform lifecycle supervisor.

### Scope
1. Single launch authority.
2. Remove duplicate run.py/backend browser lifecycle.
3. Single canonical port source.
4. Single-instance lock.
5. Configuration loading/validation.
6. Database initialization.
7. Backend start.
8. Real health readiness check.
9. Controlled timeout.
10. Open UI only after READY.
11. Clean shutdown.
12. Backend crash handling.
13. Launcher logs.
14. Actionable error codes/states.
15. Recoverable startup failure UX hooks.
16. Launch/stop/restart/crash tests.

### Success
Two competing Digital Crown runtime instances or UI-on-dead-backend states are prevented.

### Proof
Runtime tests with injected failure scenarios.

---

## P3 — Cabinet data portability — 13 EP

### Goal
Make the cabinet belong to Digital Crown, not to a specific computer or OS.

### Scope
Create an OS-independent Cabinet Bundle including, as applicable:
1. SQLCipher database.
2. Media.
3. Radiographs.
4. Documents.
5. Portable cabinet settings.
6. Metadata.
7. Schema version.
8. Manifest.
9. Checksums/integrity.
10. Controlled export.
11. Controlled import.
12. Pre-restore validation.
13. Schema migration.
14. Incompatibility handling.
15. Restore rollback.
16. Windows → Windows.
17. macOS → macOS.
18. Windows → macOS.
19. macOS → Windows.

Machine-bound secrets/licensing material must not be naively copied as cabinet data.

### Success
A cabinet can move between supported machines without losing clinical data integrity.

### Proof
Windows cabinet → backup/export → macOS restore → clinically usable identical cabinet, then reverse direction.

---

## P4 — Cross-platform licence, secrets & machine identity — 8 EP

### Goal
Keep licensing secure and stable on both OSes without coupling clinical data to one machine.

### Scope
1. Audit current machine fingerprint.
2. Create DeviceIdentityProvider abstraction.
3. Windows implementation.
4. macOS implementation.
5. Define identity stability contract.
6. Test reboot.
7. Test Digital Crown update.
8. Test reasonable OS update.
9. Define hardware-change behavior.
10. Separate licensing from cabinet data.
11. Secure local secret storage.
12. Test existing Firebase online/offline behavior as applicable.
13. Fail closed without blocking cabinet recovery.

### Success
Licensing behaves coherently on both platforms and does not endanger cabinet portability.

### Proof
Validated Windows/macOS licence/device scenario matrix.

---

## P5 — Scientific runtime & native dependencies on macOS — 13 EP

### Goal
Prove real scientific/runtime parity, especially on Apple Silicon.

### Scope
Certify, where used:
1. Python runtime.
2. SQLCipher.
3. OpenCV.
4. ONNX Runtime.
5. PyTorch if still required.
6. Pillow.
7. PDF generation stack.
8. Cryptography stack.
9. Cephalometric models.
10. Panoramic models.
11. Frozen resource/model loading.
12. Apple Silicon arm64 architecture.
13. Memory behavior.
14. Model startup.
15. Real inference.
16. Windows/macOS numerical comparison when relevant.

### Success
Scientific functions produce equivalent acceptable outputs on Windows and Apple Silicon.

### Proof
Golden dataset executed on both OSes with predefined tolerances.

---

## P6 — Industrialized Windows packaging — 8 EP

### Goal
Make Windows distribution deterministic and production-grade while keeping the shared architecture.

### Scope
1. Reproducible build.
2. Clean PyInstaller configuration.
3. Controlled bundled resources.
4. Canonical versioning.
5. Installer.
6. Shortcuts.
7. Autostart if retained.
8. Uninstall behavior.
9. Explicit preservation of cabinet data.
10. Upgrade over existing installation.
11. Clean install.
12. Installer logs.
13. Signing where applicable.
14. Clean-Windows tests.

### Success
Install/update/uninstall are deterministic and preserve intended cabinet data.

### Proof
Certified installation on a clean Windows machine.

---

## P7 — Native macOS packaging — 13 EP

### Goal
Deliver a normal, signed/notarized macOS application without Terminal workarounds.

### Scope
1. Build Digital Crown.app.
2. Apple Silicon arm64 target.
3. Bundle Python/backend.
4. Bundle frontend.
5. Bundle models/resources.
6. .icns icon.
7. Bundle metadata.
8. Application Support paths.
9. Logs.
10. Permissions.
11. Lifecycle integration.
12. Autostart if retained.
13. DMG or PKG.
14. Developer ID signing.
15. Hardened runtime if required.
16. Apple notarization.
17. Stapling.
18. Clean installation.
19. Documented uninstall.
20. Upgrade from previous version.
21. Gatekeeper validation.

### Success
A normal macOS user can install and launch Digital Crown without bypassing Gatekeeper or using Terminal.

### Proof
Clean Mac installation of exact signed/notarized artifact.

---

## P8 — Hardware & peripheral compatibility — 21 EP

### Goal
Know and prove what hardware is truly supported on each OS.

### Scope
Build a canonical matrix: Peripheral | Windows | macOS | Driver | SDK | Alternative mode.

Test/qualify as relevant:
1. RVG sensors.
2. Direct radiographic acquisition.
3. Import from manufacturer software.
4. USB devices.
5. Relevant scanners.
6. Printers.
7. PDF printing.
8. Cameras if used.
9. Network peripherals.
10. macOS permissions.
11. ARM compatibility of vendor SDKs.
12. File-import fallback where direct acquisition is impossible.

Every device must be explicitly classified: SUPPORTED / LIMITED / FILE-IMPORT / UNSUPPORTED.

### Success
Hardware compatibility is known, reproducible and not inferred from software-only compatibility.

### Proof
Tests on real hardware where available, or explicit manufacturer evidence where physical testing is impossible, with the distinction recorded.

---

## P9 — Backup, Recovery & Disaster Recovery — 8 EP

### Goal
Make computer loss or runtime failure recoverable without losing the cabinet.

### Scope
1. Automatic backup.
2. Manual backup.
3. Rotation.
4. Integrity validation.
5. Encryption.
6. Restore.
7. Simulated corruption.
8. Unavailable disk.
9. Insufficient space.
10. Interrupted backup.
11. Interrupted restore.
12. Legacy-format migration.
13. Recovery onto a new machine.
14. Windows → macOS recovery.
15. macOS → Windows recovery.
16. Cabinet recovery runbook.

### Success
Loss of one computer does not imply loss of the cabinet.

### Proof
Complete disaster-recovery drill.

---

## P10 — Cross-platform Update Engine — 13 EP

### Goal
Provide safe updates with verification, migration and automatic rollback.

### Scope
1. Canonical versioning.
2. New-version detection.
3. Signed update manifest.
4. Authenticity verification.
5. Download.
6. Checksum verification.
7. Pre-update backup.
8. Preflight.
9. Runtime shutdown.
10. Apply Windows update.
11. Apply macOS update.
12. Database migration.
13. Restart.
14. Health check.
15. Installed-version validation.
16. Automatic rollback.
17. Incompatible downgrade protection.
18. Logs.
19. Network-loss scenario.
20. Corrupt-package scenario.

### Success
An update cannot be declared successful until the new runtime is healthy.

### Proof
N → N+1 update plus injected failure and successful rollback on both OSes.

---

## P11 — Launcher & Recovery UX — 8 EP

### Goal
Expose lifecycle/recovery states clearly without exposing technical internals to normal cabinet users.

### Mandatory visual protocol
Before implementation: BEFORE captures, written visual goal, mockup/reference. After implementation: same viewports, AFTER captures, visual comparison, tests and score.

### Scope
Support truthful states such as:
- Starting
- Preparing
- Updating
- Restoring
- Recoverable error
- Critical error
- Digital Crown ready

Then implement:
1. Mockup.
2. UI implementation.
3. Actionable messages.
4. Real progress only, never fake progress.
5. Retry.
6. Recovery entrypoints.
7. Technical logs accessible without polluting normal UX.
8. Accessibility.
9. Windows/macOS visual coherence.
10. AFTER captures on same targets.
11. Visual scoring.

### Success
Common failures are understandable and recoverable without Terminal/console use.

### Proof
UX tests + BEFORE/mockup/AFTER + visual score.

---

## P12 — CI & certification matrix — 13 EP

### Goal
Prevent platform regressions and certify exact build artifacts.

### Scope
Create Windows/macOS arm64 coverage for:
1. Core.
2. Backend.
3. Frontend.
4. SQLCipher.
5. Launcher.
6. Models.
7. Backup.
8. Restore.
9. Packaging.
10. Upgrade.
11. Recovery.
12. Platform-specific dependency guards.
13. Certification artifacts/reports.

Tests should include unit, integration, runtime, frozen build, artifact smoke, scientific golden, backup/restore, update and reasonable regression coverage.

### Success
A shared change cannot silently break one supported OS.

### Proof
Green certification matrix plus native artifact validation.

---

## P13 — Real cabinet certification — 13 EP

### Goal
Prove real end-to-end cabinet parity across supported platforms.

### Scope
Windows clean-machine flow:
install → licence → cabinet → patient → radiograph → analysis → document → backup → restart.

macOS clean-machine flow:
same critical flow.

Cross-platform migration:
Windows → backup/export → macOS restore, then macOS → backup/export → Windows restore.

Failure scenarios include, where safely testable:
- backend crash
- controlled DB lock/corruption
- interrupted update
- Firebase network unavailable
- missing/corrupt model
- insufficient disk space

### Success
Critical clinical workflow is equivalent on both platforms within explicitly documented hardware limitations.

### Proof
Reproducible certification record tied to exact artifacts/commits.

---

## P14 — Closeout & permanent compass — 5 EP

### Goal
Close the chantier with canonical documentation matching the certified HEAD.

### Scope
Update as relevant:
1. README.
2. Architecture docs.
3. Roadmap.
4. OS support matrix.
5. Hardware matrix.
6. Backup/recovery runbook.
7. Windows installation guide.
8. macOS installation guide.
9. Troubleshooting.
10. Release process.
11. Update process.
12. Governance for OS-specific dependencies.
13. Remove obsolete legacy paths after proof.
14. Verify docs ↔ code consistency.
15. Final certification record.
16. Planned Git closeout operations.

### Success
A future maintainer can preserve Windows/macOS compatibility without rediscovering architecture decisions.

### Proof
Canonical docs consistent with certified HEAD and final test evidence.

---

## Canonical effort summary

| Lot | Effort |
|---|---:|
| P0 — Baseline & portability contract | 5 EP |
| P1 — OS abstraction layer | 13 EP |
| P2 — Runtime Supervisor / Launcher V2 | 13 EP |
| P3 — Cabinet data portability | 13 EP |
| P4 — Licence, secrets & machine identity | 8 EP |
| P5 — Scientific runtime & native dependencies | 13 EP |
| P6 — Windows packaging | 8 EP |
| P7 — macOS packaging | 13 EP |
| P8 — Hardware & peripherals | 21 EP |
| P9 — Backup / Recovery / DR | 8 EP |
| P10 — Cross-platform Update Engine | 13 EP |
| P11 — Launcher & Recovery UX | 8 EP |
| P12 — CI & certification matrix | 13 EP |
| P13 — Real cabinet certification | 13 EP |
| P14 — Closeout | 5 EP |
| **TOTAL** | **162 EP** |

The 162 EP total is a relative complexity budget, not an hour estimate. P8 has the highest uncertainty because manufacturer drivers/SDKs can materially change scope.

## Canonical execution order

P0 → P1 → P2 → P3 → P4 → P5

Then parallelization is allowed where dependencies permit:

P6 Windows packaging + P7 macOS packaging + P8 Hardware

Then:

P9 → P10 → P11 → P12 → P13 → P14

## Gates

### Gate A — CORE PORTABLE
After P5: the same shared core actually runs and produces acceptable scientific/runtime behavior on Windows and macOS.

### Gate B — PRODUCT PORTABLE
After P10: installation, cabinet data portability, recovery and update mechanisms exist on both platforms.

### Gate C — CABINET CERTIFIED
After P13: real cabinet critical flows and cross-platform migration are proven.

## Architectural invariants

1. **One product, one shared core.** No functional Windows/macOS fork.
2. OS-specific behavior must live behind explicit platform adapters.
3. Feature parity and hardware parity are different claims and must be certified separately.
4. Cabinet data must be portable independently of machine-bound licensing secrets.
5. One lifecycle supervisor owns startup/readiness/shutdown.
6. Update success requires post-update health validation; failure requires safe rollback.
7. Cross-platform recovery is a first-class requirement, not an optional export feature.
8. No platform may be declared supported without native certification evidence.
9. UI/UX work follows the mandatory BEFORE → written goal → mockup → implementation → AFTER → visual score protocol.
10. No Vercel deployment is part of this chantier without explicit user authorization.

## Current execution state

**NOT STARTED.**

The roadmap is stored now only as the future canonical compass. Execution must wait until the currently active Digital Crown chantiers are completed and the Portability & Launcher chantier is explicitly resumed.
