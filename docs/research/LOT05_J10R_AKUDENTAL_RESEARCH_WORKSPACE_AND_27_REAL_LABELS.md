# LOT05 / J10R — Workspace FDI32 sur AKUDENTAL : recherche uniquement

Date : 2026-10-22. PR [#1032](https://github.com/hraaaaf/Digital_crown/pull/1032), DRAFT. Pas de merge ni Vercel.

## État vérifié

La source de référence est [AKUDENTAL](https://github.com/melihoz/AKUDENTAL) au commit de l'éditeur `92e2cc3ae5eebc9de509311a3edefb7106fca7dd`. Les 333 panoramiques et les fichiers de labels YOLO existent dans l'arbre GitHub. La source annonce **CC BY-NC-SA 4.0**, réservée aux usages non commerciaux. **Ce n'est pas une licence commerciale acquise**. Les outils de préparation ci-dessous ne constituent pas une permission d'entraînement ou de lancement de fonctionnalités Digital Crown.

**Contrôle séparé des vraies annotations, en lecture GitHub uniquement :** 27 fichiers `AKUDENTAL/folds/fold_0/labels/{train,val,test}/*.txt` répartis équitablement (9 par partition), **803 annotations** au total : train **287**, val **254**, test **262**. Chaque annotation testée comportait une classe entière dans 0–34 et 4 coordonnées YOLO valides dans l'image. Une duplication de la classe 23 (FDI **38**) dans `fold_0/labels/val/9.txt` : **deux instances de dent FDI 38 dans un seul fichier**. Ce point est à vérifier manuellement par expert, ne pas réécrire la source ni supprimer une annotation sans relecture.

Important : ces 27 fichiers échantillonnés ne constituent pas un audit exhaustif des 333 images. La qualité et l'exactitude médicale des contours, la présence d'artefacts, l'indépendance par patient, le sens droite/gauche et les performances d'un modèle restent **INCONNUS**.

## Workspace reproductible et sécurisé

Implémentation expérimentale, dans la branche DRAFT :
- `experiments/lot05_j10q_akudental_fdi_yolo_text_only.py` : QA de labels YOLO uniquement.
- `experiments/lot05_j10r_akudental_private_research_workspace.py` : contrôle des **333 labels** locaux et construction d'un workspace YOLO35 à 3 partitions, sans lire/copier les images.
- `experiments/test_lot05_j10r_akudental_private_research_workspace.py` : **6 tests synthétiques** sur de faux fichiers `.jpg` sans pixels.
- `.github/workflows/lot05-j10o-public-panoramic-research-qa.yml` : **47 tests offline** (17 J10O + 12 J10P + 12 J10Q + 6 J10R).

**Preuve CI :** [run #39864599079](https://github.com/hraaaaf/Digital_crown/actions/runs/39864599079) au SHA `e85fb1551cd7a504bbc16245cca0266d204da054`, job offline **SUCCESS, 47/47**. Le workflow global **FAILURE** car Roboflow reste 403 et Mendeley 401. Ces échecs externes n'indiquent pas une erreur des tests locaux. **Aucune image réelle n'a été ouverte, téléchargée ou entraînée par cette CI.**

Sur une machine de recherche dûment autorisée seulement, avec copie locale privée du **commit exact** de la source et Python 3.11+ :

```bash
python experiments/lot05_j10r_akudental_private_research_workspace.py \
  --source-repo "/chemin/prive/AKUDENTAL" \
  --fold fold_0 \
  --workspace "/chemin/prive/sortie-recherche-fdi"
```

**Attention :** `--source-repo` doit cibler la racine du checkout Git contenant le sous-dossier `AKUDENTAL/`. La sortie ne doit pas exister, ne doit pas se situer dans le checkout ni le contenir, et doit rester privée. Le script crée un `data.yaml` YOLO à 35 classes (32 FDI + bridge, filling-crown, implant), copie seulement des `.txt` après validation, et crée **333 liens symboliques locaux** pour les JPEG. Aucun téléchargement, conversion JPEG, mise en ligne, inférence, entraînement ou publication de poids. Le script peut nécessiter les privilèges de symlink en environnement Windows.

La sortie peut hériter d'une information de données de santé via les JPEG pointés : **ne jamais pousser le dossier en Git, GitHub Actions, cloud, Notion ni répertoire partagé**. Certains `.json` LabelMe éditeur contiennent `imageData` base64 ; ce workspace les ignore.

Les cinq folds ne sont **pas cinq cohortes de patients distinctes** : chaque fold redistribue les 333 cas. Les duplications FDI dans les labels réels sont **signalées**, pas corrigées.

## Suite scientifique, distincte des droits

1. Examiner la duplication FDI 38 ainsi que l'orientation, les édentements, restaurations et incertitudes avec un professionnel.
2. Valider l'indépendance par sujet/source et le protocole d'évaluation à partir des données originales et de leurs métadonnées autorisées.
3. Seulement dans un environnement de recherche non commercial conforme aux conditions de la source, envisager une expérience pilote avec plafonds de ressources et traçabilité, sans intégration produit ni publication de poids.
4. **Pour un usage commercial Digital Crown :** obtenir une permission écrite/licence compatible avant tout entraînement ou réutilisation commerciale. Ne pas qualifier implicitement cette étape comme accomplie.

## Décision

**J10R : outillage local testé sur faux exemples ; échantillon réel de 803 annotations contrôlé au niveau des métadonnées YOLO ; modèle entraîné NON ; données commercialement qualifiées NON ; utilisation clinique NO-GO.**
