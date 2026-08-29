# Portability & Launcher — roadmap canonique

Dernière mise à jour vérifiée : 2026-08-29.

> **Source de vérité unique du chantier.**

## Goal global
Digital Crown doit offrir un seul produit local-first, issu d’un cœur partagé, installable et exploitable sur Windows et macOS avec démarrage, données cabinet, restauration, licence/secrets, packaging, mises à jour, récupération et certification maîtrisés.

## Effort canonique
| Lot | Effort | État |
|---|---:|---|
| P0 — Baseline & portability contract | 5 EP | CLOSED ✅ |
| P1 — OS abstraction layer | 13 EP | CLOSED ✅ |
| P2 — Runtime Supervisor / Launcher V2 | 13 EP | CLOSED ✅ |
| P3 — Cabinet data portability | 13 EP | CLOSED ✅ |
| P4 — Licence, secrets & machine identity | 8 EP | CLOSED ✅ |
| P5 — Scientific/native runtime portability | 13 EP | CLOSED ✅ |
| P6 — Industrialized Windows packaging | 8 EP | CLOSED ✅ |
| P7 — Native macOS packaging | 13 EP | TECHNICALLY CERTIFIED — merge/closeout pending |
| P8 — Hardware & peripherals | 21 EP | CLOSED ✅ |
| P9 — Backup / Recovery / DR | 8 EP | ACTIVE |
| P10 — Cross-platform Update Engine | 13 EP | TECHNICALLY CERTIFIED — merge/closeout pending |
| P11 — Launcher & Recovery UX | 8 EP | CLOSED ✅ |
| P12 — CI & certification matrix | 13 EP | PREPARED — 0 EP |
| P13 — Real cabinet certification | 13 EP | PLANNED |
| P14 — Closeout | 5 EP | PLANNED |
| **TOTAL** | **162 EP** | |

Aucun EP partiel n’est crédité pour un lot ouvert.

## Closed evidence
- P0: `docs/portability/PORTABILITY_P0_BASELINE.md`.
- P1: PR #219, merge `2907b3d1ea529dde27468f27ce5835d2655275e9`.
- P2: PR #220, merge `19bf42b61001c77c219fc2b957d6dadc84f79480`.
- P3: PR #222, merge `98fe4440806b38d33cbdfb32eab6e7bc85e9b573`.
- P4: PR #224, merge `40cb22d6dddcbae6dee7340dc23956decaf701d8`.
- P5: candidate `3ee3447e1cd3d92575e3b930abeef8e31061bfb8`.
- P6: PR #259, candidate `6eea148ceede740ea4646023e5f3aa58ea1ee8d1`.
- P8: PR #275, merge `b5e1ea41fa039cc174da5d1690f6d9bd3332728b`.
- P11: PR #241, merge `455e7603c78b0139c0b39e217bed768bfe1186e7`.

## P7 / P10 exact technical certification
Candidate HEAD: `705bdfc56cf53fc383c9e54934d599fa7befa4c1` on PR #274.
Exact-head: 12/12 PR-triggered workflows SUCCESS.

Clean Hosted run `33267234774` — SUCCESS:
- macOS artifact `9719162213`, digest `sha256:157a45ed0246c7fbcd6a42144e04d48682d41ac10f2c29d6967bf2889312a1e4`;
- Windows artifact `9719279025`, digest `sha256:f6fedb68873d0f6f77827b0a936e4e845e188a6e1c59b9603a87f47f1109e977`.

### P7 proved
- fresh Apple Silicon runner;
- real DMGs 1.0.0/1.0.1;
- exact bundle identity/version + strict ad-hoc codesign;
- Gatekeeper default policy rejection via `spctl`, as expected for private ad-hoc distribution;
- signed-manifest/exact-SHA update;
- package self-test + runtime health;
- interruption recovery;
- package + encrypted DB rollback;
- uninstall preserves cabinet data.

No Developer ID, notarization, stapling or Apple Gatekeeper approval is claimed. Human first-launch ceremony remains P13 real-cabinet validation.

### P10 proved
- signed Ed25519 manifest trust root;
- Windows Authenticode private PKI on both 1.0.0/1.0.1 installers + DigiCert timestamp;
- clean Windows signed update lifecycle;
- clean macOS private update lifecycle;
- target health/self-test;
- interruption recovery;
- package + DB rollback on both platforms.

## P9 — Backup / Recovery / DR — ACTIVE
Remaining real gate: off-machine destination plus restore on an independent clean packaged target and Windows ↔ macOS recovery evidence where applicable. GitHub artifact transfer between independent fresh OS runners is the planned zero-cost certification path; it must still be executed and proved.

## P12 — CI & certification matrix — PREPARED
Final matrix waits for merged P7/P10 closeouts plus P9 evidence. P12 remains 0 EP until its own matrix closes.

## P13 — Real cabinet certification — PLANNED
Real-cabinet validation remains distinct from technical CI. It includes administrator first-launch behavior on an actual cabinet Mac and critical cabinet workflows on real installed systems.

## P14 — Closeout — PLANNED
Final docs, matrices, guides, troubleshooting, governance and evidence consistency.

## Ordre canonique restant
P7 merge/closeout → P10 post-merge closeout → P9 → P12 → P13 → P14.

## État courant
- credited: **102 / 162 EP = 63,0 %**;
- P7/P10 technical evidence: green but not yet credited before merge/post-merge verification;
- no Vercel;
- Next exact: commit closeout docs → verify CI → merge PR #274 → post-merge verify/credit.
