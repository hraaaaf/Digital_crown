# CEPH-UXCLIN-01 / R23-K — 38 points appariés CL-Detection2023, comparateur LOCAL

**Statut : OUTIL PRÊT POUR CERTIFICATION TECHNIQUE ; COMPARAISON RÉELLE BLOQUÉE PAR ABSENCE D'UNE PAIRE OFFICIELLE AUTORISÉE.** Cette documentation ne présente aucune mesure inventée. C'est un chantier distinct de R23-J (#1029) : correction d'UX approuvée, sans validation clinique.

## But exact

Comparer, sur **la même radio source**, les **38 canaux ordonnés du poids SRPose38** avec les 38 annotations humaines originales du challenge CL-Detection2023, **indice 0 du poids ↔ point 1 du challenge**, etc. Aucun nom anatomique, aucun angle SNA, aucune norme/décision clinique, aucun réentraînement. La comparaison d'un cas de TRAIN ne démontre pas la généralisation (risque de données vues à l'entraînement).

## Ce qui a été vérifié

- [Organisateurs / GitHub](https://github.com/cwwang1979/CL-detection2023) : `train-gt.json.zip`, format original `points[].name` 1..38, `point:[x,y,z]` où **z est le numéro d'image à partir de 1**, et `scale` pour mm/px ; README CC BY-NC 4.0 pour leurs annotations.
- [Radios officielles / Zenodo 7787671](https://zenodo.org/records/7787671) : `train_stack.mha` 400 images **RESTRICTED**. Accès réservé aux participants autorisés, publication / réutilisation encadrées, ne pas contourner.
- [Dépôt de notre poids](https://github.com/5k5000/CLdetection2023) : `SRPose38` checkpoint technique exact exporté vers ONNX, 38 sorties ; aucun mapping anatomique 0..37 nominatif démontré dans le dépôt source.
- [Baseline de démonstration](https://github.com/szuboy/CL-Detection2023) : un `stack1.mha` de 2 clichés et `expected_output.json` contenant des **prédictions de baseline**, NON 38 vérités humaines associées. Ne pas utiliser en tant que goldset.
- Recherche dans Google Drive du projet : `CLdetection2023` (code/checkpoint source) présent, **`train_stack.mha` absent** ; Drive ne constitue donc pas une source d'une paire vérifiée. Machine de test DESKTOP-3MAJEEH précédemment OFFLINE.
- Aariz déjà goldset mais 29 repères, et échec documenté de 23/24 points compatibles du candidat SRPose38 sous `REFERENCE_EQUIVALENCE_V1` ; résultat à conserver, n'est pas une comparaison source CL2023 des 38 indices.

## Programme

`scripts/compare_srpose38_cl2023_38.py` réalise **tout localement**, sans réseau, sur une machine autorisée :
1. Refuse toute exécution sans confirmation de droits d'accès `--confirm-dataset-rights` (**ce drapeau ne procure aucun droit**).
2. Lit **la slice z correspondant exactement au `--case-id`** dans un MHA brut LOCAL, avec seek positionnel sans charger 400 radios. Format non pris en charge (compressé, mauvais nombre de canaux/dimensions) = FAIL, aucun « repli » supposant une identité image.
3. Lit `train-gt.json` ou `train-gt.json.zip` officiel, exige exactement **38 indices uniques** pour le même z, coordonnées finies, scale positif cohérent, aucune annotation hors cadre après recadrage officiel du bas/droite.
4. Vérifie modèle exact `267484931` octets et SHA256 `a5ecd466d6d2c4ef02e145a143076a05720c0be56a260224812c23e2ecf42ddb`, et `backend/scientific_assets.json`, puis fait l'authentique inférence ONNX CPU et son décodage DarkPose depuis le runtime Digital Crown.
5. Produit `channels.csv` pour **38 canaux** (GT x/y, préd x/y, dx/dy px, distance px, mm, état in-frame), `overlay_local_only.png` avec anneaux verts (GT), points rouges (prédictions) et vecteurs jaunes d'erreur ; `report.json` avec hash source image/GT et modèle, explicitement **non-clinical** et **not independent**.
6. Le p95 résultant est seulement **le 95e percentile des 38 distances sur une seule radio**, pas un p95 statistique sur un ensemble de patients.
7. **Aucune radiographie ni annotation originale ne doit être uploadée sur GitHub, Cloud CI, Drive partagé ou des endpoints non autorisés.** Les sorties restent sur la machine locale autorisée.

Exemple **à exécuter UNIQUEMENT après permission explicite du déposant** :

```bash
python scripts/compare_srpose38_cl2023_38.py \
  --mha /chemin/autorise/train_stack.mha \
  --gt /chemin/autorise/train-gt.json.zip \
  --case-id 1 \
  --model backend/ai_models/srpose38-tta-1024.onnx \
  --output /chemin/prive/r23k-case-1 \
  --confirm-dataset-rights
```

Le test `--check-pair-only` vérifie la paire SANS inférence et écrit `PAIR_VERIFIED_MODEL_NOT_RUN`. Un *PASS* de tests synthétiques CI vérifie le logiciel de comparaison, PAS une mesure vraie.

## Limites obligatoires

- Pour une comparaison **indépendante** à la sortie du challenge, le train 400 cas est insuffisant. Il faut des cas d'acceptance non vus + annotations accessibles légalement selon l'accord.
- **Légitimité dataset et checkpoint** : droit challenge ne signifie pas droit d'utilisation commerciale des clichés, et Apache-2.0 sur code source n'est pas forcément la licence du poids distribué sur Drive.
- L'index du canal modèle peut être validé opérationnellement par la comparaison numérotée, mais cela ne prouve pas le nom anatomique canonique S/N/A pour chaque canal. Aucun label clinique « correct » n'est auto-inféré.
- La proposition conserve **CLINICAL NO-GO**, `CEPH_DETECTOR_SELECTED` NON satisfait et 41/99 inchangé.
- PR DRAFT, **aucun merge, déploiement, Production**.

## Droits d'accès : action externe non réalisée

Le déposant exige un formulaire d'inscription / autorisation à [Grand Challenge](https://cl-detection2023.grand-challenge.org/) avec les contacts publiés : Prof. Ching-Wei Wang `cweiwang@mail.ntust.edu.tw` et Hikam Muzakky `m11123801@mail.ntust.edu.tw`. Le projet devrait demander **l'autorisation actuelle pour un test de recherche comparatif non publié et un seul cas apparié**, sans envoyer de données ou engager une licence sans confirmation. Aucun email d'accès n'a été envoyé.

## Définition de done

**Outil interne test-only vert** et preuve réelle source-pair vérifiée (fichier original et GT même case z + droits d'usage), 38 distances/overlays extraits du véritable poids hashé. Tant que la paire est absente : **R23-K = BLOCKED_BY_RESTRICTED_IMAGE**, même si les tests parser sont verts.
