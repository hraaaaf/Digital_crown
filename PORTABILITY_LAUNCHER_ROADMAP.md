# Portability & Launcher — roadmap canonique

Dernière mise à jour vérifiée : 2026-08-26.

> **Source de vérité unique du chantier.** `docs/PORTABILITY_LAUNCHER_ROADMAP.md` est déprécié et renvoie ici. Les états sont réconciliés avec la base d’intégration `portability/p10-update-engine` et le sous-lot P6 scientifique.

## Goal global

Un seul Digital Crown local-first, cœur partagé Windows/macOS, installable, restaurable, updatable et certifiable avec données cabinet, licence/secrets, assets scientifiques et hardware maîtrisés.

## Doctrine

- un cœur React/FastAPI commun ;
- frontières OS explicites ;
- données cabinet distinctes des secrets machine ;
- aucun asset scientifique non autorisé dans le repo produit public ;
- benchmark technique ≠ validation clinique ;
- capacité scientifique non qualifiée = indisponible/fail-closed ;
- aucun Vercel sans autorisation explicite.

## Effort canonique

| Lot | EP | État |
|---|---:|---|
| P0 — Baseline & portability contract | 5 | CLOSED ✅ |
| P1 — OS abstraction layer | 13 | CLOSED ✅ |
| P2 — Runtime Supervisor / Launcher V2 | 13 | CLOSED ✅ |
| P3 — Cabinet data portability | 13 | CLOSED ✅ |
| P4 — Licence, secrets & machine identity | 8 | CLOSED ✅ |
| P5 — Scientific/native runtime portability | 13 | CLOSED ✅ |
| P6 — Industrialized Windows packaging | 8 | ACTIVE — 0/8 EP |
| P7 — Native macOS packaging | 13 | PLANNED |
| P8 — Hardware & peripherals | 21 | PLANNED |
| P9 — Backup / Recovery / DR | 8 | PLANNED |
| P10 — Cross-platform Update Engine | 13 | PLANNED |
| P11 — Launcher & Recovery UX | 8 | CLOSED ✅ |
| P12 — CI & certification matrix | 13 | PLANNED |
| P13 — Real cabinet certification | 13 | PLANNED |
| P14 — Closeout | 5 | PLANNED |
| **TOTAL** | **162** | |

Aucun EP partiel n’est crédité pour un lot ouvert.

## Lots fermés vérifiés

### P0–P5
- P0 : baseline de portabilité fermée.
- P1 : PR `#219`, Portability `32599659706` SUCCESS Windows/macOS/Ubuntu.
- P2 : PR `#220`, Runtime `32601811079` SUCCESS Windows/macOS/Ubuntu.
- P3 : PR `#222`, CI `32605929015` SUCCESS.
- P4 : PR `#224`, CI `32610745134` SUCCESS.
- P5 : PR `#233`, candidat `3ee3447e1cd3d92575e3b930abeef8e31061bfb8`, natif `32750343308` SUCCESS Windows x64 + macOS ARM64, CI `32750343210` SUCCESS.

Sous-total P0–P5 : **65 EP**.

### P11 — Launcher & Recovery UX — CLOSED ✅ — 8 EP

P11 a été fermé hors ordre sur la base d’intégration `portability/p10-update-engine`; cela ne ferme ni ne crédite P7–P10.

Preuves :
- candidat `cbaf21a066fb6b8b70f4c9d6b3ec1a950cda890b` ; PR `#241` ;
- P11 final `32783305559` — SUCCESS ;
- AFTER artifact `9540590729`, digest `sha256:47ffdcee25d9237ac89f9665c2a0d34603005b8b2786412b63eb30f2a0457cf1` ;
- 15/15 captures AFTER 1440 / 1024 / 768 / 430 / 390 ; zéro overflow / erreur runtime ;
- Runtime `32783305528`, T2 `32783305594`, Catalog `32783305574`, Patient `32783305575`, RBAC `32783305530`, Security `32783305489`, CI `32783305627` — SUCCESS ;
- score Startup **9,3/10**, Guided Restore **9,1/10** ;
- merge vers `portability/p10-update-engine` : `455e7603c78b0139c0b39e217bed768bfe1186e7` ;
- closeout : `docs/portability/P11_LAUNCHER_RECOVERY_UX.md`.

Total validé avant fermeture de P6 : **73 EP**.

---

# P6 — Industrialized Windows packaging — ACTIVE — 0/8 EP

## Goal

Produire un artefact Windows déterministe, installable/upgradeable/uninstallable sur machine propre, sans fuite de secrets ni perte de données, avec les capacités scientifiques non qualifiées explicitement fail-closed.

## Décision scientifique de packaging

P6 n’embarque **aucun poids scientifique non qualifié** :
- provenance/licence du poids panoramique historique non fermée ;
- gagnant céphalo `DC-Ceph-UNet29Q4 / Aariz v1` = 29 points / 512 grayscale ;
- runtime SOTA produit actuel = 38 points / 1024 couleur ;
- aucun remplacement silencieux sous `model.onnx` n’est autorisé.

## Certification Windows active

Ancienne PR `#242` : **CLOSED — SUPERSEDED**, non mergée.

PR active :
- PR `#259` — OPEN/DRAFT ;
- branche `portability/p6-windows-packaging-final-20260826` ;
- HEAD exact `e8aaa2cfd2b68bc84a777c2e07fa4e8ee7dee5fd` ;
- run `32912896028` — **IN_PROGRESS** au dernier contrôle.

Contrat :
- `DigitalCrown.spec` n’embarque plus `panoramic_model.onnx`, `ceph_weights.pth` ni poids SOTA ;
- self-test frozen rejette les chemins connus de poids non qualifiés ;
- lifecycle exigé : `cephalo_sota=deferred`, `cephalo_legacy=external`, `panoramic=external` ;
- marqueurs : `P6_SCIENTIFIC_PACKAGE_POLICY=FAIL_CLOSED_NO_WEIGHTS`, `P6_SCIENTIFIC_CAPABILITIES=FAIL_CLOSED` ;
- `protobuf==5.29.6` + `python -m pip check` ;
- aucun token inter-repo ni Release scientifique requis ;
- aucun Vercel.

### Resync base requis avant merge

La PR #259 est actuellement **8 commits derrière** sa base `portability/p10-update-engine`.

La comparaison `7ccf3181... -> 641ea732...` montre un chevauchement réel sur :
- `DigitalCrown.spec` ;
- `run.py`.

La base apporte notamment le packaging macOS/P7 et le recovery runtime/P11. Ces changements doivent être préservés. Le run `32912896028` reste utile pour qualifier le candidat P6 actuel, mais **ne pourra pas être la certification finale post-resync** si la branche est remise à jour. Après ce run : résoudre le resync, produire un seul HEAD intégré, puis une certification exact-head finale.

### Gates de fermeture P6

1. static packaging contract PASS ;
2. frontend production build PASS ;
3. installation Python + `pip check` PASS ;
4. PyInstaller frozen build + package self-test PASS ;
5. install propre + runtime health + reinstall/upgrade + uninstall PASS ;
6. données cabinet sentinel préservées ;
7. Authenticode honnête (`SUCCESS` ou `NOT_CONFIGURED`) ;
8. installer artifact retenu ;
9. resync base P10 sans perdre P7/P11 ;
10. exact-head final certifié ;
11. closeout docs + opérations Git terminés avant crédit des 8 EP.

---

## Sous-lot P6 Scientific Assets Refresh

Ce sous-lot ne crédite aucun EP et ne bloque plus le packaging Windows fail-closed.

### Céphalométrie

`DC-Ceph-UNet29Q4 / Aariz v1`
- training `32876308676` — SUCCESS ;
- evidence `1da113b8776aa2b57e42ac194f12b7a48b01558c` ;
- dataset Aariz v1 CC BY 4.0, SHA256 `d9fa872b36065dac9615cfcad0c7512c450fe2d86a1839cdec4cbe001def33ea` ;
- ONNX SHA256 `809f1d3d2347d2a34f57d4a3415bb319c29f8a25c325d41160e5f28d4e5dadad`, `7,624,307 bytes` ;
- direct-20 MRE `1.232893 mm`, SDR2 `83.1333%`, SDR4 `97.2667%` ;
- `clinical_claim=false` ; Wits fail-closed ;
- protocole : `docs/P6_CEPHALOMETRY_CLINICAL_VALIDATION_PROTOCOL.md`.

Récupération binaire exacte :
- bridge `32911633368` — SUCCESS ; artifact `9586717545` ;
- digest `sha256:3ed73e3d39325d5b880e72264ac2a8a25996aa5eaef7bedd1a14b76d9b03ec55`.

Rétention privée : **OPEN**, mais archivage séparé ; le runner du repo privé échoue avant toute step (`32911736812`, `steps=null`). Ne pas relancer aveuglément.

### Panoramique Phase A

Cible : **localisation dentaire + FDI**, pas diagnostic automatique de pathologies.

Mendeley V3 first-party :
- `32910743873` — SUCCESS ;
- 107 images ; 25 avec géométrie ; 772 régions ;
- 540 clés `Teeth`, toutes vides ;
- 0 code FDI ; `direct_fdi_ground_truth_ready=false`.

Pack clinicien :
- HEAD `6f7614f23b793dd6804d6c7d770f62928a3a09f0` ;
- run `32912109975` — SUCCESS ;
- artifact `9586914372`, digest `sha256:a72599acf4b96b3d8519f174614feca3cec011dddce0dcc594f01ac4c656ea09` ;
- 107 images, 772 propositions géométriques ;
- FDI attribué `0`, orientation confirmée `0`, split `0` ;
- protocole : `docs/P6_PANORAMIC_FDI_ANNOTATION_PROTOCOL.md`.

Human clinical gate : orientation → validation géométrique → FDI → déduplication/splits → double review test → adjudication. Aucun benchmark pano lourd avant ces gates.

---

## P7–P10 / P12–P14

- P7 : PLANNED — packaging macOS natif signé/notarisé.
- P8 : PLANNED — hardware/peripherals par OS.
- P9 : PLANNED — backup/recovery/DR.
- P10 : PLANNED — update engine cross-platform. La branche `portability/p10-update-engine` est une base d’intégration ; son nom ne crédite pas P10.
- P12 : PLANNED — matrice CI/certification.
- P13 : PLANNED — certification cabinet réel.
- P14 : PLANNED — closeout permanent.

## Next exact

1. Aucun push sur la branche Windows pendant `32912896028`.
2. Résultat du run → inspecter logs/artifact une fois nécessaire.
3. En parallèle, préparer le resync P10 en conservant les changements P7/P11 de `DigitalCrown.spec` et `run.py` avec le contrat P6 fail-closed.
4. Après le run : un commit intégré final → un run exact-head final.
5. Si vert : artifact + closeout + merge #259 + post-merge → créditer P6 8 EP.
6. Pano reste au gate clinique humain, séparé du packaging.

## État courant

- P0–P5 CLOSED ✅ ;
- P6 ACTIVE — 0/8 EP ;
- P7–P10 PLANNED ;
- P11 CLOSED ✅ ;
- P12–P14 PLANNED ;
- **73/162 EP = 45,1 %** ;
- PR P6 : `#259` ;
- HEAD Windows : `e8aaa2cfd2b68bc84a777c2e07fa4e8ee7dee5fd` ;
- run Windows : `32912896028` — IN_PROGRESS au dernier contrôle ;
- aucun Vercel.
