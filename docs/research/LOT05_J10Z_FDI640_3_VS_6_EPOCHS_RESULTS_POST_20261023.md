# LOT05 J10Z — POST 2026-10-23 — 640px 3 contre 6 époques : résultats authentiques

**Exécution prouvée** : [workflow J10Z #39924541179](https://github.com/hraaaaf/Digital_crown/actions/runs/39924541179), SUCCESS, **HEAD exact du code exécuté `4171cfcdfee1877ea4b9699c2a98677d721e792d`** ; source académique AKUDENTAL figée à `92e2cc3ae5eebc9de509311a3edefb7106fca7dd`.

## Périmètre

Un seul modèle Torchvision Faster R-CNN MobileNetV3 FPN, 640px min / 1280px max, préentraînement générique COCO, backbone gelé, RPN + ROI heads entraînées. Même sélection des **96 images entraînement**, **6 époques au total**, évaluation du même modèle à la fin de l'époque **3 et 6**, sur les mêmes **33 radiographies de validation**. Les 34 images de l'ancien test interne **n'ont pas été utilisées pour entraînement/évaluation de J10Z** ; vérification des noms seulement. Tous les résultats sont exploratoires : la validation a déjà été utilisée dans plusieurs essais antérieurs, donc risque de sur-ajustement au protocole de sélection.

**Seuils :** score ≥0,25, géométrie IoU ≥0,50, catégorie FDI strictement exacte pour les valeurs P/R ; AP50 = interpolation sur **prédictions tronquées** (<=> cap modèle 100 objets/image et score minimum interne), ce n'est **pas** une mAP COCO officielle ni une performance dentaire clinique.

## Comparaison FDI-32, toutes les 33 validation

| Mesure | Après 3 époques | Après 6 époques | Variation |
|---|---:|---:|---:|
| Annotations dentaires GT | 834 | 834 | — |
| TP FDI | 375 | **454** | **+79** |
| FP FDI | **550** | 601 | **+51 (régression)** |
| FN FDI | 459 | **380** | -79 |
| Précision | 40,541 % | **43,033 %** | **+2,492 points** |
| Rappel | 44,964 % | **54,436 %** | **+9,472 points** |
| Macro AP50 indicative tronquée | 43,219 % | **49,422 %** | +6,203 points |
| Boîtes de dents localisées spatialement sans vérification de numéro | 462 | 544 | +82 |
| Parmi localisées, numéro FDI correct (matching spatial distinct) | 332 | 419 | +87 |
| Parmi localisées, numéro FDI incorrect | 130 | 125 | -5 |

**Coût associé :** 79 TP supplémentaires mais **51 FP supplémentaires** sur le même jeu de 33 panoramiques. Le gain de rappel ne doit pas masquer une sensibilité aux fausses détections.

## Classes prioritaires, mêmes vérités terrain

| Dent FDI | GT validation | TP à 3 époques | TP à 6 | FP à 3 | FP à 6 | Interprétation |
|---|---:|---:|---:|---:|---:|---|
| **24** | 30 | 4 | **12** | 9 | 16 | Amélioration du nombre de dents trouvées, mais FP augmentent |
| **31** | 30 | 5 | **9** | 11 | 17 | Encore **21 dents manquées** |
| **32** | 32 | 4 | **10** | 7 | **34** | **Hausse marquée des faux positifs : +27** |
| 23 | 32 | 10 | **14** | 6 | 17 | TP et FP montent |
| 25 | 28 | 8 | **11** | 9 | 7 | Amélioration sur les deux axes |
| 33 | 33 | 4 | **13** | 5 | 38 | Réponse très agressive et FP élevés |
| 41 | 31 | 9 | **10** | 31 | 32 | Encore 21 FN |
| 42 | 31 | 9 | **9** | 23 | 17 | Pas de gain TP, FP réduits |

La FDI32 est **un point de blocage majeur malgré le gain 4→10 TP** : 34 FP pour seulement 10 TP à six époques. Ne pas déclarer cette classe résolue. FDI24 a aussi un meilleur rappel mais plus de FP. Les restaurations restent **non qualifiées** : 3 époques TP24 FP94 FN92 (P 20,339%, R 20,690%) ; 6 époques TP26 FP133 FN90 (P 16,352%, R 22,414%) : rappel presque inchangé et perte de précision.

## Pertes et reproduction

Loss moyenne par époque sur la série exacte **3.34835, 2.84991, 2.53453, 2.39760, 2.22187, 2.10781**. Moyenne cumulée après 3 : **2.91093**, après 6 : **2.57668** ; la diminution n'est **pas** une preuve de généralisation. Le point 3 époques reproduit les métriques J10Y 640 à la précision de log, facilitant l'audit comparatif.

Le workflow a exécuté **quatre tests purement synthétiques** et l'entraînement CPU réel ; a fini SUCCESS et nettoyé les données/poids via `J10Z_EPHEMERAL_IMAGES_LABELS_AND_WEIGHTS_REMOVED`. Aucun checkpoint, aucune image, donnée cabinet, ID patient ou annotation source exportée comme artefact.

[Workflow J10O #39924812040](https://github.com/hraaaaf/Digital_crown/actions/runs/39924812040) sur HEAD `3bffb0bb570108c6e139ee0f6a1e5cdcd50187f6` : **80/80 tests offline PASS**. J10O global reste **FAILURE** car trois anciens jobs Roboflow/Mendeley HTTP externes 403/401 ; le J10Z dédié est SUCCESS.

## Décision et portes encore fermées

**Recherche validée techniquement, modèle commercial/clinique NO-GO.** Six époques est un **candidat de recherche** pour expériences supplémentaires ; ne pas augmenter les époques à l'aveugle, notamment à cause de la hausse FP FDI32. Il faut une réévaluation des seuils et erreurs sur une cohorte de **développement** distincte, contrôler orientation/latéralité et annotations, et réserver une **nouvelle cohorte patient-indépendante** pour un vrai test final. Les **28 images académiques signalées en J10W/J10X** n'ont toujours **pas** été révisées visuellement par un dentiste (0/28) ; poste Desktop Commander encore hors ligne.

Le dataset AKUDENTAL est déclaré **CC BY-NC-SA 4.0**, droits commerciaux **NON obtenus**, pas de licence présumée ; aucune intégration Digital Crown, fusion de la PR #1032, déploiement, Vercel/Production ou rétention de poids. Aucune revendication de diagnostic clinique.
