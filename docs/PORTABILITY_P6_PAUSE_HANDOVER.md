# Portability P6 — Pause / Scientific Assets Refresh

Status: **ACTIVE / HUMAN GATE — P6 Windows packaging 0/8 EP**.

## Goal

Fermer les assets scientifiques réellement packagés puis certifier un installateur Windows déterministe sans perte de données ni fuite de secrets.

## État vérifié

- roadmap canonique : `/PORTABILITY_LAUNCHER_ROADMAP.md` ;
- progression : `65/162 EP = 40,1 %` ;
- P6 : `0/8 EP` ;
- aucun Vercel.

### Packaging

- PR `#242` OPEN/DRAFT, mergeable ;
- branche `portability/p6-windows-packaging-resume` ;
- HEAD `90b1262cb13b22172d6d0d2f36aa6eb96d360cdf` ;
- dernier heavy run `32803814701` FAILURE ;
- candidat préparé `4501ad8d167c65a64e174d923e6f1d3a36b14399`.

Ne pas lancer le heavy run : le provisioner attend encore les assets legacy pano + CephLD et doit être réconcilié avec le set final.

### Céphalométrie

- gagnant : `DC-Ceph-UNet29Q4 / Aariz v1` ;
- training `32876308676` SUCCESS ;
- ONNX SHA256 `809f1d3d2347d2a34f57d4a3415bb319c29f8a25c325d41160e5f28d4e5dadad` ;
- taille `7,624,307 bytes` ;
- direct-20 MRE `1.232893 mm`, SDR2 `83.1333%`, SDR4 `97.2667%` ;
- clinical claim false ; Wits fail-closed.

Bridge courant : commit `efb56d3879a658d2db2afc99db09cfa5821a478d`, run `32911633368` SUCCESS, artifact `9586717545`. Il prouve/rend disponible le binaire exact mais **ne le retient pas dans le repo privé**.

### Human gate exact

Run privé historique `32911260037` a échoué uniquement sur :

`P6_ASSET_TOKEN secret missing`

Après création de ce secret dans `hraaaaf/Digital_crown`, limité à `hraaaaf/DigitalCrown-assets`, rejouer **ce run historique** et exiger `P6_PRIVATE_RETENTION=OK` + SHA privé exact.

Ne jamais envoyer le token dans le chat.

### Panoramique

Mendeley V3 first-party :

- `32910249394` SUCCESS inventaire ;
- `32910743873` SUCCESS sémantique ;
- 107 images metadata / 25 images avec régions / 772 régions ;
- 540 attributs `Teeth`, tous `""` ;
- 0 FDI ;
- 96 hashes uniques / 11 doublons exacts.

Décision : source auxiliaire image/segmentation uniquement. FDI clinique à produire selon `docs/P6_PANORAMIC_FDI_ANNOTATION_PROTOCOL.md`, avec split groupé par SHA/source.

## Next exact

1. Human : créer `P6_ASSET_TOKEN`.
2. Rerun `32911260037` → vérifier private retention + SHA.
3. Pool pano rights-cleared/dédupliqué → annotation FDI clinique.
4. Benchmark pano Phase A → portabilité Windows/macOS.
5. Réconcilier le provisioner.
6. Avancer PR `#242` → un seul heavy Windows run.
7. Installer/frozen smoke/install-upgrade-uninstall/signing status → closeout P6 seulement si preuves vertes.
