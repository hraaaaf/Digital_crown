# CEPH-PREMIUM-V1 — J2.1-M1 : contrat de scène céphalométrique canonique

**Statut : candidat de schéma isolé / NON clinique / pas de persistance.**

## GOAL

Définir un contrat de données pour le futur tracé premium, sans toucher à l'application de cabinet. Un seul brouillon explicite contiendra :

- Scope : `employer_id`, `patient_id`, `study_id`, `original_asset_id`.
- Identité octets : `original_sha256` déclaré, dimensions pixels de la source et repère `SOURCE_IMAGE_PIXELS_TOP_LEFT`.
- Graph scientifique : `scientific_revision`, `scientific_digest`, `scene_revision` et `parent_scene_sha256`.
- Modèle landmarks : nom et empreinte SRPose38 épinglés, mapping marqué `LEGACY_LOCAL_UNVERIFIED`.
- Données : landmarks 38 locaux (plus constructions manuelles explicites), contours anatomiques parmi six IDs, constructions déterministes par références de points, mesures et état d'indisponibilité.
- Calibration : seulement `UNVERIFIED` ou `CANDIDATE` avec preuve ; aucune mesure en millimètres disponible tant que la validation n'est pas établie.
- Statut clinique : **seul `NONCLINICAL_DRAFT` est accepté**, `clinical_release=false`, aucune approbation dans ce lot.

**Une empreinte canonique** SHA-256 est produite à partir du JSON strict, à champs ordonnés et collections triées par ID. L'ordre d'un tableau de landmarks ne doit pas changer le hash scientifique d'une même scène. Les tuples/frozen empêchent les modifications accidentelles du snapshot par les attributs.

## SUCCESS / PROOF

1. Python/Pydantic valide la structure, refuse les champs ajoutés et la coercition silencieuse des IDs.
2. Sources/revisions/modèles/digests déclarés sont structurellement valides ; aucune preuve fictive de correspondance anatomique officielle.
3. Points/contours hors pixels, duplication d'IDs, confusion `Occ_Ant` (construit vs ONNX), score non fini, mesures MM non autorisées ou valeurs manquantes remplacées par 0 sont refusés.
4. Pour chaque contour `AUTO_PROPOSED`, un modèle de contours distinct et son digest sont requis ; **ce lot ne contient aucun tel modèle**. La structure permet de le renseigner ultérieurement.
5. Après correction, `scene_revision>1` exige le SHA-256 du parent. Ce champ seul ne prouve ni transaction CAS ni immutabilité de DB : à tester en J2.1-M3/M4.
6. Tests pytest sur fixtures inventées ; artefact FUE JSON Schema + scène synthétique + rapport, à valider sur HEAD GitHub exact.

## LIMITES / GATES

**M1 n'effectue AUCUNE authentification de l'image**, aucun appel au modèle ONNX, aucun pixel de radio réel, aucune vérification du graph scientifique, aucun accès patient/tenant, aucune sauvegarde, aucun dessin, aucune approbation praticien, aucune migration, aucun PDF. Les empreintes déclarées ne prouvent pas les octets. Une nouvelle révision **mentionne** le parent, mais sa valeur n'est pas encore vérifiée contre la base : futur verrou CAS indispensable.

Le mapping historique 0..37 n'est **PAS certifié par une table anatomique primaire** (PR #510). Ne pas convertir les labels en autorité clinique.

Le schéma et les tests ne sont importés ni enregistrés dans le runtime ou les routes. Le runner CI charge ces deux sources exactes dans un espace isolé car l'import normal du package backend entraîne des initialisations ; ce contournement de l'initialisation s'applique **aux tests de contrat uniquement**.

**NEXT : J2.1-M2** : vérifier transformation EXIF/orientation/zoom/crop contre pixels originaux avec une véritable image autorisée, puis M3 : invariants de révision/CAS en environnement isolé et M4 : branchement prouvé à DC-DOS-05, sans migration clinique.

Références de continuité : [roadmap Céphalo](https://app.notion.com/p/3ec77c663362811db11ec59dbd9eb7d3) · [checklist J1–J5](https://app.notion.com/p/41377c66336281218361e1671f11c231).
