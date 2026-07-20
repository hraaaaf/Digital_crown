# Digital Crown â€” Guide Codex

Logiciel de gestion de cabinet dentaire. **On-premise, pas un SaaS** : tourne
localement chez le cabinet (poste unique ou LAN cabinet), pas sur un serveur
distant. Firebase sert uniquement Ã  la licence/auth, jamais aux donnÃ©es
patients.

## Architecture

- **Backend** : FastAPI + SQLAlchemy â€” **PostgreSQL 15+ obligatoire pour production** (SQLite rÃ©servÃ© aux tests/dev)
- **Frontend** : React 19 + Vite 7 + TypeScript + Zustand, servi par le
  backend en mode packagÃ© (un seul port, pas de frontend sÃ©parÃ© en prod)
- **Mobile** : PWA appairÃ©e par QR (ZKA/ECDH), JWT mobile 365 jours, LAN
  cabinet uniquement
- **IA** : ONNX local (panoramique, cÃ©phalomÃ©trie) + moteurs locaux déterministes â€”
  aucune dépendance LLM cloud ou locale
- **Packaging** : PyInstaller â†’ `DigitalCrown.exe` (`console=False`, aucun
  terminal visible), puis `installer/DigitalCrown.iss` (Inno Setup) â†’
  `DigitalCrownSetup.exe`, installeur un clic pour cabinet solo (secrets
  auto-gÃ©nÃ©rÃ©s au 1er lancement, tÃ¢che planifiÃ©e au logon, pas de droits
  admin) â€” voir `docs/CABINET_ONPREM_GUIDE.md`

## Environnements (`ENVIRONMENT`)

`development` / `local` / `test` : aucun invariant bloquant.
`cabinet` : production-like (DEBUG interdit, CORS wildcard interdit) **mais
autorise SQLite/SQLCipher** (c'est le mode solo cabinet).
`production` : comme cabinet, **mais exige PostgreSQL** (refuse SQLite).
Logique dans `backend/main.py::validate_environment_invariants()`.

## PiÃ¨ges connus (chers Ã  re-dÃ©couvrir â€” lire avant de toucher)

- **`--reload` interdit sur le port 8005 (cabinet rÃ©el)** : un `uvicorn --reload` lancÃ© Ã  la
  main sur le port rÃ©el recharge automatiquement le process Ã  chaque Ã©dition de fichier Python
  dans le dÃ©pÃ´t â€” y compris pendant une session de dev sur une feature non terminÃ©e. Incident
  rÃ©el (P0-TREATMENT-JOURNEY-1, 2026-07-10) : des Ã©ditions de `backend/*.py` ont fait apparaÃ®tre
  une table + des routes non validÃ©es sur `digitalcrown_db` sans dÃ©ploiement explicite. Le
  cabinet rÃ©el doit **toujours** dÃ©marrer via `backend/scripts/run_real_backend.ps1` (jamais
  `uvicorn --reload` Ã  la main), qui lance une **release immuable** (`backend/scripts/create_release.ps1`,
  copiÃ©e hors du dÃ©pÃ´t dans `C:\Users\lenovo\DigitalCrown-Runtime\releases\<id>\`) â€” le dÃ©pÃ´t de
  travail n'est jamais le runtime de production. `npm run build` (frontend) refuse aussi
  d'Ã©craser `frontend/dist` tant que le port 8005 rÃ©pond (`frontend/scripts/build-guard.mjs`) ;
  utiliser `build:rehearsal` pour tout build de test.
- **`load_backend_env()`** (`backend/env_loader.py`) : `main.py` doit
  appeler `override=False` en premier (ne JAMAIS Ã©craser des vars dÃ©jÃ 
  injectÃ©es par l'OS/orchestrateur), puis `override=True` seulement si
  `ENVIRONMENT` rÃ©sout Ã  dev/local/test. Sinon un `.env.local` oubliÃ© dans
  un dÃ©ploiement Ã©crase silencieusement la config rÃ©elle.
- **PyInstaller** (`DigitalCrown.spec`) : `passlib` et `jose` rÃ©solvent
  leurs handlers/backends *par nom* au runtime â€” invisibles Ã  l'analyse
  statique. Sans `passlib.handlers.bcrypt` et `jose.backends.*` en
  `hiddenimports`, l'EXE crashe au boot (passlib) ou au premier login
  (jose). **Ne jamais embarquer `backend/.env`** dans l'EXE (secrets) â€” la
  config vient de `DIGITALCROWN_ENV_FILE` ou `%APPDATA%/DigitalCrown/.env`.
- **Alembic** existe (`alembic/versions/`) mais n'est **jamais invoquÃ©
  automatiquement**. Le schÃ©ma est gÃ©rÃ© par `create_all()` +
  `migrate_appointment_columns()` (les deux additifs, jamais de DROP) dans
  le lifespan de `main.py`. Ne pas supposer qu'une migration Alembic
  s'applique toute seule.
- **Isolation tenant** : toujours `current_user.get_employer_id()`, jamais
  un `employer_id` venant du client. `assert_patient_access(patient_id,
  current_user, db)` â€” attention Ã  l'ordre des paramÃ¨tres (un bug passÃ©
  avait `db` et `current_user` inversÃ©s, silencieux jusqu'au crash runtime).
- **MÃ©dias patients** : servis par des routes FastAPI authentifiÃ©es
  (`main.py::serve_panoramic/serve_radios/...`), jamais par un mount
  `StaticFiles` public. Ne jamais rÃ©introduire `/api/static/uploads` en
  accÃ¨s anonyme.
- **Licence Firebase hors-ligne** : `validate_license_with_expiry()`
  retourne `active=None` (pas `False`) quand Firebase est injoignable â€”
  l'appelant doit conserver l'Ã©tat local, pas le rÃ©voquer. `active=False`
  reste une vraie rÃ©vocation Firebase.
- **Backup automatique = routage par moteur actif, jamais un chemin codÃ© en dur**
  (AUTO-BACKUP-POSTGRES-ROUTING-FIX-1, 2026-07-10) : `backend/services/backup_service.py`
  ciblait auparavant en dur `clinical_vault.db` (fichier SQLite hÃ©ritÃ© de la V1
  prÃ©-PostgreSQL, aujourd'hui migrÃ© transparemment en SQLCipher par `database.py`),
  ouvert via `sqlite3.connect()` standard â€” qui ne sait pas lire du SQLCipher. RÃ©sultat :
  `digitalcrown_db` (PostgreSQL rÃ©el) n'a **jamais** Ã©tÃ© sauvegardÃ©e automatiquement,
  silencieusement, pendant plus d'un mois. Doctrine dÃ©sormais verrouillÃ©e : **PostgreSQL
  utilise exclusivement `pg_dump`** (jamais `sqlite3` sur une base PostgreSQL) ; le
  scheduler (`daily_scheduler.py`) route via `BackupService.backup_active_database()`,
  qui dÃ©tecte le moteur rÃ©ellement actif via `backend.database.engine.dialect.name`
  (le mÃªme pattern que `migrate_appointment_columns()`) â€” jamais une heuristique fichier.
  **SQLite/SQLCipher ne doit jamais Ãªtre ouvert avec `sqlite3` standard** : le driver
  `pysqlcipher` (`engine.driver`) est dÃ©tectÃ© explicitement et route vers un Ã©chec propre
  (`SKIPPED_UNSUPPORTED_ENGINE`, jamais prÃ©sentÃ© comme un succÃ¨s) â€” backlog sÃ©parÃ©
  `SQLCIPHER-AUTO-BACKUP-FIX-1` pour un vrai mÃ©canisme SQLCipher si un dÃ©ploiement
  solo-cabinet en a besoin un jour. **Une rÃ©ussite de chiffrement ne suffit pas** : le
  dump source et le restore doivent Ãªtre vÃ©rifiÃ©s (voir la validation rehearsal de cette
  mission dans `STATE.md`) avant de faire confiance Ã  un backup automatique.
- **`backend/scripts/backup_db.py` et `backup_media.py` sont importables comme
  librairies** (utilisÃ©s par `backup_service.py` et `scheduled_backup.py` en plus de
  leur usage CLI) : ne jamais rÃ©introduire un `load_backend_env(override=True)` ou un
  import de `settings` au niveau module dans ces fichiers â€” Ã§a Ã©craserait
  silencieusement la config rÃ©elle du process serveur qui les importe. Le chargement
  d'env et l'import de `settings` sont volontairement paresseux (dans
  `backup_db()`/`backup_media()`, ou sous `if __name__ == "__main__":`).
- **Backup planifiÃ© Windows = tÃ¢che indÃ©pendante, jamais un rafistolage du scheduler
  in-app** (SCHEDULED-TASK-BACKUP-REPLACE-1, 2026-07-11) : `DigitalCrown_DailyBackup_User`
  (l'ancienne tÃ¢che, `python backend\scripts\backup_db.py` sans `-m`, mauvais
  interprÃ©teur) n'a **jamais** produit un seul backup depuis sa crÃ©ation â€” ~5 semaines
  d'Ã©chec silencieux. RemplacÃ©e par `DigitalCrown_DailyBackup_v2`, qui appelle
  `C:\Users\lenovo\DigitalCrown-Runtime\bin\run_scheduled_backup.ps1` â†’
  `python -m backend.scripts.scheduled_backup` (orchestrateur DB+mÃ©dias, rÃ©utilise
  `BackupService._backup_postgres()` et `backup_media._build_media_archive()`, jamais
  une 3e/4e implÃ©mentation de pg_dump ou du chiffrement). **Doctrine verrouillÃ©e** :
  cette tÃ¢che exÃ©cute toujours son propre backup DB+mÃ©dias indÃ©pendant du scheduler
  in-app â€” un backup DB seul (ce que produit le scheduler in-app) n'est jamais
  considÃ©rÃ© comme un backup complet, donc aucune logique de saut/coordination entre les
  deux n'est nÃ©cessaire ; seul un verrou fichier (`scheduled\.backup.lock`, dÃ©tection de
  pÃ©remption par PID+Ã¢ge) protÃ¨ge contre deux exÃ©cutions de la tÃ¢che Windows elle-mÃªme
  qui se chevauchent. RÃ©pertoires dÃ©diÃ©s
  (`DigitalCrown-Runtime\backups\scheduled\{db,media,manifests,logs}\`) â€” **jamais**
  mÃ©langÃ©s avec les backups manuels (`backend/backups/`, aucune rÃ©tention) ni ceux du
  scheduler in-app (`%APPDATA%\DigitalCrown\backups\`). RÃ©tention configurable
  (`SCHEDULED_DB_RETENTION_DAYS`, `SCHEDULED_MEDIA_RETENTION_DAYS`,
  `SCHEDULED_MIN_BACKUPS_TO_KEEP`) mais **toujours dry-run par dÃ©faut** â€” seul
  `--apply-retention` (prÃ©sent dans la commande de `DigitalCrown_DailyBackup_v2`) la
  rend rÃ©elle, et jamais en dessous du plancher `MIN_BACKUPS_TO_KEEP`.
- **Backup planifiÃ© = release immuable dÃ©diÃ©e, jamais exÃ©cutÃ© depuis le dÃ©pÃ´t**
  (SCHEDULED-BACKUP-RELEASE-EXECUTION-FIX-1, 2026-07-11) : la premiÃ¨re version de
  `run_scheduled_backup.ps1` (ci-dessus) faisait `Push-Location $RepoRoot` avant
  d'invoquer `-m backend.scripts.scheduled_backup` â€” le code exÃ©cutÃ© venait donc
  entiÃ¨rement du dÃ©pÃ´t de travail mutable, jamais d'une release, contrairement Ã 
  `run_real_backend.ps1`. CorrigÃ© : `backend/scripts/create_backup_release.ps1`
  construit une release dÃ©diÃ©e (`DigitalCrown-Runtime\backup-releases\<id>\`) via
  `git archive` sur un commit exact (**jamais** une copie du dÃ©pÃ´t courant, mÃªme
  propre) ; `DigitalCrown-Runtime\backup-current.json` est le pointeur atomique vers
  la release active ; `run_scheduled_backup.ps1` (dÃ©sormais **versionnÃ©** dans
  `backend/scripts/`, dÃ©ployÃ©/copiÃ© vers `DigitalCrown-Runtime\bin\` avec vÃ©rification
  de checksum) lit ce pointeur, revalide les hashes SHA-256 des 5 fichiers critiques
  contre le manifeste (`backup-release-manifest.json`), puis `Push-Location` vers la
  release â€” jamais `$RepoRoot`. **Seconde ligne de dÃ©fense cÃ´tÃ© Python** :
  `scheduled_backup.py::_check_execution_provenance()` s'exÃ©cute en tout premier dans
  `run()`, avant mÃªme le verrou â€” si `__file__` d'un des 5 modules critiques
  (`scheduled_backup`, `backup_service`, `backup_db`, `backup_media`, `database`)
  rÃ©sout sous le dÃ©pÃ´t de travail plutÃ´t qu'une release, le backup est refusÃ©
  (`overall_status=FAILED`, `error_code=EXECUTION_PROVENANCE_VIOLATION`), aucune
  tentative de pg_dump. `sys.executable` (le venv du dÃ©pÃ´t) reste une exception
  explicite â€” seul le **code** ne doit jamais venir du dÃ©pÃ´t, pas l'interprÃ©teur.
  **DÃ©pendance rÃ©siduelle documentÃ©e** : l'interprÃ©teur Ã©pinglÃ© reste celui du venv du
  dÃ©pÃ´t de travail (`...\DigitalCrown\venv\Scripts\python.exe`) â€” aucun Python
  n'existe encore de faÃ§on indÃ©pendante dans `DigitalCrown-Runtime` ; backlog sÃ©parÃ©
  `RUNTIME-PYTHON-INDEPENDENCE-1` si une vraie indÃ©pendance est requise un jour.
- **VÃ©rifier en live, pas juste en unitaire** : plusieurs bugs bloquants
  (RVG cassÃ©, `NoneType.strftime` sur gÃ©nÃ©ration PDF) passaient les tests
  unitaires (mocks/objets en mÃ©moire) mais crashaient sur le vrai chemin
  API. AprÃ¨s une modif sur `backend/routers/*.py` ou
  `backend/services/generators/*.py`, booter et taper l'API rÃ©ellement
  avant de dÃ©clarer "terminÃ©".
- **`backend/ai_models/` contient des dÃ©pÃ´ts de recherche vendored, pas
  seulement des poids** (INSTALL-AUTOMATION-1, 2026-07-14) : plusieurs
  sous-dossiers (`CLdetection2023-master/`, `dentex_repo/`,
  `CL-Detection2023/`, `cephalometric-master/`, `cephmark/`,
  `cephld_cca/model/`) sont des vestiges de compÃ©titions/entraÃ®nement
  (~1,7 Go) **jamais chargÃ©s au runtime** â€” vÃ©rifiÃ© au cas par cas (grep sur
  `backend/services`/`backend/routers`, comparaison taille/date avec les
  vrais poids chargÃ©s). `CLdetection2023-master/` a une arborescence assez
  profonde pour faire Ã©chouer la compilation Inno Setup (limite de longueur
  de chemin Windows). `DigitalCrown.spec` les exclut du packaging EXE via
  `_collect_ai_models_datas()` (jamais supprimÃ©s du dÃ©pÃ´t Git). **Avant
  d'ajouter un nouveau modÃ¨le dans `ai_models/`, ne pas vendorer tout un
  dÃ©pÃ´t de recherche si seul un fichier de poids est nÃ©cessaire** â€” sinon la
  taille du build explose silencieusement (4,9 Go avant nettoyage, 3,2 Go
  aprÃ¨s) et un futur nettoyage devra refaire cette vÃ©rification.
- **PyInstaller `console=False` = plus de stdout du tout** : `run.py`
  configure un `RotatingFileHandler` (`%APPDATA%/DigitalCrown/logs/`) et un
  `sys.excepthook` avant d'importer `backend.main`, sinon toute exception
  non interceptÃ©e en mode packagÃ© disparaÃ®t silencieusement (l'app se ferme
  sans aucune trace, impossible Ã  diagnostiquer sans terminal). Ne jamais
  retirer cette config si `console=False` reste actif dans `DigitalCrown.spec`.
- **`run.py::_first_boot_bootstrap()` doit s'exÃ©cuter avant `from backend.main
  import app`** : `backend/main.py` appelle `load_backend_env()` dÃ¨s son
  import (niveau module), qui lit `%APPDATA%/DigitalCrown/.env` s'il existe
  dÃ©jÃ . Le bootstrap gÃ©nÃ¨re ce fichier (secrets alÃ©atoires, `ENVIRONMENT=cabinet`)
  au tout premier lancement de l'EXE packagÃ© â€” s'il s'exÃ©cutait aprÃ¨s cet
  import, il serait trop tard pour que `load_backend_env()` le voie. N'importe
  volontairement que `backend.env_loader`/`backend.core.paths` (jamais
  `backend.config`/`backend.database`) pour ne jamais dÃ©clencher la lecture
  des settings avant que le fichier n'existe. No-op complet hors `sys.frozen`
  (aucun changement pour les postes de dev).
- **Exporter `DATABASE_URL` dans le shell NE SUFFIT PAS Ã  isoler un test d'une
  DB rÃ©elle** (QR-LOGO-POSITION-ENV-LEAK-1, 2026-07-15) : `load_backend_env()`
  fait un premier passage `override=False` (n'Ã©crase rien), puis un second
  passage `override=True` dÃ¨s que `ENVIRONMENT` rÃ©sout Ã 
  `development`/`local`/`test` â€” ce second passage recharge `backend/.env.local`
  et **Ã©crase silencieusement** toute variable dÃ©jÃ  exportÃ©e manuellement dans
  le shell, y compris `DATABASE_URL`. Un test lancÃ© avec `DATABASE_URL=<db_test>
  uvicorn ...` peut donc quand mÃªme finir connectÃ© Ã  `digitalcrown_db` (la vraie
  base du cabinet) si `backend/.env.local` pointe dessus. Incident rÃ©el : un
  smoke-test PDF isolÃ© a fini par exÃ©cuter une migration additive (colonnes
  nullable, `ALTER TABLE ADD COLUMN`, aucune perte de donnÃ©e) directement sur
  `digitalcrown_db`, en dehors de tout dÃ©ploiement officiel â€” mÃªme famille que
  P0-TREATMENT-JOURNEY-1. **Pour tout test qui doit toucher une DB isolÃ©e,
  utiliser `DIGITALCROWN_ENV_FILE` pointant vers un fichier `.env` dÃ©diÃ©**
  (jamais de simples variables shell), et vÃ©rifier explicitement aprÃ¨s coup
  (`load_backend_env()` doit rapporter le bon fichier, `DATABASE_URL` doit
  rester celui attendu) avant de lancer quoi que ce soit qui Ã©crit.

## Documents PDF (`backend/services/generators/`)

14 gÃ©nÃ©rateurs (ordonnance, certificat, devis, note d'honoraires, bilan
ortho, cÃ©phalo, panoramique...). Utiliser le registre typographique
existant plutÃ´t que des tailles ad-hoc :
- `document_typography.py` â€” constantes de taille (`TITLE_SIZE`,
  `PRESCRIPTION_*`, `MIN_READABLE_SIZE`, largeurs de colonnes)
- `document_layout_safety.py` â€” `join_unbreakable()` (groupe insÃ©cable,
  ex. "33 ans"), `protect_unit_patterns()` (protÃ¨ge nombre+unitÃ© dans du
  texte libre)
- `base_template.py` â€” `get_adaptive_font_size()`, `get_document_margins()`
  : ne jamais dupliquer, toujours rÃ©utiliser/Ã©tendre

`ordonnance_elite.html` est du **code mort** (aucune rÃ©fÃ©rence Python) â€”
le vrai gÃ©nÃ©rateur d'ordonnance est `ordonnance_gen.py` (ReportLab).

## Tests

- Backend : `pytest backend/tests/` â€” ~2200+ tests, **9-15 minutes** (lancer
  en background). Fixtures rÃ©elles dans `conftest.py` : `db`, `dentiste`,
  `auth_headers`, `client`, helper `make_user()`. Ne pas halluciner
  `current_user`/`db_session`/`other_employer` â€” n'existent pas.
- Frontend : `npm test` et `npm run build` depuis la racine
  (delegation vers `frontend`), ou directement
  `npm --prefix frontend test` et `npm --prefix frontend run build`
- CI (`ci.yml`) : backend uniquement (`pytest` + `prod_safety_check.py`) â€”
  **pas de job frontend actuellement**.

## DÃ©ploiement / opÃ©rations

- `docs/CABINET_ONPREM_GUIDE.md` â€” architecture cible, installation,
  update, backup/restore cabinet
- `docs/PREPROD_RUNBOOK.md` â€” health checks, logs, rollback
- `docs/PATIENT_DATA_ROLLBACK.md` â€” procÃ©dure d'urgence courte
- Scripts : `backend/scripts/backup_db.py`, `backup_media.py`,
  `restore_db.py` (chiffrÃ©s Fernet, `find_pg_binary()` gÃ¨re `pg_dump`/`psql`
  hors PATH Windows)

## RÃ¨gles absolues

- Ne jamais perdre de vraie donnÃ©e patient : toujours backup avant
  restore/migration, jamais de restore sur la DB principale sans
  confirmation explicite, jamais de `seed_demo` sur une vraie DB cabinet
- Ne jamais logger secrets/tokens/mots de passe/`CABINET_MASTER_KEY_HEX`
- Contexte7 MCP pour toute question de doc de librairie (rÃ¨gle globale
  utilisateur, prioritaire sur la recherche web)
