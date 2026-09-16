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

Le correctif candidat reste ciblé et additif :

1. la migration versionnée `d0b000000001` crée explicitement les quatre tables Companion, sans backfill ;
2. la migration versionnée `d0b000000002` ajoute les colonnes/index compatibles, les tables Agenda/catalogue et `A_ENCAISSER`, sans suppression ni réécriture des données patient/document existantes ;
3. la migration versionnée `d0b000000003` ajoute le schéma NGAP/linkage assurance sans réécriture des lignes historiques ;
4. l'upgrade Alembic est exécuté explicitement après backup et rehearsal, avant le service ;
5. le boot `cabinet`/`production` vérifie en lecture seule l'head Alembic et refuse un schéma obsolète ; il ne fait ni `create_all()`, ni migration implicite, ni seed admin ;
6. le boot dev/test conserve `create_all()` uniquement après attestation d'isolation explicite.

## Rehearsal représentatif déterministe

Le script canonique est :

`backend/scripts/cabinet_upgrade_rehearsal.py`

Contrat :

- la DB cabinet source est lue **uniquement par `pg_dump`** ;
- le même dump est restauré dans deux nouvelles DB `dc_rehearsal_*` ;
- `BEFORE` reste contrôle immuable ;
- `AFTER` seul reçoit `alembic upgrade head` puis le smoke backend ;
- toutes les tables/lignes/PK historiques sont fingerprintées ;
- les FK historiques doivent rester présentes avec le même nombre d'orphelins ;
- les nouvelles FK additives sont autorisées ;
- les médias source sont hashés avant/après copie ; toute mutation concurrente bloque le run ;
- tous les `DocumentArchive.file_path` historiques doivent résoudre vers un fichier existant avec SHA-256 cohérent quand `file_hash` est disponible ;
- le second `alembic upgrade head` doit être un no-op de schéma ;
- le boot rehearsal doit rendre `/api/health = 200` sans changer schéma, données historiques, relations ni médias ;
- en échec, les clones et le dossier de preuve sont conservés ;
- `--cleanup` ne peut supprimer que les DB créées par ce run et uniquement après PASS.

### Préconditions opérateur

- checkout exact de la branche/HEAD candidat ;
- PostgreSQL local joignable avec droit de créer deux DB temporaires ;
- `pg_dump` et `pg_restore` disponibles ;
- environnement Python complet du backend installé ;
- `DIGITALCROWN_REHEARSAL_SOURCE_DATABASE_URL` chargé depuis la configuration cabinet existante sans publier le secret dans les logs ;
- `MEDIA_ROOT` cabinet connu et accessible en lecture.

### Commande Windows / PowerShell

Première exécution : **ne pas utiliser `--cleanup`**, afin de conserver les preuves et clones pour inspection.

```powershell
python backend/scripts/cabinet_upgrade_rehearsal.py `
  --media-root "$env:APPDATA\DigitalCrown\media" `
  --work-dir "$env:TEMP\digitalcrown_rehearsal_final" `
  --confirm-source-dump-only
```

Le script lit l'URL source depuis `DIGITALCROWN_REHEARSAL_SOURCE_DATABASE_URL` si `--source-database-url` n'est pas fourni.

Verdict acceptable : `report.json` avec `"status": "PASS"`. Toute sortie `REHEARSAL BLOCKED` maintient le lot en NO-GO.

Le rapport ne contient pas les lignes patient ni le mot de passe DB ; il contient seulement identités de cibles masquées, compteurs/fingerprints, révision Alembic, preuves médias/archives et résultat health.

## Critères obligatoires du prochain rehearsal

Le candidat exact ne devient **GO** que si une nouvelle copie fraîche des données réelles prouve :

- mêmes tables/lignes/PK historiques BEFORE/AFTER ;
- mêmes patients BEFORE/AFTER ;
- mêmes documents DB BEFORE/AFTER ;
- mêmes liens patient-document ;
- mêmes fichiers et SHA-256 historiques ;
- mêmes actes/paiements historiques ;
- toutes les FK historiques conservées sans nouvelle rupture ;
- `appointments.praticien_id` créé, nullable, indexé, sans réécriture des rendez-vous historiques ;
- scheduler sans `UndefinedColumn` ;
- enum PostgreSQL comprenant `A_ENCAISSER` après migration Alembic explicite ;
- aucun seed admin ni génération/impression de mot de passe en mode cabinet ;
- boot rehearsal `/api/health = 200` sans mutation de données/médias/schéma ;
- CI exacte du même HEAD verte pour auth/tenant/PDF/documents et certifications ciblées applicables.

## Scoring du gate courant

- `EXECUTION_SCORE` interne du sous-lot rehearsal harness : **9.3/10** ;
- `ADVERSARIAL_SCORE` interne : **9.4/10** ;
- score retenu : **9.3/10** (minimum, jamais moyenne) ;
- écart : **0.1** ;
- cap même agent respecté ;
- score du lot global : **maximum 7.9/10 tant que le rehearsal représentatif frais et la CI exact-HEAD ne sont pas tous deux prouvés verts** ;
- statut global : `IN_PROGRESS`, jamais `VERIFIED` avant tous les gates binaires verts puis Perfection Pass finale.

## Gate de merge / installation

- CI verte : nécessaire, **non suffisante**.
- Tests unitaires : nécessaires, **non suffisants**.
- Rehearsal représentatif `PASS` : obligatoire.
- Aucun merge de ce correctif avant verdict `GO` sur une copie fraîche.
- Aucune installation ni aucun alignement du runtime réel avant ce même verdict.
- Toute activation réelle ultérieure exige encore backup DB + médias, compteurs BEFORE/AFTER et smoke patient/document connu.
- Le lot ne peut être `VERIFIED` qu'avec tous les gates binaires verts et un score retenu >= 9.0/10 selon `.claude/rules/material-step-scoring.md`.
