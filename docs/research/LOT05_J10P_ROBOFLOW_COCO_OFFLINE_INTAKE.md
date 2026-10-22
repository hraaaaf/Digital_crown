# LOT05/J10P — Admission locale de l'export COCO Roboflow FDI-32

**2026-10-22 — Recherche offline, aucun entraînement ni activation clinique.** Cette étape prépare l'examen des annotations sans contourner HTTP 403, sans image clinique dans GitHub Actions, sans déploiement.

## Source et export officiel

Source exacte : https://universe.roboflow.com/dentalxray-yjztn/panoramic-dental-xray-fdi/dataset/1
Documentation éditeur pour l'export : https://roboflow.com/blog/getting-started-with-roboflow et https://roboflow.com/integration/yolov8

Le propriétaire autorisé ouvre cette version dans son propre compte Roboflow, choisit **Download Dataset → COCO JSON**, puis place l'export dans un répertoire **local et privé** autorisé pour traiter ce type de radiographies. Ne communiquer ni clé API, ni archive, ni images, ni noms de fichiers à ChatGPT, GitHub ou à une CI distante. L'export peut exiger une authentification. Ne pas contourner cette exigence.

La structure attendue de cette version annoncée par l'éditeur est `train/`, `valid/`, `test/` avec un fichier `_annotations.coco.json` par partition et les images correspondantes. Attendus version 1 : 3 032 / 315 / 156, 3 503 au total. Si le format effectif diverge, l'auditeur refuse et le schéma doit être étudié, pas accepté silencieusement.

## Exécution sur poste autorisé, en local uniquement

```bash
python experiments/lot05_j10p_roboflow_coco_offline_intake.py --dataset-dir "/chemin/local/prive/export-coco"
```

Option facultative : `--output-json "/chemin/local/prive/rapport-agrege.json"`. Ne jamais publier le rapport sans revue de contenu. Le script utilise seulement la bibliothèque standard Python ; il ne copie, n'ouvre, ne décode ni n'exporte les pixels. Aucune requête réseau. Aucun entraînement, poids, prédiction ou mAP.

## Contrôles auditables

- Exactement 32 identifiants FDI `11–18`, `21–28`, `31–38`, `41–48`, sans classe manquante ou dupliquée, sur chacune des trois partitions.
- Documents COCO valides, IDs d'images et annotations uniques, références existantes, boîtes `xywh` numériques finies et dans les limites des dimensions déclarées.
- Présence locale et absence de symlink pour les images mentionnées, extensions autorisées, blocage des chemins absolus et traversées. Il s'agit d'une vérification de présence **sans décodage** et sans analyse de métadonnées d'identification intégrées.
- Répartition et nombre d'exemples identiques à la version 1 annoncée. Comptage agrégé des boîtes, labels absents et doublons FDI possibles.
- Comparaison **heuristique** de suffixes de fichiers `.rf.<hash>` entre partitions ; une collision mérite enquête, et zéro collision ne démontre pas l'indépendance patient ni l'absence de clones augmentés.

Les tests CI de cet outil sont exécutés **uniquement sur 3 503 faux fichiers créés à la volée** avec faux COCO. Aucun corpus universitaire ou image réelle ne passe dans GitHub Actions via ce contrôle.

## Garde-fous scientifiques et juridiques

**Une validation de structure COCO n'autorise ni l'entraînement clinique/commercial, ni une revendication de reconnaissance des dents.** Les 90° rotations éditoriales et la dispersion possible de versions augmentées dans les partitions empêchent d'utiliser le split publié comme preuve d'un benchmark indépendant. Il faut obtenir les originaux, les identifiants sources/patients quand ils sont légitimement disponibles, les conditions d'acquisition, la chaîne de droits de diffusion et d'entraînement, et un ensemble de test indépendant non augmenté.

Avant toute activation : revue des annotations dent par dent par un professionnel, résolution orientation gauche/droite, patients partiellement édentés, dents surnuméraires, restaurations, implants et images incertaines ; protocole clinique, validation externe, gestion des incertitudes et revue de qualification réglementaire adaptée aux fonctions réellement envisagées.

**Règle :** jamais de données patients du cabinet pour ce banc d'essai ; pas de publication de pixels réels ou annotations nominatives ; pas de contournement authentification Roboflow/Mendeley ; pas de déploiement Vercel, merge ou activation Product.

## Critère de suite

1. **Accès/chaîne de droits** démontrés sur l'export exact, avec validation humaine.
2. **Contrat COCO** vérifié sur l'export exact via le contrôleur, sans confondre résultats synthétiques et réels.
3. **Indépendance source/patient** démontrée avec revue des images originales et des augmentations.
4. **Vérité terrain** FDI 32 revue et métriques pertinentes définies avant entraînement expérimental.
5. Décision clinique, privacy et qualification appropriées consignées. Tant que ces preuves manquent : **OPEN / NO-GO**.
