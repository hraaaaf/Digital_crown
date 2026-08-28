# Portability & Launcher — roadmap canonique

Dernière mise à jour vérifiée : 2026-08-28.

> **Source de vérité unique du chantier.** L’ancienne roadmap `docs/PORTABILITY_LAUNCHER_ROADMAP.md` est dépréciée et renvoie vers ce fichier.

## Goal global
Digital Crown doit offrir **un seul produit local-first**, issu d’un cœur partagé, installable et exploitable sur Windows et macOS avec démarrage, données cabinet, restauration, licence/secrets, packaging, mises à jour, récupération et certification maîtrisés.

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
| P7 — Native macOS packaging | 13 EP | NEXT |
| P8 — Hardware & peripherals | 21 EP | CLOSED ✅ |
| P9 — Backup / Recovery / DR | 8 EP | PLANNED |
| P10 — Cross-platform Update Engine | 13 EP | ACTIVE — 0 EP |
| P11 — Launcher & Recovery UX | 8 EP | CLOSED ✅ |
| P12 — CI & certification matrix | 13 EP | PREPARED — 0 EP |
| P13 — Real cabinet certification | 13 EP | PLANNED |
| P14 — Closeout | 5 EP | PLANNED |
| **TOTAL** | **162 EP** | |

Aucun EP partiel n’est crédité pour un lot ouvert.

## Closed evidence
- P0: `docs/portability/PORTABILITY_P0_BASELINE.md`.
- P1: PR `#219`, merge `2907b3d1ea529dde27468f27ce5835d2655275e9`.
- P2: PR `#220`, merge `19bf42b61001c77c219fc2b957d6dadc84f79480`.
- P3: PR `#222`, merge `98fe4440806b38d33cbdfb32eab6e7bc85e9b573`, closeout `docs/portability/PORTABILITY_P3_CLOSEOUT.md`.
- P4: PR `#224`, merge `40cb22d6dddcbae6dee7340dc23956decaf701d8`, closeout `docs/portability/PORTABILITY_P4_CLOSEOUT.md`.
- P5: candidate `3ee3447e1cd3d92575e3b930abeef8e31061bfb8`, run `32750343308` SUCCESS Windows/macOS Apple Silicon.
- P6: PR `#259`, candidate `6eea148ceede740ea4646023e5f3aa58ea1ee8d1`, run `32999393374` SUCCESS, closeout `docs/portability/PORTABILITY_P6_CLOSEOUT.md`.
- P8: PR `#275`, merge `b5e1ea41fa039cc174da5d1690f6d9bd3332728b`, matrix `docs/portability/P8_HARDWARE_COMPATIBILITY_MATRIX.md`.
- P11: PR `#241`, merge `455e7603c78b0139c0b39e217bed768bfe1186e7`, closeout `docs/portability/P11_LAUNCHER_RECOVERY_UX.md`.

## P6 — distribution production boundary
P6 packaging est CLOSED, mais la distribution Windows signée reste un gate pour P10/P12/P13. Le workflow exige:
- `WINDOWS_CODESIGN_PFX_B64`
- `WINDOWS_CODESIGN_PASSWORD`

L’évidence existante reste `P6_AUTHENTICODE=NOT_CONFIGURED` tant qu’un certificat production n’est pas provisionné.

## P7 — Native macOS packaging — NEXT
- candidat `53563b1b22ddb6905a54c16ca8486412130c3921`, PR `#274`;
- workflow `Portability P7 macOS Distribution Certification` en `workflow_dispatch`;
- secrets requis: `MACOS_DEVELOPER_ID_P12_B64`, `MACOS_DEVELOPER_ID_P12_PASSWORD`, `MACOS_CODESIGN_IDENTITY`, `APPLE_NOTARY_KEY_P8_B64`, `APPLE_NOTARY_KEY_ID`, `APPLE_NOTARY_ISSUER_ID`, `P6_SCIENTIFIC_BUNDLE_SHA256`;
- gate: Developer ID + notarisation acceptée + stapling + Gatekeeper + lifecycle réel Apple Silicon.

## P9 — Backup / Recovery / DR — PLANNED
Moteur préparé. Gate restant: destination externe réelle + restauration sur cible packagée propre + preuve inter-OS applicable, dépendante de P7.

## P10 — Cross-platform Update Engine — ACTIVE — 0/13 EP
### Goal
Updates authentifiées avec signature, rescue point, health post-update et rollback automatique Windows/macOS.

### Certifié
- PR `#239`;
- production trust root: deux clés publiques Ed25519 réelles `primary` + `recovery`, privés conservés hors ligne;
- HEAD produit certifié `e4d16ffdbf4bf91cf9315c00ab1ba611dbf654ed`;
- P10 #49 `33195861612` SUCCESS: secure-core + Windows worker + lifecycle packagé;
- artifact `9696388069`;
- digest `sha256:5af1d77b184f0a744bf51dd57f1171c2ddb6b29b26b44c26a4280b6312cfb1d5`;
- merge proof `05d4ec176e39768521bbfba45746d5c7e38ca67d`, exact merge dans base P9;
- Windows réel: `1.0.0 → 1.0.1`, self-test, health, finalization, package rollback, SQLCipher DB rescue, interruption recovery et target-start/runtime-bind rollback verts;
- contrat: `docs/portability/P10_UPDATE_ENGINE.md`;
- cérémonie/custody: `docs/portability/P10_UPDATE_SIGNING_KEY_CEREMONY.md`.

### Gates restants
1. P6 Windows production Authenticode signé + timestampé et apply réel certifié;
2. P7 macOS signé/notarisé/staplé/Gatekeeper + lifecycle/update réel;
3. Windows + macOS clean-machine;
4. closeout cohérence/evidence.

P10 reste 0/13 EP jusqu’à fermeture de tous ces gates.

## P12 — CI & certification matrix — PREPARED — 0/13 EP
- PR `#270`, merge `8e1d0d6d9c676b39d40f75a18fc0db168dcc5257`;
- matrix `docs/portability/P12_CERTIFICATION_MATRIX.md`;
- reste 0 EP tant que P7/P9/P10 et matrice finale cross-platform ne sont pas certifiés.

## P13 — Real cabinet certification — PLANNED
Prouver le flow cabinet critique sur machines propres Windows/macOS et migration croisée, avec scénarios d’échec contrôlés.

## P14 — Closeout — PLANNED
Fermer le chantier avec docs, matrices, guides d’installation/recovery/update, troubleshooting, gouvernance et preuves cohérentes.

## Ordre canonique
P0 → P1 → P2 → P3 → P4 → P5 → P6 → P7 → P8 → P9 → P10 → P11 → P12 → P13 → P14.

P8, P11 et le travail parallèle P10 ont avancé hors ordre sans contourner leurs gates. **P7 reste le Next canonique** et débloque les preuves finales P9/P10/P12/P13.

## État courant
- P0–P6: CLOSED ✅
- P7: NEXT / credentials Apple requis
- P8: CLOSED ✅
- P9: PLANNED / moteur préparé
- P10: ACTIVE / trust + lifecycle Windows certifiés / 0 EP
- P11: CLOSED ✅
- P12: PREPARED / 0 EP
- P13–P14: PLANNED
- validé: **102 / 162 EP = 63,0 %**
- aucun Vercel
- Next canonique: **P7 Native macOS packaging**
- Next P10: **provisionner Authenticode Windows → certifier artifact signé/apply → P7 macOS → clean-machine**.
