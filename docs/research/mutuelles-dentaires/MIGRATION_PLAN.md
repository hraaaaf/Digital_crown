# Migration plan — Mutuelles dentaires

Statut : PLAN ONLY — aucune migration exécutée.
Date : 2026-09-14.

## Goal
Préparer une évolution strictement additive permettant la liaison robuste des lignes Honoraires et des actes au catalogue, ainsi que les données assurance optionnelles, sans perte ni obligation de backfill.

## Périmètre cible futur
### Honoraires / Acte
- `source_line_uid` nullable sur `Acte` ;
- `catalog_act_id` nullable sur `Acte`, FK vers `catalog_acts.id` ;
- extension du snapshot Honoraires avec `source_line_uid` et `catalog_act_id` pour les nouveaux documents.

### Patient / assurance
Champs futurs uniquement si nécessaires au renderer :
- CIN ;
- n° affiliation/immatriculation/compte ;
- qualité assuré/ayant-droit ;
- identité assuré distincte si besoin.

Tous nullable/optionnels et masqués hors contexte assurance.

### Référentiel NGAP
Préférer une table/version réglementaire liée à `CatalogAct` plutôt qu'un second catalogue métier. Les références source/version/hash doivent être immuables pour une version publiée.

## Ordre de migration proposé
1. sauvegarde/copie représentative de la DB cabinet ;
2. baseline comptages + checksums logiques des tables critiques ;
3. ajout de colonnes/tables uniquement ;
4. aucun backfill automatique de données ambiguës ;
5. démarrage application avec dossiers historiques ;
6. tests lecture/édition/génération Honoraires existants ;
7. tests nouveaux documents avec UID ;
8. tests mapping CatalogAct/NGAP ;
9. tests rollback ;
10. seulement après preuves : migration réelle dans chantier séparé.

## Preuves avant/après obligatoires
Avant :
```text
count(Patient)
count(Acte)
count(DocumentArchive)
count(CatalogAct)
set(Patient.id)
set(Acte.id)
```

Après migration :
- mêmes nombres pour les lignes préexistantes ;
- mêmes IDs ;
- aucune valeur ancienne modifiée ;
- nouvelles colonnes NULL sur historique sauf donnée explicitement connue ;
- anciens documents réouvrables ;
- Honoraires existants toujours éditables ;
- aucun nouveau paiement/Acte créé par simple migration.

## Politique de backfill
Interdit de déduire automatiquement :
- `catalog_act_id` depuis `Acte.libelle` ;
- code NGAP depuis `CatalogAct.code` non typé ;
- CIN/affiliation depuis notes libres ;
- `source_line_uid` historique en prétendant restaurer une identité inconnue.

L'historique utilise le fallback documenté par index + contrôles d'intégrité. Les nouveaux flux utilisent l'UID.

## Rollback
Le rollback doit :
- désactiver le code consommant les nouveaux champs ;
- laisser les colonnes/tables additives en place si leur suppression créerait un risque ;
- ou utiliser une migration inverse testée uniquement si aucune donnée nouvelle utile ne peut être perdue ;
- prouver que l'ancienne version applicative relit les données historiques.

## Tests P0
1. migration sur copie DB sans erreur ;
2. nombre patients inchangé ;
3. IDs patients inchangés ;
4. données patients existantes byte/logiquement identiques sur colonnes historiques ;
5. aucun Acte/Payment créé ou supprimé ;
6. documents historiques lisibles ;
7. création/édition Honoraires historique inchangée ;
8. rollback testé ;
9. nouveau champ absent ne casse aucune API historique.

## Human gate
Aucune migration réelle sur la DB cabinet ne doit partir depuis la branche de recherche. Elle appartient à un chantier d'intégration séparé après audit final, tests automatisés et validation explicite du périmètre.