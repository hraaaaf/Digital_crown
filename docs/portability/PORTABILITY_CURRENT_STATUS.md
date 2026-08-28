# Digital Crown — Portability & Launcher — current verified state

Last verified: 2026-08-28.

## Closed
- P0 — Baseline & portability contract — 5 EP — CLOSED
- P1 — OS abstraction layer — 13 EP — CLOSED; merge `2907b3d1ea529dde27468f27ce5835d2655275e9`
- P2 — Runtime Supervisor / Launcher V2 — 13 EP — CLOSED
- P3 — Cabinet data portability — 13 EP — CLOSED; merge `98fe4440806b38d33cbdfb32eab6e7bc85e9b573`
- P4 — Licence & local secrets cross-platform — 8 EP — CLOSED; merge `40cb22d6dddcbae6dee7340dc23956decaf701d8`
- P5 — Scientific/native runtime portability — 13 EP — CLOSED; candidate `3ee3447e1cd3d92575e3b930abeef8e31061bfb8`
- P6 — Industrialized Windows packaging — 8 EP — CLOSED; certified product candidate `6eea148ceede740ea4646023e5f3aa58ea1ee8d1`, PR `#259`
- P8 — Hardware & peripheral compatibility — 21 EP — CLOSED; candidate `5c583761f204c6c0de7cd9c2c60976c7dcf7e23b`, PR `#275`, merge `b5e1ea41fa039cc174da5d1690f6d9bd3332728b`
- P11 — Launcher & Recovery UX — 8 EP — CLOSED; merge `455e7603c78b0139c0b39e217bed768bfe1186e7`

## P6 exact evidence
- P6 run `32999393374`, job `98276906459` — SUCCESS on `6eea148ceede740ea4646023e5f3aa58ea1ee8d1`.
- Exact-head regressions all SUCCESS: Runtime `32999393381`, T2 `32999393529`, P5 Native `32999393360`, Catalog `32999393394`, P11 `32999393369`, Patient P7 `32999393410`, CI `32999393419`, P8 Hardware `32999393352`.
- Lifecycle artifact `9618198566`, digest `sha256:a68fbcdc17953a5995c50c1ea6271d710c997aa2a7b6aadcbe286656bde4fb7a`.
- Installer artifact `9618206397`, digest archive `sha256:de9b4a82ef39e51c755be578d04fd65334ad00cfe7c4255cb30104a3697e1398`.
- Exact EXE `DigitalCrownSetup-1.0.0.exe`, SHA256 `24e662dd88a941b7c10017e0c34470a1b4206185852102e79bd624f372163edd`.
- Product Authenticode: `NOT_CONFIGURED`; exact uploaded PE has no Certificate Table. No signed Windows distribution is claimed.
- Frozen + installed self-tests: `status=ok`, scientific state `FAIL_CLOSED_NO_WEIGHTS`.

## P8 exact evidence
- Compatibility candidate `5c583761f204c6c0de7cd9c2c60976c7dcf7e23b`.
- Portability P8 Hardware Compatibility Contract `33057900937`, job `98469174459` — SUCCESS exact-head.
- P12 Certification Matrix Prep `33057900997` — SUCCESS exact-head.
- PR `#275` — MERGED; integration merge `b5e1ea41fa039cc174da5d1690f6d9bd3332728b`.
- Canonical matrix: `docs/portability/P8_HARDWARE_COMPATIBILITY_MATRIX.md`.

## P10 exact verified state
- Branch `portability/p10-update-engine`, PR `#239`.
- Certified software HEAD: `fc00ae80ce1420bcda8ff9085c1060f2de076ceb`.
- P10 #46 `33186846468` — SUCCESS integral: `secure-core`, `windows-worker`, `windows-packaged-lifecycle`.
- Secure-core #46: `45 passed`.
- Artifact #46 `9692725081`, digest `sha256:cde0d71cbcd9755d87b1107c17c06dd03a76956f5b5908f7aa2f30752e7b25e7`.
- Artifact workflow head SHA: `fc00ae80ce1420bcda8ff9085c1060f2de076ceb`.
- PR merge proof SHA: `9c7968d0754d4525b2003752db76e2985d7b1b20`, exact merge of `fc00ae80...` into P9 base `24965613a02f148d50bcdaee985d34c32373561b`.
- Real packaged Windows proof remains green after trust hardening: positive `1.0.0 -> 1.0.1`, package self-test, runtime health, finalization, package rollback, SQLCipher DB rescue, interruption recovery and target application-start/runtime-bind failure rollback.
- Target-start drill: `UPDATE_WINDOWS_RUNTIME_HEALTH_FAILED` -> worker exit `2` -> package restored `1.0.0` -> rollback `passed` -> `database_rollback=not_needed` -> rollback runtime health `passed`.
- Trust software gate certified: production no longer reads `DIGITALCROWN_UPDATE_PUBLIC_KEY_B64`; embedded keyring only; active-key overlap supports rotation; unknown/revoked keys fail closed; explicit `public_key_b64` injection remains a test/certification seam only.
- No fake production public key is committed. The embedded production keyring remains empty until the real key ceremony.
- P10 remains OPEN and **0/13 EP credited** because final production signing/macOS/clean-machine gates remain unsatisfied.

## Prepared / active
- P7 — Native macOS packaging — candidate `53563b1b22ddb6905a54c16ca8486412130c3921`, PR `#274`; signed/notarized workflow still required.
- P9 — DR engine prepared; real external target + clean packaged restore + applicable inter-OS proof required.
- P10 — Windows update/rollback/recovery + trust software candidate certified; production credentials and cross-platform distribution gates remain.
- P12 — certification matrix prepared and merged via PR `#270`, merge `8e1d0d6d9c676b39d40f75a18fc0db168dcc5257`; 0 EP credited.

## Real remaining gates
1. Offline Ed25519 production signing-key ceremony; only the public key/keyid may enter the repository.
2. Pin that real public key in `PINNED_UPDATE_KEYS` and certify the exact-head update trust path.
3. P6 Windows production Authenticode certificate provisioned; signed + timestamped exact artifact and real apply proof.
4. P7 macOS Developer ID + Apple credentials; signed/notarized/stapled/Gatekeeper-verified package and real lifecycle proof.
5. Windows + macOS clean-machine certification, then P9/P10/P12/P13 closeout sequence.

Key-ceremony procedure: `docs/portability/P10_UPDATE_SIGNING_KEY_CEREMONY.md`.

## Active next
P7 remains the canonical product-order next lot. For the active P10 branch, the next executable step is the production update signing-key ceremony, a human/security gate.

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
- P10: PR `#239`, run `33186846468`, artifact `9692725081`.
- P11: `docs/portability/P11_LAUNCHER_RECOVERY_UX.md`.
- P12 prep: `docs/portability/P12_CERTIFICATION_MATRIX.md`.
- Canonical scope/ordering: `PORTABILITY_LAUNCHER_ROADMAP.md`.
