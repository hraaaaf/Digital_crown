# Céphalo-N — Provenance SRPose38 / CL-Detection2023

Statut : **SOURCE-LOCK TERMINÉ — MAPPING LOGICIEL LOCAL PRÉSENT, SÉMANTIQUE ANATOMIQUE AMONT NON DÉMONTRÉE**

Date : 2026-09-15

Dépend de : `docs/audits/CEPHALO_LANDMARKS_PLANES_SOURCE_LOCK.md`

## Goal / Succès / Preuve

**Goal** — déterminer si le mapping `sortie SRPose38 index 0..37 → landmark anatomique` utilisé par Digital Crown peut être prouvé depuis le modèle réellement embarqué, son checkpoint source ou les sources officielles du challenge.

**Succès** — soit un mapping anatomique officiel et versionné est trouvé et recoupé, soit la limite de preuve est formellement documentée et toute extension clinique reste fail-closed.

**Preuve** — runtime Digital Crown, historique Git, PR de certification ONNX, dépôt source exact du checkpoint SRPose, métadonnées MMPose du dataset et dépôts officiels CL-Detection2023.

---

# 1. Modèle réellement certifié dans Digital Crown

Le runtime actuel fixe :

- modèle : `srpose38-tta-1024.onnx` ;
- SHA256 ONNX : `a5ecd466d6d2c4ef02e145a143076a05720c0be56a260224812c23e2ecf42ddb` ;
- taille : `267484931` octets ;
- provider certifié : `CPUExecutionProvider` ;
- sortie attendue : exactement `38` heatmaps `1024×1024`.

La PR #388 documente la provenance de cet asset :

- modèle : `SRPose / CL-Detection 2023` ;
- dépôt source : `5k5000/CLdetection2023` ;
- commit source : `18d17d1934970016e7610c4849311900b8d1f191` ;
- checkpoint SHA256 : `fb1a781ac1c83149b379cb15724e3b0fae06ba2d567978f35c61e9d06b46fdcc` ;
- export/certification ONNX : PR #377, run `34281082926` ;
- runtime parity intégrée : PR #388.

La certification prouve la **parité numérique et géométrique des 38 sorties**. Elle ne prouve pas leur nom anatomique.

## 1.1 Contrat du checkpoint source exact

Dans le commit source exact `18d17d...`, le fichier :

`mmpose_package/mmpose/configs/_base_/datasets/cephalometric.py`

définit `keypoint_info` de `0` à `37`, mais chaque entrée porte uniquement un nom numérique :

`0 -> "0"`, `1 -> "1"`, …, `37 -> "37"`.

Il ne contient :

- aucun nom anatomique ;
- aucune définition clinique ;
- aucun alias S/N/A/B/Po/Or/etc. ;
- aucun dictionnaire permettant de démontrer le mapping Digital Crown.

Le script de conversion du dataset source conserve également les annotations comme `landmark_1 ... landmark_38` / catégories numériques.

**Conclusion vérifiée** : le checkpoint dont dérive l’ONNX Digital Crown a un ordre de 38 catégories stable, mais son dépôt source public ne fournit pas la sémantique anatomique de ces catégories.

---

# 2. Mapping présent dans Digital Crown

Contrairement à l’hypothèse initiale de ce lot, Digital Crown possède bien un mapping logiciel local dans :

`backend/services/sota_vision_service.py`

avec notamment :

`0:S, 1:N, 2:Or, 3:Po, 4:A, 5:B, ... 37:L6`.

Le code actuel précise explicitement :

> la parité d’inférence porte sur les indices `0..37`; la validation clinique de la nomenclature est un gate séparé.

Le runtime transforme donc aujourd’hui les canaux numériques en IDs cliniques, et `cephalo_runtime_evidence.py` exige ensuite exactement l’ensemble de ces IDs pour une preuve `SOTA_ONNX_38`.

### Classification scientifique

Ce mapping est :

`LEGACY_LOCAL_MAPPING / SOURCE_LOCK_REQUIRED`

Il constitue un **contrat logiciel observé**, pas une preuve anatomique amont.

Aucune modification de ce mapping n’est réalisée dans ce lot afin de préserver la non-régression. En revanche, il ne peut pas servir de preuve pour activer de nouvelles mesures ou déclarer la sémantique clinique des canaux comme validée.

---

# 3. Historique Git du mapping

L’historique contient le commit :

`5cd74729e8bfd718454d0c8cbd6c5e9ec6aee086`

message : `fix(cephalo): definitive 38-point MICCAI mapping and backend package structure`.

Le journal associé affirme qu’un « official challenge table » aurait été utilisé. Cependant :

1. aucun lien, document, fichier d’annotation ou hash de cette table n’est attaché à cette affirmation ;
2. le parent Git inspecté contient déjà le même mapping anatomique dans `sota_vision_service.py` ;
3. le dépôt source exact du checkpoint certifié expose uniquement les noms numériques `0..37` ;
4. les sources officielles publiques CL-Detection2023 inspectées décrivent 38 catégories mais ne fournissent pas le dictionnaire anatomique revendiqué.

**Décision** : le texte historique est une trace d’intention, pas une source scientifique suffisante. Il ne lève pas le gate.

---

# 4. Recoupement amont

## 4.1 CL-Detection2023 / MMPose

Les métadonnées du dataset utilisées par le modèle source définissent 38 catégories numériques. Le README décrit également les sorties comme catégories `1..38`.

## 4.2 Baseline officielle CL-Detection2023

La baseline officielle décrit un réseau de 38 heatmaps et un format de vérité terrain indexé par `p1 ... p38` / catégories numériques.

## 4.3 SRPose, solution challenge

Le repo `5k5000/CLdetection2023` est précisément celui épinglé par Digital Crown pour le checkpoint certifié. Son code d’inférence évalue les points par indice (`pid = i + 1`) ; il ne leur assigne pas de noms anatomiques.

---

# 5. Verdict scientifique

## Vérifié

- Digital Crown exécute un ONNX dérivé d’un checkpoint SRPose public précisément hashé et sourcé.
- La parité PyTorch → ONNX → runtime est certifiée sur 38 sorties.
- Le checkpoint source utilise un contrat de 38 catégories `0..37`.
- Digital Crown possède un mapping local `0..37 → IDs cliniques`.
- Le code Digital Crown lui-même sépare explicitement la parité d’inférence de la validation clinique de cette nomenclature.

## Non démontré

- que `0=S`, `1=N`, `2=Or`, `3=Po`, etc. correspond au contrat anatomique officiel du dataset d’entraînement ;
- que tous les noms locaux (`D_point`, `PT_point`, `Bo`, `C_point`, `Ls2`, `Li2`, etc.) correspondent exactement aux définitions des annotateurs CL-Detection2023 ;
- que les catégories voisines ou construites sont interchangeables avec les conventions Steiner/Tweed/McNamara/Ricketts ;
- que l’ancien libellé Git « definitive MICCAI mapping » est soutenu par une source primaire récupérable.

## Décision fail-closed

Le mapping anatomique automatique reste :

`SOURCE_LOCK_REQUIRED`

Règles :

1. préserver l’existant tant qu’aucune migration clinique contrôlée n’est décidée ;
2. ne pas utiliser le mapping local comme preuve scientifique pour **étendre** l’analyse ;
3. ne jamais déduire une nouvelle sémantique clinique à partir de la position d’un canal ;
4. les nouvelles mesures nécessitent des landmarks dont la définition est source-lockée indépendamment du détecteur ;
5. la liaison automatique d’un canal SRPose à ce landmark reste bloquée jusqu’à preuve ou nouvelle validation contrôlée.

---

# 6. Chemins acceptables pour lever le gate

Un seul des chemins suivants est acceptable :

1. récupérer le dictionnaire anatomique original des annotations CL-Detection2023 auprès des organisateurs / du package distribué aux participants et le versionner ;
2. retrouver un artefact historique Digital Crown contenant cette source primaire et vérifier son identité ;
3. obtenir une confirmation écrite/versionnée de l’auteur ou des organisateurs reliant explicitement les catégories 1..38 aux définitions anatomiques ;
4. créer un **nouveau contrat Digital Crown** par validation clinique contrôlée sur un jeu de référence, avec mapping figé, hashé, tests et validation praticien.

Le chemin 4 constitue une nouvelle validation sémantique du modèle, pas une simple documentation.

---

# 7. Conséquence sur le chantier

Le gate SRPose est maintenant **borné** : il n’existe plus de recherche repo évidente non exécutée pouvant transformer le mapping local en source primaire.

Le chantier peut avancer sur :

- définitions anatomiques source-lockées des landmarks nommés ;
- plans/lignes versionnés par analyse ;
- constructions géométriques indépendantes du détecteur ;
- tests sur fixtures explicites/manuelles ;
- matrice de couverture `landmark requis → disponible manuellement / disponible auto non validé / manquant / modalité bloquée`.

Il reste interdit d’étendre l’autorité clinique automatique de SRPose38 à partir du seul mapping local.

## Next exact

Poursuivre `CEPHALO_LANDMARKS_PLANES_SOURCE_LOCK.md` en séparant pour chaque landmark :

1. **définition scientifique** ;
2. **existence dans les moteurs DC** ;
3. **disponibilité manuelle** ;
4. **liaison automatique SRPose38** marquée `LEGACY_UNVERIFIED` tant que le gate anatomique n’est pas levé.