# LOT05/J10Q — Alternative Roboflow : AKUDENTAL, labels FDI-32 vérifiés sur GitHub

**Statut : research-only, licence NC ; aucune autorisation commerciale ou clinique.**

## Première preuve source directe (22 octobre 2026)

- Article scientifique : Oz M, Sengul A, Hatipoglu M, Danisman T, *AKUDENTAL teeth instance segmentation dataset: a cross-dataset analysis*, BMC Oral Health **26:247**, 12 janvier 2026, DOI `10.1186/s12903-025-07645-0`, https://pmc.ncbi.nlm.nih.gov/articles/PMC12874774/
- Dépôt académique d'origine : https://github.com/melihoz/AKUDENTAL (commit source **`92e2cc3ae5eebc9de509311a3edefb7106fca7dd`** daté 3 avril 2026). L'article et le README indiquent **l'accès uniquement à la recherche académique non commerciale** ; README déclare **CC BY-NC-SA 4.0**. Les conditions ne sont pas une licence pour entraîner une fonction commerciale dans Digital Crown.
- Inspection de l'arbre Git officiel via API : **333 JPEG** `AKUDENTAL/images/`, un fichier COCO `AKUDENTAL/akudental_instances.json`, des LabelMe JSON parfois avec `imageData` contenant des pixels et des fichiers YOLO texte par fold. Lire un LabelMe JSON ou le stocker en CI peut récupérer sans le vouloir les pixels embarqués ; **interdire les LabelMe JSON pour les tests d'annotations à distance**.
- `AKUDENTAL/dataset.yaml` confirme **35 classes** : indices 0–31 couvrent exactement FDI `11–18, 21–28, 31–38, 41–48`, index 32 bridge, 33 filling/crown, 34 implant. **Important : ne PAS rejeter 35 classes parce que l'objectif de dentition FDI porte sur 32 dents.**
- Cinq partitions de validation croisée : pour chacun des folds 0, 1, 2, 266/33/34 ou 267/33/33 fichiers de labels train/val/test, union **333** ; intersection des noms fichiers 0 à l'intérieur de chaque fold. **Ce contrôle ne garantit ni une absence de sujets répétés, ni l'indépendance par patient.** Les mêmes cas réapparaissent nécessairement d'un fold à l'autre pour la validation croisée, et ne doivent jamais être agrégés comme 1 665 patients.
- Trois **vrais** fichiers YOLO textuels, à la source, lus et validés en mémoire via connexion GitHub : `fold_0/train/1.txt` **41 instances**, `fold_0/val/103.txt` **26 instances**, `fold_0/test/101.txt` **31 instances** ; **98 instances au total** ; cinq champs par ligne, classes dans 0–34, coordonnées normalisées / boîtes dans l'image, aucun numéro de dent dupliqué dans ces trois exemples. Aucun résultat de reconnaissance IA, aucune métrique mAP, aucune vérification de pixels. Les fichiers texte eux-mêmes ne sont pas stockés dans Digital Crown.
- Source figée des labels examinés : https://github.com/melihoz/AKUDENTAL/tree/92e2cc3ae5eebc9de509311a3edefb7106fca7dd/AKUDENTAL/folds/fold_0/labels

## Implémentation locale dans la branche de PR

- `experiments/lot05_j10q_akudental_fdi_yolo_text_only.py` : adaptateur de lecture des **.txt uniquement**, bornes de fichiers et nombre de lignes, refus symlinks et image/JSON, conversion des indices FDI 0–31, comptage séparé des restaurations 32–34, géométrie des boîtes YOLO et doublons FDI par image. **Aucun accès réseau**, aucune image, aucun modèle, aucun apprentissage. Sortie uniquement agrégée sans nom de fichier, coordonnées ni donnée individuelle.
- `experiments/test_lot05_j10q_akudental_fdi_yolo_text_only.py` : 12 tests **synthétiques**, jamais exécutés sur image, patient ou annotation tiers ; l'analyse de trois fichiers authentiques ci-dessus a été faite séparément et n'est **pas** un résultat de la CI.
- Commande sur un répertoire de travail privé **légitimement autorisé pour de la recherche académique non commerciale** :
  ```bash
  python experiments/lot05_j10q_akudental_fdi_yolo_text_only.py /path/to/labels/one.txt /path/to/labels/two.txt
  ```
  Pour un contexte commercial, **NE PAS procéder à un entraînement ou un benchmarking du produit sur ces labels sans permission écrite du titulaire des droits**. Les métadonnées publiques vérifiées ne suffisent pas à en déduire cette permission.

## Qualifications et blocages

- Le récit éthique de l'article indique l'approbation du comité KAEK-72 et la dispense de consentement pour l'analyse rétrospective anonymisée. Cela ne constitue pas une certification de conformité ou un droit de transfert des images patients du cabinet.
- Les images du corpus restent dans le dépôt éditeur. Digital Crown ne télécharge/commit aucun pixel, aucun LabelMe JSON et aucun jeu de données protégé dans GitHub Actions.
- Aucune preuve d'orientation correcte selon miroir/gauche-droite au niveau du modèle, de performance FDI ni de validation clinique.
- **Pour l'usage commercial :** demander explicitement une licence commerciale à l'équipe AKUDENTAL OU trouver un corpus avec droits sous-jacents démontrés permettant l'évaluation commerciale. Ne pas utiliser l'accès public comme prétexte pour contourner CC BY-NC-SA.
- **Production : NO-GO ; PR DRAFT ; pas de merge, déploiement, entraînement commercial, modification FUE ou activation clinique.**
