# FUE-G04 — Windows solo : préparation et activation séparées

Statut : préparation sur branche dédiée. Ce runbook ne constitue ni une certification
INSTALLABLE_CERTIFIED, ni une autorisation d'activation.

## Invariants

Un PC héberge backend, frontend et SQLCipher. L'assistante utilise uniquement le
compagnon mobile, avec son compte individuel. Les données historiques restent un
chantier séparé : aucun import, migration, rekey ou seed sur les originaux.

Une base SQLCipher qui refuse SQLite ordinaire n'est pas déclarée corrompue.

## Instance neuve

Racine proposée : `%USERPROFILE%\DigitalCrown-NewCabinet-20261010`.
La base doit être `data\clinical_vault.db`; configuration, runtime, logs et médias
restent dans cette même racine dédiée. Les sauvegardes et leur `backup.key` vivent
dans le nouveau répertoire de données.

Les cinq variables DIGITALCROWN_USER_DATA_DIR, DIGITALCROWN_CONFIG_DIR,
DIGITALCROWN_RUNTIME_DIR, DIGITALCROWN_LOG_DIR et DIGITALCROWN_ENV_FILE sont
explicites. Le fichier explicite manquant doit provoquer un refus, jamais un repli
sur l'ancien cabinet. DATABASE_URL doit résoudre exactement la nouvelle base.

Le premier démarrage et le provisionnement du propriétaire sont des opérations
explicites, distinctes du démarrage ordinaire. L'opérateur de provisionnement
utilise Alembic puis crée un propriétaire actif, sans licence artificielle, et
CabinetConfig. Aucun patient n'est créé par cet opérateur. Le poste est enrôlé
par le parcours authentifié existant ; un enregistrement SQL inventé ne remplace
pas une identité de poste ni son cookie.

Le marqueur de setup lie une reprise à l'instance. Une base contenant des données
ne peut jamais être adoptée comme cabinet neuf. Le verrou de setup empêche deux
provisionnements simultanés.

## Gate de release

Le workflow cabinet-release-certification exige le SHA exact du HEAD courant de
master. Une PR non fusionnée ne peut pas être certifiée par ce workflow.
Une fusion ne suffit pas : code, assets, hashes, attestations et preuves de
l'installable doivent ensuite réussir. Aucun EXE de remplacement ni démarrage
direct du dépôt ne contourne ce gate.

## Plan à soumettre avant activation réelle

1. Identifier l'artefact certifié, son SHA, son manifest, ses signatures et hashes.
2. Montrer l'AppId et les chemins programmes/config/data de cette instance ;
   vérifier les identités Windows existantes et l'absence de collision.
3. Présenter les commandes exactes d'installation et de setup, les écritures prévues
   et le rollback limité aux nouveaux fichiers programme. Ne jamais désinstaller
   l'ancien cabinet ni supprimer une tâche historique.
4. Présenter séparément la tâche d'autostart éventuelle, son utilisateur Windows,
   son action exacte et son nom propre à l'instance. Aucun remplacement automatique.
5. Présenter l'accès LAN HTTPS :8005, le nom/adresse couverts par le certificat,
   la chaîne de confiance et la règle de pare-feu proposée. Attendre le GO.
6. Après GO seulement, initialiser le cabinet, obtenir la licence conforme, vérifier
   Hub → Cabinet → Dashboard et enrôler le poste propriétaire.
7. Créer un compte assistante avec les permissions nécessaires uniquement, générer
   le QR pour ce compte, tester ECDH, expiration, consommation unique, accès refusés
   et révocation. Ne jamais publier le QR ou ses secrets.
8. Créer un patient fictif identifiable sur le banc autorisé, vérifier sauvegarde
   chiffrée et restauration sur clone. Le redémarrage Windows exige son propre GO.
9. Contrôler santé DB/storage, patient persistant, identité processus/poste et
   accès mobile après reboot. Tout contrôle non exécuté reste NON EXÉCUTÉ.

## TLS et mobile

La présence de fichiers TLS ne démontre ni SAN correct, ni confiance du téléphone,
ni connectivité LAN. Le téléphone doit valider HTTPS sans exception de certificat.
Une capture de QR seule ne prouve pas l'appairage. Aucun second serveur ou PC n'est
nécessaire ; la connectivité Wi-Fi locale reste nécessaire.

## Limites des tests

Les tests SQLCipher persistants utilisent exclusivement des données fictives et
des dossiers temporaires isolés. Un processus Python neuf démontre la persistance
inter-processus ; il ne constitue pas un test de reboot Windows. Une sauvegarde DB
ne démontre pas une sauvegarde exhaustive de tous les médias et documents.
