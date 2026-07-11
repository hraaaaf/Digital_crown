# Digital Crown — Guide d'installation cabinet (on-premise)

Digital Crown n'est **pas un SaaS distant** : l'application tourne localement
sur une machine du cabinet. Firebase sert uniquement à la licence/identité.
Les données patients, médias, DB et backups restent locaux.

Ce guide couvre : architecture cible, lancement, installation, mise à jour,
backup/restore, et le comportement licence hors-ligne.

---

## 1. Architecture cible cabinet

```
┌─────────────────────── Machine cabinet (Windows) ───────────────────────┐
│                                                                          │
│  DigitalCrown.exe (PyInstaller) ── uvicorn :8005                        │
│    ├── Backend FastAPI (API + génération PDF + IA locale ONNX)          │
│    ├── Frontend buildé servi par le backend (frontend/dist embarqué)    │
│    └── Ouvre le navigateur sur http://127.0.0.1:8005 au démarrage       │
│                                                                          │
│  Données (%APPDATA%/DigitalCrown/) :                                     │
│    ├── clinical_vault.db      SQLite chiffré SQLCipher (mode simple)     │
│    ├── media/                 radios, RVG, documents archivés            │
│    ├── backups/               sauvegardes chiffrées locales              │
│    ├── license_vault.bin      coffre licence hors-ligne (grace 72h)      │
│    └── backup.key                                                        │
│                                                                          │
│  OU (mode avancé) : PostgreSQL local via DATABASE_URL                    │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
         │                                    │
         │ LAN cabinet (PWA mobile,           │ Internet (uniquement)
         │ appairage QR, port 8005)           │ Firebase licence/auth
         ▼                                    ▼
   Téléphones assistante/dentiste        Firestore licenses/{public_id}
```

### ⚠️ Base de données — PostgreSQL obligatoire

**PostgreSQL 15+ est la seule base supportée pour toute installation cabinet/client.**

SQLite est réservé aux tests unitaires et au développement local — jamais pour production.

Chaque installation cabinet requiert :
- Installation PostgreSQL 15+ sur le poste principal ou un serveur local
- Une base de données dédiée au cabinet
- Un utilisateur PostgreSQL dédié (jamais le superuser `postgres`)

---

## 2. Mode de lancement

### ⚠️ Doctrine runtime réel (2026-07-10, suite incident P0-TREATMENT-JOURNEY-1)

Tant que le cabinet réel tourne depuis un checkout de dépôt (pas encore l'EXE packagé pour ce
poste) :
- **Jamais `uvicorn --reload` sur le port 8005.** Un `--reload` recharge le process à chaque
  édition de fichier Python dans le dépôt — y compris des fonctionnalités non terminées/non
  validées, sans déploiement explicite.
- **Démarrage uniquement via `backend/scripts/run_real_backend.ps1`**, qui exige une release
  immuable créée par `backend/scripts/create_release.ps1` (snapshot copié hors du dépôt dans
  `C:\Users\lenovo\DigitalCrown-Runtime\releases\<id>\`), une confirmation explicite
  (`-ConfirmRealActivation "YES"`), et refuse toute config ressemblant à du rehearsal.
- **`npm run build` (frontend) refuse d'écraser `frontend/dist`** tant que le port 8005 répond
  (`frontend/scripts/build-guard.mjs`) — utiliser `npm run build:rehearsal` pour tester sans
  risque, `npm run build:real` (garde-fou + confirmation) uniquement pour une activation
  délibérée après arrêt contrôlé du runtime réel.
- Toute activation réelle (nouvelle release en service) exige : backup DB + médias au préalable,
  compteurs avant/après, arrêt maîtrisé de l'ancien process, démarrage du nouveau sans `--reload`.

Une fois l'EXE packagé utilisé en production (section ci-dessous), ce risque disparaît
structurellement : l'EXE n'a pas de mode `--reload` et n'est jamais lancé depuis un dépôt éditable.

### Actuel (dev/démo) : `DigitalCrown.exe`
Le build PyInstaller (`DigitalCrown.spec` → `dist/DigitalCrown/DigitalCrown.exe`)
lance uvicorn sur `127.0.0.1:8005` et ouvre le navigateur.

### ⚠️ Deux limites du build actuel à corriger avant un vrai pilote

1. **Bind `127.0.0.1` uniquement** (`run.py`) : la PWA mobile ne peut PAS
   joindre le backend depuis un téléphone du LAN. Pour l'usage cabinet réel
   (appairage QR mobile), le backend doit écouter sur `0.0.0.0` ou l'IP LAN.
   → changement d'une ligne dans `run.py` (`host="0.0.0.0"`), à faire au
   moment du packaging pilote, avec le pare-feu Windows configuré pour
   n'autoriser que le sous-réseau du cabinet.
2. **`backend/.env` embarqué dans l'EXE** (`DigitalCrown.spec`, ligne datas) :
   le fichier versionnable (placeholders) est empaqueté. S'assurer que le
   build n'embarque JAMAIS `backend/.env.local` (secrets réels) et que le
   `.env` embarqué ne contient que des placeholders — la config réelle du
   cabinet doit vivre dans `%APPDATA%` ou en variables d'environnement du
   service (cf. `DIGITALCROWN_ENV_FILE` supporté par `env_loader.py`).

### Recommandé pour le pilote : service Windows auto-start

Windows ne gère pas les services Python nativement — deux options éprouvées :

**Option A — NSSM (recommandée, la plus simple) :**
```powershell
# https://nssm.cc — wrapper service pour n'importe quel exe
nssm install DigitalCrown "C:\DigitalCrown\DigitalCrown.exe"
nssm set DigitalCrown AppDirectory "C:\DigitalCrown"
nssm set DigitalCrown AppStdout "C:\DigitalCrown\logs\service.log"
nssm set DigitalCrown AppStderr "C:\DigitalCrown\logs\service_err.log"
nssm set DigitalCrown Start SERVICE_AUTO_START
nssm start DigitalCrown
```

**Option B — Tâche planifiée au démarrage (zéro dépendance) :**
```powershell
schtasks /create /tn "DigitalCrown" /tr "C:\DigitalCrown\DigitalCrown.exe" ^
  /sc onstart /ru SYSTEM /rl HIGHEST
```

Logs locaux : rediriger stdout/stderr vers `C:\DigitalCrown\logs\` (NSSM le
fait nativement, avec rotation via `AppRotateFiles`).

Ports : backend+frontend = **8005** (un seul port, le backend sert le
frontend buildé). Pas de port frontend séparé en mode cabinet.

---

## 3. Variables d'environnement cabinet

Fichier recommandé : `%APPDATA%\DigitalCrown\.env` référencé via
`DIGITALCROWN_ENV_FILE`, ou variables du service NSSM (`nssm set
DigitalCrown AppEnvironmentExtra ...`).

| Variable | Valeur cabinet | Note |
|---|---|---|
| `ENVIRONMENT` | `production` | Active les invariants de démarrage fail-fast (SECRET_KEY fort, pas de wildcard CORS). NB : en `production`, `DATABASE_URL` SQLite est refusé par le garde — pour le mode SQLite cabinet, utiliser `ENVIRONMENT=cabinet` n'existe pas encore ; utiliser `development` + vérifs manuelles, OU PostgreSQL local. **Point à trancher avant le pilote.** |
| `SECRET_KEY` | généré (64 hex) | `python -c "import secrets;print(secrets.token_hex(32))"` — sert aussi aux JWT (pas de JWT_SECRET séparé dans ce codebase) |
| `DATABASE_URL` | absent (SQLite) ou `postgresql://...` local | |
| `CABINET_MASTER_KEY_HEX` | généré (64 hex) | Chiffre DB SQLCipher + backups |
| `ALLOWED_ORIGINS` | `http://localhost:8005,http://<IP_LAN>:8005` | Jamais `*` |
| `TELEMETRY_ENABLED` | `false` | Opt-in explicite uniquement |
| `CLOUD_AI_ENABLED` | `false` | IA locale (Ollama) par défaut |
| `SUPERADMIN_EMAIL` | email support Digital Crown | |
| Firebase (`GOOGLE_APPLICATION_CREDENTIALS` ou config service) | fournie à l'installation | Licence uniquement |

**Garantie importante (corrigée en `d6d217d`)** : en `ENVIRONMENT` autre que
dev/local/test, `backend/.env.local` n'écrase JAMAIS les variables déjà
définies par le service/OS — la config du service fait foi.

Médias et backups : chemins dérivés de `%APPDATA%` automatiquement
(`AppPaths.get_user_data_dir()`). Pour les isoler sur un autre disque,
redéfinir `APPDATA` dans l'environnement du service (technique validée en
rehearsal) — pas de variable `MEDIA_ROOT`/`BACKUP_DIR` dédiée à ce jour.

---

## 4. Procédure d'installation cabinet

**Prérequis machine :** Windows 10/11 Pro, 8 Go RAM min (16 recommandé — IA
ONNX locale), 50 Go disque libre, antivirus avec exclusion du dossier
d'installation, horloge synchronisée (anti-rollback licence).

1. **Copier le build** `dist/DigitalCrown/` vers `C:\DigitalCrown\`
2. **Configurer l'environnement** : créer le fichier env cabinet (section 3),
   générer `SECRET_KEY` et `CABINET_MASTER_KEY_HEX`, poser les credentials
   Firebase fournis
3. **DB** :
   - SQLite (défaut) : rien à faire — créée+chiffrée au premier démarrage
   - PostgreSQL : installer PG 15+, `CREATE DATABASE digitalcrown_cabinet;`,
     renseigner `DATABASE_URL`
4. **Installer le service** (NSSM, section 2) et démarrer
5. **Vérifier le démarrage** : `curl http://127.0.0.1:8005/api/health` →
   `{"status":"ok","database":"ok",...}` + `/api/health/db` + `/api/health/storage`
6. **Créer le cabinet réel** via le Setup Wizard de l'UI (PAS `seed_demo` —
   celui-ci est réservé aux démos commerciales)
7. **Activer la licence** : le `public_id` du cabinet créé doit exister dans
   Firestore `licenses/` avec `active=true` (dashboard SuperAdmin)
8. **Smoke tests post-install** (checklist §5 du PREPROD_RUNBOOK.md) :
   login, patient test, upload/lecture document, RVG, agenda, ordonnance PDF,
   accès anonyme → 401
9. **Appairage mobile** : générer le QR depuis Réglages → scanner depuis le
   téléphone (nécessite le bind LAN, cf. §2 limite 1)
10. **Programmer le backup quotidien** (section 6)

---

## 5. Procédure de mise à jour

1. **Backup complet AVANT toute mise à jour** :
   ```
   python -m backend.scripts.backup_db
   python -m backend.scripts.backup_media
   ```
2. Arrêter le service : `nssm stop DigitalCrown`
3. Renommer `C:\DigitalCrown\` → `C:\DigitalCrown_old\` (rollback instantané)
4. Copier le nouveau build vers `C:\DigitalCrown\`
5. Migrations : automatiques au démarrage (`create_all()` additif +
   `migrate_appointment_columns()` idempotent) — aucune commande manuelle.
   Les migrations sont non-destructives (jamais de DROP).
6. Redémarrer : `nssm start DigitalCrown`
7. Vérifier `/api/health` (le champ `version` = hash git du build)
8. Smoke tests rapides (login + 1 document + 1 patient)
9. Si KO → rollback : stop service, restaurer `C:\DigitalCrown_old\`,
   restaurer le backup DB si des migrations ont modifié le schéma, restart

---

## 6. Backup / restore cabinet

### Backup quotidien automatique (tâche planifiée)

```powershell
schtasks /create /tn "DigitalCrown Backup" ^
  /tr "C:\DigitalCrown\python\python.exe -m backend.scripts.backup_db && C:\DigitalCrown\python\python.exe -m backend.scripts.backup_media" ^
  /sc daily /st 22:00
```

- `backup_db.py` : dump chiffré Fernet (clé dérivée de `CABINET_MASTER_KEY_HEX`)
  — supporte SQLite ET PostgreSQL, trouve `pg_dump` automatiquement sur
  Windows même hors PATH (fix `d6d217d`)
- `backup_media.py` : zip chiffré du dossier média complet
- **Copier les `.enc` sur un disque externe/USB chaque semaine** — un backup
  sur la même machine ne protège pas d'une panne disque
- La clé `CABINET_MASTER_KEY_HEX` doit être conservée HORS de la machine
  (coffre du cabinet) : sans elle, les backups sont indéchiffrables
- **Utiliser impérativement `-m backend.scripts.backup_db`** (module), jamais
  `python backend\scripts\backup_db.py` (script direct) — ce dernier échoue avec
  `ModuleNotFoundError: No module named 'backend'` (le script a besoin d'être
  importé comme package depuis la racine du dépôt, pas exécuté comme fichier
  isolé). **Constat réel (AUTO-BACKUP-POSTGRES-ROUTING-FIX-1, 2026-07-10)** : la
  tâche planifiée Windows réellement configurée sur ce cabinet
  (`DigitalCrown_DailyBackup_User`) utilise `python backend\scripts\backup_db.py`
  (sans `-m`, sans chemin venv explicite) et échoue silencieusement depuis un
  temps indéterminé (`LastTaskResult=1`, code d'erreur générique). Diagnostic
  read-only fait, correction non appliquée — backlog séparé
  `SCHEDULED-TASK-BACKUP-FIX-1` (corriger la commande de la tâche planifiée,
  utiliser le python du venv explicitement, vérifier `LastTaskResult=0` après).

### Scénario sinistre : machine cabinet HS → machine neuve

Testé en conditions simulées (PREPROD-OPS-HARDENING-1, restore validé sur DB
jetable avec correspondance exacte des données) :

1. Installer Digital Crown sur la machine neuve (section 4, étapes 1-4,
   **sans** créer de cabinet)
2. Restaurer l'env : reposer `SECRET_KEY` et surtout `CABINET_MASTER_KEY_HEX`
   d'origine (depuis le coffre du cabinet)
3. Restaurer la DB :
   ```
   python -m backend.scripts.restore_db <backup.sql.enc> --yes
   ```
   (SQLite : écrase le fichier ; PostgreSQL : psql vers la DB cible)
4. Restaurer les médias : déchiffrer le zip (procédure PREPROD_RUNBOOK.md §3)
   et extraire vers `%APPDATA%\DigitalCrown\media\`
5. Démarrer le service, vérifier `/api/health`
6. Vérifier : login, un dossier patient existant, une radio existante
   s'affiche, l'agenda contient les RDV

---

## 7. Licence Firebase hors-ligne — analyse de risque

### Comportement AVANT cette mission (bug observé en rehearsal)

Le sync licence (`_sync_all_licenses_from_firebase`, exécuté au démarrage et
toutes les 6h) écrivait `is_licensed=False` en DB dès que Firebase était
injoignable — coupure internet du cabinet = cabinet verrouillé au prochain
redémarrage, alors même qu'un mécanisme de grace period 72h existait déjà
(`validate_license()` + coffre local anti-rollback) mais n'était utilisé que
par le recheck manuel.

### Comportement APRÈS (patch minimal appliqué dans cette mission)

`validate_license_with_expiry()` distingue désormais :
- **`active=None`** : Firebase injoignable/non configuré → le sync **conserve
  l'état local** (log warning, pas d'écriture)
- **`active=False`** : Firebase a répondu et dit révoquée/inexistante →
  fail-closed appliqué normalement
- **`active=True`** : licence confirmée, état + expiration mis à jour

### Ce qui reste couvert / non couvert

| Scénario | Comportement |
|---|---|
| Coupure internet, cabinet déjà licencié | ✅ continue de fonctionner (état conservé + expiry locale vérifiée par le gate de login) |
| Licence expirée localement (`license_expires_at` passé) | ✅ bloqué par le gate de login même hors-ligne |
| Révocation par l'admin, cabinet en ligne | ✅ appliquée au prochain sync (≤ 6h) |
| Révocation par l'admin, cabinet hors-ligne | ⚠️ non appliquée tant que le cabinet reste hors-ligne — inhérent au on-premise, borné par `license_expires_at` |
| Grace period progressive avec alertes UI (7-30 j) | ❌ non implémenté — la 72h du coffre local existe mais ne concerne que le chemin `validate_license` ; une vraie grace period configurable avec bannières d'alerte progressive reste à concevoir (mission dédiée recommandée avant commercialisation large, pas bloquant pour le pilote) |

---

## 8. Ce qui reste à faire avant le premier pilote (hors scope de cette mission)

1. **Bind LAN** dans `run.py` (1 ligne) + règle pare-feu — nécessaire pour la PWA mobile
2. **Trancher le mode `ENVIRONMENT`** pour cabinet SQLite (le garde prod
   refuse SQLite ; soit ajouter un mode `cabinet`, soit imposer PostgreSQL
   local, soit assouplir le garde pour SQLCipher)
3. **Rebuild PyInstaller** avec le code à jour (le `dist/` actuel date d'un
   commit antérieur) et vérifier qu'aucun secret réel n'est embarqué
4. **Script d'installation** (PowerShell) automatisant la section 4
5. **Grace period licence UI** (bannières progressives) — post-pilote
