# P13 — Real Cabinet Certification

**Status:** ACTIVE — real-hardware execution required. **0 EP credited.**

## Goal
Prove the critical Digital Crown cabinet flow on real physical Windows and macOS machines, including first launch, cabinet continuity, off-machine recovery and controlled failures, without re-labelling CI simulation as cabinet evidence.

## Success
P13 closes only when the same release candidate is proved on:

1. one physical Windows x64 cabinet-class machine;
2. one physical Apple Silicon Mac;
3. real installation from the release package for each OS;
4. first launch and subsequent normal launch;
5. one deterministic synthetic cabinet, never real patient data;
6. a real off-machine backup destination: USB/removable storage, NAS mount, or independently administered equivalent;
7. Windows ↔ macOS recovery where the portable SQLite/SQLCipher contract applies;
8. authenticated update and rollback on the installed systems;
9. controlled fail-closed cases;
10. one evidence bundle per machine plus a validated Windows/macOS pair.

No partial EP is credited.

## Boundary inherited from P12
P12 already owns CI evidence for runtime/single-instance, frozen packaging, scientific fail-closed behavior, clean hosted runners, DR, update/rollback, launcher recovery and the conservative hardware matrix.

P13 consumes that evidence. It adds only what CI cannot honestly prove: physical machine behavior, human first-launch ceremony, operational off-machine media and installed-cabinet continuity.

P13 does not claim Microsoft SmartScreen reputation, Developer ID, notarization, stapling, Apple approval, or direct dental-device support beyond P8.

## P13-R remote bare-metal rehearsal
A remote bare-metal rehearsal may be used to reduce the remaining physical risk before the final cabinet gate. Canonical runbook: `docs/portability/P13_REMOTE_BARE_METAL_REHEARSAL.md`.

P13-R can exercise real Apple Silicon bare metal and x86 `.metal` hardware, but it never credits P13 EP by itself. In particular, a remote Windows `.metal` host or Windows Server is not accepted as the final cabinet workstation proof.

Final closure is additionally guarded by `scripts/p13_real_cabinet_closure_guard.py`, which requires the final Windows evidence to come from a local Windows 11 cabinet context with USB/removable/NAS off-machine storage. A genuine remote Apple Silicon `.metal` Mac may remain part of the final pair when all required physical observations are actually attested.

## Physical targets

### Windows
Record machine model, CPU/architecture, Windows edition/build, free disk, package filename/SHA-256 and the Digital Crown signer certificate thumbprint/trust state.

### macOS
Record Mac model, Apple Silicon family, macOS exact version/build, free disk, DMG filename/SHA-256 and installed bundle ID/version.

Private-distribution truth remains:
- strict ad-hoc codesign integrity must verify;
- default Gatekeeper rejection may occur;
- administrator-controlled first launch / `Open Anyway` is performed once and evidenced;
- subsequent normal launch succeeds.

## Synthetic cabinet fixture
Create one deterministic synthetic cabinet containing:
- one owner/admin;
- one synthetic patient;
- one persisted synthetic clinical record;
- one deterministic media/document sentinel with SHA-256;
- one deterministic DB marker/value checked after migration/restore.

Never use real patient data.

## Certification sequence

### A. Clean install and first launch — each OS
1. Start with no Digital Crown user-data directory.
2. Record machine/OS identity.
3. Verify package SHA-256 against the signed release manifest.
4. Install the package.
5. Complete the platform-specific first-launch ceremony.
6. Verify the frozen application reaches loopback `/health` with `status=ok` and `db=ok`.
7. Close and relaunch normally.
8. Launch a second instance and verify the healthy existing instance is reused/focused.
9. Create and verify the synthetic cabinet fixture.

### B. Real off-machine DR
1. Connect/mount the real off-machine destination.
2. Record destination type and non-secret mount/path identity.
3. Create the production `.dcbundle` + `.sha256` sidecar.
4. Verify bundle SHA-256 and sidecar.
5. Disconnect/unmount or otherwise remove source-machine access after snapshot completion.
6. Keep the recovery secret independently from the source workstation.

A second directory on the source internal disk is not acceptable evidence.

### C. Cross-OS recovery
1. Access the independently stored bundle from the opposite OS machine.
2. Verify exact SHA-256 before conversion.
3. Convert through the production portable → Guided Restore path.
4. Restore through the installed/frozen Digital Crown runtime.
5. Verify post-restore `/health`.
6. Verify DB marker/value and media sentinel SHA-256.
7. Verify source-machine secrets were not transported and destination-local identity/secrets remain valid.
8. Repeat in the reverse OS direction when the same candidate and setup allow it.

### D. Update / recovery
For each OS:
1. install/current baseline;
2. apply the authenticated next-version package through the certified update path;
3. verify target version + package self-test + `/health`;
4. execute one controlled interrupted/failing update drill;
5. verify package/data rollback returns to a healthy cabinet state.

### E. Controlled failures
Demonstrate without production data:
- wrong migration secret rejected;
- tampered bundle rejected;
- unavailable/offline DR destination fail-closed;
- unready second instance reaches recovery instead of creating another runtime;
- insufficient-space simulation or safely bounded equivalent when practical;
- interrupted restore/update leaves a recoverable truthful state.

If a destructive physical simulation is unsafe, use status `CI_SUBSTITUTED` only for the failure gates permitted by the evidence tool and record the exact upstream CI proof. Core physical gates can never be substituted by CI.

## Operator evidence tool
Canonical tool: `scripts/p13_real_cabinet_evidence.py`.

It automatically records machine/OS facts, package SHA-256, free disk, `/health`, Windows Authenticode truth or macOS codesign/Gatekeeper truth, DR bundle/sidecar SHA-256 and media sentinel SHA-256. It never accepts recovery secrets, private keys or PFX passwords as evidence fields.

### 1. Collect on Windows

```text
python scripts/p13_real_cabinet_evidence.py collect --operator <initials> --release-id <candidate> --package <installer.exe> --health-url <loopback-health-url> --data-path <cabinet-data-path> --dr-bundle <snapshot.dcbundle> --dr-sidecar <snapshot.dcbundle.sha256> --media-sentinel <synthetic-media-file> --output p13-windows.json
```

### 2. Collect on macOS

```text
python3 scripts/p13_real_cabinet_evidence.py collect --operator <initials> --release-id <same-candidate> --package <image.dmg> --app-path <Digital Crown.app> --health-url <loopback-health-url> --data-path <cabinet-data-path> --dr-bundle <snapshot.dcbundle> --dr-sidecar <snapshot.dcbundle.sha256> --media-sentinel <synthetic-media-file> --output p13-macos.json
```

### 3. Record each observed gate

```text
python scripts/p13_real_cabinet_evidence.py set-gate --file <evidence.json> --gate <gate> --status PASS --note <observable-proof>
```

Allowed statuses: `PENDING`, `PASS`, `FAIL`, `NOT_APPLICABLE`, `CI_SUBSTITUTED`.

`CI_SUBSTITUTED` is restricted to controlled failure gates and requires an exact evidence note. It cannot replace clean install, first launch, normal relaunch, single-instance, synthetic fixture, off-machine DR, cross-OS restore, authenticated update or rollback.

### 4. Validate each machine

```text
python scripts/p13_real_cabinet_evidence.py validate --file <evidence.json> --require-pass
```

### 5. Validate the physical pair

```text
python scripts/p13_real_cabinet_evidence.py validate-pair --first p13-windows.json --second p13-macos.json
```

Pair validation requires exactly one Windows file and one macOS file, the same non-empty `release_id`, healthy `/health`, required package trust/integrity evidence, matching DR sidecar, hashed media sentinel and acceptable gate states.

`PASS_ATTESTED` means evidence completeness is machine-validated and the physical observations are operator-attested. It does **not** turn a human observation into CI proof.

### 6. Enforce rehearsal versus closure context

```text
python scripts/p13_real_cabinet_closure_guard.py validate-rehearsal --first p13-windows.json --second p13-macos.json --context p13-context.json
python scripts/p13_real_cabinet_closure_guard.py validate-closure --first p13-windows.json --second p13-macos.json --context p13-context.json
```

`validate-rehearsal` proves only that the remote bare-metal evidence is structurally acceptable. `validate-closure` additionally requires the Windows 11 local cabinet and real USB/removable/NAS boundary.

## Evidence bundle
Retain for each machine/direction:
- timestamp, OS/model/architecture;
- package filename/version/SHA-256;
- platform signing/integrity truth;
- first-launch and relaunch result;
- `/health` before/after migration/update;
- single-instance result;
- synthetic DB marker before/after;
- media sentinel SHA-256 before/after;
- DR bundle SHA-256 + sidecar match;
- destination type and non-secret mount description;
- restore/update/rollback result;
- controlled failure results;
- operator initials and explicit status per gate;
- screenshots/log excerpts only where they add observable proof.

Never include recovery secrets, private signing keys, PFX passwords or real patient data.

## Closure gate
P13 is CLOSED only when:
- Windows physical evidence = PASS;
- macOS physical evidence = PASS;
- real off-machine DR = PASS;
- cross-OS cabinet continuity = PASS where applicable;
- authenticated update/rollback on installed targets = PASS;
- final Windows evidence is a local Windows 11 cabinet target with USB/removable/NAS off-machine storage;
- no unsupported platform/hardware claim was introduced;
- the evidence pair validates;
- the closure guard validates;
- all non-secret evidence references are committed to the canonical closeout.

Until then: **P13 = 0 EP**.

## Human gate
The remaining execution requires the physical targets, a real off-machine storage medium and the administrator action needed for private macOS first launch. GitHub-hosted CI cannot substitute for those gates. Remote bare metal reduces risk but does not remove the final Windows 11 cabinet gate.

No Vercel.