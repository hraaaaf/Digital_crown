# Mutuelles dentaires — préparation isolée

Statut : RESEARCH ONLY — aucune intégration applicative.
Date : 2026-09-14.
Master recroisé : `1ce5bc8a6297c89e9b69a8b455ada576d374a6fc`.

## Goal
Préparer l’automatisation future des feuilles de soins dentaires CNOPS, CNSS et Mutuelle des FAR en réutilisant les données déjà présentes dans Digital Crown, sans dupliquer Patient, Actes, Honoraires, Ordonnance ou catalogue d’actes et sans mettre en risque la base existante.

## Résultats verrouillés
- audit anti-doublon documenté ;
- CNSS `610-1-04` validé métier comme formulaire utilisé au cabinet ;
- FAR `Feuille de Mutuelle FAR 2021-1` validée métier comme référence cabinet ;
- CNOPS : page institutionnelle et exigences métier identifiées ; binaire exact/hash encore à verrouiller ;
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

## Templates
- CNSS : `VERIFIED_CABINET_REFERENCE / PRIMARY_LOCK_PENDING` ; PDF de référence observé comme 2 pages, hash non calculé faute d’accès fiable aux octets.
- FAR : `VERIFIED_CABINET_REFERENCE / PRIMARY_LOCK_PENDING` ; validation cabinet acquise, binaire primaire/hash non verrouillés.
- CNOPS : `VERIFIED_INSTITUTIONAL_PAGE / BINARY_HASH_PENDING` ; page institutionnelle confirme la feuille de soins dentaires, binaire exact non récupéré dans cette session.

Aucun hash n’est inscrit tant qu’il n’a pas été calculé sur les octets réellement récupérés.

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

## Gate avant intégration
Restent : verrouillage réel des binaires/hashes lorsqu’accessible, audit final anti-doublon/cohérence, validation métier d’un échantillon NGAP représentatif, puis chantier d’intégration séparé avec tests et migration sur copie DB.

La branche de recherche ne doit ni migrer la DB ni activer de renderer.