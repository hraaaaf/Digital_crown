# P10 — Cross-platform Update Engine

**Status:** TECHNICALLY CERTIFIED — canonical closeout/merge pending. **0 EP credited until merge.**

## Goal
Install only an authentic, fresh, strictly newer Digital Crown release with verified rescue, exact package/runtime health and automatic rollback.

## Certified foundations
- signed update manifest with pinned Ed25519 trust root (`primary` + cold `recovery`);
- exact package SHA-256/size validation;
- fail-closed worker/recovery/finalization paths;
- package self-test + loopback `/health` runtime truth;
- package rollback + encrypted DB rescue;
- interruption recovery.

## Exact clean-hosted cross-platform certification
Candidate HEAD: `705bdfc56cf53fc383c9e54934d599fa7befa4c1`.
Workflow: `Portability P7/P10 Clean Hosted Certification`.
Run: `33267234774` — SUCCESS.

### macOS ARM64 — SUCCESS
Job `clean-macos-private-lifecycle`.
Artifact `9719162213`.
Digest `sha256:157a45ed0246c7fbcd6a42144e04d48682d41ac10f2c29d6967bf2889312a1e4`.
Verified: clean baseline, real 1.0.0/1.0.1 DMGs, strict ad-hoc codesign, Gatekeeper default rejection via `spctl`, signed-manifest update, target self-test, runtime health, interruption recovery, package rollback, encrypted DB rollback, uninstall data preservation.

### Windows x64 — SUCCESS
Job `clean-windows-signed-lifecycle`.
Artifact `9719279025`.
Digest `sha256:f6fedb68873d0f6f77827b0a936e4e845e188a6e1c59b9603a87f47f1109e977`.
Verified on a fresh `windows-2025` runner:
- real installers 1.0.0 and 1.0.1;
- both installers Authenticode-signed with Digital Crown private PKI;
- RFC3161/DigiCert timestamp present;
- public certificate trusted only ephemerally in LocalMachine `Root` + `TrustedPublisher`;
- both signatures verified valid;
- real signed `1.0.0 -> 1.0.1` lifecycle succeeded;
- target self-test/runtime health, interruption recovery, package rollback and DB rollback succeeded;
- private PFX and temporary trust removed after the run.

## Exact-head regression proof
On HEAD `705bdfc56cf53fc383c9e54934d599fa7befa4c1`, 12/12 PR-triggered workflows completed SUCCESS, including P6 Windows Packaging, P6 Authenticode Probe, P7 Private Distribution, P7/P10 Clean Hosted, P10 macOS Update, P10 Update Engine, Runtime, CI, Catalog, T2, Patient and P11.

## Distribution truth
### Windows
Private Digital Crown PKI is used for known clinic machines. This is not Microsoft SmartScreen reputation. Clinic machines receive only the public `.cer`; private PFX/password never leave controlled signing custody.

The **private key** remains outside the repository and outside clinic machines. It exists only in controlled signing custody; CI imports the encrypted PFX ephemerally, signs, verifies, then removes the PFX and temporary trust material before the runner is destroyed.

### macOS
Private distribution uses signed-manifest authenticity + exact SHA + ad-hoc codesign integrity. No Developer ID, notarization, stapling or Apple Gatekeeper approval is claimed. Human first-launch ceremony remains a P13 real-cabinet check.

## Remaining canonical action
The technical P10 gates are satisfied. P10 remains uncredited until:
1. this closeout evidence is committed coherently;
2. PR #274 merges P7 into `portability/p10-update-engine`;
3. post-merge exact state is verified.

After that, P10 may be marked CLOSED and credited 13 EP if no contradiction appears.

No Vercel.
