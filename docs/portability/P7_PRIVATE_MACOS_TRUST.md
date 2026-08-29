# P7 — Private macOS Trust

## Goal
Support Digital Crown on known clinic Macs without a paid Apple Developer membership while preserving fail-closed update authenticity, package integrity, rollback and recovery.

## Trust boundary
- Update authenticity remains anchored in Digital Crown's signed update manifest.
- The manifest pins the exact DMG SHA-256 and size before apply.
- The app bundle must have the exact bundle ID `com.saninova.digitalcrown` and exact target version.
- The app bundle must pass `codesign --verify --deep --strict` with an ad-hoc signature.
- Ad-hoc signing is an integrity mechanism only. It is **not** an Apple publisher identity and must never be represented as Developer ID or notarization.
- Developer ID, Apple notarization, stapling and standard Gatekeeper approval are intentionally not claimed.

## First install / Gatekeeper
The first installation on a known clinic Mac is an administrator-controlled ceremony. macOS may require the administrator to explicitly allow/open Digital Crown because the package is not Apple-notarized.

## Updates
After bootstrap, Digital Crown only accepts an update artifact whose exact bytes match the already-verified signed manifest. P10 then keeps the existing self-test, runtime health, rescue snapshot, interruption recovery, package rollback and encrypted DB rollback gates.

## Required clean-Mac proof
P7 is not complete until a clean physical Mac proves:
1. administrator-controlled first install;
2. app launches and `/health` is healthy;
3. signed-manifest + exact-SHA update `1.0.0 -> 1.0.1`;
4. target package self-test and runtime health;
5. interruption recovery;
6. package + DB rollback on injected failure;
7. uninstall does not delete cabinet data.

## Non-claims
Do not label this distribution as Apple notarized, Developer ID signed, App Store distributed, or Gatekeeper-approved by Apple.
