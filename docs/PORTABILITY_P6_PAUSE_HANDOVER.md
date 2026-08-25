# Portability P6 — Pause / Scientific Assets Refresh

Status: **ACTIVE / HUMAN GATE — P6 Windows packaging 0/8 EP**.

## Goal P6

Produire un installateur Windows déterministe avec les assets scientifiques exacts et autorisés, self-test frozen, install/upgrade/uninstall, conservation des données et statut de signature explicite.

## Roadmap

Source de vérité : `/PORTABILITY_LAUNCHER_ROADMAP.md`.

Portability validé : **65/162 EP = 40,1 %**. Le sous-lot Scientific Assets Refresh ne gagne aucun EP séparé.

## Packaging P6

- PR `#242` — OPEN/DRAFT, mergeable ;
- branche `portability/p6-windows-packaging-resume` ;
- HEAD publié `90b1262cb13b22172d6d0d2f36aa6eb96d360cdf` ;
- dernier heavy run `32803814701` — FAILURE après static gate + frontend build verts ;
- candidat préparé `4501ad8d167c65a64e174d923e6f1d3a36b14399` ;
- correction préparée : `protobuf==5.29.6`, `pip check`, source assets privée obligatoire.

**Ne pas lancer ce candidat lourd maintenant.** Le provisioner exige encore `panoramic_model.onnx` + `cephld_cca/ceph_weights.pth` legacy et doit être réconcilié avec le set scientifique final.

## Céphalométrie

Candidat sélectionné : `DC-Ceph-UNet29Q4 / Aariz v1`.

- training `32876308676` — SUCCESS ;
- ONNX SHA256 `809f1d3d2347d2a34f57d4a3415bb319c29f8a25c325d41160e5f28d4e5dadad` ;
- taille `7,624,307 bytes` ;
- direct-20 held-out : MRE `1.232893 mm`, SDR2 `83.1333%`, SDR4 `97.2667%` ;
- clinical claim : false ;
- `Occ_Ant`/`Occ_Post` absents ; Wits fail-closed.

Bridge exact du binaire : run `32911022192` — SUCCESS.

Protocole clinique : `docs/P6_CEPHALOMETRY_CLINICAL_VALIDATION_PROTOCOL.md`.

## Rétention privée — HUMAN GATE

Repo : `hraaaaf/DigitalCrown-assets` — PRIVATE.
Branche : `training/p6-ceph-unet29`.

Workflow : `.github/workflows/p6-ceph-winner-private-retention.yml`.
Run : `32911260037` — FAILURE.

Cause exacte :

`P6_ASSET_TOKEN secret missing`

Le runner public fonctionne et le binaire exact est récupérable. Le seul blocage de transfert est l’absence du secret Actions `P6_ASSET_TOKEN` sur `hraaaaf/Digital_crown`.

Après ajout du secret, rejouer ce run et exiger `P6_PRIVATE_RETENTION=OK` + SHA privé exact avant toute suppression/réinitialisation de la branche publique gagnante.

## Panoramique Phase A

Cible : **tooth localization + FDI enumeration**, pas diagnostic automatique de pathologies.

### Mendeley V3 first-party

Dataset `73n3kz2k4k.3`, CC BY 4.0.

- inventaire `32910249394` — SUCCESS ;
- sémantique `32910743873` — SUCCESS ;
- 111 fichiers / `84,254,649` octets ;
- 107 images metadata ;
- 25 images avec régions ;
- 772 régions ;
- 540 attributs `Teeth` et les 540 valeurs sont `""` ;
- 0 FDI source ;
- `direct_fdi_ground_truth_ready=false` ;
- 96 hashes image uniques / 11 doublons exacts.

Preuve : `docs/P6_MENDELEY_V3_PROVENANCE_RESULT.md`.

Décision : auxiliaire/image+segmentation uniquement. FDI doit être annoté cliniquement selon `docs/P6_PANORAMIC_FDI_ANNOTATION_PROTOCOL.md`, avec split groupé par SHA/source.

## Next exact

1. Ajouter `P6_ASSET_TOKEN` comme repository Actions secret du repo produit, avec accès minimal au repo privé assets.
2. Rejouer `32911260037` ; vérifier rétention + SHA privé.
3. Figer/dédupliquer le pool pano rights-cleared ; annotation FDI clinique.
4. Benchmark pano seulement après annotation/split/provenance fermés.
5. Portabilité Windows/macOS des assets finaux.
6. Réconcilier `provision_p6_scientific_assets.py` avec le set final.
7. Avancer PR `#242` et lancer **un seul** heavy Windows run.

Aucun Vercel.
