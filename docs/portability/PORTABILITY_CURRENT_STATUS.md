# Digital Crown — Portability & Launcher — current verified state

Last verified: 2026-08-28.

## Closed
- P0 — 5 EP — CLOSED
- P1 — 13 EP — CLOSED; merge `2907b3d1ea529dde27468f27ce5835d2655275e9`
- P2 — 13 EP — CLOSED
- P3 — 13 EP — CLOSED; merge `98fe4440806b38d33cbdfb32eab6e7bc85e9b573`
- P4 — 8 EP — CLOSED; merge `40cb22d6dddcbae6dee7340dc23956decaf701d8`
- P5 — 13 EP — CLOSED; candidate `3ee3447e1cd3d92575e3b930abeef8e31061bfb8`
- P6 — 8 EP — CLOSED; packaging certified, private Authenticode distribution gate remains
- P8 — 21 EP — CLOSED; merge `b5e1ea41fa039cc174da5d1690f6d9bd3332728b`
- P11 — 8 EP — CLOSED; merge `455e7603c78b0139c0b39e217bed768bfe1186e7`

## P10 exact product proof
- branch `portability/p10-update-engine`, PR `#239`;
- certified product HEAD `e4d16ffdbf4bf91cf9315c00ab1ba611dbf654ed`;
- P10 #49 `33195861612` — SUCCESS: secure-core + windows-worker + windows-packaged-lifecycle;
- artifact `9696388069`;
- digest `sha256:5af1d77b184f0a744bf51dd57f1171c2ddb6b29b26b44c26a4280b6312cfb1d5`;
- merge proof `05d4ec176e39768521bbfba45746d5c7e38ca67d`, exact merge into P9 base `24965613a02f148d50bcdaee985d34c32373561b`;
- real production Ed25519 trust root: `primary` + cold `recovery`, public keys pinned active, private material offline;
- runtime re-derives SHA-256 key IDs; environment cannot replace trust root; unknown/revoked/malformed keys fail closed;
- packaged Windows evidence green: `1.0.0 -> 1.0.1`, self-test, health/finalization, package rollback + DB rescue, interruption recovery, target-start/runtime-bind failure rollback;
- P10 remains OPEN, **0/13 EP**.

## Distribution gates
### Windows — zero-cost private PKI selected
Repository secrets required:
- `WINDOWS_CODESIGN_PFX_B64`
- `WINDOWS_CODESIGN_PASSWORD`

Repository variable:
- `WINDOWS_CODESIGN_CERT_SHA256`

The signing certificate is generated offline and privately controlled by Digital Crown. CI validates the public certificate SHA-256 pin, requires Code Signing EKU, signs with SHA-256 + timestamp, verifies Authenticode and deletes temporary private material from the runner.

Each known clinic Windows machine receives only the public `.cer`, installed once into LocalMachine `Root` + `TrustedPublisher`. This is private trust, not public SmartScreen reputation.

Existing evidence remains `P6_AUTHENTICODE=NOT_CONFIGURED` until certificate ceremony and GitHub provisioning are completed.

Ceremony: `docs/portability/P6_PRIVATE_WINDOWS_CODESIGN_CEREMONY.md`.

### macOS
P7 candidate `53563b1b22ddb6905a54c16ca8486412130c3921`, PR `#274`.
Required repository secrets:
- `MACOS_DEVELOPER_ID_P12_B64`
- `MACOS_DEVELOPER_ID_P12_PASSWORD`
- `MACOS_CODESIGN_IDENTITY`
- `APPLE_NOTARY_KEY_P8_B64`
- `APPLE_NOTARY_KEY_ID`
- `APPLE_NOTARY_ISSUER_ID`
- `P6_SCIENTIFIC_BUNDLE_SHA256`

P7 gate: Apple Silicon + Developer ID + notarization accepted/no notary errors + stapling + Gatekeeper + install/runtime/upgrade/uninstall smoke.

## Remaining
1. Generate private Windows code-signing certificate offline + provision GitHub secrets/variable + certify signed/timestamped P6 artifact.
2. Install public `.cer` on clean Windows clinic machine + certify private trust and real P10 signed apply.
3. P7 signed/notarized/stapled/Gatekeeper macOS + lifecycle/update proof.
4. Windows + macOS clean-machine certification and P9/P10/P12/P13 final closeout.

## Progress
- total 162 EP
- credited 102 EP
- global **63.0%**
- no partial EP for open lots
- P7 remains canonical next
- no Vercel without explicit authorization

## Canonical files
- roadmap: `PORTABILITY_LAUNCHER_ROADMAP.md`
- P10: `docs/portability/P10_UPDATE_ENGINE.md`
- update trust ceremony: `docs/portability/P10_UPDATE_SIGNING_KEY_CEREMONY.md`
- Windows private signing ceremony: `docs/portability/P6_PRIVATE_WINDOWS_CODESIGN_CEREMONY.md`
