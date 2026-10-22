# LOT05 J10V — POST / résultats FDI-32 par dent sur test interne

**Date : 22 octobre 2026. Source du résultat :** [workflow J10V #39873048174](https://github.com/hraaaaf/Digital_crown/actions/runs/39873048174), `completed/success`, **HEAD exact évalué `ed888b5710b56e4d8530046cc4f255eae718e53d`**. Source académique AKUDENTAL figée `92e2cc3ae5eebc9de509311a3edefb7106fca7dd`.

## Protocole et limites

Modèle `torchvision_fasterrcnn_mobilenet_v3_large_320_fpn`, préentraînement COCO générique, backbone gelé, RPN + ROI heads adaptées, 96 images entraînement × 3 époques, validation source **33** et partition **test interne 34**, sans ajustement des hyperparamètres après test. Références test/train/val disjointes par nom ; **aucun contrôle d'indépendance par patient, établissement ou origine réelle démontré**. Aucun patient/image du cabinet. Aucune utilisation commerciale ou clinique autorisée.

Les valeurs ci-dessous sont des **correspondances de boîte IoU >=0.5 et classe exacte**, confiance minimale **0.25** pour les chiffres P/R. La `macro_ap50_101pt_truncated_predictions` est une AP50 indicative sur les prédictions retournées par le modèle (seuil minimal interne 0.05, au maximum 100 prédictions/image), **pas COCO mAP@[0.50:0.95]**. Toutes les métriques sont expérimentales et **ne constituent pas une qualité de numérotation utilisable cliniquement**.

## Métriques réellement mesurées

| Groupe | Split | GT | TP | FP | FN | Précision | Rappel | AP50 tronquée macro |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| FDI-32 seules | validation 33 | 834 | 290 | 783 | 544 | 27.027 % | 34.772 % | 22.905 % |
| FDI-32 seules | test interne 34 | 904 | 347 | 899 | 557 | 27.849 % | 38.385 % | 24.525 % |
| Restaurations 3 classes | validation 33 | 116 | 1 | 16 | 115 | 5.882 % | 0.862 % | 0.161 % |
| Restaurations 3 classes | test interne 34 | 129 | 1 | 28 | 128 | 3.448 % | 0.775 % | 0.695 % |

À ce stade **aucune des trois catégories de restauration n'est correctement apprise de manière exploitable**. La partie FDI produit encore **899 fausses détections sur seulement 34 images** au seuil prévu, pour 347 vrais positifs.

### Dents particulièrement faibles sur test interne

- **FDI 31 : 0 TP / 31 FN** ; aucune détection exacte de la classe.
- **FDI 32 : 0 TP / 31 FN** ; aucune détection exacte.
- **FDI 42 : 3 TP / 29 FN**.
- **FDI 23 : 5 TP / 29 FN**.
- **FDI 47 : 20 TP / 8 FN** et FDI 46 : 16 TP / 5 FN sont meilleures sur ce seul jeu interne ; cela n'autorise pas une généralisation clinique.

### Matrice de confusion FDI, conditionnée par une bonne localisation

Le script J10V a généré la **matrice agrégée 32×32** dans les logs du [run J10V](https://github.com/hraaaaf/Digital_crown/actions/runs/39873048174), sans annotation nominative ni coordonnées. Matrice de **dents localisées spatialement** (IoU50, appariement sans exigence de classe), **pas** matrice exhaustive sur toutes les dents.

Test interne 34 : **430** dents localisées spatialement (avec ou sans erreur de numéro), dont **317** bien numérotées dans cet appariement spatial et **113** mal numérotées. **474** dents GT non localisées et **816** prédictions dentaires non appariées dans cette procédure spatiale. **Attention :** les 317 matches diagonaux de la matrice spatiale ne sont pas les 347 vrais positifs issus de l'algorithme *classe exacte*, car la politique de matching est différente ; **ne pas les assimiler**. Les erreurs de localisation sont exclues des cases 32×32 et comptées séparément.

Confusions les plus répétées **réel → prédit** : FDI **25→24 : 13**, **23→22 : 5**, **37→36 : 5**, **15→14 : 4**, **21→11 : 4**, **23→24 : 4**, **33→32 : 4**, **34→33 : 4**, **34→35 : 4**, **44→43 : 4**. Les inversions/numéros adjacents nécessitent une revue de radiographies et orientation, pas seulement une augmentation des époques.

## Révision QA des 31 labels FDI dupliqués

L'outil lit uniquement les `.txt` publics étiquetés FDI et n'a fait **aucune correction**. Bilan sur la source complète **333/333** :
- train : **25** instances FDI excédentaires sur **23** images ;
- validation : **3** excédents sur **3** images ;
- test : **3** excédents sur **2** images ;
- total **31** excédents dans **28** images signalées.

Ces chiffres sont des **anomalies structurelles potentielles**, non des diagnostics d'erreurs d'experts. Sans revue visuelle et clinique autorisée, ne pas déduire des corrections et ne pas réétiqueter automatiquement.

## Vérifications

- J10V [run #39873048174](https://github.com/hraaaaf/Digital_crown/actions/runs/39873048174) : **SUCCESS**, 9 tests purement synthétiques du protocole, exécution train/val/test, sortie agrégée; effacement final confirmé **`J10V_TRANSIENT_SOURCE_AND_WEIGHTS_REMOVED`**. Aucune image/poids distribués.
- [J10O workflow #39873131763](https://github.com/hraaaaf/Digital_crown/actions/runs/39873131763) sur HEAD docs `5d07430694f01158518473a451279b4fd49a47fd` : job hors ligne **61/61 PASS** (17 J10O + 12 J10P + 12 J10Q + 6 J10R + 5 J10T + 9 J10V). Le workflow J10O est toujours **globalement rouge** à cause des trois jobs HTTP externes Roboflow/Mendeley 403/401, sans impact sur la réussite du workflow J10V.
- **Source juridique :** le README AKUDENTAL déclare CC BY-NC-SA 4.0 ; **aucun droit commercial confirmé**, aucune application propriétaire ni clinique permise sur cette seule base. Entraînement noncommercial expérimental uniquement.

## Décision scientifique et produit

**RESEARCH PROTOCOL PASS ; MODEL CLINICAL / COMMERCIAL NO-GO.** Priorités : revue clinique de 28 images/31 doublons ; audit d'indépendance patients et cohorte externe ; séparer développement FDI et restaurations ; traiter faux positifs sévères et classes FDI31/32, documenter orientation / politique de mapping FDI avant toute nouvelle comparaison. N'entraîner ni déployer un modèle produit sur ce corpus sans droits pertinents. Maintenir [PR #1032](https://github.com/hraaaaf/Digital_crown/pull/1032) **DRAFT, non fusionnée** ; pas de Vercel/Production, pas de patients cabinet, pas de poids conservés.
