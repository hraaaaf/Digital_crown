# P12 — CI & Certification Matrix

**Status:** PREPARED — certification matrix only. **0 EP credited.**

## Goal

Certify the exact Windows and macOS artifacts across runtime, packaging, scientific fail-closed behavior, backup/restore, update/recovery, and regression gates before any cross-platform support claim.

## Doctrine

P12 is an evidence aggregator, not a substitute for the owning lots. A green static matrix does not certify an OS or artifact.

A platform row may become `CERTIFIED` only when every mandatory upstream artifact gate for that OS is independently green on the exact candidate and the resulting evidence is recorded in the P12 closeout.

## Current verified inputs

| Capability | Windows x64 | macOS arm64 | Owning lot | P12 state |
|---|---|---|---|---|
| Core/runtime portability | proved by P5 | proved by P5 | P5 | AVAILABLE |
| Frozen/package lifecycle | proved by P6 | proved by P7 private distribution | P6/P7 | AVAILABLE |
| Scientific assets policy | FAIL_CLOSED_NO_WEIGHTS | FAIL_CLOSED_NO_WEIGHTS required | P5/P6/P7 | PARTIAL |
| Hardware truth matrix | certified conservative boundary | certified conservative boundary | P8 | AVAILABLE |
| Disaster recovery | deterministic candidate | deterministic candidate | P9 | OPEN_REAL_TARGET |
| Update secure core | certified signed lifecycle | certified private lifecycle | P10 | AVAILABLE |
| Launcher/recovery UX | proved by P11 | shared UX proved by P11 | P11 | AVAILABLE |
| Clean-machine E2E | not P12-closed | not P12-closed | P12/P13 | OPEN |

## P7 / P10 upstream evidence now available

P7 and P10 are no longer blockers for matrix preparation. Their technical evidence is available from the clean-hosted cross-platform certification and exact-head regression runs. This does not close P12 by itself.

- Windows: real signed 1.0.0 → 1.0.1 lifecycle, package self-test, runtime health, interruption recovery, package rollback and DB rollback.
- macOS: real private 1.0.0 → 1.0.1 DMG lifecycle, Gatekeeper default-boundary proof, package self-test, runtime health, interruption recovery, package rollback and DB rollback.
- Human first-launch behavior on an actual cabinet Mac remains P13, not a hidden P7/P10 claim.

## Required final matrix

P12 closure requires exact evidence for both `windows-amd64` and `macos-arm64`:

1. runtime/startup readiness and single-instance behavior;
2. frozen/package self-test with no forbidden secrets or unqualified scientific weights;
3. native/scientific runtime gate and fail-closed scientific capability state;
4. install/upgrade/uninstall lifecycle with cabinet-data preservation;
5. backup/restore and DR failure scenarios appropriate to the platform;
6. authenticated update current → next, health verification and rollback drills;
7. launcher/recovery regression;
8. artifact identity, checksum and platform signing/notarization truth;
9. clean-machine execution evidence;
10. no unsupported hardware capability promoted to `SUPPORTED` without P8 evidence.

## Current blockers

- P9 real external/off-machine destination + independent clean packaged restore proof remains open (`OPEN_REAL_TARGET`).
- P12 still needs its own final exact matrix closeout after P9 evidence is integrated.
- P13 remains the real-cabinet certification layer after P12.

P8 is an available upstream contract: it certifies the current conservative boundary, not native dental-device support. Any future `SUPPORTED` hardware claim still requires real-device evidence on every claimed OS.

No Vercel.
