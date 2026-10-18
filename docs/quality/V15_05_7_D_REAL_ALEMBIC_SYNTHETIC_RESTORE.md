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


## PG18 : deparser — règle sémantique strictement bornée

La comparaison du vrai catalogue comporte **112 tables, 576 index et 1 215 contraintes** sur la source et la destination. Après `pg_dump -Fc` / `pg_restore`, PostgreSQL 18 modifie uniquement la représentation de certains **tableaux de littéraux** : `ARRAY['X'::character varying]::text[]` devient `ARRAY['X'::character varying::text]`. L'index partiel `uq_ortho_cases_one_open_per_patient` reçoit de surcroît des parenthèses différentes.

La normalisation est **en liste fermée, jamais générique**. Huit règles nominatives préexistantes au sein du laboratoire (sept CHECK simples contrôlés et un index partiel) vérifient la totalité des valeurs et des opérateurs. **Six** autres contraintes CHECK sont désormais autorisées à rapprocher leurs seules graphies de cast PostgreSQL 18, avec vérification obligatoire du **nom + table + type CHECK + expression SQL complète** : `ortho_phase_events.ck_ortho_phase_events_phase_key`, `ortho_phase_events.ck_ortho_phase_events_phase_only_on_start_or_enter`, `station_print_claim_events.ck_station_print_event_transition`, `station_print_configurations.ck_station_print_mode`, `station_print_held_claims.ck_print_claim_state` et `station_print_printer_drafts.ck_print_draft_location`.

Pour chacun de ces six objets, seuls les deux encodages observés `ARRAY['X'::character varying]::text[]` / `ARRAY['X'::character varying::text]` sont réduits à une forme canonique, puis l'intégralité du CHECK est confrontée à un modèle exact (colonnes, ordre/valeurs de tous les littéraux, opérateurs, parenthèses, clauses `OR`). **Toutes les autres contraintes sont comparées sans aucune transformation.** Le test négatif refuse un littéral modifié, l'opérateur `<> ANY`, un `OR TRUE` et un autre nom de table. Ces exceptions ne valent pas autorisation de modifier un schéma : toute extension exige une preuve source/restaurée et une revue adversariale sur le même HEAD.

Une égalité de catalogues après normalisation vérifie la structure observée mais **ne constitue pas une preuve formelle de toutes les propriétés sémantiques ni un contrôle terrain**. La nature et le nombre des exceptions ne permettent aucun GO de migration réelle ; la dette demeure consignée dans `techdoubt.md`.
