# LOT05/J10R–J10S — Pilot FDI-32 sur données académiques AKUDENTAL

**Date : 2026-10-22. Statut : recherche technique, licence commerciale non vérifiée, jamais clinique.**

## Ce qui est réellement disponible

- Source éditeur : https://github.com/melihoz/AKUDENTAL, **SHA `92e2cc3ae5eebc9de509311a3edefb7106fca7dd`**.
- **333** panoramiques JPEG, annotations YOLO de détection et cinq folds (chacun totalise 333 cas). `AKUDENTAL/dataset.yaml` : **35 classes** dont FDI **11–48 pour indices 0–31** et **bridge, filling/crown, implant** pour indices 32–34.
- Résultat direct d'échantillonnage via GitHub Connector au SHA source : **27 fichiers YOLO authentiques, 803 annotations**, couvrant fold_0/train, val et test. Toutes les 803 lignes ont cinq colonnes, des IDs de classe 0–34 et des coordonnées de boîtes centrées normalisées dans l'image. **Une anomalie confirmée** : `fold_0/labels/val/9.txt`, classe 23 correspondant à **FDI 38**, annotée **deux fois**. Nécessite revue clinique des formes concernées et de l'image originale, sans correction automatique.
- En-têtes JPEG réellement récupérés depuis GitHub (base64 lu transitoirement en mémoire, **pas écrit dans le repo**) pour `1.jpg` = **2943×1435**, `9.jpg` = **2943×1435**, `101.jpg` = **2871×1536**. Les tailles sont compatibles avec la résolution de la source, sans validation d'orientation clinique ni décodage d'image en modèle.
- Risque supplémentaire : les LabelMe `.json` amont peuvent contenir `imageData` base64 ; ne pas utiliser ces JSON pour le contrôle CI texte.

## Code et protocole

### J10Q : vérification des labels sans pixels

`experiments/lot05_j10q_akudental_fdi_yolo_text_only.py` valide 35 classes et géométrie YOLO, exclut les images, JSON et symlinks, émet uniquement les agrégats.

### J10R : reconstruire un dossier YOLO local en environnement privé

`experiments/lot05_j10r_akudental_private_research_workspace.py` prend une copie locale, licitement obtenue pour recherche, de la source éditeur et génère un dossier `data.yaml` plus `images/{train,val,test}` (symlinks locaux vers les vrais JPEG, **aucune image copiée par le script**) et `labels/{train,val,test}` (TXT validés). Les **333** labels sont validés avant création, partitions sans chevauchement par ID.

Exemple dans un poste de recherche autorisé :

```bash
git clone https://github.com/melihoz/AKUDENTAL.git /chemin/prive/AKUDENTAL-source
git -C /chemin/prive/AKUDENTAL-source checkout --detach 92e2cc3ae5eebc9de509311a3edefb7106fca7dd
python experiments/lot05_j10r_akudental_private_research_workspace.py \
  --source-repo /chemin/prive/AKUDENTAL-source \
  --fold fold_0 \
  --workspace /chemin/prive/akudental-yolo-pilot
```

**Important :** le script présente la révision exacte exigée dans le rapport, mais ne peut pas en lui-même certifier que le clone source est au bon commit Git : vérifier `git rev-parse HEAD` en amont comme montré. `data.yaml` décrit 35 catégories, **pas 32 uniquement**, afin de préserver les annotations de restauration. Cinq folds permettent une comparaison ultérieure si la provenance/split patient est validée. Une même radiographie peut réapparaître entre folds et ne constitue pas un nouveau patient.

### J10S : contrôle de **tous les 333 labels réels**, sans images, par runner CI séparé

Workflow `.github/workflows/lot05-j10s-akudental-text-only-real-label-audit.yml` : clone Git *sparse* de la partie `AKUDENTAL/folds/fold_0/labels/` seulement, commit source **figé et vérifié**, agrégation exacte de 333 TXT et vérification des 35 classes / bbox / doublons FDI. **Ne télécharge aucun JPEG**, n'exécute aucune IA, n'upload aucun artefact et efface les labels de l'environnement éphémère. Ne revendiquer PASS qu'après lecture des logs pour le HEAD exact.

## Garde-fous

- **Pas de vérité juridique inventée :** la source déclare CC BY-NC-SA 4.0 et ne fournit pas d'autorisation commerciale documentée. Préparer un prototype technique n'est pas une licence commerciale, ni une approbation de distribution du dataset ou des poids.
- Pas de patient ou média du cabinet ; le jeu est une publication académique tierce ; pas de migration des données cabinets vers le cloud.
- Aucune précision, sensibilité, recall, mAP, qualité clinique ni supervision dentaire réelle démontrée. Le doublon FDI 38 peut avoir une explication d'annotation qui exige revue et ne doit pas être réparé automatiquement.
- Aucun entraînement sur 333 JPEG effectué dans ce lot, aucune prédiction IA, aucun modèle déployé, aucune modification de production, PR #1032 DRAFT et non mergée.
- **NO-GO diffusion, clinique, commercial** tant que licences, provenance et validation humaine restent non confirmées. L'utilisateur autorise à avancer la recherche technique sans attendre la négociation ; cette instruction ne constitue pas une permission du détenteur.
