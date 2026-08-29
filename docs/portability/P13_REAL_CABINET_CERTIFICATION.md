# P13 — Real Cabinet Certification

**Status:** PREPARED — real-hardware execution required. **0 EP credited.**

## Goal
Prove the critical Digital Crown cabinet flow on real physical Windows and macOS machines, including first launch, cabinet continuity, off-machine recovery and controlled failures, without re-labelling CI simulation as cabinet evidence.

## Success
P13 closes only when the same release candidate is proved on:

1. one physical Windows x64 cabinet-class machine;
2. one physical Apple Silicon Mac;
3. real installation from the release package for each OS;
4. first launch and subsequent normal launch;
5. one synthetic cabinet flow with no real patient data;
6. real off-machine backup destination (USB/removable storage, NAS mount, or independently administered equivalent);
7. restore/migration across Windows ↔ macOS where the portable SQLite/SQLCipher contract applies;
8. authenticated update and recovery behavior on the installed systems;
9. controlled failure cases with fail-closed behavior;
10. evidence bundle containing machine, package, runtime, data and recovery proofs.

No partial EP is credited.

## P12 evidence that must NOT be repeated as fake “real cabinet” proof
P12 already owns technical CI evidence for runtime/single-instance, frozen packaging, scientific fail-closed behavior, clean hosted runners, DR, update/rollback, launcher recovery and the conservative hardware matrix.

P13 consumes that evidence. It only adds what CI cannot honestly prove: physical machine behavior, human first-launch ceremony and an operational off-machine backup medium.

## Physical targets

### Windows
Record:
- machine model;
- CPU/architecture;
- Windows edition + exact build;
- free disk before install;
- package filename + SHA-256;
- Digital Crown public signing certificate fingerprint/trust state used for this known machine.

P13 does not claim Microsoft SmartScreen reputation.

### macOS
Record:
- Mac model;
- Apple Silicon family;
- macOS exact version/build;
- free disk before install;
- DMG filename + SHA-256;
- bundle ID/version after install.

Expected private-distribution truth:
- strict ad-hoc codesign integrity must verify;
- default Gatekeeper rejection may occur;
- administrator-controlled first launch / `Open Anyway` must be performed and evidenced once;
- subsequent normal launch must succeed.

P13 does not claim Developer ID, notarization, stapling or Apple approval.

## Synthetic cabinet fixture
Never use real patient data for certification.

Create one deterministic synthetic cabinet containing:
- one owner/admin;
- one synthetic patient;
- one synthetic treatment/note or equivalent persisted clinical record;
- one deterministic media/document sentinel with recorded SHA-256;
- one deterministic DB marker/value that can be checked after migration/restore.

Record the pre-migration values and hashes.

## Certification sequence

### A. Clean install and first launch — each OS
1. start from a machine with no Digital Crown user-data directory;
2. record machine/OS identity;
3. verify package SHA-256 against the signed release manifest;
4. install package;
5. complete the platform-specific first-launch ceremony;
6. verify the real frozen application reaches loopback `/health` with `status=ok` and `db=ok`;
7. close and relaunch normally;
8. launch a second instance and verify the existing healthy instance is reused/focused rather than creating a second cabinet runtime;
9. create/verify the synthetic cabinet fixture.

### B. Real off-machine DR
For the first source machine:
1. connect/mount the real off-machine destination;
2. record destination type and mount/path identity without secrets;
3. create the production `.dcbundle` + `.sha256` sidecar;
4. verify bundle SHA-256 and sidecar;
5. physically disconnect/unmount or otherwise remove source-machine access to the destination after snapshot completion;
6. retain the recovery secret independently from the source workstation.

A second directory on the source internal disk is not acceptable evidence.

### C. Cross-OS recovery
1. move/access the independently stored bundle from the opposite OS machine;
2. verify the exact SHA-256 before conversion;
3. convert through the production portable → Guided Restore path;
4. execute the restore through the installed/frozen Digital Crown runtime;
5. verify post-restore `/health`;
6. verify DB marker/value;
7. verify media/document sentinel SHA-256;
8. verify source machine secrets were not transported and destination-local identity/secrets remain valid;
9. repeat in the reverse OS direction if the same candidate and operational setup allow it.

### D. Update / recovery on installed systems
For each OS:
1. install/current baseline;
2. apply the authenticated next-version package through the certified update path;
3. verify target version + package self-test + `/health`;
4. execute one controlled interrupted/failing update drill;
5. verify package/data rollback returns to a healthy cabinet state.

Do not provision new public-trust claims solely for P13.

### E. Controlled failures
Must demonstrate, without risking production data:
- wrong migration secret rejected;
- tampered bundle rejected;
- unavailable/offline DR destination reported fail-closed;
- insufficient-space simulation or safely bounded equivalent if practical on the physical target;
- unready second instance opens/reaches the recovery path instead of silently creating another runtime;
- interrupted restore/update leaves a recoverable, truthful state.

If a physical destructive simulation is unsafe, record the reason and use the already-certified CI failure proof instead; do not pretend the physical scenario was executed.

## Hardware boundary
P8 remains authoritative. P13 does not promote RVG, pano, cephalo, DICOM, TWAIN/WIA/Image Capture, USB/serial, scanners or cameras to `SUPPORTED` unless an actual Digital Crown integration and real-device test exist for every claimed OS.

File-import paths may be exercised with synthetic files. That is not direct-device certification.

## Evidence bundle
For each machine/direction retain:
- timestamp;
- OS/model/architecture;
- package filename, version, SHA-256;
- signing/integrity truth appropriate to platform;
- first-launch result;
- `/health` result before and after migration/update;
- single-instance result;
- synthetic DB marker before/after;
- media sentinel SHA-256 before/after;
- DR bundle filename/SHA-256/sidecar result;
- destination type and non-secret path/mount description;
- restore/update job result;
- controlled failure results;
- screenshots/log excerpts only where they add observable proof;
- operator name/initials and explicit PASS/FAIL per gate.

Never include recovery secrets, private signing keys, PFX passwords or real patient data in the evidence bundle.

## Closure gate
P13 is CLOSED only when:
- Windows physical evidence = PASS;
- macOS physical evidence = PASS;
- real off-machine DR evidence = PASS;
- cross-OS cabinet continuity = PASS where applicable;
- no unsupported platform/hardware claim was introduced;
- all evidence references are committed to the canonical closeout without secrets.

Until then: **P13 = 0 EP**.

## Human gate
The remaining work cannot be completed by GitHub-hosted CI alone. It requires access to the two physical target machines and the real off-machine storage medium, plus the administrator action needed for private macOS first launch.

No Vercel.
