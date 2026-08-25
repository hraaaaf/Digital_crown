# P6 Scientific Assets Refresh

Status: **ACTIVE — CEPH TECHNIQUE FERMÉ; MENDELEY V3 FIRST-PARTY FERMÉ; RÉTENTION PRIVÉE ET FDI CLINIQUE PANO OUVERTS**.

Ce sous-lot ne remplace pas Portability P6 et ne crédite aucun EP.

## Goal

Fournir à P6 des assets scientifiques reproductibles, légalement utilisables, techniquement qualifiés, portables et fail-closed, sans transformer un benchmark en claim clinique.

## Céphalométrie

Candidat sélectionné : `DC-Ceph-UNet29Q4 / Aariz v1`.

- training `32876308676` — SUCCESS ;
- evidence commit `1da113b8776aa2b57e42ac194f12b7a48b01558c` ;
- dataset Aariz v1, DOI `10.6084/m9.figshare.27986417.v1`, CC BY 4.0 ;
- dataset SHA256 `d9fa872b36065dac9615cfcad0c7512c450fe2d86a1839cdec4cbe001def33ea` ;
- ONNX SHA256 `809f1d3d2347d2a34f57d4a3415bb319c29f8a25c325d41160e5f28d4e5dadad` ;
- taille `7,624,307 bytes` ;
- direct-20 held-out : MRE `1.232893 mm`, SDR2 `83.1333%`, SDR4 `97.2667%` ;
- `clinical_claim=false` ;
- `Occ_Ant`/`Occ_Post` non synthétisés ; Wits fail-closed.

Protocole clinique préparé : `docs/P6_CEPHALOMETRY_CLINICAL_VALIDATION_PROTOCOL.md`. Il n’est pas exécuté et ne constitue pas une certification clinique.

## Binaire céphalo

La récupération exacte est prouvée sans réentraînement :

- bridge `32911022192` — SUCCESS ;
- bridge courant `32911633368` — SUCCESS ;
- artifact `9586717545` ;
- digest artifact `sha256:3ed73e3d39325d5b880e72264ac2a8a25996aa5eaef7bedd1a14b76d9b03ec55` ;
- SHA et taille du modèle vérifiés avant upload.

## Rétention privée — OPEN / HUMAN GATE

Cible : `hraaaaf/DigitalCrown-assets`, branche `training/p6-ceph-unet29`.

Run de transfert privé `32911260037` : FAILURE au premier gate avec `P6_ASSET_TOKEN secret missing`; aucune étape de transfert n’a exécuté de copie.

Le commit `efb56d3879a658d2db2afc99db09cfa5821a478d` a ensuite repurposé `.github/workflows/p6-ceph-winner-private-retention.yml` en bridge binaire sans secret. Son run `32911633368` est vert, mais il ne pousse rien dans le repo privé.

La rétention reste donc non prouvée. Après création de `P6_ASSET_TOKEN`, le run historique `32911260037` peut être rejoué et doit produire `P6_PRIVATE_RETENTION=OK` ainsi que le SHA privé exact.

## Panoramique — contrat Phase A

Le produit doit automatiser **tooth localization + FDI enumeration**. La pathologie automatique reste hors scope Phase A ; la sémiologie clinique est praticien/déterministe.

## Mendeley V3 — first-party truth

Dataset `73n3kz2k4k.3`, DOI `10.17632/73n3kz2k4k.3`, record CC BY 4.0.

- inventaire `32910249394` — SUCCESS ;
- sémantique `32910743873` — SUCCESS ;
- 111 fichiers / `84,254,649` octets ;
- 107 images metadata ; 25 annotées ; 772 régions ;
- `annotations.json` SHA256 `b6de2c396cb76758227562798141a00fb5d769f9d8f9eb3919470f4ff23578bd` ;
- 540 régions ont une clé `Teeth`; les 540 valeurs sont `""` ;
- 0 code FDI ; 0 région FDI ;
- `direct_fdi_ground_truth_ready=false`.

Le miroir ancien limité à trois images était incomplet. La source first-party confirme cependant plus fortement la même conclusion : **pas de vérité FDI source**.

Les 107 images représentent **96 hashes uniques**, donc 11 doublons exacts. Les splits futurs doivent être groupés par SHA/source.

Preuve : `docs/P6_MENDELEY_V3_PROVENANCE_RESULT.md`.

Décision : Mendeley V3 est un candidat auxiliaire image/segmentation, pas un corpus direct-FDI.

## Autres leads pano

- Humans in the Loop : HOLD tant que droits upstream images non fermés.
- AKUDENTAL : recherche-only, non-commercial.
- Zhou dual-labeled : HOLD licence.
- TL-pano : recherche-only non-commercial.
- STS : HOLD droits.
- Roboflow FDI : HOLD provenance.

Aucun corpus direct-FDI n’est actuellement autorisé pour un entraînement commercial Digital Crown.

## Packaging P6

PR `#242`, branche `portability/p6-windows-packaging-resume`, HEAD `90b1262cb13b22172d6d0d2f36aa6eb96d360cdf`.
Candidat préparé `4501ad8d167c65a64e174d923e6f1d3a36b14399`.

Ne pas lancer le heavy run : `provision_p6_scientific_assets.py` attend encore `panoramic_model.onnx` + `cephld_cca/ceph_weights.pth` legacy. Le provisioner doit être aligné sur le set final plutôt que nourri avec des poids historiques non prouvés.

## Next exact

1. Créer `P6_ASSET_TOKEN` dans Actions secrets du repo produit, limité au repo privé assets ; ne pas le coller dans le chat.
2. Rejouer `32911260037` et prouver rétention + SHA privé.
3. Pool pano rights-cleared/dédupliqué → annotation FDI clinique selon `docs/P6_PANORAMIC_FDI_ANNOTATION_PROTOCOL.md`.
4. Benchmark Phase A pano après droits/labels/splits fermés.
5. Portabilité des assets finaux Windows/macOS.
6. Réconcilier le provisioner.
7. Un seul heavy Windows packaging run.

Portability : **65/162 = 40,1 %**, P6 = **0/8 EP**. Aucun Vercel.
