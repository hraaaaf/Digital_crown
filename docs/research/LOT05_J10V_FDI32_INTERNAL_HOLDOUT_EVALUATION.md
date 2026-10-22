# LOT05/J10V — Evaluation réelle FDI-32, matrice de confusion et test interne séparé

Date : 2026-10-22. Stratégie A. **Recherche académique isolée, PAS de qualification commerciale ni clinique.**

## Preuves déjà établies

J10U exact SHA `57865c8015da9513f8dd0f8c66103eb157be0475`, [run #39872090093](https://github.com/hraaaaf/Digital_crown/actions/runs/39872090093) SUCCESS : Faster R-CNN MobileNetV3 320 FPN, 96 images train x3 epochs, 33 val, score .25 => **263 TP, 699 FP, 687 FN** sur *l'ensemble* des **35 classes** (32 FDI + 3 restaurations), précision 27.339%, rappel 27.684%. Le mélange des 35 catégories ne permettait **pas** d'affirmer les performances de numérotation FDI seule. Les poids avaient été détruits.

## Protocole J10V — à évaluer sur SHA exact

- Reproduction sans réglage des hyperparamètres de J10U, seed `20261022`, même modèle générique COCO avec backbone gelé, 96 train x3, détection de 35 classes + fond, **pas d'Ultralytics**.
- Trois partitions `fold_0` source : 266 train / 33 val / **34 test séparé**. La séparation est avérée par noms de fichiers source, mais **indépendance des patients, de l'origine clinique et des images dérivées NON vérifiée**. Ne pas appeler le test une cohorte externe ou une validation clinique indépendante. Les 34 fichiers test ne servent pas à ajuster les hyperparamètres, ni aux gradients.
- **Rapports distincts val et test** pour FDI32 et restaurations3 : TP/FP/FN, précision et rappel à confiance 0.25 et IoU 0.5 classe exacte, métriques par classe, AP50 interpolée 101 points (seuil de sortie modèle 0.05, cap 100 propositions par image, donc **AP50 tronquée et NON COCO mAP@[.5:.95]**).
- **Matrice 32×32 des numéros FDI** : lignes réelles, colonnes prédites, obtenue en reliant les boîtes par proximité spatiale IoU 0.5 **sans exiger que la classe corresponde**. Les erreurs de localisation, absences de détection et faux positifs restent **hors de la matrice** et sont comptés séparément pour ne pas exagérer la numérotation. 10 principales confusions FDI ; noms/sources individuels non inclus.
- **31 doublons d'étiquettes FDI sur la totalité du corpus** : calcul séparé par partitions, type de FDI concerné et nombre d'images signalées. Aucun effacement ni correction de vérité terrain ; statut revue experte **NON EFFECTUÉE**.
- Aucun poids, fichier image, annotation originale, boite individuelle ou patient source dans GitHub Actions artifacts ou repo. Runner éphémère uniquement, nettoyage de travail et cache prévu à la fin, aussi en erreur. **Seuls les agrégats apparaissent dans les logs** ; la confusion est agrégée, non issue d'un cliché cabinet.
- Licence du dataset source **CC BY-NC-SA 4.0 selon éditeur** : pas d'acquisition présumée des droits commerciaux. Entraînement académique temporaire ne constitue ni une autorisation de produits propriétaires, ni une validation dispositif médical.

## Artefacts de code (PR DRAFT #1032)

- `experiments/lot05_j10v_akudental_fdi_holdout_eval.py`
- `experiments/test_lot05_j10v_akudental_fdi_holdout_eval.py` — neuf tests synthétiques hors ligne des calculs, notamment mauvaise dent mais bonne localisation, restaurations et absence de GT.
- `.github/workflows/lot05-j10v-fdi32-holdout-eval.yml` — workflow CPU plafonné et jetable avec source AKUDENTAL fixée au SHA `92e2cc3ae5eebc9de509311a3edefb7106fca7dd`.
- PR : https://github.com/hraaaaf/Digital_crown/pull/1032 . Nouveau workflow J10V : https://github.com/hraaaaf/Digital_crown/actions/workflows/lot05-j10v-fdi32-holdout-eval.yml

**Critères go/no-go :** présence de vrais TP FDI sur val ET test interne ; vérifier FP et confusions dent à dent ; score de validation non clinique ; ensuite revue clinique des 31 labels suspects et examen de l'indépendance patient/source, et droits commerciaux à régulariser avant tout usage de produit. Sans ces éléments : **NO-GO clinique, distribution ou déploiement**.
