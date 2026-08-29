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
| P7 — Native macOS packaging | 13 EP | CLOSED ✅ |
| P8 — Hardware & peripherals | 21 EP | CLOSED ✅ |
| P9 — Backup / Recovery / DR | 8 EP | ACTIVE |
| P10 — Cross-platform Update Engine | 13 EP | CLOSED ✅ |
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
- P7: PR #274, merge `04d286041fe85743920d633aea4f6a24f3ceae3f`; post-merge P7 #25 `33272768846` SUCCESS + Clean Hosted #7 `33272768876` SUCCESS.
- P8: PR #275, merge `b5e1ea41fa039cc174da5d1690f6d9bd3332728b`.
- P10: post-merge exact HEAD `3bc4f781e9ad496b86c72b4cade56da9241555c7`; P10 #139 `33272768851` SUCCESS, P10 macOS #57 `33272768868` SUCCESS, Clean Hosted #7 SUCCESS.
- P11: PR #241, merge `455e7603c78b0139c0b39e217bed768bfe1186e7`.

## P7 / P10 certified boundary
P7 private macOS distribution uses signed-manifest authenticity + exact DMG SHA/size + strict ad-hoc codesign integrity. Gatekeeper default rejection is explicitly proved; no Developer ID, notarization, stapling or Apple approval is claimed. Human first-launch remains P13.

P10 authenticates updates with the signed Ed25519 manifest, exact package identity/hash/size, target package self-test + `/health`, interruption recovery and package/DB rollback. Windows installers are private-PKI Authenticode signed with RFC3161 timestamp; private signing material is ephemeral and removed after use.

## P9 — Backup / Recovery / DR — ACTIVE
Remaining real gate: off-machine independently persisted destination plus restore on an independent clean packaged target and Windows ↔ macOS recovery evidence where applicable. The certification must prove the storage boundary rather than treating a same-run temp directory as external DR.

## P12 — CI & certification matrix — PREPARED
P7/P10 are now AVAILABLE upstream inputs. Final matrix waits primarily for P9 evidence. P12 remains 0 EP until its own matrix closes.

## P13 — Real cabinet certification — PLANNED
Real-cabinet validation remains distinct from technical CI. It includes administrator first-launch behavior on an actual cabinet Mac and critical cabinet workflows on real installed systems.

## P14 — Closeout — PLANNED
Final docs, matrices, guides, troubleshooting, governance and evidence consistency.

## Ordre canonique restant
P9 → P12 → P13 → P14.

## État courant
- credited: **128 / 162 EP = 79,0 %**;
- P7: CLOSED — 13 EP;
- P10: CLOSED — 13 EP;
- P9: ACTIVE;
- no Vercel;
- Next exact: execute P9 off-machine independent clean packaged restore + cross-OS DR certification.
