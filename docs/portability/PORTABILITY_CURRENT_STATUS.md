# Digital Crown — Portability & Launcher — current verified state

Last verified: 2026-08-26.

## Closed
- P0 — Baseline & portability contract — 5 EP — CLOSED
- P1 — OS abstraction layer — 13 EP — CLOSED; merge `2907b3d1ea529dde27468f27ce5835d2655275e9`
- P2 — Runtime Supervisor / Launcher V2 — 13 EP — CLOSED
- P3 — Cabinet data portability — 13 EP — CLOSED; merge `98fe4440806b38d33cbdfb32eab6e7bc85e9b573`
- P4 — Licence & local secrets cross-platform — 8 EP — CLOSED; merge `40cb22d6dddcbae6dee7340dc23956decaf701d8`
- P5 — Scientific/native runtime portability — 13 EP — CLOSED; candidate `3ee3447e1cd3d92575e3b930abeef8e31061bfb8`
- P6 — Industrialized Windows packaging — 8 EP — CLOSED; certified product candidate `6eea148ceede740ea4646023e5f3aa58ea1ee8d1`, PR `#259`
- P11 — Launcher & Recovery UX — 8 EP — CLOSED; merge `455e7603c78b0139c0b39e217bed768bfe1186e7`

## P6 exact evidence
- P6 run `32999393374`, job `98276906459` — SUCCESS on `6eea148ceede740ea4646023e5f3aa58ea1ee8d1`.
- Exact-head regressions all SUCCESS: Runtime `32999393381`, T2 `32999393529`, P5 Native `32999393360`, Catalog `32999393394`, P11 `32999393369`, Patient P7 `32999393410`, CI `32999393419`, P8 Hardware `32999393352`.
- Lifecycle artifact `9618198566`, digest `sha256:a68fbcdc17953a5995c50c1ea6271d710c997aa2a7b6aadcbe286656bde4fb7a`.
- Installer artifact `9618206397`, digest archive `sha256:de9b4a82ef39e51c755be578d04fd65334ad00cfe7c4255cb30104a3697e1398`.
- Exact EXE `DigitalCrownSetup-1.0.0.exe`, SHA256 `24e662dd88a941b7c10017e0c34470a1b4206185852102e79bd624f372163edd`.
- Product Authenticode: `NOT_CONFIGURED`; exact uploaded PE has no Certificate Table. No signed Windows distribution is claimed.
- Frozen + installed self-tests: `status=ok`, scientific state `FAIL_CLOSED_NO_WEIGHTS`.
- Clean install, `/health`, upgrade/reinstall, uninstall and cabinet-data sentinel preservation are enforced by the successful lifecycle step.

## Active next
P7 — Native macOS packaging.

## Progress accounting
Roadmap total: 162 EP.
Credited: 81 EP.
Global progress: **50.0%**.

No partial EP are credited for an open lot.

## Deployment rule
No Vercel deployment without explicit product authorization.

## Evidence
- P3: `docs/portability/PORTABILITY_P3_CLOSEOUT.md`.
- P4: `docs/portability/PORTABILITY_P4_CLOSEOUT.md`.
- P6: `docs/portability/PORTABILITY_P6_CLOSEOUT.md`.
- P11: `docs/portability/P11_LAUNCHER_RECOVERY_UX.md`.
- Canonical scope/ordering: `PORTABILITY_LAUNCHER_ROADMAP.md`.
