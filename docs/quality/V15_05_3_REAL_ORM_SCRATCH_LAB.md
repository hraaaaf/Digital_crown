# LOT05.3-B LAB — vraies contraintes ORM sur une base physique synthétique : constats et limites

Cible de ce passage : remédier au principal défaut de la PR #861 (score LAB limité 7,2/10) : ses tests écrivaient dans une miniature SQLite à deux tables **qui n'avait pas les vraies contraintes SQLAlchemy de Digital Crown**.

Ce sous-lot reste **STRICTEMENT TEST-ONLY** empilé sur [PR #861](https://github.com/hraaaaf/Digital_crown/pull/861), elle-même empilée sur les PR Draft #857/#856/#854/#853/#850. **Aucun merge, API, auth, alembic, produit ou déploiement**.

## Construction réelle et preuve

- Le banc `backend/tests/test_legacy_sql_real_orm_scratch_v15.py` charge, dans un namespace Python isolé sans démarrer `backend/__init__.py` ni `backend.database`, les vraies classes de `backend/models.py` pour `users`, `agenda_resources`, `patients`, `appointments`.
- Il copie leurs déclarations avec `Table.to_metadata`, crée physiquement leurs vrais types de colonnes, nullabilités, clés étrangères, uniques et indexes avec SQLAlchemy sur une DB éphémère **`sqlite+pysqlite:///:memory:`**, active `PRAGMA foreign_keys=ON` et compare les colonnes/nullable de la base effectivement créée aux déclarations originales. **Ce n'est PAS un Alembic upgrade, un clone de toute la DB, une version physique cabinet, PostgreSQL ni SQLCipher.**
- Avant l'insertion « ORM réel » S01/S02/S03, les **mêmes fausses lignes** et **même MappingDraft** passent le simulateur 05.3-A et son rollback zéro. S01 deux patients fictifs + deux RDV, S02 un patient fictif + un RDV **lu d'un fichier SQLite fictif**, S03 deux patients fictifs + un RDV. Les valeurs S01 et S03 sont déclarées dans le banc en Python : aucun INSERT de fichier `.sql` n'est exécuté.
- Dans la vraie projection ORM, un faux propriétaire `777`, une fausse identité additionnelle `778` et un faux patient préexistant `id=900` sont créés dans la transaction **jamais committée**. Les IDs du legacy sont régénérés et les RDV sont reliés par ID cible ; l'helper de labo refuse le lien entre deux tenants différents, vérifie FK et comptages.
- Les tests négatifs prouvent que la contrainte réelle `uq_patients_numero_dossier_employer` refuse une double référence dans le même cabinet mais accepte la même dans deux cabinets, que les colonnes obligatoires sont effectivement non nullables, qu'un RDV orphelin est rejeté par la vraie FK et que toute transaction revient à zéro ligne après rollback.

## Constat adversarial qu'il faut **garder visible**

**La vraie définition ORM `appointments` ne fournit pas de FK composite (`patient_id`, `employer_id`) vers le patient de ce même cabinet.** Les deux FK séparées n'interdisent donc pas, à elles seules, un RDV dont le cabinet est B mais dont le patient appartient à A. Le test physique le démontre *intentionnellement* dans une transaction isolée qui sera rollback, tandis qu'une fonction de validation stricte dédiée au **LAB** bloque ce cas dans le flux simulé. Ce refus de laboratoire **ne certifie aucun chemin d'import runtime** et ne corrige pas l'architecture backend. Un gate serveur tenant-aware indépendant et un traitement de ce défaut sont **BLOCKERS de tout import réel**.

Autre vérité : les doublons de rendez-vous ne sont pas interdits par une contrainte physique unique de `appointments`. Le laboratoire 05.3-A les bloque explicitement comme candidats, mais les vrais chemins runtime doivent définir idempotence, rejet ou résolution humaine multi-batch. **Ne pas ajouter d'index unique simpliste** : le métier peut autoriser plusieurs actes/RDV de même heure avec règles plus fines.

## Gates supplémentaires bloquants

Schéma de **4 vraies tables SQLAlchemy** créé via `create_all`, pas restauration PostgreSQL/SQLite complète ni Alembic, ni chargement source propriétaire, vrais dossiers, imagerie, paiements, comptes/praticiens, relations au-delà de patient/RDV, enums/dates toutes variantes ; pas de données existantes réelles ni collisions historiques. Pas de preuve du serveur authentifiant propriétaire (tenant dérivé via `get_current_user().get_employer_id()`), de profil chiffré approuvé, sauvegarde vérifiée/restore, replay idempotent ou déploiement. L'identité fictive en mémoire n'est ni un utilisateur réel ni une approbation. UI staff et PWA mobile pas testées, aucun contrôle visuel du parcours utilisateur.

**Succès attendu** = CI exact SHA des 10 cas de modèle réel et 109 régressions (119 tests exécutés) + deux revues adversariales internes réellement distinctes et confirmation. Ce succès ne vaut **jamais GO de LOT05/05.3 clinique**. Le score est limité par les gates manquants : aucune revendication 9/10 sans vrai Schéma physique/Alembic + authentication/tenant + sauvegarde/restore et revue indépendante.

NEXT : proposer un **service runtime sûr en lecture-seule**, lié à propriétaire auth et version Alembic réellement installée, sur lot séparé, puis test de migrations de bases synthétiques PostgreSQL/SQLite complètes. La faille de contrainte inter-cabinets doit être traitée **avant tout import** par politique applicative certifiée ou contrainte DB compatible avec l'architecture, et protégée par un test E2E.
