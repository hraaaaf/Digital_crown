# P7 — Private macOS Trust

**Status:** CLOSED ✅ — **13 EP credited.**

## Goal
Support Digital Crown on known clinic Macs without a paid Apple Developer membership while preserving fail-closed update authenticity, package integrity, rollback and recovery.

## Trust boundary
- Update authenticity is anchored in Digital Crown's signed update manifest.
- The manifest pins exact DMG SHA-256 and size before apply.
- Bundle ID must be `com.saninova.digitalcrown` and version must equal the target version.
- The app must pass `codesign --verify --deep --strict` with an ad-hoc signature.
- Ad-hoc signing is integrity only, not Apple publisher identity.
- Developer ID, notarization and stapling are intentionally not claimed.
- Contract wording retained explicitly: the private build is **not Apple-notarized**.

## Clean independent macOS certification — SUCCESS
Technical proof candidate HEAD: `705bdfc56cf53fc383c9e54934d599fa7befa4c1`.
Initial Clean Hosted run: `33267234774` — SUCCESS.
Artifact: `9719162213`.
Digest: `sha256:157a45ed0246c7fbcd6a42144e04d48682d41ac10f2c29d6967bf2889312a1e4`.

Verified on a fresh GitHub-hosted `macos-15` ARM64 runner with no pre-existing Digital Crown state:
1. real DMGs `1.0.0` and `1.0.1` built;
2. exact bundle ID/version + strict ad-hoc codesign verified;
3. Gatekeeper policy boundary checked with `spctl`: the ad-hoc app is rejected by default as expected;
4. signed-manifest + exact-SHA update `1.0.0 -> 1.0.1` succeeded;
5. target package self-test and runtime health succeeded;
6. interruption recovery succeeded and rolled back;
7. package + encrypted DB rollback succeeded;
8. uninstall preserved cabinet data.

## Merge and post-merge proof
PR #274 merged into `portability/p10-update-engine` as `04d286041fe85743920d633aea4f6a24f3ceae3f`.
Post-merge exact HEAD `3bc4f781e9ad496b86c72b4cade56da9241555c7` passed:
- `Portability P7 macOS Private Distribution Certification` #25 / run `33272768846` — SUCCESS;
- `Portability P7/P10 Clean Hosted Certification` #7 / run `33272768876` — SUCCESS;
- `Portability P10 macOS Update Engine` #57 / run `33272768868` — SUCCESS;
- general CI #2183 / run `33272768872` — SUCCESS.

## Gatekeeper / first install truth
The historical requirement used the wording **clean physical Mac**. For P7/P10 technical certification it is superseded by the independently provisioned clean-hosted ARM64 runner, which proves the default Gatekeeper policy reaction and complete packaged lifecycle without prior Digital Crown state.

This does not simulate or claim the human GUI action `Open Anyway`. Administrator-controlled first launch on a real cabinet Mac remains a P13 real-cabinet validation.

## Non-claims
Do not label this distribution as Apple notarized, Developer ID signed, App Store distributed, or Gatekeeper-approved by Apple.
