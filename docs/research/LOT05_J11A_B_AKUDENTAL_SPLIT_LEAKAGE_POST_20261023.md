# LOT05/J11A–J11B — POST : empreintes JPEG inter-partitions et revue privée des paires proches

**Date 23 octobre 2026. Statut : screening d'intégrité technique RÉUSSI / indépendance patient NON PROUVÉE.**

## Provenance et preuve exacte

- Éditeur : [AKUDENTAL](https://github.com/melihoz/AKUDENTAL) version Git **`92e2cc3ae5eebc9de509311a3edefb7106fca7dd`**, licence déclarée **CC BY-NC-SA 4.0**, aucun droit commercial acquis pour Digital Crown.
- Source réelle contrôlée : les **333 JPEG académiques originaux** correspondant aux fichiers d'annotations du fold 0 (train 266, val 33, test 34), sans fichier de patient du cabinet. [J11A GitHub Actions #39929756032](https://github.com/hraaaaf/Digital_crown/actions/runs/39929756032) **SUCCESS**, sur **HEAD exact `4c9fc8b000cffb4f4d52a07d4ac4921ee14f1d84`**.
- Le job a téléchargé les JPEG dans un **runner éphémère**, calculé SHA-256 des octets et des pixels RGB décodés, plus une empreinte perceptuelle **dHash 64 bits** sur l'image normale et inversée en miroir. Toutes les données individuelles et tous les fichiers sources restent absents des logs ; seules des métriques agrégées sont affichées.
- Huit tests **entièrement synthétiques** de comparaison et de confidentialité ont réussi avant l'audit tiers. Nettoyage confirmé par `J11A_EPHEMERAL_ACADEMIC_IMAGES_REMOVED_NO_ARTIFACTS`. Aucun artefact, image, liste de patients, hash individuel, modèle, checkpoint ou projection d'image n'a été publié.

## 18 944 paires inter-splits comparées

| Split comparé | Paires examinées | JPEG strictement identiques | Pixels RGB décodés identiques | dHash normal/miroir distance ≤4 | dHash distance ≤6 |
|---|---:|---:|---:|---:|---:|
| Train ↔ validation | **8 778** | **0** | **0** | **3** | 33 |
| Train ↔ test interne | **9 044** | **0** | **0** | **3** | 53 |
| Validation ↔ test interne | **1 122** | **0** | **0** | **0** | 4 |
| **Total** | **18 944** | **0** | **0** | **6** | **90** |

Au seuil ≤2 bits : **0 paires candidates**. Distances minimales parmi toutes les paires : train/val **3**, train/test **4**, val/test **6**.

**Interprétation stricte :**
1. **Aucune répétition strictement identique au niveau des octets JPEG ou des pixels décodés** n'a été détectée entre les partitions du fold 0. C'est une preuve limitée à ces deux catégories de répétition, pas une preuve que les radiographies sont toutes indépendantes.
2. Les **six paires dHash à distance ≤4** sont des *candidates de ressemblance visuelle* et **PAS six mêmes patients, six mêmes examens ou six fuites confirmées**. Plusieurs clichés panoramiques distincts peuvent présenter des empreintes perceptuelles similaires par leur composition standardisée. Le seuil ≤6 en produit 90 et illustre la faible spécificité possible de dHash sur cette modalité.
3. Une radiographie répétée avec contraste, recadrage, projection légèrement différente, augmentation ou à une autre date peut ne déclencher ni pixel-SHA ni dHash. Le miroir est traité, mais pas toutes les transformations. **Patient-level/source-level independence, absence de fuite de l'acquisition, consentement et licence d'utilisation ne sont PAS établis.**
4. Les **34 images test internes ont déjà été analysées dans J10V** pour les erreurs FDI. Un futur modèle optimisé ne peut pas s'appuyer sur ce même test pour prétendre à une évaluation externe aveugle, même si aucun doublon exact n'y apparaît.

## J11B — Roster de revue des six paires, LOCALEMENT et UNIQUEMENT en environnement privé

- Code `experiments/lot05_j11b_private_candidate_pair_roster.py`, **jamais exécuté sur les vrais JPEG dans GitHub Actions**, sans noms de radiographies dans les logs/Notion/ChatGPT. Les tests du filtre et des protections de dossier utilisent des empreintes synthétiques.
- Sous poste privé autorisé, reconstitue la liste de toutes les paires inter-splits à distance perceptuelle ≤4 (ou pixels strictement identiques), avec identifiants de fichiers nécessaires au praticien, et les écrit en **JSON local mode 0600**. Refuse d'écrire dans un dépôt Git, dans le dossier source ou sur un chemin existant. La sortie console ne contient que le nombre agrégé de paires.
- Exemple, après clone autorisé de la révision éditeur, **dans un dossier privé qui n'est PAS un dépôt Git** :
  ```bash
  python experiments/lot05_j11b_private_candidate_pair_roster.py \
    --images-dir /dossier_prive/AKUDENTAL/AKUDENTAL/images \
    --labels-dir /dossier_prive/AKUDENTAL/AKUDENTAL/folds/fold_0/labels \
    --private-output-json /autre_dossier_prive/J11B_PAIRES_A_REVOIR.json
  ```
- Chaque paire doit être examinée côte à côte par le praticien : même panoramique / patient répété possible / même anatomie mais autre examen / image différente / incertain. L'analyse clinique peut exiger métadonnées d'acquisition et provenance du fournisseur, non disponibles dans les seules empreintes. **Paires réellement adjugées à ce jour : 0/6**.
- Le lot antérieur J10X avait séparément signalé **28 clichés et 31 répétitions de labels FDI** ; cette revue d'annotations reste elle aussi **0/28**. Ne pas assimiler les deux listes sans examen de leurs références en station privée.

## Décisions et prochains critères

**Screening technique J11A : PASS, mais source d'évaluation patient-indépendante : BLOCKED/UNPROVEN.** Ne pas supprimer ou modifier des images/labels à partir d'une distance dHash. Faire examiner les six paires en privé, vérifier auprès de l'éditeur les identifiants patients, centres d'acquisition, séries éventuelles et l'absence de duplication source, puis acquérir une **nouvelle cohorte d'évaluation externe** avec droits documentés et split par patient.

La source est **CC BY-NC-SA 4.0 selon l'éditeur** ; aucune autorisation commerciale ni clinique confirmée. **PR #1032 toujours DRAFT / pas de merge, aucune mise en Production ou Vercel, aucun poids de modèle stocké, aucun cliché cabinet.**
