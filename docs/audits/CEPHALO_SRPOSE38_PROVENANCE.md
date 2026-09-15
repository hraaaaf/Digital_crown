# Céphalo-N — Provenance SRPose38 / CL-Detection2023

Statut : **SOURCE-LOCK EXTERNE — MAPPING ANATOMIQUE NON DÉMONTRÉ**

Date : 2026-09-15

Dépend de : `docs/audits/CEPHALO_LANDMARKS_PLANES_SOURCE_LOCK.md`

## Goal / Succès / Preuve

**Goal** — déterminer si le mapping `sortie SRPose38 index 0..37 → landmark anatomique` peut être prouvé depuis les sources amont officielles.

**Succès** — soit un mapping anatomique officiel et versionné est trouvé et recoupé, soit l’absence de preuve est formellement documentée et l’activation automatique reste fail-closed.

**Preuve** — dépôt officiel CL-Detection2023-MMPose, dépôt baseline CL-Detection2023, publication de description du dataset CL-Detection et ressource Zenodo du challenge.

## Sources amont vérifiées

### 1. Baseline officielle CL-Detection2023-MMPose

Dépôt : `szuboy/CL-Detection2023-MMPose`.

Le fichier officiel :

`mmpose_package/mmpose/configs/_base_/datasets/cephalometric.py`

définit exactement 38 catégories, indexées `0..37`.

Point crucial : les champs `name` sont eux-mêmes purement numériques (`'0'`, `'1'`, …, `'37'`). Le fichier ne fournit **aucun nom anatomique**, aucune définition anatomique, aucun alias clinique et aucun couple index→landmark.

Conclusion : cette source officielle prouve l’ordre numérique des 38 sorties, **mais pas leur sémantique anatomique**.

### 2. README officiel CL-Detection2023-MMPose

Le README décrit le format de soumission avec des points nommés `1..38` comme catégories de keypoints. Il ne fournit pas non plus de dictionnaire anatomique.

### 3. Baseline officielle CL-Detection2023

Le dépôt baseline décrit un réseau de heatmaps à **38 canaux** et l’extraction d’un point par maximum de heatmap. Là encore, le contrat public trouvé est numérique, pas anatomique.

### 4. Publication CL-Detection

La publication de description du challenge/dataset confirme :

- 600 téléradiographies latérales dans CL-Detection2023 ;
- 38 landmarks par image ;
- challenge MICCAI CL-Detection2023.

Elle confirme l’existence et la cardinalité du jeu de landmarks mais ne fournit pas, dans les éléments publics vérifiés ici, un tableau officiel exploitable `index → nom anatomique`.

### 5. Zenodo CL-Detection2024

La ressource officielle 2024 décrit l’extension du challenge : 53 landmarks au total, avec catégories soft-tissue / tooth / skull / cervical spine / ruler. Elle confirme la filiation du dataset, mais ne résout pas le dictionnaire anatomique 2023 indexé 0..37.

---

# Verdict scientifique

## Vérifié

- Le runtime Digital Crown `SRPose38` produit 38 sorties.
- La baseline officielle CL-Detection2023 produit 38 catégories.
- Le contrat MMPose officiel les indexe `0..37` et les nomme uniquement par leurs indices numériques.
- Le format de soumission du challenge utilise des catégories `1..38`.

## Non démontré

- `index 0..37 → S/N/A/B/Po/Or/...`
- équivalence entre les indices SRPose38 Digital Crown et un vocabulaire clinique particulier ;
- présence de tous les landmarks requis par Steiner/Tweed/McNamara/Ricketts dans ces 38 sorties ;
- distinction automatique de points cliniquement voisins (`Pog` dur vs `Pog'`, `Gn` anatomique vs construit, `Pt` vs `PTM`, bord incisif vs surface labiale coronaire).

## Décision fail-closed

Le mapping anatomique SRPose38 reste :

`SOURCE_LOCK_REQUIRED`

Il est **interdit** d’activer de nouveaux calculs cliniques en attribuant des noms anatomiques aux indices 0..37 par inférence visuelle, proximité avec l’ISBI-19, littérature secondaire non contractuelle ou correspondance géométrique approximative.

---

# Chemins acceptables pour lever le gate

Un seul des chemins suivants est acceptable :

1. retrouver le dictionnaire d’annotation original distribué avec le jeu d’entraînement CL-Detection2023 et vérifier son identité avec le modèle Digital Crown ;
2. retrouver une source officielle des organisateurs donnant explicitement les définitions anatomiques des catégories 1..38 ;
3. obtenir le contrat/export ayant servi à entraîner le modèle ONNX réellement embarqué dans Digital Crown ;
4. créer un nouveau contrat Digital Crown par annotation clinique manuelle contrôlée et validation indépendante sur un jeu de référence, sans prétendre qu’il s’agit du contrat historique du modèle.

Le chemin 4 constitue une **nouvelle validation de modèle**, pas une simple documentation.

---

# Conséquence sur le chantier

La phase suivante peut continuer pour :

- formaliser les IDs scientifiques des landmarks ;
- réutiliser les landmarks déjà explicitement fournis par les contrats actuels ;
- versionner les plans/lignes dont les points sont source-lockés ;
- écrire des tests géométriques isolés sur fixtures explicites.

Elle ne peut pas :

- déclarer que SRPose38 détecte automatiquement un nouveau landmark clinique sans mapping prouvé ;
- substituer un alias logiciel à une définition anatomique ;
- activer les mesures dépendant de points encore `MISSING` / `SOURCE_LOCK_REQUIRED` / `BLOCKED_MODALITY`.

## Next exact

Chercher en priorité dans les artefacts d’entraînement/modèle réellement utilisés par Digital Crown un manifeste d’annotations ou un mapping de classes. À défaut, conserver SRPose38 comme sortie numérique et poursuivre les contrats géométriques uniquement sur landmarks explicitement identifiés.