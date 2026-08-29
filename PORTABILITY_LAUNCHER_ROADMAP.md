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
| P9 — Backup / Recovery / DR | 8 EP | CLOSED ✅ |
| P10 — Cross-platform Update Engine | 13 EP | CLOSED ✅ |
| P11 — Launcher & Recovery UX | 8 EP | CLOSED ✅ |
| P12 — CI & certification matrix | 13 EP | CLOSED ✅ |
| P13 — Real cabinet certification | 13 EP | PLANNED |
| P14 — Closeout | 5 EP | PLANNED |
| **TOTAL** | **167 EP** | |

Aucun EP partiel n’est crédité pour un lot ouvert.

### Correction arithmétique canonique
Le tableau d’effort introduit le 2026-08-24 listait déjà ces mêmes 15 valeurs mais affichait `TOTAL 162 EP`. Leur somme vérifiée est **167 EP**. Aucun lot n’est réduit artificiellement pour conserver l’ancien dénominateur.

## Closed evidence
- P0: `docs/portability/PORTABILITY_P0_BASELINE.md`.
- P1: PR #219, merge `2907b3d1ea529dde27468f27ce5835d2655275e9`.
- P2: PR #220, merge `19bf42b61001c77c219fc2b957d6dadc84f79480`; Runtime `32601811079` SUCCESS.
- P3: PR #222, merge `98fe4440806b38d33cbdfb32eab6e7bc85e9b573`.
- P4: PR #224, merge `40cb22d6dddcbae6dee7340dc23956decaf701d8`.
- P5: candidate `3ee3447e1cd3d92575e3b930abeef8e31061bfb8`; P5 current regression #168 `33274684195` SUCCESS.
- P6: PR #259, candidate `6eea148ceede740ea4646023e5f3aa58ea1ee8d1`; Windows Packaging `32999393374` SUCCESS.
- P7: PR #274, merge `04d286041fe85743920d633aea4f6a24f3ceae3f`; P7 #27 `33274684146` SUCCESS.
- P8: PR #275, merge `b5e1ea41fa039cc174da5d1690f6d9bd3332728b`.
- P9: candidate `4590e2975e71ca89fc404e96e717646155b8fc14`; P9 #11 `33276520623`, 5/5 SUCCESS.
- P10: PR #239 merge `aec7f27cbc075e3eb9e53aa651f19c4cdac64a13`; P10 #141 `33274684115`, macOS #59 `33274684087`, Clean Hosted #9 `33274684081` SUCCESS.
- P11: PR #241, merge `455e7603c78b0139c0b39e217bed768bfe1186e7`; current regression #119 `33274684098` SUCCESS.
- P12: final matrix aggregates the independently verified P2/P5/P6/P7/P8/P9/P10/P11 evidence and preserves the P13 physical/human boundary.

## P12 certified technical boundary
P12 certifies the current Windows x64 and macOS ARM64 technical matrix: runtime/single-instance, frozen packaging, scientific fail-closed policy, conservative hardware truth, cross-OS DR, authenticated update/rollback, launcher recovery and clean-machine technical execution.

P12 does not certify human first launch on a physical Mac, operational USB/NAS handling or direct dental hardware beyond P8's conservative classifications. Those remain P13/product-distribution boundaries.

## P13 — Real cabinet certification — PLANNED
Real-cabinet validation includes administrator first-launch behavior on actual cabinet hardware, physical/off-machine backup setup, operator recovery ceremony and critical cabinet workflows on real installed systems.

## P14 — Closeout — PLANNED
Final docs, matrices, guides, troubleshooting, governance and evidence consistency.

## Ordre canonique restant
P13 → P14.

## État courant
- credited: **149 / 167 EP = 89,2 %**;
- P12: CLOSED — 13 EP;
- P13: PLANNED — 13 EP;
- no Vercel;
- Next exact: define and execute the P13 real-cabinet certification protocol without duplicating CI-only proofs.
