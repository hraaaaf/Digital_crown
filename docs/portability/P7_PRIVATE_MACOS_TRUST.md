# P7 — Private macOS Trust

## Goal
Support Digital Crown on known clinic Macs without a paid Apple Developer membership while preserving fail-closed update authenticity, package integrity, rollback and recovery.

## Trust boundary
- Update authenticity is anchored in Digital Crown's signed update manifest.
- The manifest pins exact DMG SHA-256 and size before apply.
- Bundle ID must be `com.saninova.digitalcrown` and version must equal the target version.
- The app must pass `codesign --verify --deep --strict` with an ad-hoc signature.
- Ad-hoc signing is integrity only, not Apple publisher identity.
- Developer ID, notarization and stapling are intentionally not claimed.

## Clean independent macOS certification — SUCCESS
Exact candidate HEAD: `705bdfc56cf53fc383c9e54934d599fa7befa4c1`.
Workflow: `Portability P7/P10 Clean Hosted Certification`.
Run: `33267234774`.
Job: `clean-macos-private-lifecycle` — SUCCESS.
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

## Gatekeeper / first install truth
The clean-hosted gate proves the default Gatekeeper policy reaction and the complete technical lifecycle. It does not simulate or claim the human GUI action `Open Anyway`. The administrator-controlled first-launch ceremony on a real cabinet Mac remains a P13 real-cabinet validation, not a P7 technical packaging blocker.

## Status
P7 technical gates are satisfied on exact HEAD `705bdfc56cf53fc383c9e54934d599fa7befa4c1`.
P7 remains uncredited until the canonical closeout commit is merged through PR #274 into `portability/p10-update-engine`.

## Non-claims
Do not label this distribution as Apple notarized, Developer ID signed, App Store distributed, or Gatekeeper-approved by Apple.
