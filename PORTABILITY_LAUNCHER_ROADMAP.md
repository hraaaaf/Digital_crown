# Portability & Launcher — roadmap canonique

Dernière mise à jour vérifiée : 2026-08-26.

> **Source de vérité unique du chantier.** `docs/PORTABILITY_LAUNCHER_ROADMAP.md` est déprécié et renvoie ici.

## Goal global

Un seul Digital Crown local-first, cœur partagé Windows/macOS, installable, restaurable, updatable et certifiable avec données cabinet, licence/secrets, assets scientifiques et hardware maîtrisés.

## Doctrine

- un cœur React/FastAPI commun ;
- frontières OS explicites ;
- données cabinet distinctes des secrets machine ;
- aucun asset scientifique non autorisé dans le repo produit public ;
- une dépendance importable n’est pas une preuve clinique ;
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
| P11 — Launcher & Recovery UX | 8 | PLANNED |
| P12 — CI & certification matrix | 13 | PLANNED |
| P13 — Real cabinet certification | 13 | PLANNED |
| P14 — Closeout | 5 | PLANNED |
| **TOTAL** | **162** | |

Aucun EP partiel n’est crédité pour un lot ouvert.

## P0–P5 — état fermé

- P0 : baseline de portabilité fermée.
- P1 : PR `#219`, Portability `32599659706` SUCCESS Windows/macOS/Ubuntu.
- P2 : PR `#220`, Runtime `32601811079` SUCCESS Windows/macOS/Ubuntu.
- P3 : PR `#222`, bundle cabinet/restore inter-OS ; CI `32605929015` SUCCESS.
- P4 : PR `#224`, secrets/licence/restore cross-platform ; CI `32610745134` SUCCESS.
- P5 : PR `#233`, candidat `3ee3447e1cd3d92575e3b930abeef8e31061bfb8`, natif `32750343308` SUCCESS Windows x64 + macOS ARM64, CI `32750343210` SUCCESS.

Validé avant P6 : **65 EP**.

---

# P6 — Industrialized Windows packaging — ACTIVE — 0/8 EP

## Goal

Produire un artefact Windows déterministe, installable/upgradeable/uninstallable sur machine propre, sans fuite de secrets ni perte de données, avec les assets scientifiques réellement autorisés et fail-closed.

## Packaging

- PR `#242` — OPEN/DRAFT, mergeable ;
- branche `portability/p6-windows-packaging-resume` ;
- HEAD publié `90b1262cb13b22172d6d0d2f36aa6eb96d360cdf` ;
- dernier heavy run `32803814701` — FAILURE après static gate + frontend build verts ;
- candidat préparé `4501ad8d167c65a64e174d923e6f1d3a36b14399` : `protobuf==5.29.6`, `pip check`, source scientifique privée.

**Ne pas lancer le heavy run maintenant.** `scripts/provision_p6_scientific_assets.py` exige encore les assets legacy `panoramic_model.onnx` et `cephld_cca/ceph_weights.pth`. Le provisioner doit être réconcilié avec le set scientifique final.

---

## Sous-lot P6 Scientific Assets Refresh

Ce sous-lot est un prérequis de P6, pas un lot EP autonome.

### Céphalométrie — gagnant technique verrouillé

`DC-Ceph-UNet29Q4 / Aariz v1`

- training scellé `32876308676` — SUCCESS ;
- ONNX SHA256 `809f1d3d2347d2a34f57d4a3415bb319c29f8a25c325d41160e5f28d4e5dadad` ;
- taille `7,624,307 bytes` ;
- direct-20 held-out : MRE `1.232893 mm`, SDR2 `83.1333%`, SDR4 `97.2667%` ;
- `clinical_claim=false` ;
- `Occ_Ant` / `Occ_Post` absents ; Wits fail-closed ;
- protocole clinique : `docs/P6_CEPHALOMETRY_CLINICAL_VALIDATION_PROTOCOL.md`.

### Binaire gagnant — récupération exacte prouvée

- bridge initial `32911022192` — SUCCESS ;
- bridge courant sans secret `32911633368` — SUCCESS ;
- artifact `9586717545`, digest `sha256:3ed73e3d39325d5b880e72264ac2a8a25996aa5eaef7bedd1a14b76d9b03ec55` ;
- source winner exacte et SHA/size vérifiés avant artifact.

Le binaire est donc récupérable sans réentraînement.

### Rétention privée — NON FERMÉE

Repo cible : `hraaaaf/DigitalCrown-assets` — PRIVATE.
Branche cible : `training/p6-ceph-unet29`.

Tentative de transfert privé `32911260037` : FAILURE au premier gate, log exact `P6_ASSET_TOKEN secret missing`; aucune copie privée n’a été exécutée.

Le commit scientifique courant `efb56d3879a658d2db2afc99db09cfa5821a478d` a ensuite transformé `.github/workflows/p6-ceph-winner-private-retention.yml` en **Binary Bridge sans secret**, run `32911633368` SUCCESS. Ce workflow produit l’artifact vérifié mais **ne constitue pas une rétention privée**.

Le prochain transfert privé doit donc utiliser un credential inter-repo explicite. Le chemin déjà prouvé et rerunnable est le run historique `32911260037` après ajout du secret `P6_ASSET_TOKEN` avec accès minimal au repo privé.

Aucune rétention privée n’est créditée avant présence du modèle dans `DigitalCrown-assets` et vérification du SHA exact.

---

## Panoramique Phase A

Cible : **localisation dentaire + FDI**, pas diagnostic automatique de pathologies.

### Mendeley V3 `10.17632/73n3kz2k4k.3`

First-party fermé :

- inventaire `32910249394` — SUCCESS ;
- sémantique `32910743873` — SUCCESS ;
- 111 fichiers / `84,254,649` octets ;
- 107 images metadata ;
- 25 images avec régions ;
- 772 régions ;
- 540 attributs `Teeth`, **540 valeurs `""`** ;
- 0 code FDI / 0 région FDI ;
- `direct_fdi_ground_truth_ready=false` ;
- 96 hashes image uniques / 11 doublons exacts.

Décision : **auxiliaire image/segmentation, jamais vérité FDI directe**. Le vieux miroir « 3 images » était incomplet ; la conclusion sans FDI est maintenant prouvée first-party.

Preuve : `docs/P6_MENDELEY_V3_PROVENANCE_RESULT.md`.
Protocole : `docs/P6_PANORAMIC_FDI_ANNOTATION_PROTOCOL.md`.

Tout split futur doit être groupé par SHA/source avant train/validation/test.

---

## Next exact P6

1. **Human gate** : créer le secret Actions `P6_ASSET_TOKEN` dans `hraaaaf/Digital_crown`, avec accès minimal nécessaire à `hraaaaf/DigitalCrown-assets`; ne jamais coller le token dans le chat.
2. Rejouer le run historique `32911260037`; exiger `P6_PRIVATE_RETENTION=OK` + SHA privé exact.
3. Figer le pool pano rights-cleared + dédupliqué ; produire la vérité FDI clinique.
4. Benchmark pano Phase A seulement après droits/annotations/split fermés.
5. Portabilité Windows x64 + macOS ARM64 des assets finaux.
6. Réconcilier le provisioner P6 avec le set scientifique final.
7. Avancer PR `#242` puis lancer **un seul heavy Windows run**.
8. P6 ne ferme qu’après build + frozen smoke + install/upgrade/uninstall + préservation données + statut signing vérifiés.

---

## P7–P14

- P7 : packaging macOS natif signé/notarisé.
- P8 : matrice hardware/peripherals par OS.
- P9 : backup/recovery/DR.
- P10 : update engine cross-platform avec rollback.
- P11 : launcher/recovery UX avec BEFORE → mockup → AFTER.
- P12 : matrice CI/certification Windows/macOS.
- P13 : certification cabinet réel sur machines propres.
- P14 : closeout permanent docs/gouvernance/preuves.

## État courant

- P0–P5 CLOSED ✅ ;
- P6 ACTIVE — 0/8 EP ;
- P7–P14 PLANNED ;
- **65/162 EP = 40,1 %** ;
- aucun Vercel ;
- blocage réel actuel : rétention privée du gagnant céphalo nécessitant un credential inter-repo.
