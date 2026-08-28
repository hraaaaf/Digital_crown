# Digital Crown — Portability & Launcher — current verified state

Last verified: 2026-08-28.

## Closed
- P0 — Baseline & portability contract — 5 EP — CLOSED
- P1 — OS abstraction layer — 13 EP — CLOSED; merge `2907b3d1ea529dde27468f27ce5835d2655275e9`
- P2 — Runtime Supervisor / Launcher V2 — 13 EP — CLOSED
- P3 — Cabinet data portability — 13 EP — CLOSED; merge `98fe4440806b38d33cbdfb32eab6e7bc85e9b573`
- P4 — Licence & local secrets cross-platform — 8 EP — CLOSED; merge `40cb22d6dddcbae6dee7340dc23956decaf701d8`
- P5 — Scientific/native runtime portability — 13 EP — CLOSED; candidate `3ee3447e1cd3d92575e3b930abeef8e31061bfb8`
- P6 — Industrialized Windows packaging — 8 EP — CLOSED; product packaging certified, production Authenticode distribution credential still not provisioned
- P8 — Hardware & peripheral compatibility — 21 EP — CLOSED; merge `b5e1ea41fa039cc174da5d1690f6d9bd3332728b`
- P11 — Launcher & Recovery UX — 8 EP — CLOSED; merge `455e7603c78b0139c0b39e217bed768bfe1186e7`

## P6 exact distribution boundary
- certified P6 candidate `6eea148ceede740ea4646023e5f3aa58ea1ee8d1`, PR `#259`;
- P6 run `32999393374` — SUCCESS;
- exact installer evidence remains `P6_AUTHENTICODE=NOT_CONFIGURED`; no signed Windows production distribution is claimed;
- production workflow requires GitHub Actions secrets `WINDOWS_CODESIGN_PFX_B64` and `WINDOWS_CODESIGN_PASSWORD`;
- when present, workflow signs SHA-256, timestamps through DigiCert and verifies Authenticode before upload.

## P8 exact evidence
- candidate `5c583761f204c6c0de7cd9c2c60976c7dcf7e23b`;
- Portability P8 `33057900937` — SUCCESS exact-head;
- PR `#275` — MERGED; integration merge `b5e1ea41fa039cc174da5d1690f6d9bd3332728b`;
- canonical matrix: `docs/portability/P8_HARDWARE_COMPATIBILITY_MATRIX.md`.

## P10 exact verified state
- branch `portability/p10-update-engine`, PR `#239`;
- production-key admission HEAD: `e4d16ffdbf4bf91cf9315c00ab1ba611dbf654ed`;
- P10 #49 `33195861612` — **SUCCESS** exact-head;
- jobs `secure-core`, `windows-worker`, `windows-packaged-lifecycle` — SUCCESS;
- artifact `9696388069`;
- digest `sha256:5af1d77b184f0a744bf51dd57f1171c2ddb6b29b26b44c26a4280b6312cfb1d5`;
- workflow artifact HEAD `e4d16ffdbf4bf91cf9315c00ab1ba611dbf654ed`;
- PR merge proof `05d4ec176e39768521bbfba45746d5c7e38ca67d`, exact merge of `e4d16ffd...` into P9 base `24965613a02f148d50bcdaee985d34c32373561b`;
- production trust root now contains two real Ed25519 public keys created by the offline ceremony: operational `primary` + cold `recovery`, both active;
- only public material is committed; runtime re-derives SHA-256 key IDs; environment cannot replace the trust root; unknown/revoked/malformed keys fail closed;
- packaged proof remains green with the production keyring: positive `1.0.0 -> 1.0.1`, exact package self-test, runtime health/finalization, package rollback + DB rescue, interruption recovery, and target application-start/runtime-bind failure rollback;
- target-start drill: `UPDATE_WINDOWS_RUNTIME_HEALTH_FAILED` -> worker exit `2` -> package restored `1.0.0` -> rollback health passed -> DB rollback not needed for that scenario;
- P10 remains OPEN and **0/13 EP credited** because platform distribution and clean-machine gates remain unsatisfied.

## Documentation closeout above product proof
- all commits after certified product HEAD `e4d16ffd...` are documentation-only;
- files touched: `PORTABILITY_LAUNCHER_ROADMAP.md`, `docs/portability/P10_UPDATE_ENGINE.md`, `docs/portability/P10_UPDATE_SIGNING_KEY_CEREMONY.md`, `docs/portability/PORTABILITY_CURRENT_STATUS.md`;
- product/runtime proof remains #49 on `e4d16ffd...`.

## Prepared / active
- P7 — Native macOS packaging — candidate `53563b1b22ddb6905a54c16ca8486412130c3921`, PR `#274`; signed/notarized workflow still required.
- P9 — DR engine prepared; real external target + clean packaged restore + applicable inter-OS proof required.
- P10 — Windows update/rollback/recovery + production update trust root certified; Authenticode/macOS/clean-machine gates remain.
- P12 — certification matrix prepared and merged via PR `#270`, merge `8e1d0d6d9c676b39d40f75a18fc0db168dcc5257`; 0 EP credited.

## P7 required distribution credentials
The `Portability P7 macOS Distribution Certification` workflow is `workflow_dispatch` and requires these GitHub Actions repository secrets:

- `MACOS_DEVELOPER_ID_P12_B64`
- `MACOS_DEVELOPER_ID_P12_PASSWORD`
- `MACOS_CODESIGN_IDENTITY`
- `APPLE_NOTARY_KEY_P8_B64`
- `APPLE_NOTARY_KEY_ID`
- `APPLE_NOTARY_ISSUER_ID`
- `P6_SCIENTIFIC_BUNDLE_SHA256`

The workflow requires Apple Silicon, Developer ID signing, notarization acceptance, notary log without errors, stapling, Gatekeeper, and clean install/runtime/upgrade/uninstall smoke.

## Real remaining gates
1. Provision Windows production Authenticode credentials in GitHub Actions secrets; certify signed + timestamped exact artifact and real P10 apply path.
2. Provision P7 Apple distribution credentials; certify Developer ID signed + notarized + stapled + Gatekeeper-verified macOS package and real lifecycle/update path.
3. Windows + macOS clean-machine certification.
4. Final P9/P10/P12/P13 evidence consistency and closeout sequence.

Key ceremony procedure: `docs/portability/P10_UPDATE_SIGNING_KEY_CEREMONY.md`.
P10 contract/evidence: `docs/portability/P10_UPDATE_ENGINE.md`.

## Active next
P7 remains the canonical product-order next lot. For P10, the next human/security gate is Windows production Authenticode provisioning, followed by signed exact-artifact certification.

## Progress accounting
Roadmap total: 162 EP.
Credited: 102 EP.
Global progress: **63.0%**.

No partial EP are credited for an open lot.

## Deployment rule
No Vercel deployment without explicit product authorization.

## Evidence
- P3: `docs/portability/PORTABILITY_P3_CLOSEOUT.md`.
- P4: `docs/portability/PORTABILITY_P4_CLOSEOUT.md`.
- P6: `docs/portability/PORTABILITY_P6_CLOSEOUT.md`.
- P8: `docs/portability/P8_HARDWARE_COMPATIBILITY_MATRIX.md`.
- P10: PR `#239`, run `33195861612`, artifact `9696388069`, `docs/portability/P10_UPDATE_ENGINE.md`.
- P11: `docs/portability/P11_LAUNCHER_RECOVERY_UX.md`.
- P12 prep: `docs/portability/P12_CERTIFICATION_MATRIX.md`.
- Canonical scope/ordering: `PORTABILITY_LAUNCHER_ROADMAP.md`.
