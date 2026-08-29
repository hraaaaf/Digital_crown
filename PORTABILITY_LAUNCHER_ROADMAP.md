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
| P12 — CI & certification matrix | 13 EP | PREPARED — 0 EP |
| P13 — Real cabinet certification | 13 EP | PLANNED |
| P14 — Closeout | 5 EP | PLANNED |
| **TOTAL** | **167 EP** | |

Aucun EP partiel n’est crédité pour un lot ouvert.

### Correction arithmétique canonique
Le tableau d’effort introduit le 2026-08-24 listait déjà ces mêmes 15 valeurs mais affichait `TOTAL 162 EP`. Leur somme vérifiée est **167 EP**. Aucun lot n’est réduit artificiellement pour conserver l’ancien dénominateur. Les pourcentages canoniques sont donc calculés sur 167 EP à partir de cette correction.

## Closed evidence
- P0: `docs/portability/PORTABILITY_P0_BASELINE.md`.
- P1: PR #219, merge `2907b3d1ea529dde27468f27ce5835d2655275e9`.
- P2: PR #220, merge `19bf42b61001c77c219fc2b957d6dadc84f79480`.
- P3: PR #222, merge `98fe4440806b38d33cbdfb32eab6e7bc85e9b573`.
- P4: PR #224, merge `40cb22d6dddcbae6dee7340dc23956decaf701d8`.
- P5: candidate `3ee3447e1cd3d92575e3b930abeef8e31061bfb8`.
- P6: PR #259, candidate `6eea148ceede740ea4646023e5f3aa58ea1ee8d1`.
- P7: PR #274, merge `04d286041fe85743920d633aea4f6a24f3ceae3f`; exact-head P7/P10 closeout `a30bec961a6e5fb51f46fd7a5f4b2ed36d7f196e`, 19/19 workflows SUCCESS.
- P8: PR #275, merge `b5e1ea41fa039cc174da5d1690f6d9bd3332728b`.
- P9: candidate `4590e2975e71ca89fc404e96e717646155b8fc14`; P9 #11 run `33276520623`, 5/5 jobs SUCCESS with independently persisted off-runner cross-OS frozen restores.
- P10: PR #239 merged into P9 branch as `aec7f27cbc075e3eb9e53aa651f19c4cdac64a13`; exact-head pre-merge CI 19/19 SUCCESS.
- P11: PR #241, merge `455e7603c78b0139c0b39e217bed768bfe1186e7`.

## P9 certified boundary
P9 proves machine-loss-style technical recovery for the portable SQLite/SQLCipher cabinet path in both directions: macOS → Windows and Windows → macOS. Each direction uses an independently persisted off-runner artifact, a distinct fresh target runner, a real frozen packaged executable, Guided Restore, `/health`, SQLCipher integrity, DB truth and media-byte verification. Wrong migration secrets and tampered bundles fail closed.

This certification does not turn GitHub Actions into the cabinet backup provider and does not certify a physical USB/NAS. Actual operational media/NAS setup and human recovery ceremony remain P13.

## P12 — CI & certification matrix — PREPARED
P7/P9/P10 are now AVAILABLE upstream inputs. P12 remains 0 EP until its own final matrix closes. Remaining analysis centers on aggregating the already verified scientific/native, clean-machine, runtime, packaging, DR, update, launcher and hardware evidence without stealing P13's real-cabinet scope.

## P13 — Real cabinet certification — PLANNED
Real-cabinet validation remains distinct from technical CI. It includes administrator first-launch behavior on an actual cabinet Mac, physical/off-machine backup setup and critical cabinet workflows on real installed systems.

## P14 — Closeout — PLANNED
Final docs, matrices, guides, troubleshooting, governance and evidence consistency.

## Ordre canonique restant
P12 → P13 → P14.

## État courant
- credited: **136 / 167 EP = 81,4 %**;
- P9: CLOSED — 8 EP;
- P12: PREPARED — 0 EP;
- no Vercel;
- Next exact: finalize P12 exact certification matrix from all closed upstream evidence.
