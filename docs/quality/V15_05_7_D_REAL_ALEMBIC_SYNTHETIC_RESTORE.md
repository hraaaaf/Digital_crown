# Digital Crown LOT05.7-D — vrai head Alembic PostgreSQL 18, restauration synthétique

**Périmètre strict 05.7-D.** Ce laboratoire est empilé sur 05.7-C (PR #965), après 05.7-B (#964) et 05.7-A (#963). Il est **test-only** : aucun changement d'API d'import, Alembic, modèle applicatif, frontend, station/mobile ni démarrage du Cabinet. **Import clinique réel : NO-GO.**

## Différence fondamentale avec 05.7-C

La base source PostgreSQL 18 est initialement entièrement vide dans un service GitHub Actions CI jetable dédié `lot05d_fake_source`. Elle reçoit une vraie commande opérateur `alembic upgrade head` du dépôt et doit atteindre la **révision canonique `neo000000031`** avec toutes les tables et contraintes présentes dans la metadata réelle du repository, et pas des tables de démonstration inventées.

Le script `backend/tests/test_legacy_sql_057d_real_alembic_pg_restore.py` utilise les **vraies classes ORM** `User`, `Patient`, `Appointment`, `Acte`, `Payment`, `DocumentArchive`, mais exclusivement avec des informations **fictives** (2 owners, 6 patients, 12 RDV, 4 actes, 4 paiements, 2 métadonnées de documents FAKE sans fichiers médicaux). Le test collecte le SHA du catalogue physique des colonnes/index/contraintes, l'empreinte logique des six tables, les décomptes et totaux financiers. Une vraie sauvegarde `pg_dump -Fc` est restaurée avec `pg_restore --single-transaction --exit-on-error` sur une **seconde base vide distincte**, puis toutes les preuves sont comparées et la révision Alembic du restore est vérifiée. Des contrôles négatifs couvrent SHA invalide, archive corrompue, double restauration refusée, nom de base interdit, snapshot historique et contrôle des références patient/RDV croisées entre tenants.

La référence média est **une métadonnée fictive** et son chemin volontairement inexistant : ce lot ne restaure aucun octet d'image ou fichier médical. Le risque de relation cross-tenant est vérifié via une transaction de laboratoire supprimée à la fin, sans en déduire que l'ORM est tenant-safe à lui seul.

## Isolation et preuve exigée

Workflow dédié `.github/workflows/v15-05-7-d-real-alembic-synthetic-restore.yml`, déclenché pour cette seule branche et la PR, contrôlant checkout SHA exact et diff par rapport à 05.7-C. Le script refuse tout autre `DATABASE_URL`, exige la marque `LOT05D_REAL_ALEMBIC_SYNTHETIC_ONLY=1` et un ID Docker hexadécimal du service PostgreSQL CI. Il ne crée/détruit que la base supplémentaire **jetable** `lot05d_fake_restored`, sur la même instance CI. Les secrets publiés dans ce workflow sont strictement des *identifiants de laboratoire*, jamais des identifiants utilisateurs. Aucun artefact n'exporte les données de test.

L'ancien schéma 05.7-C simplifié ne doit pas être présenté comme la preuve 05.7-D. Inversement, un vrai schéma dans une base neuve jetable n'est **pas** un vrai historique Cabinet ou une source tierce à migrer. Les résultats CI, logs et revues A/B sur le même HEAD sont obligatoires avant de déclarer ce sous-lot convergé.

## Réserves connues, voir techdoubt.md

**BLOCKERS de certification clinique réelle** : origine/provenance légale du source SQL externe, accord propriétaire et tenant runtime, copie autorisée de données réelles dans un environnement de conformité, sauvegarde **et restauration** SQLCipher et médias réellement chiffrés, sauvegarde système/Windows NTFS/reparse/crash et RPO/RTO, régénération/traitement des doublons historiques, cohérence des actes/factures, synchronisation transactionnelle des médias, contrôles d'accessibilité et consentement humain. Le schéma physique PostgreSQL 18 ne suffit pas à garantir l'isolation cross-tenant : une référence `patient_id` qui existe sous un autre `employer_id` doit être refusée explicitement par le pipeline si les FKs de base ne l'imposent pas. Un test qui insère temporairement une telle relation ne doit jamais être réutilisé comme autorisation d'écriture.

**Ce lot n'implémente et n'autorise aucune fonction d'import réel**. SQLCipher à la révision Alembic réelle sera une preuve de chantier séparée si besoin, jamais implicitement couverte par un passage PG vert. Les revues adversariales sont internes si aucun réviseur externe n'a participé. Statut initial : **DRAFT / non certifié avant CI**.


## PG18 : différences de texte de décompilation autorisées (bornées)

Un véritable `pg_dump -Fc` / `pg_restore` de la base Alembic a montré 112 tables, 576 index et 1 215 contraintes de chaque côté, mais PostgreSQL réécrit `ARRAY['X'::character varying]::text[]` en `ARRAY['X'::character varying::text]` (et variantes de parenthèses) : le texte renvoyé par `pg_get_constraintdef`/`pg_indexes` n'est donc pas systématiquement stable. Les différences identifiées concernent **exclusivement** un index partiel `uq_ortho_cases_one_open_per_patient` et quatre contraintes `ck_clinical_assets_asset_type`, `ck_clinical_assets_source_kind`, `ck_ngap_mapping_code_kind`, `ck_ngap_mapping_verification_status`.

Le laboratoire normalise **seulement** ces cinq objets précis après vérification des noms, du type CHECK, de la colonne, des opérateurs, des tables, de l'ordre et de l'exactitude des valeurs d'énumération. Tous les autres objets et toute déviation hors ces formes restent comparés littéralement et échouent en fail-closed. Un test négatif injecte un libellé d'énumération différent, un opérateur modifié et `OR TRUE` : ils doivent tous être refusés. Cette normalisation n'est **pas** une attestation formelle d'équivalence de toutes les contraintes, ni une exemption autorisant un schéma réel modifié. Consulter `techdoubt.md` pour le risque résiduel et la preuve à obtenir avant clinique.
