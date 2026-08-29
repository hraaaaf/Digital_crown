# P10 — Cross-platform Update Engine

**Status:** CLOSED ✅ — **13 EP credited.**

## Goal
Install only an authentic, fresh, strictly newer Digital Crown release with verified rescue, exact package/runtime health and automatic rollback.

## Certified foundations
- P10 depends on the certified **P6/P7** packaging outputs before any update lifecycle can be credited;
- signed update manifest with pinned Ed25519 trust root (`primary` + cold `recovery`);
- exact package SHA-256/size validation;
- fail-closed worker/recovery/finalization paths;
- package self-test + loopback `/health` runtime truth;
- Windows program snapshot + uninstall registry rollback;
- package rollback + encrypted DB rescue owned by the old packaged executable;
- PostgreSQL DB rollback remains outside the certified portable SQLite path;
- Windows PowerShell 5.1 worker runtime;
- interrupted update recovery.

## Clean-hosted cross-platform certification
Technical proof candidate HEAD: `705bdfc56cf53fc383c9e54934d599fa7befa4c1`.
Initial Clean Hosted run `33267234774` — SUCCESS.

### macOS ARM64 — SUCCESS
Artifact `9719162213`.
Digest `sha256:157a45ed0246c7fbcd6a42144e04d48682d41ac10f2c29d6967bf2889312a1e4`.
Verified: clean baseline, real 1.0.0/1.0.1 DMGs, strict ad-hoc codesign, Gatekeeper default rejection via `spctl`, signed-manifest update, target package self-test, runtime `/health`, interrupted update recovery, package rollback, encrypted DB rollback, uninstall data preservation.

### Windows x64 — SUCCESS
Artifact `9719279025`.
Digest `sha256:f6fedb68873d0f6f77827b0a936e4e845e188a6e1c59b9603a87f47f1109e977`.
Verified on a fresh `windows-2025` runner:
- real installers 1.0.0 and 1.0.1;
- both installers Authenticode-signed with Digital Crown private PKI;
- RFC3161/DigiCert timestamp present;
- public certificate trusted only ephemerally in LocalMachine `Root` + `TrustedPublisher`;
- both signatures verified valid;
- real signed `1.0.0 -> 1.0.1` lifecycle succeeded;
- target package self-test/runtime `/health`, interrupted update recovery, Windows program snapshot rollback, uninstall registry rollback and DB rollback succeeded;
- private PFX and temporary trust removed after the run.

## Merge and post-merge proof
PR #274 merged as `04d286041fe85743920d633aea4f6a24f3ceae3f`.
Post-merge exact HEAD `3bc4f781e9ad496b86c72b4cade56da9241555c7` passed:
- P10 Update Engine #139 / run `33272768851` — SUCCESS;
- P10 macOS Update Engine #57 / run `33272768868` — SUCCESS;
- P7/P10 Clean Hosted #7 / run `33272768876` — SUCCESS;
- P7 macOS Private Distribution #25 / run `33272768846` — SUCCESS;
- P12 Certification Matrix Prep #69 / run `33272768866` — SUCCESS;
- general CI #2183 / run `33272768872` — SUCCESS.

## Distribution truth
### Windows
Private Digital Crown PKI is used for known clinic machines. This is not Microsoft SmartScreen reputation. Clinic machines receive only the public `.cer`; private PFX/password never leave controlled signing custody.

The **private key** remains outside the repository and outside clinic machines. It exists only in controlled signing custody; CI imports the encrypted PFX ephemerally, signs, verifies, then removes the PFX and temporary trust material before the runner is destroyed.

### macOS
Private distribution uses signed-manifest authenticity + exact SHA + ad-hoc codesign integrity. No Developer ID, notarization, stapling or Apple Gatekeeper approval is claimed. Human first-launch ceremony remains a P13 real-cabinet check.

No Vercel.
