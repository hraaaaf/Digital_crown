# P6 Scientific Assets Refresh

Status: **ACTIVE — CEPH WINNER TECHNIQUE PROUVÉ; MENDELEY V3 FIRST-PARTY FERMÉ; RÉTENTION PRIVÉE BLOQUÉE PAR SECRET MANQUANT; FDI CLINIQUE PANO ENCORE OUVERT**.

Ce sous-lot scientifique est un prérequis de Portability P6 (`Industrialized Windows packaging`). Il ne remplace pas P6 et ne crédite aucun EP Portability à lui seul.

## Goal

Remplacer les assets scientifiques historiques par des candidats dont provenance, droits, métriques, contrats runtime et comportement fail-closed sont démontrés, puis fournir à P6 un set réellement autorisé à packager.

## Succès

1. provenance + hashes exacts ;
2. benchmark technique scellé ;
3. contrat produit explicite et fail-closed ;
4. chaîne de droits compatible avec un produit propriétaire commercial ;
5. binaire gagnant retenu dans le repo privé ;
6. portabilité Windows x64 + macOS ARM64 ;
7. validation clinique séparée des métriques de benchmark ;
8. aucune vérité FDI synthétisée géométriquement.

---

## Céphalométrie — candidat sélectionné

### DC-Ceph-UNet29Q4 / Aariz v1

- dataset : Aariz v1, DOI `10.6084/m9.figshare.27986417.v1`, CC BY 4.0 ;
- dataset SHA256 : `d9fa872b36065dac9615cfcad0c7512c450fe2d86a1839cdec4cbe001def33ea` ;
- training run : `32876308676` — **SUCCESS** ;
- evidence commit : `1da113b8776aa2b57e42ac194f12b7a48b01558c` ;
- meilleur epoch : `24` ;
- modèle entraîné from scratch par Digital Crown ;
- ONNX opset 17 ; input `[1,1,512,512]` ; output `[1,29,128,128]` ;
- ONNX SHA256 : `809f1d3d2347d2a34f57d4a3415bb319c29f8a25c325d41160e5f28d4e5dadad` ;
- taille : `7,624,307 bytes` ;
- Linux ORT CPU median : `115.28 ms` ;
- `clinical_claim=false`.

### Held-out test

All-29 :
- MRE `1.369337 mm` ;
- SDR2 `80.1839%` ;
- SDR4 `95.6782%`.

Digital Crown direct-20 :
- MRE `1.232893 mm` ;
- SDR2 `83.1333%` ;
- SDR4 `97.2667%`.

Référence Aariz publiée utilisée comme benchmark : MRE `1.789 mm`, SDR2 `78.44%`, SDR4 `94.44%`.

### Contrat Digital Crown

`CephaloEngine` consomme 22 points canoniques :
`S, N, Po, Or, A, B, Go, Me, U1i, U1a, L1i, L1a, Prn, Pog_soft, Sn, Ls, Li, Co, Gn, ANS, Occ_Ant, Occ_Post`.

Aariz couvre directement 20/22. `Occ_Ant` et `Occ_Post` ne sont pas synthétisés. Wits reste manuel/fail-closed tant qu’une définition clinique séparée du plan occlusal n’est pas validée.

Protocole clinique préparé : `docs/P6_CEPHALOMETRY_CLINICAL_VALIDATION_PROTOCOL.md`.

---

## Récupération du binaire gagnant — PROUVÉE

Le blob Git public existe mais le connecteur GitHub ne peut pas transférer ce binaire directement. La stratégie a donc été changée vers un bridge Actions public contrôlé.

- workflow : `.github/workflows/p6-ceph-winner-transfer-bridge.yml` ;
- run : `32911022192` — **SUCCESS** ;
- le runner a checkout le commit gagnant exact ;
- taille vérifiée : `7,624,307 bytes` ;
- SHA256 vérifié : `809f1d3d2347d2a34f57d4a3415bb319c29f8a25c325d41160e5f28d4e5dadad` ;
- handoff artifact temporaire : `9586526569`.

Conclusion : le binaire exact est récupérable sans réentraînement.

---

## Rétention privée — BLOQUÉE HUMAIN

Repo cible : `hraaaaf/DigitalCrown-assets` — PRIVATE.
Branche cible : `training/p6-ceph-unet29`.

Workflow prêt : `.github/workflows/p6-ceph-winner-private-retention.yml`.

Run `32911260037` : **FAILURE** au premier gate uniquement.

Preuve exacte du log :

`P6_ASSET_TOKEN secret missing`

`GH_TOKEN` était vide. Toutes les étapes de checkout/clone/copie/commit privé ont été skipped.

Le blocage n’est donc plus scientifique ni lié au binaire. Il manque le secret Actions `P6_ASSET_TOKEN` dans `hraaaaf/Digital_crown`, avec accès minimal au repo privé `hraaaaf/DigitalCrown-assets`.

Aucune rétention privée n’est créditée avant un run montrant `P6_PRIVATE_RETENTION=OK` et le SHA privé exact.

---

## Panoramique — contrat produit

La route produit active doit restaurer **tooth localization + FDI enumeration**. La sémiologie/pathologie automatique n’est pas requise pour Phase A ; les findings cliniques restent praticien/déterministes.

Le legacy `detect_teeth_only()` s’appuie sur un modèle de pathologies puis infère FDI géométriquement. Cette architecture est dette technique et ne constitue pas la cible scientifique.

---

## Mendeley V3 `73n3kz2k4k.3` — FIRST-PARTY FERMÉ

DOI : `10.17632/73n3kz2k4k.3`.
Record : CC BY 4.0.

### Probe exact

- inventaire run `32910249394` — SUCCESS ;
- sémantique run `32910743873` — SUCCESS ;
- 111 fichiers ;
- `84,254,649` octets téléchargés ;
- 107 entrées image dans `annotations.json` ;
- 25 images avec régions ;
- 772 régions ;
- polygons 676 ; polylines 96 ;
- `annotations.json` SHA256 `b6de2c396cb76758227562798141a00fb5d769f9d8f9eb3919470f4ff23578bd`.

### Vérité `Teeth`

- 540 régions possèdent l’attribut `Teeth` ;
- les **540 valeurs exactes sont `""`** ;
- 0 token dentaire ;
- 0 code FDI ;
- 0 région FDI ;
- `source_fdi_labels_present=false` ;
- `direct_fdi_ground_truth_ready=false`.

L’ancien miroir public n’exposait que 3 images annotées : il était incomplet. La conclusion FDI reste toutefois confirmée, désormais par la source first-party exhaustive : **aucune vérité FDI source**.

Preuve dédiée : `docs/P6_MENDELEY_V3_PROVENANCE_RESULT.md`.

### Déduplication

Les 107 images représentent seulement **96 SHA256 uniques** : **11 doublons exacts**.

Tout futur split train/validation/test doit être groupé par SHA/source avant séparation afin d’éviter toute fuite inter-split.

### Décision V3

**ELIGIBLE AUXILIARY / IMAGE + SEGMENTATION SOURCE; NOT DIRECT-FDI GROUND TRUTH.**

Le dataset peut servir de pool d’images/segmentation sous ses droits, mais le FDI doit venir d’une annotation clinique traçable selon `docs/P6_PANORAMIC_FDI_ANNOTATION_PROTOCOL.md`.

---

## Autres leads panoramiques

- Humans in the Loop `5884500` : annotations CC0 prometteuses, mais chaîne de droits upstream images López `4457648` non suffisamment fermée → HOLD commercial.
- AKUDENTAL : direct FDI mais CC BY-NC-SA 4.0 → recherche uniquement.
- Zhou dual-labeled : FDI expert, licence dataset non fermée → HOLD.
- TL-pano : non-commercial explicite → recherche uniquement.
- STS-2D / STS-2024 : conflit/ambiguïté de droits → HOLD.
- Roboflow Panoramic-Dental-Xray-FDI : page CC BY 4.0 mais provenance amont insuffisante → HOLD.

Aucun de ces datasets n’est actuellement benchmark-authorized pour entraîner commercialement le modèle FDI Digital Crown.

---

## Packaging P6 — dépendance scientifique encore ouverte

PR packaging : `#242` — OPEN/DRAFT, mergeable.
Branche : `portability/p6-windows-packaging-resume`.
HEAD publié : `90b1262cb13b22172d6d0d2f36aa6eb96d360cdf`.
Candidat préparé : `4501ad8d167c65a64e174d923e6f1d3a36b14399`.

Le candidat corrige notamment `protobuf==5.29.6`, ajoute `pip check` et exige un repo scientifique privé.

Mais `scripts/provision_p6_scientific_assets.py` exige encore le set legacy :
- `backend/ai_models/panoramic_model.onnx` ;
- `backend/ai_models/cephld_cca/ceph_weights.pth` ;
- sources CephLD.

Ce provisioner n’est donc **pas encore compatible avec le set scientifique final**. Le pousser et lancer le benchmark Windows maintenant serait prématuré et risquerait de réintroduire des poids legacy non qualifiés.

---

## Décisions verrouillées

- DC-Ceph-UNet29Q4 / Aariz v1 = gagnant technique céphalo.
- Pas de claim clinique depuis le benchmark public.
- Pas de synthèse `Occ_Ant`/`Occ_Post`; Wits fail-closed.
- Binaire céphalo exact récupérable et vérifié.
- Rétention privée bloquée uniquement par `P6_ASSET_TOKEN` absent.
- Mendeley V3 = aucune vérité FDI source ; 25 images annotées/772 régions, pas 3.
- 107 images V3 = 96 hashes uniques / 11 doublons exacts ; split futur groupé par SHA.
- Panoramique Phase A = localisation/FDI uniquement.
- Pas de modèle legacy réinjecté pour faire passer packaging.
- Aucun heavy pano benchmark avant droits + annotations FDI + dedup/splits fermés.
- Aucun Vercel.

## Next exact

1. Human gate : ajouter le secret GitHub Actions `P6_ASSET_TOKEN` au repo produit, limité à `hraaaaf/DigitalCrown-assets` avec droits nécessaires au push privé.
2. Rejouer le run de rétention et exiger `P6_PRIVATE_RETENTION=OK` + SHA privé exact.
3. Figer le pool pano rights-cleared + dédupliqué et appliquer le protocole FDI clinique.
4. Ensuite seulement : benchmark Phase A pano → portabilité Windows/macOS.
5. Réconcilier le provisioner P6 avec les assets finaux.
6. Lancer un seul heavy Windows packaging run lorsque toutes les gates sont réellement vertes.

## Portability EP

P0–P5 = `65 EP` validés. P6 reste `0/8 EP`. Avancement canonique : **65/162 = 40,1 %**.
