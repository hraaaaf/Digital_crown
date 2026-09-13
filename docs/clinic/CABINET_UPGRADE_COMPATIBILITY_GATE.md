# Digital Crown — Cabinet upgrade compatibility gate

## Statut

**GO INSTALLATION certifié pour le candidat exact `b4f213b7095e3a93b2b4b155700dee7881ead23d` sur copie fraîche de la DB et des médias réels.**

Ce verdict remplace le NO-GO intermédiaire documenté pendant le rehearsal initial. Il ne vaut pas autorisation permanente pour n'importe quelle future release : toute activation réelle ultérieure conserve l'exigence backup DB + médias, compteurs BEFORE/AFTER et smoke patient/document connu.

Aucune donnée réelle, configuration réelle ni release réelle n'a été modifiée pendant les audits/rehearsals de certification ; les manipulations ont été exécutées sur copie isolée.

## Runtime cabinet audité

- Runtime configuré au début de l'audit : release immuable `aaa28ef97b22df2c5654c4e0da7efc15692787a8`.
- Environnement : `cabinet`.
- Base réelle : PostgreSQL 18.2, base locale `digitalcrown_db`.
- User-data root : `%APPDATA%/DigitalCrown`.
- Médias : `%APPDATA%/DigitalCrown/media`.

## Inventaire réel BEFORE

Sans publier de données médicales ni d'identité patient :

- Patients : 293 total, 290 actifs, 3 soft-deleted.
- Documents archivés : 395 total.
- Orphelins document → patient : 0.
- Chemins document NULL/vides : 0.
- Fichiers référencés physiquement absents : 0.
- Écarts taille DB/fichier : 0.
- Écarts SHA-256 DB/fichier : 0.
- Actes : 281.
- Paiements : 212.

Anomalies historiques indépendantes de l'upgrade :

- 31 patients sans `numero_dossier` ;
- 2 documents `ACTIF` avec `deleted_at` renseigné ;
- 2 247 fichiers média présents physiquement mais non référencés par `document_archives`.

Ces anomalies n'ont pas été corrigées implicitement par l'upgrade.

## Preuve de préservation acquise avant correction runtime

Sur une copie PostgreSQL + médias isolée, le candidat P2 avait déjà conservé strictement :

- 293/293 patients et le même ensemble d'IDs ;
- 395/395 `DocumentArchive` et les mêmes liens `patient_id` ;
- 2 642 fichiers média / 353 518 486 octets ;
- les SHA-256 des 395 fichiers historiques référencés ;
- 281 actes et 212 paiements.

Attribuer puis retirer un praticien référent sur la copie n'avait modifié ni les lignes Patient ni les `DocumentArchive` historiques.

## NO-GO intermédiaire découvert par le premier rehearsal

### 1. `appointments.praticien_id` absent au runtime

La migration Alembic `d3a55e700003` créait la colonne, la FK et l'index, mais le runtime cabinet historique ne lançait pas automatiquement Alembic au démarrage. `create_all()` ne modifie pas une table existante.

Conséquence observée : erreurs PostgreSQL `UndefinedColumn` dans le scheduler.

### 2. Enum PostgreSQL `A_ENCAISSER` absent

Le modèle Python `PaiementStatut` et l'endpoint Finances utilisaient `A_ENCAISSER`, alors que l'enum PostgreSQL réel ne contenait que `EN_ATTENTE`, `PAYE`, `PARTIEL`.

Conséquence observée : endpoint Finances HTTP 500.

### 3. Seed admin automatique inadapté au cabinet

Le démarrage appelait `seed_admin_user()` inconditionnellement. En absence de `SUPERADMIN_INITIAL_PASSWORD`, ce chemin pouvait générer un mot de passe automatique et l'imprimer.

Un cabinet/production ne doit jamais créer automatiquement un compte privilégié au boot.

## Correctifs certifiés

Le candidat final reste ciblé et additif :

1. self-migration réellement exécutée ajoutant `appointments.praticien_id` nullable + index sans backfill ;
2. FK praticien vers `users(id)` avec `ON DELETE SET NULL` ;
3. sur PostgreSQL, découverte du type enum attaché à `actes.statut_paiement` et ajout de `A_ENCAISSER` uniquement s'il manque ;
4. `seed_admin_user()` interdit en `cabinet` et `production` avant toute ouverture de session DB ou génération de secret ;
5. seeds de données système/référentielles idempotentes conservés séparément ;
6. pas d'exécution forcée de toute la chaîne Alembic historique ;
7. aucun backfill Patient/Document ;
8. chemins DB/media inchangés.

## Preuves exact-head du candidat

Candidat certifié : `b4f213b7095e3a93b2b4b155700dee7881ead23d`.

- CI `34691089478` : success.
- T2 Runtime Browser `34691089498` : success.
- PostgreSQL 18 certification `34691089505` : success.
- PR #439 mergée avec garde SHA exacte.
- merge : `f7e652acdae5454303d82a07c03e98a267b4a976`.
- `master` post-merge vérifié sur ce merge, commit GitHub signé/valide.

## Rehearsal final sur copie fraîche de la vraie installation

Verdict : **GO INSTALLATION**.

Conservation BEFORE/AFTER :

- Patients : 293 → 293 ; mêmes IDs/champs critiques ; hash inchangé `8297e1086f27bc6ff527b35f1d6c69ed6e46ca01aed74791ba3ef5b079027e23`.
- Documents DB : 395 → 395 ; mêmes IDs/champs critiques ; hash inchangé `5db831ecc8e1e347b8a6bba330729791094e58f040923802e523ac634533b153`.
- Relations patient-document : hash inchangé `b545fe8bf4386364939eafabb501d7b74c13131e61d048c0715737dfe880d45f`.
- Médias : 2 642 fichiers / 353 518 486 octets avant/après ; hash arbre média inchangé `2564dbb1a7d6d0d507a401f7480307800725bea8a7f0510fd51db6d394e6cfd8`.
- Actes : 281 → 281.
- Paiements : 212 → 212.
- `appointments.praticien_id` disponible au runtime sans backfill historique imposé.
- Scheduler : aucune erreur `UndefinedColumn`, aucun `Daily scheduler failed`.
- enum PostgreSQL : `A_ENCAISSER` disponible après self-migration additive.
- Finances : HTTP 200.
- attribution/désattribution praticien : Patient et `DocumentArchive` inchangés.
- seed admin en `cabinet` : utilisateurs 12 → 12, admins 3 → 3, aucun mot de passe généré/imprimé.

L'anomalie des 2 247 médias physiques non référencés est restée hors périmètre et inchangée.

## Gate de future installation

Le GO ci-dessus certifie le candidat exact audité, pas une règle d'installation aveugle pour les releases futures.

Pour toute future installation cabinet :

- backup DB + médias ;
- copie/rehearsal lorsque la migration touche le stockage ou le schéma critique ;
- mêmes compteurs/hashes critiques BEFORE/AFTER ;
- smoke patient/document connu ;
- CI et tests nécessaires mais jamais substituts à la preuve de conservation lorsque le risque porte sur des données locales réelles.
