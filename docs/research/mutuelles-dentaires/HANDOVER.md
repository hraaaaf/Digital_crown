# HANDOVER — Mutuelles dentaires Digital Crown

Date : 2026-09-14.
Statut : `READY_FOR_INTEGRATION_DESIGN / NOT_READY_FOR_RUNTIME`.
Repo : `hraaaaf/Digital_crown`.
Branche : `research/mutuelles-dentaires-prep-20260914`.

## Goal
Préparer l’automatisation future des feuilles de soins dentaires CNOPS, CNSS et FAR en réutilisant Patient, Cabinet, Honoraires, Ordonnance, Acte, CatalogAct et DocumentArchive existants, avec mapping NGAP déterministe/versionné/traçable et sans risque DB.

## À lire EN PREMIER
Les 13 fichiers sous `docs/research/mutuelles-dentaires/` :
`README.md`, `HANDOVER.md`, `VISUAL_REFERENCES.md`, `EXISTING_APP_AUDIT.md`, `FIELD_MATRIX.md`, `SOURCES.md`, `NGAP_POLICY.md`, `INSURANCE_SUBMISSION_DRAFT.md`, `ACT_CATALOG_LINK_STRATEGY.md`, `NGAP_REFERENCE_SCHEMA.md`, `TEMPLATE_LOCK_STATUS.md`, `TEST_MATRIX.md`, `MIGRATION_PLAN.md`.

Puis revérifier réellement master, HEAD branche, diff, PR et CI. Les SHA ci-dessous sont des preuves historiques, pas des vérités éternelles.

## État vérifié au closeout documentaire
- master recroisé : `1ce5bc8a6297c89e9b69a8b455ada576d374a6fc` ;
- diff `master → branche` limité à 13 fichiers sous `docs/research/mutuelles-dentaires/` ;
- branche divergente de master car créée depuis `5e1802901301a36fa4acf3d34adbfbde84258c18` ; rebase/contrôle requis avant tout éventuel merge ;
- aucun PR associé à cette branche au dernier contrôle ;
- aucun status/check CI associé au HEAD au dernier contrôle (`statuses=[]`, `total_count=0`) ;
- aucun runtime/UI/DB/migration applicative modifié.

## Décisions verrouillées
- `InsuranceSubmissionDraft` = DTO de sortie, jamais source clinique/financière ;
- historique ligne Honoraires ↔ Acte : fallback contrôlé par `document_archive_id + index actif` ;
- cible future : `source_line_uid` immuable + `catalog_act_id` nullable explicite ;
- `CatalogAct` reste le catalogue unique ;
- référentiel NGAP = couche réglementaire versionnée liée à `CatalogAct`, pas second catalogue ;
- aucun fuzzy matching silencieux ;
- mapping `AMBIGUOUS/NO_MATCH/OUTDATED` = fail-closed + validation praticien ;
- données assurance Patient optionnelles et contextuelles ;
- migration future additive uniquement, sans backfill inventé ;
- aucun cachet/signature/accord assureur fabriqué.

## Templates
### CNSS
- `610-1-04`, Réf. ANAM `1.2.03.01` ;
- `VERIFIED_CABINET_REFERENCE / BINARY_HASH_PENDING / PRIMARY_LOCK_PENDING` ;
- PDF de référence observé comme 2 pages ;
- binaire non récupéré de façon fiable dans l’environnement courant, donc aucun SHA-256 déclaré.

### FAR
- `Feuille de Mutuelle FAR 2021-1` ;
- `VERIFIED_CABINET_REFERENCE / BINARY_HASH_PENDING / PRIMARY_LOCK_PENDING` ;
- validation cabinet déjà acquise ; ne pas la redemander sauf divergence de version/binaire ;
- binaire institutionnel exact non verrouillé.

### CNOPS
- page institutionnelle et page de téléchargement confirment explicitement `Feuille de soins dentaires` ;
- convention hébergée CNOPS : article 10 impose l’utilisation de feuilles conformes aux modèles ANAM ;
- copie visuelle secondaire observée comme PDF 2 pages ;
- `VERIFIED_INSTITUTIONAL_PAGE / OFFICIAL_BINARY_RETRIEVAL_PENDING` ;
- récupération directe du binaire institutionnel en échec/timeout dans cette session ; aucun hash inventé.

## Gate de fin du lot recherche
Le lot documentaire est prêt pour concevoir l’intégration, mais PAS pour activer le runtime.

Avant runtime :
1. récupérer/verrouiller les binaires + SHA-256 lorsqu’un accès fiable existe ;
2. construire le référentiel NGAP réel depuis sources primaires versionnées ;
3. valider métier un échantillon représentatif ;
4. ouvrir un chantier d’intégration séparé ;
5. tester migration additive + rollback sur copie DB ;
6. faire passer les tests automatisés ;
7. seulement ensuite envisager activation cabinet.

## Next exact
Si l’utilisateur reste en préparation documentaire : seul blocage restant immédiatement identifié = récupération fiable des binaires/hash templates ; ne pas répéter les audits déjà clos.

Si l’utilisateur demande de passer au code : créer un chantier d’intégration séparé depuis master courant, revalider l’existant, puis implémenter par lots `source_line_uid/catalog_act_id` → données assurance optionnelles → référentiel NGAP → DTO → renderer, avec tests avant chaque étape.

## Blocages réels
- accès fiable aux octets des templates web pour SHA-256 ;
- mapping NGAP réel et validation métier finale ;
- runtime volontairement hors périmètre de cette branche.

## Interdits
- pas de migration réelle ici ;
- pas de renderer activé ;
- pas de déploiement.