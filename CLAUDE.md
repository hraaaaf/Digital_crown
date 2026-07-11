# Digital Crown — Guide Claude Code

Logiciel de gestion de cabinet dentaire. **On-premise, pas un SaaS** : tourne
localement chez le cabinet (poste unique ou LAN cabinet), pas sur un serveur
distant. Firebase sert uniquement à la licence/auth, jamais aux données
patients.

## Architecture

- **Backend** : FastAPI + SQLAlchemy — **PostgreSQL 15+ obligatoire pour production** (SQLite réservé aux tests/dev)
- **Frontend** : React 19 + Vite 7 + TypeScript + Zustand, servi par le
  backend en mode packagé (un seul port, pas de frontend séparé en prod)
- **Mobile** : PWA appairée par QR (ZKA/ECDH), JWT mobile 365 jours, LAN
  cabinet uniquement
- **IA** : ONNX local (panoramique, céphalométrie) + Ollama pour le LLM —
  aucune IA cloud par défaut (`CLOUD_AI_ENABLED=false`)
- **Packaging** : PyInstaller → `DigitalCrown.exe` (voir
  `docs/CABINET_ONPREM_GUIDE.md`)

## Environnements (`ENVIRONMENT`)

`development` / `local` / `test` : aucun invariant bloquant.
`cabinet` : production-like (DEBUG interdit, CORS wildcard interdit) **mais
autorise SQLite/SQLCipher** (c'est le mode solo cabinet).
`production` : comme cabinet, **mais exige PostgreSQL** (refuse SQLite).
Logique dans `backend/main.py::validate_environment_invariants()`.

## Pièges connus (chers à re-découvrir — lire avant de toucher)

- **`--reload` interdit sur le port 8005 (cabinet réel)** : un `uvicorn --reload` lancé à la
  main sur le port réel recharge automatiquement le process à chaque édition de fichier Python
  dans le dépôt — y compris pendant une session de dev sur une feature non terminée. Incident
  réel (P0-TREATMENT-JOURNEY-1, 2026-07-10) : des éditions de `backend/*.py` ont fait apparaître
  une table + des routes non validées sur `digitalcrown_db` sans déploiement explicite. Le
  cabinet réel doit **toujours** démarrer via `backend/scripts/run_real_backend.ps1` (jamais
  `uvicorn --reload` à la main), qui lance une **release immuable** (`backend/scripts/create_release.ps1`,
  copiée hors du dépôt dans `C:\Users\lenovo\DigitalCrown-Runtime\releases\<id>\`) — le dépôt de
  travail n'est jamais le runtime de production. `npm run build` (frontend) refuse aussi
  d'écraser `frontend/dist` tant que le port 8005 répond (`frontend/scripts/build-guard.mjs`) ;
  utiliser `build:rehearsal` pour tout build de test.
- **`load_backend_env()`** (`backend/env_loader.py`) : `main.py` doit
  appeler `override=False` en premier (ne JAMAIS écraser des vars déjà
  injectées par l'OS/orchestrateur), puis `override=True` seulement si
  `ENVIRONMENT` résout à dev/local/test. Sinon un `.env.local` oublié dans
  un déploiement écrase silencieusement la config réelle.
- **PyInstaller** (`DigitalCrown.spec`) : `passlib` et `jose` résolvent
  leurs handlers/backends *par nom* au runtime — invisibles à l'analyse
  statique. Sans `passlib.handlers.bcrypt` et `jose.backends.*` en
  `hiddenimports`, l'EXE crashe au boot (passlib) ou au premier login
  (jose). **Ne jamais embarquer `backend/.env`** dans l'EXE (secrets) — la
  config vient de `DIGITALCROWN_ENV_FILE` ou `%APPDATA%/DigitalCrown/.env`.
- **Alembic** existe (`alembic/versions/`) mais n'est **jamais invoqué
  automatiquement**. Le schéma est géré par `create_all()` +
  `migrate_appointment_columns()` (les deux additifs, jamais de DROP) dans
  le lifespan de `main.py`. Ne pas supposer qu'une migration Alembic
  s'applique toute seule.
- **Isolation tenant** : toujours `current_user.get_employer_id()`, jamais
  un `employer_id` venant du client. `assert_patient_access(patient_id,
  current_user, db)` — attention à l'ordre des paramètres (un bug passé
  avait `db` et `current_user` inversés, silencieux jusqu'au crash runtime).
- **Médias patients** : servis par des routes FastAPI authentifiées
  (`main.py::serve_panoramic/serve_radios/...`), jamais par un mount
  `StaticFiles` public. Ne jamais réintroduire `/api/static/uploads` en
  accès anonyme.
- **Licence Firebase hors-ligne** : `validate_license_with_expiry()`
  retourne `active=None` (pas `False`) quand Firebase est injoignable —
  l'appelant doit conserver l'état local, pas le révoquer. `active=False`
  reste une vraie révocation Firebase.
- **Backup automatique = routage par moteur actif, jamais un chemin codé en dur**
  (AUTO-BACKUP-POSTGRES-ROUTING-FIX-1, 2026-07-10) : `backend/services/backup_service.py`
  ciblait auparavant en dur `clinical_vault.db` (fichier SQLite hérité de la V1
  pré-PostgreSQL, aujourd'hui migré transparemment en SQLCipher par `database.py`),
  ouvert via `sqlite3.connect()` standard — qui ne sait pas lire du SQLCipher. Résultat :
  `digitalcrown_db` (PostgreSQL réel) n'a **jamais** été sauvegardée automatiquement,
  silencieusement, pendant plus d'un mois. Doctrine désormais verrouillée : **PostgreSQL
  utilise exclusivement `pg_dump`** (jamais `sqlite3` sur une base PostgreSQL) ; le
  scheduler (`daily_scheduler.py`) route via `BackupService.backup_active_database()`,
  qui détecte le moteur réellement actif via `backend.database.engine.dialect.name`
  (le même pattern que `migrate_appointment_columns()`) — jamais une heuristique fichier.
  **SQLite/SQLCipher ne doit jamais être ouvert avec `sqlite3` standard** : le driver
  `pysqlcipher` (`engine.driver`) est détecté explicitement et route vers un échec propre
  (`SKIPPED_UNSUPPORTED_ENGINE`, jamais présenté comme un succès) — backlog séparé
  `SQLCIPHER-AUTO-BACKUP-FIX-1` pour un vrai mécanisme SQLCipher si un déploiement
  solo-cabinet en a besoin un jour. **Une réussite de chiffrement ne suffit pas** : le
  dump source et le restore doivent être vérifiés (voir la validation rehearsal de cette
  mission dans `STATE.md`) avant de faire confiance à un backup automatique.
- **`backend/scripts/backup_db.py` et `backup_media.py` sont importables comme
  librairies** (utilisés par `backup_service.py` et `scheduled_backup.py` en plus de
  leur usage CLI) : ne jamais réintroduire un `load_backend_env(override=True)` ou un
  import de `settings` au niveau module dans ces fichiers — ça écraserait
  silencieusement la config réelle du process serveur qui les importe. Le chargement
  d'env et l'import de `settings` sont volontairement paresseux (dans
  `backup_db()`/`backup_media()`, ou sous `if __name__ == "__main__":`).
- **Backup planifié Windows = tâche indépendante, jamais un rafistolage du scheduler
  in-app** (SCHEDULED-TASK-BACKUP-REPLACE-1, 2026-07-11) : `DigitalCrown_DailyBackup_User`
  (l'ancienne tâche, `python backend\scripts\backup_db.py` sans `-m`, mauvais
  interpréteur) n'a **jamais** produit un seul backup depuis sa création — ~5 semaines
  d'échec silencieux. Remplacée par `DigitalCrown_DailyBackup_v2`, qui appelle
  `C:\Users\lenovo\DigitalCrown-Runtime\bin\run_scheduled_backup.ps1` (lanceur **hors
  dépôt**, résout la release immuable active, épingle l'interpréteur — jamais `python`
  du PATH) → `python -m backend.scripts.scheduled_backup` (orchestrateur DB+médias,
  réutilise `BackupService._backup_postgres()` et
  `backup_media._build_media_archive()`, jamais une 3e/4e implémentation de pg_dump ou
  du chiffrement). **Doctrine verrouillée** : cette tâche exécute toujours son propre
  backup DB+médias indépendant du scheduler in-app — un backup DB seul (ce que produit
  le scheduler in-app) n'est jamais considéré comme un backup complet, donc aucune
  logique de saut/coordination entre les deux n'est nécessaire ; seul un verrou fichier
  (`scheduled\.backup.lock`, détection de péremption par PID+âge) protège contre deux
  exécutions de la tâche Windows elle-même qui se chevauchent. Répertoires dédiés
  (`DigitalCrown-Runtime\backups\scheduled\{db,media,manifests,logs}\`) — **jamais**
  mélangés avec les backups manuels (`backend/backups/`, aucune rétention) ni ceux du
  scheduler in-app (`%APPDATA%\DigitalCrown\backups\`). Rétention configurable
  (`SCHEDULED_DB_RETENTION_DAYS`, `SCHEDULED_MEDIA_RETENTION_DAYS`,
  `SCHEDULED_MIN_BACKUPS_TO_KEEP`) mais **toujours dry-run par défaut** — seul
  `--apply-retention` (présent dans la commande de `DigitalCrown_DailyBackup_v2`) la
  rend réelle, et jamais en dessous du plancher `MIN_BACKUPS_TO_KEEP`. **Dépendance
  résiduelle documentée** : l'interpréteur épinglé reste celui du venv du dépôt de
  travail (`...\DigitalCrown\venv\Scripts\python.exe`) — aucun Python n'existe encore
  de façon indépendante dans `DigitalCrown-Runtime` ; backlog séparé
  `RUNTIME-PYTHON-INDEPENDENCE-1` si une vraie indépendance est requise un jour.
- **Vérifier en live, pas juste en unitaire** : plusieurs bugs bloquants
  (RVG cassé, `NoneType.strftime` sur génération PDF) passaient les tests
  unitaires (mocks/objets en mémoire) mais crashaient sur le vrai chemin
  API. Après une modif sur `backend/routers/*.py` ou
  `backend/services/generators/*.py`, booter et taper l'API réellement
  avant de déclarer "terminé".

## Documents PDF (`backend/services/generators/`)

14 générateurs (ordonnance, certificat, devis, note d'honoraires, bilan
ortho, céphalo, panoramique...). Utiliser le registre typographique
existant plutôt que des tailles ad-hoc :
- `document_typography.py` — constantes de taille (`TITLE_SIZE`,
  `PRESCRIPTION_*`, `MIN_READABLE_SIZE`, largeurs de colonnes)
- `document_layout_safety.py` — `join_unbreakable()` (groupe insécable,
  ex. "33 ans"), `protect_unit_patterns()` (protège nombre+unité dans du
  texte libre)
- `base_template.py` — `get_adaptive_font_size()`, `get_document_margins()`
  : ne jamais dupliquer, toujours réutiliser/étendre

`ordonnance_elite.html` est du **code mort** (aucune référence Python) —
le vrai générateur d'ordonnance est `ordonnance_gen.py` (ReportLab).

## Tests

- Backend : `pytest backend/tests/` — ~2200+ tests, **9-15 minutes** (lancer
  en background). Fixtures réelles dans `conftest.py` : `db`, `dentiste`,
  `auth_headers`, `client`, helper `make_user()`. Ne pas halluciner
  `current_user`/`db_session`/`other_employer` — n'existent pas.
- Frontend : `npm test` et `npm run build` depuis la racine
  (delegation vers `frontend`), ou directement
  `npm --prefix frontend test` et `npm --prefix frontend run build`
- CI (`ci.yml`) : backend uniquement (`pytest` + `prod_safety_check.py`) —
  **pas de job frontend actuellement**.

## Déploiement / opérations

- `docs/CABINET_ONPREM_GUIDE.md` — architecture cible, installation,
  update, backup/restore cabinet
- `docs/PREPROD_RUNBOOK.md` — health checks, logs, rollback
- `docs/PATIENT_DATA_ROLLBACK.md` — procédure d'urgence courte
- Scripts : `backend/scripts/backup_db.py`, `backup_media.py`,
  `restore_db.py` (chiffrés Fernet, `find_pg_binary()` gère `pg_dump`/`psql`
  hors PATH Windows)

## Règles absolues

- Ne jamais perdre de vraie donnée patient : toujours backup avant
  restore/migration, jamais de restore sur la DB principale sans
  confirmation explicite, jamais de `seed_demo` sur une vraie DB cabinet
- Ne jamais logger secrets/tokens/mots de passe/`CABINET_MASTER_KEY_HEX`
- Contexte7 MCP pour toute question de doc de librairie (règle globale
  utilisateur, prioritaire sur la recherche web)
