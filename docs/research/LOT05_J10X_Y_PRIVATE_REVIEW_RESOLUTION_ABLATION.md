# LOT05/J10X–J10Y — Revue privée des anomalies et comparaison de résolution

**Date : 2026-10-22 ; état : expérimentation académique sur branche PR DRAFT, aucun modèle clinique.**

## J10X — Revue visuelle sécurisée des 28 radiographies signalées

La [source AKUDENTAL](https://github.com/melihoz/AKUDENTAL) au SHA `92e2cc3ae5eebc9de509311a3edefb7106fca7dd` contient 333 radiographies et leurs annotations FDI sous licence déclarée **CC BY-NC-SA 4.0**. L'audit J10W a identifié 31 occurrences de numéros FDI répétés dans 28 images ; 30 paires géométriquement disjointes IoU<0,30, une seule paire à IoU>=0,70. **Cela ne constitue pas une preuve de 31 erreurs cliniques.**

- Script `experiments/lot05_j10x_local_private_fdi_visual_reviewer.py` : établit la liste de 28 cas depuis les étiquettes `*.txt`, vérifie la structure/source complète et prépare des overlays PNG des deux régions portant le même numéro FDI. **Seule une exécution sur une station privée explicitement autorisée permet de les produire** ; les PNG sont dérivés de radiographies et ne doivent pas être déposés dans un dépôt Git, GitHub Actions/Artifacts, Notion, ChatGPT, ou accessible par URL publique.
- Le script **refuse tout output existant**, sortie sous .git ainsi que sortie chevauchant la source; crée un répertoire privé et des fichiers PNG en permissions restrictives, puis rapporte seulement le nombre de cas préparés.
- Exemple sur poste d'étude privé où les données académiques ont été obtenues de façon autorisée :

```bash
python experiments/lot05_j10x_local_private_fdi_visual_reviewer.py \
  --images-dir /private/AKUDENTAL/AKUDENTAL/images \
  --labels-dir /private/AKUDENTAL/AKUDENTAL/folds/fold_0/labels \
  --private-output-dir /private/CLINICAL_REVIEW_28_NOT_FOR_UPLOAD
```

- Dépendance locale requise : `Pillow`. Ne pas modifier les labels d'origine. **Statut de revue clinique : 0/28**, car aucun professionnel n'a effectivement statué sur les 28 overlays. L'outil n'a pas été exécuté sur les vrais pixels dans la CI, seulement testé sur fixtures synthétiques.
- Protocole clinique : vérifier la latéralité, le sens panoramique, la présence et la morphologie dentaire, les éventuelles dents surnuméraires ou incluses, puis distinguer **annotation correcte / erreur probable / indéterminé** ; jamais autocorriger les classes FDI. Ne pas mélanger ces radiographies académiques avec les patients du cabinet.

## J10Y — ABLATION PRÉ-ENREGISTRÉE : 320px contre 640px (validation uniquement)

**Hypothèse** : le modèle Faster R-CNN MobileNetV3 320 FPN manque de résolution pour les incisives mandibulaires, même si la taille de bbox normalisée et le nombre d'exemples FDI31/32 sont comparables aux controlatérales. Cette hypothèse **n'est pas prouvée** et doit être confrontée à une expérimentation à protocole fixe.

- Script `experiments/lot05_j10y_akudental_resolution_ablation.py` et [workflow J10Y](https://github.com/hraaaaf/Digital_crown/actions/workflows/lot05-j10y-fdi32-val-resolution-ablation.yml).
- Deux modèles identiques initialisés depuis le même COCO générique, tête RPN/ROI entraînée, backbone gelé, **96 mêmes images train ×3 époques**, mêmes poids initiaux et mêmes ordres d'échantillons, mêmes hyperparamètres et seuil de score 0,25 / IoU 0,50. Seule différence volontaire : `min_size=320,max_size=640` vs `min_size=640,max_size=1280`.
- **33 images de validation** pour sélectionner/diagnostiquer; 34 images de test **NE SONT PAS LUES** (seule la séparation des noms est contrôlée). La partition test a déjà été examinée analytiquement dans J10V, et ne peut donc plus être réutilisée comme preuve finale indépendante après optimisation.
- Rapports agrégés : FP/FN, précision, rappel, AP50 tronquée (pas COCO mAP) des 32 dents isolément, restaurations séparées, FDI ciblées **31,32,41,42,24,25,23,33** et erreurs de numérotation conditionnées par localisation. Aucun média, poids, annotations individuels ni matrice par patient.
- **Ne pas revendiquer un bénéfice sans lire les logs exacts** ; l'échec par OOM ou dimension haute doit être consigné, pas masqué.
- Vérifications : neuf nouveaux tests unitaires entièrement synthétiques pour J10X/J10Y, ajoutés à la CI de gouvernance J10O. **Résultat final des nouveaux runs non renseigné ici avant vérification.**

## Interdictions et décision

Droits commerciaux et provenance des images sous-jacentes **non vérifiés**, même si le propriétaire demande de faire avancer la technique. CC BY-NC-SA du dataset source implique un blocage de commercialisation, pas la nécessité d'arrêter une étude technique séparée. PR #1032 DRAFT ; **aucune fusion, Vercel/Production, image patient du cabinet, modèle appliqué à un soin ou poids diffusé.** Nouvelle cohorte indépendante par patient et revue professionnelle indispensables avant tout GO clinique.
