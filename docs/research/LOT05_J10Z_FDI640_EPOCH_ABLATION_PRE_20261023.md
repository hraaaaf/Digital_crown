# LOT05 J10Z — FDI640 3 vs 6 époques, validation uniquement (PRE)

Date : 23 octobre 2026. Statut PRE, exécution initiale non encore qualifiée ; aucun modèle clinique ou commercial.

## Objet

J10Y a montré un gain global de 320→640 px sur 33 radiographies de **validation**, mais un sous-résultat contradictoire : FDI 31 progresse de 0 à 5 TP (GT 30), FDI32 régresse de 5 à 4 TP (GT32), FDI24 régresse de 10 à 4 TP (GT30), et la numérotation des prémolaires adjacentes demeure fragile. Les 34 fichiers de **test interne** ont été examinés en J10V et sont explicitement exclus de tout ajustement et évaluation J10Z.

Hypothèse isolée J10Z : prolonger de 3 à 6 époques une **même instance** de Faster R-CNN MobileNetV3 FPN à min_size=640/max_size=1280, backbone COCO gelé, RPN/ROI heads entraînées, améliore potentiellement les classes 24/32. Une baisse de loss ne suffira pas ; priorité aux TP/FP/FN FDI par dent et aux compromis des 32 classes.

## Protocole figé

- Corpus universitaire AKUDENTAL source `melihoz/AKUDENTAL@92e2cc3ae5eebc9de509311a3edefb7106fca7dd`, licence éditeur déclarée **CC BY-NC-SA 4.0 ; droits commerciaux NON établis**. Usage strictement expérimental non clinique.
- mêmes 96 train source (sélection seed `20261022`) ; 33 val ; **6 époques au maximum**, avec métriques après époque **3 et 6** sur le même modèle ; aucune ouverture des images ou annotations test pendant J10Z.
- paramètres fixes : LR 0.0004 AdamW, weight decay 0.0001, RPN+ROI dégelées, backbone gelé, IoU seuil 0.50, score 0.25 pour métriques, 35 classes + fond. Comparaison de modèles dans une seule exécution **sans export de checkpoints**, et non deux exécutions ayant des seeds fluctuantes.
- sortie agrégée uniquement : FDI32 vs restaurations, TP/FP/FN, précision/rappel et AP50 tronquée indicatives, matrice des erreurs conditionnées spatialement, classes ciblées 31/32/41/42/24/25/23/33, pertes moyennes par époque. Aucune image, fichier source par ID, coordonnées, ou matrice par patient.
- workflow dédié [J10Z #39924541179](https://github.com/hraaaaf/Digital_crown/actions/runs/39924541179) sur **commit initial exact `4171cfcdfee1877ea4b9699c2a98677d721e792d`**, état initial IN_PROGRESS ; Python `experiments/lot05_j10z_fdi640_epoch_ablation.py`, QA `experiments/test_lot05_j10z_fdi640_epoch_ablation.py`, workflow `.github/workflows/lot05-j10z-fdi640-epochs-val-only.yml`.
- ne pas prétendre que les paramètres choisis conservent une validité sur cohorte indépendante : la validation 33 a déjà été réutilisée pour comparer des modèles ; tout score est exploratoire, risque de surajustement à cette validation. Une **nouvelle cohorte réellement indépendante par patient** est nécessaire.
- note logistique : la revue visuelle des **28 images avec doublons FDI** reste **0/28** ; seuls un outil de sélection et des overlays privés ont été codés en J10X. Aucune correction automatique.
- toutes les images et poids de l'essai sont temporaires sur runner CPU, et détruits en fin de workflow. Aucun patient du cabinet, merge, déploiement, Vercel, diffusion de modèle, Product activation ni autorisation commerciale fictive.

## Décision

Ne pas déclarer de résultat ou de GO avant une lecture des logs du workflow sur le SHA exact. Si 6 époques augmentent les TP 24/32 tout en maîtrisant les FP et sans perte globale majeure, retenir comme candidat de **recherche**, pas comme modèle prêt. Si dégradation, conserver la conclusion négative plutôt que de masquer les mesures.
