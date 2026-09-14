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

Puis revérifier réellement master, HEAD branche, diff, PR et CI. Les SHA ci-dessous sont des preuves historiques, pas des vérités éternelles. Git, cette machine à rappeler que le présent a déjà changé.

## État vérifié au closeout
- master : `1ce5bc8a6297c89e9b69a8b455ada576d374a6fc` ;
- commit DTO/liaison/NGAP : `5332ea19170203791ec8842170a430fe144b211f` ;
- commit templates/tests/migration : `0676fa5a7556e4f00c3d2915e3a21780ff674464` ;
- diff avant commit de closeout : 13 fichiers, tous exclusivement sous `docs/research/mutuelles-dentaires/` ;
- divergence avant commit de closeout : 21 ahead / 30 behind ;
- aucun PR ;
- aucun status/check CI observé ;
- aucun runtime/UI/DB/migration modifié.

## Décisions verrouillées
- `InsuranceSubmissionDraft` = DTO de sortie, jamais source clinique/financière ;
- historique ligne Honoraires ↔ Acte : fallback contrôlé par `document_archive_id + index actif` ;
- cible future : `source_line_uid` immuable + `catalog_act_id` nullable explicite ;
- `CatalogAct` reste le catalogue unique ;
- référentiel NGAP séparé uniquement comme couche réglementaire versionnée liée à `CatalogAct` ;
- aucun fuzzy matching silencieux ;
- mapping `AMBIGUOUS/NO_MATCH/OUTDATED` = fail-closed + validation praticien ;
- données assurance Patient optionnelles et contextuelles ;
- migration future additive uniquement, sans backfill inventé ;
- aucun cachet/signature/accord assureur fabriqué.

## Templates
- CNSS `610-1-04` : `VERIFIED_CABINET_REFERENCE / PRIMARY_LOCK_PENDING`, PDF de référence observé comme 2 pages, hash non calculé.
- FAR `Feuille de Mutuelle FAR 2021-1` : `VERIFIED_CABINET_REFERENCE / PRIMARY_LOCK_PENDING`, validation cabinet déjà acquise ; ne pas la redemander sauf divergence de version/binaire.
- CNOPS : `VERIFIED_INSTITUTIONAL_PAGE / BINARY_HASH_PENDING`, page institutionnelle et exigences dentaire confirmées ; binaire exact inaccessible dans cette session.

Aucun SHA-256 n’a été inventé.

## Gate de fin du lot recherche
Le lot documentaire est prêt pour concevoir l’intégration, mais PAS pour activer le runtime.

Avant runtime, il faut encore :
1. verrouiller les binaires/templates + SHA-256 quand l’accès le permet ;
2. construire le référentiel NGAP réel depuis sources primaires versionnées ;
3. valider métier un échantillon représentatif ;
4. implémenter dans un chantier séparé ;
5. tester migration additive + rollback sur copie DB ;
6. faire passer les tests automatisés ;
7. seulement ensuite envisager activation cabinet.

## Next exact
À la prochaine reprise : ne pas refaire la recherche préparatoire. Ouvrir un **chantier d’intégration séparé** uniquement si l’utilisateur demande de passer au code. Sinon, le seul travail documentaire restant est la récupération/hash des templates dès qu’un accès fiable aux binaires est possible.

## Blocages réels
- accès fiable aux octets des templates web pour hash ;
- validation métier NGAP finale ;
- intégration/runtime volontairement hors périmètre de cette branche.

## Interdits
- pas de migration réelle ici ;
- pas de renderer activé ;
- pas de déploiement.