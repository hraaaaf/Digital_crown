# LOT05 J10Y — POST 2026-10-23 : validation-only 320 px vs 640 px

**Exécution vérifiée :** [J10Y GitHub Actions #39875967356](https://github.com/hraaaaf/Digital_crown/actions/runs/39875967356), **SUCCESS**, head exécuté `5874eb3b9b30b4491995d80ba6e5efe29c6459f0` ; dataset AKUDENTAL figé au commit `92e2cc3ae5eebc9de509311a3edefb7106fca7dd`. Deux modèles Torchvision Faster R-CNN MobileNetV3 FPN, initialisation et seed fixes, backbone gelé, entraînement des têtes RPN+ROI sur mêmes **96 train x3 époques**, comparaison seulement **33 validation**, test interne de 34 **non lu pour choisir les paramètres** (noms de split vérifiés).

## Résultat agrégé réel sur 32 classes FDI seules

| Métrique IoU50 classe exacte, conf >=0.25 | 320 min / 640 max | 640 min / 1280 max |
|---|---:|---:|
| Ground truth dents FDI | 834 | 834 |
| Vrais positifs | 262 | **375** |
| Faux positifs | 686 | **550** |
| Faux négatifs | 572 | **459** |
| Précision | 27.637% | **40.541%** |
| Rappel | 31.415% | **44.964%** |
| Macro AP50 interpolée 101 points sur prédictions tronquées | 22.604% | **43.219%** |
| Dents spatialement localisées sans condition classe | 337 | **462** |
| Classes FDI correctes parmi localisées dans cet appariement distinct | 231 | **332** |
| Classes FDI erronées parmi localisées | 106 | 130 |
| Perte moyenne sur 288 mises à jour | 2.43378 | 2.91093 |

**Delta absolu 640 vs 320** : précision **+12.904 points** ; rappel **+13.549 points**, avec **136 faux positifs de moins** et **113 vrais positifs de plus**. Le gain de précision/rappel et d'AP50 est sur le **même jeu de validation seulement**, sans intervalle de confiance ni preuve de généralisation patient-indépendante. Les pertes entre résolutions **ne sont pas comparables comme scores cliniques**.

Restaurations (3 autres classes) à score >=0.25 : à 320 px, TP1 FP13 FN115 (P 7.14% / R 0.86%). À 640 px, TP24 FP94 FN92 (P 20.34% / R 20.69%). Le gain est substantiel mais très insuffisant cliniquement.

## FDI qui progressent vs régressent

| FDI | Validation GT | TP 320 | TP 640 | Note |
|---|---:|---:|---:|---|
| **31** | 30 | 0 | **5** | Amélioration, encore 25 dents manquées |
| **32** | 32 | **5** | 4 | Pas d'amélioration |
| **41** | 31 | 7 | **9** | Progression faible |
| **42** | 31 | 3 | **9** | Progression nette |
| **24** | 30 | **10** | 4 | Régression marquée malgré FP 43→9 |
| **25** | 28 | **10** | 8 | Régression |
| **23** | 32 | **12** | 10 | Régression |
| **33** | 33 | **12** | 4 | Régression |

**Interprétation :** la résolution joue un rôle dans la localisation de certaines incisives mandibulaires, mais ne suffit pas à régler l'ensemble du problème FDI (particulièrement FDI32). Le résultat est hétérogène par classe, ce qui interdit tout claim de réussite dent-par-dent. Le taux de confusion entre prémolaires 23–25 exige des revues de boîtes/numéros et un éventuel diagnostic de post-traitement, réglé exclusivement sur validation ou une nouvelle cohorte de développement.

## Garanties du protocole

- **Aucun test interne évalué pendant J10Y** : le dossier `test` a été vérifié par noms seulement, sans ouvrir JPEG/labels de test. Les 34 cas test ont été **consommés analytiquement dans J10V** et ne peuvent pas être recyclés comme preuve finale après ce choix de résolution.
- [Workflow J10Y #39875967356](https://github.com/hraaaaf/Digital_crown/actions/runs/39875967356) SUCCESS, 4 tests J10X et 5 tests J10Y synthétiques PASS. Étape de suppression `J10Y_EPHEMERAL_DATA_AND_MODEL_REMOVED_NO_ARTIFACTS` confirmée ; aucun fichier image/poids/annotation clinique publié ou sauvegardé en artifact.
- [Workflow J10O #39876137248](https://github.com/hraaaaf/Digital_crown/actions/runs/39876137248) sur SHA documentation `927c5f32658685deda72c338f0e48fba959d8369` : **76/76 tests offline PASS**, workflow global encore rouge pour les anciens accès Roboflow 403 / Mendeley 401.
- Dossier local privé `experiments/lot05_j10x_local_private_fdi_visual_reviewer.py` prêt pour produire 28 overlays sous contrôle du professionnel ; **aucune des 28 radiographies n'a été jugée cliniquement** (0/28). Aucun fichier dérivé n'est produit en CI.

## Décision

**GATE EXPÉRIMENTAL :** hypothèse résolution soutenue sur le jeu de validation ; conserver 640 comme **candidat de recherche** pour une nouvelle cohorte indépendante, pas comme modèle produit. Interprétation FDI32 non résolue et régression FDI24/33 à investiguer. Échantillonnage clinique, droits sous-jacents du dataset et licence commerciale **NON confirmés** : aucune exploitation commerciale ni clinique. Pas de Vercel/Production, pas de PR merge, pas de poids sauvegardé, pas de patients du cabinet.
