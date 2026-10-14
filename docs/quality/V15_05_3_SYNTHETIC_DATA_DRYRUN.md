# LOT05.3-LAB — dry-run **de valeurs entièrement fictives** S01 / S02 / S03 (aucune intégration cabinet)

**Statut** : test-only, empilé sur [PR #857](https://github.com/hraaaaf/Digital_crown/pull/857). Le moteur du laboratoire se trouve sous `backend/tests/lab_legacy_sql_synthetic_data_v15.py`, **PAS dans `backend/services` ni un router**. Il ne peut recevoir ni URL/engine/path cible, ni accès à un compte réel. Toute tentative de connexion au runtime, de restauration de SQL issu d'un client ou d'import réel reste explicitement hors périmètre. Ne pas déplacer ce helper vers le service sans conception et gate séparés.

## Qu'est-ce qui est *effectivement* simulé ?

1. Repartir des trois structures source certifiées dans S01–S03 et des contrats *existants* 05.1 → 05.2-A → 05.2-B2a. Utiliser les noms de colonnes tirés de `backend.models.Patient` et `Appointment` (déclarations, **pas schéma physique**). Créer un **nouveau draft explicite de laboratoire** qui mappe la table de rendez-vous en plus des patients ; confirmer son empreinte par `revalidate_mapping_draft`. Le draft n'est et ne devient jamais approuvé par l'administrateur.
2. S01 : fixture de valeurs Python **fictives uniquement**, car le SQL textuel est DDL-only pour l'inspecteur (aucun parsing/exécution des INSERT). Colonnes EN, 2 patients et 2 rendez-vous avec identifiants source différents des identifiants cible.
3. S02 : fabriquer un **vrai fichier SQLite temporaire** rempli de données fictives, lire *uniquement ces données fictives* en RO immutable via SQL paramétré/fixe et sans connexion de production, préparer 1 patient et 1 RDV. L'inspecteur 05.1 lit indépendamment le schéma du même fichier fermé.
4. S03 : valeurs Python fictives + fixture PostgreSQL DDL-only, noms ES, 2 patients et 1 rendez-vous.
5. Convertir **seulement** les formats déclarés explicitement (`%Y-%m-%d`, `%d/%m/%Y`, `%d-%m-%Y` et variantes minute pour RDV) ; refuser le faux format, la date impossible ou un padding ambivalent. Traduire `status` en `PREVU` **uniquement** si l'étiquette source correspond à la valeur explicitement revue dans la configuration du test ; ne jamais deviner l'enum.
6. Assigner des IDs cible nouveaux dans **sqlite3.connect(':memory:')**. Gérer un dictionnaire temporaire `source_id -> ID cible` afin de recâbler les clés étrangères RDV. Ajouter une FK SQLite *réellement activée*, un contrôle d'unicité et un trigger de cohérence de tenant dans le scratch. `employer_id=777` est une valeur **fictive codée dans le LAB**, pas une identité dérivée d'un JWT et **jamais à importer depuis la source**. Interdire la copie d'IDs source et les rôles/credentials.
7. Vérifier dans la DB scratch le nombre de lignes, l'intégrité FK et l'égalité des tenants, puis exécuter `ROLLBACK TO synthetic_rehearsal` et contrôler **0 patient et 0 RDV présents** avant de fermer la DB scratch. Même les succès ne persistent pas.

Le rapport ne livre que des nombres, codes et drapeaux de non-autorisation. Il ne contient aucun nom, date, email, identifiant source, statut médical ou secret. Tous les drapeaux `physical_target_verified / tenant_authenticated / human_approved / real_dry_run_completed / import_permitted` sont **false**. La mention `scratch_fk_checked` concerne une **miniature artificielle de tables**, pas le schéma Digital Crown physique et ses contraintes complètes.

## Scénarios adversariaux

S04 RDV orphelin, S05 candidat doublon (refus conservateur, **pas rapprochement clinique**), S06 identifiant source répété, S07 date impossible, S08 format absent, S09 statut inconnu, S10 nom qui ne porte pas le marqueur fictif, S11 flag approval forgé, S12 source hash différent, S13 colonne source absente, S14 date non canonique, S15 trop de lignes, S16 colonnes ORM attendues absentes, S17 statut sans traduction explicite, S18 candidat rendez-vous doublon (même patient/heure/statut, refus prudent sans fusion automatique), S19 heure invalide. Chaque cas doit **échouer par code stable non-PHI**. Les tests ne prouvent pas l'exhaustivité des détections de doublons.

## Limitations et NEXT

- S01/S03 ne lisent **aucune ligne issue des fichiers .sql** : les valeurs sont instanciées séparément dans le banc de tests. Cela évite d'exécuter du SQL inconnu, mais ce n'est **pas un adaptateur d'import MySQL/Postgres**.
- S02 lit des lignes SQLite, mais **uniquement** d'un fichier fictif fabriqué dans le test. Aucune copie SQLCipher de cabinet, aucun chiffrement de données source.
- La DB scratch n'est qu'une **projection minimale** des colonnes Patient/Appointment, pas une création des vraies tables ORM avec comptes utilisateurs, relation cabinet, SQLCipher, Alembic ou schemas PostgreSQL. Les valeurs `sexe`, `date_naissance`, `status` ne constituent pas une validation métier complète.
- Un candidat doublon détecté par même nom/prénom/date peut être un homonyme ; aucune fusion automatique n'est autorisée. D'autres doublons peuvent ne pas être reconnus.
- Les décisions manuelles des tests ne sont **pas une approbation humaine**, ni une preuve d'autorisation serveur. La fonction n'est pas sécurisée pour accepter de vraies valeurs ; elle n'a aucun droit d'accéder à une DB client.
- La version cible `orm-declared:neo000000027` n'atteste pas le vrai schéma du cabinet, et la branche LOT04 propose `neo000000028` non intégrée. Ne pas brancher la simulation sur le runtime.
- **BLOQUANTS pour réel** : 05.2-B2b physical DDL & Alembic, owner auth/tenant, profiles chiffrés et approuvés, vraie conversion types/enums, actes, paiements et documents, conflit/duplication cross-batch et source existante, provenance, journal anti-replay, reprise idempotente, contrôle d'intégrité sur base cible **isolée complète**, backups vérifiés/restauration, sécurité SQLCipher/PG, tests terrain/UX/humains.

Ce lot est un **simulation de transformation et insertion temporaire, suivies de rollback**, pas un vrai import, pas un dry-run clinique autorisé et pas une preuve d'un changement de logiciel sans perte de dossier.
