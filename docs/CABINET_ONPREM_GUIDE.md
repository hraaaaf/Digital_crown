# Digital Crown — Guide d'installation cabinet (on-premise)

Digital Crown n'est **pas un SaaS distant** : l'application tourne localement
sur une machine du cabinet. Firebase sert uniquement à la licence/identité.
Les données patients, médias, DB et backups restent locaux.

Ce guide couvre : architecture cible, lancement, installation, mise à jour,
backup/restore, et le comportement licence hors-ligne.

> **GATE 01.4 (2026-10-08)** : les commandes de service/build ci-dessous sont historiques, **pas une autorisation d'installation**. Seul `INSTALLABLE_CERTIFIED` est installable, après approbation humaine et isolation du banc. Exposition LAN cabinet/production : HTTPS :8005, certificat SAN/chaîne de confiance vérifiée sur A et B, pas de bypass. Références : `docs/CABINET_CERTIFIED_RELEASE_POLICY.md` et `docs/audits/V1_5_01_4_FUE_G_MULTIPC_PREFLIGHT_RUNBOOK.md`.

---

## 1. Architecture cible cabinet

```
┌─────────────────────── Machine cabinet (Windows) ───────────────────────┐
│                                                                          │
│  DigitalCrown.exe (PyInstaller) ── uvicorn :8005                        │
│    ├── Backend FastAPI (API + génération PDF + IA locale ONNX)          │
│    ├── Frontend buildé servi par le backend (frontend/dist embarqué)    │
│    └── Origine locale selon transport : HTTP loopback sans TLS, HTTPS avec TLS       │
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

### Base de données — règle actualisée

- Cabinet **solo** : `ENVIRONMENT=cabinet` prend en charge SQLite/SQLCipher chiffré.
- **Multi-PC FUE-G S+A+B** : PostgreSQL dédié sur banc d'essai isolé, rôle DB non-superuser, fixtures synthétiques.
- `ENVIRONMENT=production` : PostgreSQL obligatoire ; SQLite refusé.

Aucune migration, installation ni modification d'une base clinique ne découle de ce guide.

## 2. Mode de lancement

### ⚠️ Doctrine runtime réel (2026-07-10, suite incident P0-TREATMENT-JOURNEY-1)

Le démarrage direct d'un checkout sur cabinet réel est **interdit**. Le rappel historique ci-dessous concernait une situation antérieure où le cabinet tournait depuis un checkout (pas encore l'EXE packagé pour ce
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

### Installeur un clic (recommandé) : `installer/DigitalCrown.iss`

Depuis la mission d'automatisation d'installation (voir STATE.md), il existe
un installeur Windows complet qui remplace toute la procédure manuelle
ci-dessous pour un cabinet solo : `DigitalCrownSetup.exe` (compilé via
Inno Setup à partir de `installer/DigitalCrown.iss`). Il fait tout, sans
terminal visible et sans droits admin :
- Installe par utilisateur courant (`%LOCALAPPDATA%\Programs\DigitalCrown`)
- `run.py::_first_boot_bootstrap()` génère `%APPDATA%/DigitalCrown/.env` au
  tout premier lancement (`ENVIRONMENT=cabinet`, `SECRET_KEY`,
  `PAIRING_CODE_PEPPER`, `CABINET_MASTER_KEY_HEX`, `ALLOWED_ORIGINS` loopback et `CABINET_HOST=127.0.0.1`) —
  aucun secret à générer/coller à la main
- Enregistre une tâche planifiée au logon (pas de service SYSTEM)
- Lance l'app et ouvre le navigateur automatiquement en fin d'installation
- Désinstalleur qui ne touche jamais `%APPDATA%/DigitalCrown/` (données patients)

Pour compiler : `ISCC.exe installer\DigitalCrown.iss` (Inno Setup 6). Le
script committé utilise `Compression=zip` (rapide à compiler) — repasser en
`Compression=lzma2` + `SolidCompression=yes` pour une distribution finale
plus compacte si le temps de compilation n'est pas contraint.

**Ne jamais exécuter le `.exe` résultant sur une machine où un vrai cabinet
tourne déjà** (crée une vraie tâche planifiée + un vrai processus) — toujours
tester sur une VM/poste isolé.

Cet installeur couvre le cas solo (SQLite/SQLCipher, `ENVIRONMENT=cabinet`).
Pour un cabinet multi-postes (PostgreSQL, plusieurs machines), suivre la
procédure manuelle ci-dessous.

### Build manuel : `DigitalCrown.exe`
Le build PyInstaller (`DigitalCrown.spec` → `dist/DigitalCrown/DigitalCrown.exe`)
lance uvicorn et ouvre le navigateur. `console=False` (aucune fenêtre
terminal visible) — les logs vont dans `%APPDATA%/DigitalCrown/logs/`.

### État des anciennes limites (corrigées)

1. **Bind LAN** : fail-closed — le premier boot reste sur `127.0.0.1`. Un bind
   LAN doit être demandé explicitement via `CABINET_HOST` et, en mode
   `cabinet`/`production`, exige HTTPS avec certificat + clé TLS valides. La
   PWA mobile/appairage QR consomme le même contrat réseau canonique.
2. **`backend/.env` embarqué dans l'EXE** : ✅ non applicable — l'EXE
   n'embarque plus aucun `.env` du tout (`DigitalCrown.spec`, section
   `datas`) ; la config réelle vit exclusivement dans `%APPDATA%`, générée
   automatiquement au premier lancement (voir installeur ci-dessus) ou posée
   manuellement via `DIGITALCROWN_ENV_FILE` (`env_loader.py`).
3. **Taille du build** : `backend/ai_models/` contenait 4,9 Go, dont ~1,7 Go
   de dépôts de recherche/checkpoints d'entraînement jamais chargés au
   runtime (vérifiés un par un, voir commentaire en tête de
   `DigitalCrown.spec`) — exclus du packaging EXE, dossier réduit à 3,2 Go.
   Rien n'a été supprimé du dépôt Git, uniquement du binaire distribué.

### Service Windows auto-start — opération matérielle interdite sans GO
Le mécanisme de service/tâche dépend de l'installation certifiée et de la politique de release. Les anciennes commandes génériques `nssm install`, `schtasks /create` et les tâches SYSTEM ne doivent **pas** être copiées pour le FUE-G 01.4 : elles modifient le système, peuvent lancer un mauvais exécutable et rendent la récupération imprévisible. L'opérateur doit d'abord identifier dans la release certifiée le mécanisme réellement supporté, prouver le rollback et obtenir l'accord humain avant toute création, modification, activation ou redémarrage de service.

Logs locaux : `%APPDATA%/DigitalCrown/logs/digitalcrown.log` (rotation
automatique, 5 Mo × 5 fichiers) — géré par `run.py`, pas besoin de
redirection NSSM.

Ports : backend+frontend = **8005** (un seul port, le backend sert le
frontend buildé). Pas de port frontend séparé en mode cabinet.

---

## 3. Variables d'environnement cabinet

Fichier recommandé : `%APPDATA%\DigitalCrown\.env` référencé via
`DIGITALCROWN_ENV_FILE`, ou variables du service NSSM (`nssm set
DigitalCrown AppEnvironmentExtra ...`).

| Variable | Valeur cabinet | Note |
|---|---|---|
| `ENVIRONMENT` | `cabinet` (solo) ou `production` (PostgreSQL) | Active les invariants fail-fast (SECRET_KEY fort, pas de wildcard CORS). `cabinet` autorise SQLite/SQLCipher ou PostgreSQL ; `production` exige PostgreSQL. Dans les deux cas, une release certifiée et un upgrade Alembic explicite sont requis avant le boot. |
| `SECRET_KEY` | généré (64 hex) | `python -c "import secrets;print(secrets.token_hex(32))"` — sert aussi aux JWT (pas de JWT_SECRET séparé dans ce codebase) |
| `PAIRING_CODE_PEPPER` | généré (64 hex) | Secret HMAC dédié aux codes d’appairage Station. Les nouvelles installations le génèrent automatiquement ; pour un cabinet existant, générer une valeur indépendante lors d’une maintenance planifiée. |
| `DATABASE_URL` | absent (SQLite) ou `postgresql://...` local | |
| `CABINET_MASTER_KEY_HEX` | généré (64 hex) | Chiffre DB SQLCipher + backups |
| `CABINET_HOST` | `127.0.0.1` par défaut ; adresse LAN ou `0.0.0.0` seulement si HTTPS configuré | Aucun bind LAN automatique |
| `CABINET_PORT` | `8005` | Autorité unique du backend ; le contrat HTTPS mobile/WebAuthn exige 8005 et ignore `PORT` |
| `DIGITALCROWN_ENABLE_HTTPS` | `false` en loopback ; `true` obligatoire pour LAN en cabinet/production | Fail-closed |
| `DIGITALCROWN_TLS_CERT_FILE` / `DIGITALCROWN_TLS_KEY_FILE` | chemins locaux | Obligatoires quand HTTPS est activé |
| `ALLOWED_ORIGINS` | origine(s) correspondant au transport réellement configuré | Jamais `*` |
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

1. **Vérifier les preuves** de la release exacte `INSTALLABLE_CERTIFIED` (code SHA, manifest, provenance, assets, hashes et binaire), puis seulement avec GO humain copier la release certifiée sur le banc. Un dossier `dist/DigitalCrown/` générique n'est pas installable.
2. **Configurer l'environnement** : créer le fichier env cabinet (section 3),
   générer `SECRET_KEY` et `CABINET_MASTER_KEY_HEX`, poser les credentials
   Firebase fournis
3. **DB** :
   - SQLite (défaut) : rien à faire — créée+chiffrée au premier démarrage
   - PostgreSQL : installer PG 15+, `CREATE DATABASE digitalcrown_cabinet;`,
     renseigner `DATABASE_URL`
4. **Installer le service** (NSSM, section 2) et démarrer
5. **Vérifier le démarrage** : depuis S/A/B, utiliser le protocole réellement écouté : HTTPS avec SAN/CA approuvés si TLS activé (HTTP loopback seulement sans TLS). Contrôler `/api/health` →
   `{"status":"ok","database":"ok",...}` + `/api/health/db` + `/api/health/storage`
6. **Créer le cabinet réel** via le Setup Wizard de l'UI (PAS `seed_demo` —
   celui-ci est réservé aux démos commerciales)
7. **Activer la licence** : le `public_id` du cabinet créé doit exister dans
   Firestore `licenses/` avec `active=true` (dashboard SuperAdmin)
8. **Smoke tests post-install** (checklist §5 du PREPROD_RUNBOOK.md) :
   login, patient synthétique, upload/lecture document factice, RVG, agenda, ordonnance PDF,
   accès anonyme → 401
9. **Appairage mobile** : générer le QR depuis Réglages → scanner depuis le
   téléphone (nécessite le bind LAN, cf. §2 limite 1)
10. **Programmer le backup quotidien** (section 6)

---

## 5. Mise à jour / rollback : parcours certifié soumis à approbation

**Aucune commande d'arrêt, remplacement de fichiers, migration ou restauration n'est autorisée ici.** Utiliser uniquement une release `INSTALLABLE_CERTIFIED` exacte, le parcours d'activation officiel et un GO humain distinct. Un checkout/HEAD/artefact CI seul n'est jamais installable. Ne pas appliquer de migration de DB clinique sans rehearsal sur copie isolée.

1. Inventorier le service réel, le code/release SHA actif et le responsable de l'intervention.
2. Vérifier backup DB **et médias**, intégrité de chaque artefact et **restore éprouvé sur clone isolé** ; établir rollback et approbations avant toute coupure.
3. Vérifier le certificat `INSTALLABLE_CERTIFIED` de la nouvelle release, hashes, attestation et provenance, correspondance de la source code/assets et contraintes DB/migrations.
4. Si la mise à jour est explicitement autorisée, procéder avec le mécanisme certifié propre au runtime : arrêter/activer selon le runbook approuvé, tracer l'identité de la release et les étapes, appliquer seulement les migrations testées/autorisées sur les bonnes données.
5. Comparer BEFORE/AFTER santé service/DB/storage, auth, droits et intégrité de fixtures synthétiques ; consigner incidents et métriques.
6. En cas d'anomalie, exécuter **le plan de rollback validé** couvrant code, DB ET médias ; un simple renommage de répertoire n'est pas un rollback complet.

Références obligatoires : `docs/CABINET_CERTIFIED_RELEASE_POLICY.md`, `docs/PREPROD_RUNBOOK.md`, `docs/audits/V1_5_01_4_FUE_G_MULTIPC_PREFLIGHT_RUNBOOK.md`.

## 6. Backup / restore cabinet

### Backup quotidien automatique (tâche planifiée)

**Interdit de copier une commande générique de création de tâche pour le cabinet.** La fréquence, le compte d'exécution, le chemin d'exécutable, le coffre des clés et la configuration de sauvegarde doivent provenir du **runbook certifié** et être approuvés par l'opérateur avant mutation.

Le succès exige la preuve d'un backup DB **et médias**, des fichiers réellement présents/intègres et **d'une restauration validée sur clone isolé**. Un statut planificateur « succès » ou un backup sur le même disque ne suffit pas. Secrets et données patients jamais publiés.

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

## 8. Ce qui reste à faire avant le premier pilote

1. 🟡 **Bind LAN explicite** — le runtime démarre loopback-only. L’installateur
   doit configurer explicitement `CABINET_HOST` + HTTPS/certificat pour exposer
   le serveur au LAN, puis vérifier `/api/health/topology`. La règle pare-feu
   Windows reste une étape d’installation à valider sur le poste pilote.
2. ✅ **Mode `ENVIRONMENT=cabinet`** — existe et tranché : production-like
   (DEBUG interdit, pas de CORS wildcard) mais autorise SQLite/SQLCipher
   (`validate_environment_invariants()`, `backend/main.py`).
3. ✅ **Rebuild PyInstaller** — fait, `console=False`, `ai_models/` audité et
   réduit de 4,9 Go à 3,2 Go (voir section installeur ci-dessus).
4. ✅ **Installeur** — `installer/DigitalCrown.iss` (Inno Setup), remplace le
   script PowerShell initialement envisagé par une expérience un clic
   complète (voir section installeur ci-dessus). Compilé et vérifié
   (`DigitalCrownSetup.exe`), **jamais exécuté sur une machine réelle** —
   test d'installation sur VM/poste isolé toujours à faire avant un vrai pilote.
5. **Grace period licence UI** (bannières progressives) — toujours en attente,
   post-pilote.
