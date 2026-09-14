# Mutuelles dentaires — préparation isolée

Statut : `READY_FOR_INTEGRATION_DESIGN / NOT_READY_FOR_RUNTIME`.
Date : 2026-09-14.
Master recroisé au closeout : `1ce5bc8a6297c89e9b69a8b455ada576d374a6fc`.

## Goal
Préparer l’automatisation future des feuilles de soins dentaires CNOPS, CNSS et Mutuelle des FAR en réutilisant les données déjà présentes dans Digital Crown, sans dupliquer Patient, Actes, Honoraires, Ordonnance ou catalogue d’actes et sans mettre en risque la base existante.

## Résultats verrouillés
- audit anti-doublon documenté ;
- CNSS `610-1-04` validé métier comme formulaire utilisé au cabinet ;
- FAR `Feuille de Mutuelle FAR 2021-1` validée métier comme référence cabinet ;
- CNOPS : page institutionnelle et entrée de téléchargement `Feuille de soins dentaires` confirmées ; binaire exact/hash non récupérés ;
- source dents Honoraires : `DocumentArchive.clinical_data.payments[*].dent/dents` ;
- `Acte` sans dent(s) ni `catalog_act_id` actuellement ;
- `CatalogAct.code` potentiellement NGAP ou interne ;
- contrat `InsuranceSubmissionDraft` documenté ;
- liaison cible documentée : `source_line_uid` immuable + `catalog_act_id` nullable, fallback historique contrôlé par index ;
- schéma NGAP versionné documenté ;
- matrice de tests et plan de migration/rollback documentés ;
- aucun runtime/UI/DB modifié.

## Architecture cible — non implémentée
```text
Patient / Cabinet
DocumentArchive Honoraires + Actes / Payments
CatalogAct
Ordonnance existante
        ↓
adapter / extractor
        ↓
InsuranceSubmissionDraft
        ↓
mapping NGAP déterministe, typé, versionné
        ↓
renderer template assureur
   ↙        ↓        ↘
CNOPS      CNSS      FAR
```

## Décisions structurantes
- aucun second moteur Honoraires ;
- aucune Ordonnance bis ;
- aucun second catalogue NGAP ;
- aucun fuzzy matching silencieux libellé → NGAP ;
- ambiguïté = validation praticien ;
- historique : fallback `document_archive_id + index actif` uniquement avec contrôles d’intégrité ;
- nouveaux flux : `source_line_uid` stable ;
- `catalog_act_id` explicite et nullable ;
- données assurance patient futures facultatives/masquées hors contexte ;
- migration future strictement additive, sans backfill inventé ;
- aucun cachet/signature/accord assureur fabriqué.

## Templates — état de preuve
- CNSS : `VERIFIED_CABINET_REFERENCE / BINARY_HASH_PENDING / PRIMARY_LOCK_PENDING` ; PDF de référence observé comme 2 pages ; octets non récupérés de façon fiable, donc aucun hash déclaré.
- FAR : `VERIFIED_CABINET_REFERENCE / BINARY_HASH_PENDING / PRIMARY_LOCK_PENDING` ; validation cabinet acquise ; binaire institutionnel exact non verrouillé.
- CNOPS : `VERIFIED_INSTITUTIONAL_PAGE / OFFICIAL_BINARY_RETRIEVAL_PENDING` ; CNOPS expose explicitement la feuille de soins dentaires et son téléchargement ; copie secondaire observée comme 2 pages ; binaire institutionnel exact non récupéré.

Aucun SHA-256 n’est inscrit tant qu’il n’a pas été calculé sur les octets réellement récupérés.

## Fichiers canoniques de reprise
1. `README.md`
2. `HANDOVER.md`
3. `VISUAL_REFERENCES.md`
4. `EXISTING_APP_AUDIT.md`
5. `FIELD_MATRIX.md`
6. `SOURCES.md`
7. `NGAP_POLICY.md`
8. `INSURANCE_SUBMISSION_DRAFT.md`
9. `ACT_CATALOG_LINK_STRATEGY.md`
10. `NGAP_REFERENCE_SCHEMA.md`
11. `TEMPLATE_LOCK_STATUS.md`
12. `TEST_MATRIX.md`
13. `MIGRATION_PLAN.md`

## Closeout recherche — preuve
- le diff `master → branche` reste exclusivement sous `docs/research/mutuelles-dentaires/` ;
- aucun fichier runtime, UI, modèle DB ou migration applicative n’est présent dans le diff ;
- aucun PR n’est associé à cette branche au dernier contrôle ;
- aucun status/check CI n’est associé au HEAD au dernier contrôle (`statuses=[]`, `total_count=0`) ;
- la branche diverge de master car elle a été créée sur une baseline antérieure : ne pas merger mécaniquement sans rebase/contrôle de cohérence.

## Gate
`READY_FOR_INTEGRATION_DESIGN` signifie : contrat, liaisons, référentiel cible, tests et plan de migration sont suffisamment définis pour ouvrir un chantier d’intégration séparé.

`NOT_READY_FOR_RUNTIME` reste obligatoire tant que :
1. les binaires/templates et SHA-256 ne sont pas verrouillés quand techniquement accessibles ;
2. le mapping NGAP réel n’est pas construit depuis sources primaires versionnées ;
3. un échantillon représentatif n’est pas validé métier ;
4. la migration additive n’est pas testée sur copie DB ;
5. les tests automatisés du futur chantier d’intégration ne sont pas verts.

La branche de recherche ne doit ni migrer la DB ni activer de renderer.