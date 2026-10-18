# Digital Crown — LOT05.7-E — vrai BackupService + SQLCipher, head Alembic, uniquement fictif

**Périmètre : 05.7-E exclusivement.** PR Draft empilée sur #966 (05.7-D), elle-même sur #965, #964 et #963. Aucune mutation du code applicatif, schéma Alembic existant, backend de production, endpoints d'import, frontend, service Windows ou application mobile. Aucune lecture ni copie d'une base Cabinet ou données patient réelles.

## Différence par rapport aux preuves 05.7-C et D

La suite `backend/tests/test_legacy_sql_057e_real_backupservice_sqlcipher_head.py` déclenche une **vraie commande opérateur `python -m alembic upgrade head`** sur un fichier SQLCipher neuf, chiffré et dans un `TemporaryDirectory` créé par la CI. Elle n'injecte pas un faux `alembic_version`, ne fait pas un simple `Base.metadata.create_all()` de substitution et exige la révision **`neo000000031`** via `backend.core.schema_runtime.assert_database_at_current_head`.

Les six familles de données utilisent de véritables classes ORM de ce HEAD et de **fausses identités seulement** : 2 propriétaires, 6 patients, 12 RDV, 4 actes, 4 paiements et 2 **métadonnées documentaires sans fichiers réels**. Aucune présence d'images cliniques, ZIP de documents patients, mots de passe utilisables ou secrets de Cabinet.

Contrairement à 05.7-C, le backup est créé par la **méthode publique réelle** `Backend.services.backup_service.BackupService.backup_active_database()`, qui doit router le moteur SQLCipher vers `_backup_sqlite_family`, exporter une copie SQLCipher cohérente via `sqlcipher_export`, puis l'envelopper par chiffrement Fernet. La restauration utilise la **méthode réelle** `BackupService.restore_backup(..., verify_sqlcipher=True)`, vers un autre fichier fictif inexistant. Le résultat est rouvert avec SQLCipher, vérifié au head Alembic et confronté à un hash logique des vraies tables ciblées, aux effectifs et aux montants. Linux et Windows Python 3.12 sont requis.

## Prévention de l'activation abusive

Le script refuse de s'exécuter si `LOT05E_REAL_SQLCIPHER_FAKE_ONLY=1` est absent, utilise une racine créée automatiquement portant `lot05e_fake_sqlcipher_*`, un nom de source fermé `fake_source.db` et des clés **générées pour le test uniquement**. Il injecte la variable `DATABASE_URL` de cette racine pour l'opérateur Alembic, `ENVIRONMENT=cabinet` pour exiger réellement SQLCipher, une clé SQLCipher aléatoire et un secret applicatif inutilisable. Toutes les destinations sont confinées dans la racine synthétique ; le script empêche de restaurer sur une cible existante. L'exécution ne reçoit aucun chemin clinique ni identifiant humain.

La suite couvre 12 cas : head SQLCipher + chiffrage disque, backup réel/restauration réelle, clé Fernet incorrecte, modification des octets du backup, mauvaise clé SQLCipher, **détection explicite et rollback d'un lien RDV/patient entre cabinets**, restauration d'un snapshot antérieur à une mise à jour, présence des triggers d'audit append-only après restauration, backup manquant, refus de recouvrir une cible fictive, refus de source/chemin externe et export d'un WAL commité actif. Les tests adversariaux déclenchent des erreurs voulues ; seule l'issue de la suite `OK` et le SHA Git exact comptent.

## GATES et limites BLOQUANTES

**CI REQUIRED pour 05.7-E** : `.github/workflows/v15-05-7-e-real-backupservice-sqlcipher.yml`, Windows et Linux Python 3.12, 12/12 tests sans skip sur HEAD exact ; pas de faux vert si échec d'installation SQLCipher ou d'Alembic. Le gate `CI Scope` surveille le périmètre ; biométrie M6-I EXPERIMENTAL/hors scope, UI Human ne remplace pas une vérification BEFORE/AFTER et ici aucun écran n'est modifié.

**IMPORTANT : le contrôle d'isolation `assert_no_cross_tenant_appointments` est exclusivement dans la suite de tests, NON branché au runtime.** Une liaison inter-tenant peut rester possible avec les FKs actuelles ; aucun GO d'import sans contrôle effectif, authentifié, indépendant et fail-closed. De même, `BackupService.restore_backup` sait remplacer une destination existante ; l'interdiction de remplacement vient ici du **test**, et ne rend PAS la méthode applicative sûre pour une restauration clinique. Ni les ACL NTFS, ni les jonctions/reparse/symlinks, ni les crashes matériels/écriture durable, ni l'authentification humaine, ni le stockage des clés, ni la restauration des octets médias, ni les RPO/RTO et réconciliations médicales/financières vraies ne sont certifiés.

**Statut initial : DRAFT / tests à confirmer**, sans import patient, sans merge, sans Vercel, sans activation de migrations cliniques. Le head SQLCipher réel ne peut être revendiqué avant journal prouvant l'exécution `alembic upgrade head`, le restore et deux perspectives adversariales internes propres sur un même commit. Voir `techdoubt.md`.
