# Digital Crown — Portability & Launcher — current verified state

Last verified: 2026-08-29.

## Closed
- P0 — 5 EP — CLOSED
- P1 — 13 EP — CLOSED
- P2 — 13 EP — CLOSED
- P3 — 13 EP — CLOSED
- P4 — 8 EP — CLOSED
- P5 — 13 EP — CLOSED
- P6 — 8 EP — CLOSED; Windows packaging certified, private Authenticode distribution now also technically proved
- P8 — 21 EP — CLOSED
- P11 — 8 EP — CLOSED

## P7 / P10 exact candidate
Branch `portability/p7-macos-packaging`, PR #274.
Exact candidate HEAD `705bdfc56cf53fc383c9e54934d599fa7befa4c1`.

### Exact-head CI
12/12 PR-triggered workflows SUCCESS.
Clean Hosted run `33267234774` — SUCCESS on both platforms.

### macOS
- fresh `macos-15` ARM64 runner;
- real 1.0.0/1.0.1 DMGs;
- strict ad-hoc codesign;
- Gatekeeper default policy boundary via `spctl`;
- signed-manifest update + target health;
- interruption recovery + package/DB rollback;
- uninstall preserves cabinet data;
- artifact `9719162213`;
- digest `sha256:157a45ed0246c7fbcd6a42144e04d48682d41ac10f2c29d6967bf2889312a1e4`.

### Windows
- fresh `windows-2025` runner;
- real 1.0.0/1.0.1 installers;
- Authenticode on both installers + DigiCert timestamp;
- ephemeral Root + TrustedPublisher trust;
- real signed update lifecycle + health + interruption/package/DB rollback;
- cleanup of private signing material/trust;
- artifact `9719279025`;
- digest `sha256:f6fedb68873d0f6f77827b0a936e4e845e188a6e1c59b9603a87f47f1109e977`.

## Status
- P7 technical gates: SATISFIED; canonical merge/closeout pending.
- P10 technical gates: SATISFIED; canonical merge/closeout pending.
- P9: ACTIVE candidate, real external/off-machine cross-OS DR proof still open.
- P12: PREPARED, awaits final upstream closeouts/matrix.
- P13: real-cabinet certification still required; human macOS first-launch ceremony belongs here.
- P14: PLANNED.

## Progress
Current credited progress remains **102 / 162 EP = 63.0%** until PR #274 is merged and post-merge closeout is verified. No partial EP is credited for open lots.

## Next
1. merge-ready closeout commit on P7;
2. verify its CI;
3. merge PR #274 into P10;
4. post-merge verification and credit P7/P10 if coherent;
5. execute P9 off-machine cross-OS DR proof;
6. continue P12/P13/P14.

No Vercel.
