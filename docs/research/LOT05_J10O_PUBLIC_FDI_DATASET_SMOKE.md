# LOT05/J10O — Stratégie A : tests d'intégrité sur datasets panoramiques publics

**2026-10-22 — Recherche expérimentale uniquement. Aucune fusion, production, intégration clinique ou poids entraînés.**

## Objectif utilisateur

« Stratégie A ! On cherche un dataset public et on fait dessus les tests ». Contrairement aux jalons précédents J10M/J10N strictement synthétiques, ce lot **interroge en direct les publications des fournisseurs de deux corpus distincts**. Le second test tente de **charger une seule radiographie déjà rendue publique sous une licence CC BY annoncée par la source académique**, uniquement en mémoire, sans sauvegarder/redistribuer de pixels, sans tenter d'identifier les patients. Un échec d'accès réseau est un échec signalé, pas un succès fabriqué. Aucun patient du cabinet n'est impliqué.

**Attention : il n'y a pas encore une évaluation FDI sur un véritable ensemble de panoramiques avec ground truth vérifiée.** Deux sources distinctes sont utilisées pour répondre honnêtement à deux questions techniques différentes ; il ne faut jamais fusionner leurs métriques.

## Source A — Numérotation FDI 32 : Roboflow Panoramic-Dental-Xray-FDI

Source éditeur : https://universe.roboflow.com/dentalxray-yjztn/panoramic-dental-xray-fdi et version https://universe.roboflow.com/dentalxray-yjztn/panoramic-dental-xray-fdi/dataset/1

**Publié** : 1 577 images d'origine, 32 classes exactement `11–18, 21–28, 31–38, 41–48`, licence **CC BY 4.0 déclarée**. Version v1 : **3 503 exemples transformés**, split rendu public **3 032 train, 315 val, 156 test**, redimensionnement *Stretch 1280×1280* et rotations à **90 degrés** (y compris renversement). **En l'absence de données d'identité d'origine / paires augmentées, ces splits ne sont pas utilisables comme benchmark indépendant de confiance**. La fiche indique : « A description for this project has not been published yet ».

**Ce que teste le job** : https/HTML éditeur accessible sans identifiants, licence déclarée, **les 32 classes dans l'ordre exact**, 1 577 images vs 3 503 exemples, partitions et avertissement de provenance. **Aucun ZIP, aucune image, aucune boîte de vérité terrain téléchargée** dans ce job. Il ne valide ni la qualité des annotations ni une prédiction FDI. L'export COCO/YOLO officiel passe par « Download Dataset », qui peut demander une connexion/clé Roboflow ; ne pas chercher à contourner le contrôle d'accès et ne jamais publier de secrets. Un futur protocole de lecture du contenu devra documenter les droits d'origine, la présence éventuelle de données patients et la conservation des splits par patient/fichier original AVANT de commencer l'entraînement.

## Source B — Radiographies réelles issues de la recherche universitaire tunisienne (CC BY 4.0)

Source première : https://data.mendeley.com/datasets/73n3kz2k4k/3, DOI `10.17632/73n3kz2k4k.3`, auteurs Brahmi/Jdey/Drira, Université de Kairouan. La publication décrit **107 panoramiques segmentées par instance**, **60 images étiquetées en 8 types anatomiques** (incisives, canines, molaires, prémolaires) et **54 autres panoramiques**. Licence affichée **CC BY 4.0** ; acquisition des deux premières parties sur Orthoralix 9200, et de la troisième sur Dentio III. **Huit types anatomiques ne signifient pas FDI 32** et la partie 54 peut n'avoir aucune annotation de classe correspondante.

**Ce que tente le job Linux** : accéder aux métadonnées publiques via la nouvelle adresse API officielle **`api.data.mendeley.com`** (d'après [documentation Mendeley](https://data.mendeley.com/api/docs/)), vérifier la version 3 et **la licence publiée dans la réponse d'API**, lister les fichiers, sélectionner **un JPEG public de petite taille** (jusqu'à 2 Mo), le lire uniquement en mémoire RAM, vérifier qu'il s'agit d'un panoramique (forme, dimensions, variance), le convertir en image RGB redimensionnée 640×320 utilisée par notre banc d'essai. Ne sauvegarder aucun pixel, original DICOM, nom de fichier ou hash dans les artifacts. Si Mendeley exige OAuth, cache le fichier ou renvoie un HTTP 401/403, le workflow **doit échouer explicitement** et indiquer le blocage d'accès ; il ne déduit pas la réussite des fixtures.

Aucun FDI mAP / numérotation mesurable sur cette image sans annotations FDI 32. Ne pas convertir une statistique de prétraitement en « IA dentaire validée ».

## Implémentation

- `experiments/lot05_j10o_roboflow_fdi_public_metadata.py` : récupère uniquement 2 pages Roboflow autorisées, vérifie classe map et source/augmentations, accepte l'état de droits commerciaux **NO-GO** uniquement.
- `experiments/lot05_j10o_tunisia_public_opg_sample.py` : interroge les endpoints académiques Mendeley v3, vérifie le champ de licence, choisit un JPEG dans une limite d'octets stricte, valide par Pillow sans écriture de fichier. Pas de credentials/OAuth contournés.
- `experiments/test_lot05_j10o_public_dataset_smoke.py` : tests adversariaux sur mapping, licences altérées, nombre d'images augmentées, URLs arbitraires, format de fichier incorrect et prétraitement synthétique.
- `.github/workflows/lot05-j10o-public-panoramic-research-qa.yml` : préflight J10I/J10L, Roboflow metadata Linux+Windows et échantillon universitaire Linux. **Artifacts : JSON agrégé seulement**.

## Résultat et conditions de progression

Les portes suivantes doivent être distinguées : **(1) l'accès à un dataset public fonctionne ; (2) le schéma FDI/les annotations vérifiées sont corrects ; (3) les images ont une provenance / base juridique de traitement suffisante ; (4) les droits d'entraînement / redistribution commerciale de poids sont autorisés ; (5) les validations de qualité clinique ont été réalisées**. Une licence « CC BY 4.0 » affichée sur un dépôt est une donnée de l'audit, pas une preuve clinique de tous les droits sous-jacents. En l'état, **J10I/J10L/J10M/J10N maintiennent le NO-GO commercial, cloud clinique et distribution**.

Un futur entraînement efficace devrait choisir des panoramiques avec 32 positions FDI par dent, vérifier l'orientation, contrôler doublons/permutations, reconstruire un split au niveau du patient/source plutôt qu'au niveau des augmentations 90° et mesurer précision de numérotation des films entièrement corrects. Après cela, seulement, entraînement D-FINE Nano sur ces classes et comparaison indépendante sur Windows et Linux.

**Contrat de l'interface propriétaire** : le PDF panoramique validé contient **exclusivement le compte rendu écrit**, aucune image radiographique n'est insérée dans le PDF.
