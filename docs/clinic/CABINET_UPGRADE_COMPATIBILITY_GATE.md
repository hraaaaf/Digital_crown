# Digital Crown — Cabinet upgrade compatibility gate

## Statut

**NO-GO cabinet tant qu'un rehearsal frais sur copie de la DB et des médias réels n'a pas validé le candidat exact.**

Ce gate a été ouvert après un audit Codex read-only du runtime cabinet réel suivi d'un upgrade rehearsal sur copie isolée. Aucune donnée réelle, configuration réelle ni release réelle n'a été modifiée pendant cet audit.

## Runtime cabinet audité

- Runtime configuré : release immuable `aaa28ef97b22df2c5654c4e0da7efc15692787a8`.
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

Ces anomalies ne doivent pas être "corrigées" implicitement par un upgrade.

## Preuve de préservation déjà acquise

Sur une copie PostgreSQL + médias isolée, le candidat P2 a conservé strictement :

- 293/293 patients et le même ensemble d'IDs ;
- 395/395 `DocumentArchive` et les mêmes liens `patient_id` ;
- 2 642 fichiers média / 353 518 486 octets ;
- les SHA-256 des 395 fichiers historiques référencés ;
- 281 actes et 212 paiements.

Attribuer puis retirer un praticien référent sur la copie n'a modifié ni les lignes Patient ni les `DocumentArchive` historiques.

## NO-GO découvert par le rehearsal

### 1. `appointments.praticien_id` absent au runtime

La migration Alembic `d3a55e700003` crée la colonne, la FK et l'index, mais le runtime cabinet historique ne lance pas automatiquement Alembic au démarrage. `create_all()` ne modifie pas une table existante.

Conséquence observée : erreurs PostgreSQL `UndefinedColumn` dans le scheduler.

### 2. Enum PostgreSQL `A_ENCAISSER` absent

Le modèle Python `PaiementStatut` et l'endpoint Finances utilisent `A_ENCAISSER`, alors que l'enum PostgreSQL réel ne contenait que `EN_ATTENTE`, `PAYE`, `PARTIEL`.

Conséquence observée : endpoint Finances HTTP 500.

### 3. Seed admin automatique inadapté au cabinet

Le démarrage appelait `seed_admin_user()` inconditionnellement. En absence de `SUPERADMIN_INITIAL_PASSWORD`, ce chemin pouvait générer un mot de passe automatique et l'imprimer.

Un cabinet/production ne doit jamais créer automatiquement un compte privilégié au boot.

## Stratégie de correction

Le correctif candidat doit rester ciblé et additif :

1. compléter la self-migration réellement exécutée afin d'ajouter `appointments.praticien_id` nullable + index sans backfill ;
2. sur PostgreSQL, découvrir le type enum réellement attaché à `actes.statut_paiement` et ajouter uniquement la valeur `A_ENCAISSER` si elle manque ;
3. interdire `seed_admin_user()` en `cabinet` et `production` avant toute ouverture de session DB ou génération de secret ;
4. conserver séparément les seeds de données système/référentielles idempotentes ;
5. ne pas lancer automatiquement toute la chaîne Alembic sur le cabinet historique uniquement pour résoudre ces divergences ciblées.

## Critères obligatoires du prochain rehearsal

Le candidat exact ne devient **GO** que si une nouvelle copie fraîche des données réelles prouve :

- mêmes patients BEFORE/AFTER ;
- mêmes documents DB BEFORE/AFTER ;
- mêmes liens patient-document ;
- mêmes fichiers et SHA-256 historiques ;
- mêmes actes/paiements historiques ;
- `appointments.praticien_id` créé, nullable, indexé, sans réécriture des rendez-vous historiques ;
- scheduler sans `UndefinedColumn` ;
- enum PostgreSQL comprenant `A_ENCAISSER` après self-migration additive ;
- endpoint Finances HTTP 200 ;
- aucun seed admin ni génération/impression de mot de passe en mode cabinet ;
- attribution/désattribution praticien sans mutation Patient/DocumentArchive.

## Gate de merge / installation

- CI verte : nécessaire, **non suffisante**.
- Tests unitaires : nécessaires, **non suffisants**.
- Aucun merge de ce correctif avant verdict Codex `GO` sur une copie fraîche.
- Aucune installation ni aucun alignement du runtime réel avant ce même verdict.
- Toute activation réelle ultérieure exige encore backup DB + médias, compteurs BEFORE/AFTER et smoke patient/document connu.
