# Digital Crown — Guide d'installation pour nouveau cabinet

## ⚡ Cabinet solo : utiliser l'installeur un clic

Pour un cabinet à un seul poste, tout ce guide manuel est désormais remplacé
par `DigitalCrownSetup.exe` (compilé depuis `installer/DigitalCrown.iss`,
voir `docs/CABINET_ONPREM_GUIDE.md` section installeur) : aucun terminal,
aucune commande, secrets générés automatiquement par l'installation,
SQLite/SQLCipher chiffré (`ENVIRONMENT=cabinet`, mode solo officiellement
supporté). Le schéma est préparé par la procédure d'installation/Alembic
explicite ; le service ne crée ni tables ni migration au démarrage. Le reste de ce document décrit la
procédure manuelle historique, **non exécutable telle quelle** pour le multi-PC.

> **STOP — Release/FUE-G 01.4** : seul `INSTALLABLE_CERTIFIED` (code exact SHA + assets, provenance/hash vérifiés) est installable, après approbation humaine sur banc isolé. Jamais de branche, HEAD, master, EXE ad hoc ni `CODE_CERTIFIED` seul. En cabinet/production, LAN :8005 exige HTTPS/TLS et **chaîne de confiance validée sur chaque annexe**. Suivre `docs/CABINET_CERTIFIED_RELEASE_POLICY.md` et `docs/audits/V1_5_01_4_FUE_G_MULTIPC_PREFLIGHT_RUNBOOK.md`.

## Vue d'ensemble

Digital Crown est une application **on-premise**, tournant localement dans le cabinet dentaire (pas de serveur distant). Chaque installation est isolée, avec sa propre base de données et ses médias.

**Architecture :**
- Backend : FastAPI + SQLAlchemy
- Frontend : React 19 + Vite 7
- Base de données : PostgreSQL 15+ (cabinet multi-postes) ou SQLite/SQLCipher
  chiffré (cabinet solo, `ENVIRONMENT=cabinet`)
- Médias : stockés localement, servis par routes authentifiées
- Identité/Licence : Firebase (optionnel, hors-ligne supporté)

**Doctrine base de données (mise à jour — voir aussi `CLAUDE.md`)**

| Mode | `ENVIRONMENT` | Base | Cas d'usage |
|---|---|---|---|
| Solo | `cabinet` | SQLite/SQLCipher chiffré AES-256 | Un seul poste — installeur un clic |
| Multi-postes | `cabinet` ou `production` | PostgreSQL 15+ | Plusieurs postes / serveur dédié |
| Dev/test/démo | `development`/`local`/`test` | SQLite (non chiffré) | Jamais en cabinet réel |

`ENVIRONMENT=production` refuse SQLite (PostgreSQL obligatoire).
`ENVIRONMENT=cabinet` autorise les deux — c'est le mode solo qui décide,
pas une règle bloquante du garde de démarrage
(`validate_environment_invariants()`, `backend/main.py`).

---

## Architecture standard (PostgreSQL)

### Cabinet solo (1 PC)

```
┌─ PC Cabinet (windows/mac)
│  ├─ PostgreSQL (localhost)
│  ├─ Backend FastAPI (port 8005)
│  └─ Frontend React (intégré ou PWA)
```

### Cabinet multi-postes (2-5 postes)

```
┌─ PC Principal (Serveur)
│  ├─ PostgreSQL (192.168.x.1)
│  └─ Backend FastAPI (port 8005)
│
├─ PC Secrétaire
│  └─ Frontend PWA (https://192.168.x.1:8005)
│
└─ PC Salle Attente
   └─ Frontend PWA (https://192.168.x.1:8005)
```

### Clinique (10+ postes)

```
┌─ Serveur dédié
│  ├─ PostgreSQL (serveur.local)
│  ├─ Backend FastAPI (port 8005)
│  └─ Backup quotidien
│
├─ Poste 1..N
│  └─ Frontend PWA (https://serveur.local:8005)
```

---

## 1. Prérequis

### Plateforme certifiée : Windows
Le programme `DigitalCrownSetup.exe` et la chaîne PyInstaller/Inno Setup décrits par la politique de release ciblent Windows. Les anciens exemples Mac de ce guide ne démontrent aucune certification d'installeur Mac. Pour FUE-G 01.4, relever les OS réels S/A/B et vérifier la compatibilité de chaque client et de l'artefact installable avant tout GO.

**Machine cible :**
- Processeur : Intel i5 ou Mac M1+ (minimum)
- RAM : 8 GB
- Disque : 500 MB libre (app + dépendances), +2 GB pour les médias patients
- Réseau : LAN cabinet (pas d'accès distant recommandé)

**À installer :**

```
✓ Python 3.12.x (https://www.python.org — cocher "Add to PATH")
✓ PostgreSQL 15+ (https://www.postgresql.org) OU SQLite (inclus dans Python)
✓ Node.js 20+ (https://nodejs.org)
✓ Git (pour les mises à jour)
```

---

## 2. PostgreSQL — serveur multi-postes sur banc isolé
Sur S, utiliser une version compatible de PostgreSQL et un provisionnement **spécifique à la release certifiée**, uniquement sur base d'essai non clinique. Les commandes historiques de ce guide ne suffisent pas à autoriser une installation. Vérifier la version, la cible de DB réellement résolue, la sauvegarde, la restauration sur copie, les droits et les migrations nécessaires. Pour le solo en `ENVIRONMENT=cabinet`, SQLCipher reste autorisé ; `ENVIRONMENT=production` exige PostgreSQL.

## 3. Compte PostgreSQL dédié — sans exemple de secret
Le banc S+A+B utilise une base distincte et un **rôle applicatif non-superuser**, provisionnés par le parcours autorisé. Le mot de passe doit être généré aléatoirement et conservé dans un coffre sécurisé : **jamais** dans SQL, le dépôt, Notion ou un artefact de test. Vérifier les permissions réelles contre les besoins de la release, ne jamais réutiliser les identifiants DB du cabinet et ne lancer aucune migration non autorisée.

## 4. Configuration .env

Créer `backend/.env.local` ou `%APPDATA%\DigitalCrown\.env` :

```env
# Mode d'exécution
ENVIRONMENT=cabinet

# Base de données
DATABASE_URL=postgresql://cabinet_user:secure_password_here@localhost/digitalcrown_cabinet_01

# Sécurité
SECRET_KEY=generate_32_chars_minimum_randomly_e.g._use_python_secrets

# Frontend
# Exemple fictif : l'IP choisie DOIT être dans le SAN du certificat approuvé
CABINET_HOST=192.168.1.100
CABINET_PORT=8005
DIGITALCROWN_ENABLE_HTTPS=true
DIGITALCROWN_TLS_CERT_FILE=C:\certs\cabinet-test.crt
DIGITALCROWN_TLS_KEY_FILE=C:\certs\cabinet-test.key
ALLOWED_ORIGINS=https://192.168.1.100:8005

# Médias
MEDIA_DIR=%APPDATA%\DigitalCrown\media

# IA (optionnel)
CLOUD_AI_ENABLED=false
OLLAMA_API_URL=http://localhost:11434

# Firebase (optionnel, hors-ligne supporté)
FIREBASE_ADMIN_SDK_JSON={}
```

**Générer SECRET_KEY :**

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 5. Initialiser le propriétaire — environnement autorisé seulement

Sur banc isolé, utiliser le parcours d'initialisation **de la release certifiée**, un propriétaire autorisé et un secret fort unique. **Ne jamais utiliser un identifiant/mot de passe d'exemple, la commande `seed_user` ni des données cabinet réelles** pour 01.4. Vérifier identité/permissions avant tout appairage.

## 6. Lancer uniquement la release certifiée

**Ne pas utiliser `uvicorn --reload`, `uvicorn --host 0.0.0.0` sans TLS, ni `create_release.ps1` sans ses bundles certifiés.** Ordre : `CODE_CERTIFIED` (HEAD exact de master) → assets runtime certifiés pour **ce SHA** → `create_release.ps1 -CertifiedArtifactZip ... -RuntimeAssetsZip ...` → contrôle `INSTALLABLE_CERTIFIED` → GO humain → `run_real_backend.ps1 -ReleaseId ... -ConfirmRealActivation "YES"` sur banc isolé. Rien ici ne rend la PR #803 installable.

**Schéma obligatoire** : l'URL `http://127.0.0.1:8005/api/health` ne fonctionne comme health check que pour un serveur lancé en **loopback HTTP sans TLS**. Lorsque S sert HTTPS sur le port 8005, **même depuis S**, utiliser `https://<nom-ou-IP-couvert-par-le-SAN>:8005/api/health` avec validation native du certificat. A/B font la même vérification, sans contournement TLS.

## 7. Frontend — uniquement celui de la release installable
Sur le banc FUE-G 01.4, ne pas lancer `npm run dev`, `npm run build`, Vite exposé en LAN ni copier `frontend/dist` depuis un checkout. Le bundle `INSTALLABLE_CERTIFIED` fournit déjà le frontend servi par S avec le backend sur le **port 8005**. Les commandes de laboratoire ont leur propre environnement isolé, sans valeur de certification d'installation.

## 8. Premier login et configuration

1. Ouvrir l'origine exacte du serveur : loopback HTTP seulement sans TLS ; pour le FUE-G multi-PC, **HTTPS :8005** avec certificat approuvé.
2. Authentifier le propriétaire autorisé avec un compte individuel, jamais un identifiant de démonstration.
3. Changer le mot de passe (Settings → Profile)
4. Configurer le cabinet :
   - Logo
   - Adresse
   - Téléphone
   - QR code (généré automatiquement)

---

## 9. Accès multi-PC : HTTPS obligatoire

**Gate préalable** : S, A et B isolés et autorisés, DNS/IP stable de S, SAN/CA/validité TLS approuvés **depuis A et B séparément**, release `INSTALLABLE_CERTIFIED` correspondant au code exact sous test, backup DB+médias synthétiques **et restore clone prouvé**, autorisations installation/reboot/coupure explicites.

1. Configurer sur S `CABINET_HOST` LAN, `CABINET_PORT=8005`, `DIGITALCROWN_ENABLE_HTTPS=true`, chemins cert/key TLS locaux protégés et `ALLOWED_ORIGINS` correspondant aux origines HTTPS réellement servies (pas automatiquement aux IP clientes).
2. Après activation humaine et certifiée sur **banc non clinique**, constater `/api/health`, `/api/health/db`, `/api/health/storage`, `/api/health/topology` ; A et B ouvrent séparément `https://192.168.1.100:8005` **uniquement si** cette IP illustrative correspond au SAN et au réseau réellement observés.
3. Deux profils vierges, deux appairages single-use et identités distinctes ; valider rôles/droits, refus avant authentification, Hub et Station PIN.
4. Tester après GO distinct les refus HTTP LAN/cert invalide/mauvaise IP, 503/DB/423/PIN/replay, restart S/A/B et coupure/récupération ; capturer BEFORE/AFTER mêmes viewports et **mesurer** les durées, sans patient réel.

Le mobile via QR/HTTPS ne remplace pas la certification des deux postes PC. Voir `docs/audits/V1_5_01_4_FUE_G_MULTIPC_PREFLIGHT_RUNBOOK.md`.

## 10. Rôle exact de Firebase

Firebase n'est **PAS** une base patient.

**Rôle :**
- Vérification de licence (optionnel)
- Synchronisation identité propriétaire (optionnel)
- Hors-ligne : `validate_license_with_expiry()` retourne `active=None` (local cache conservé)

**Si Firebase indisponible :**
- ✓ App continue
- ✓ Patients/documents accessibles
- ✓ Offline mode actif
- ✗ Vérification licence suspendue (72h de grâce)

**Configuration :**
Laisser `FIREBASE_ADMIN_SDK_JSON={}` → mode hors-ligne assuré

---

## 11. Sauvegarde et restore

### Sauvegarde

```bash
# DB
python -m backend.scripts.backup_db
# → backend/backups/backup_YYYYMMDD_HHMMSS.sql.enc

# Médias
python -m backend.scripts.backup_media
# → backend/backups/media_backup_YYYYMMDD_HHMMSS.zip.enc
```

**Stocker en lieu sûr :**
- Disque externe chiffré
- Serveur backup cabinet
- Cloud (chiffré localement)

### Restore

```bash
# DB (confirmation requise)
python -m backend.scripts.restore_db backup_YYYYMMDD_HHMMSS.sql.enc --yes

# Médias (voir PATIENT_DATA_ROLLBACK.md)
```

---

## 12. Checklist installateur (PostgreSQL standard)

**Prérequis :**
- [ ] OS et dépendances serveur compatibles avec la release certifiée
- [ ] **PostgreSQL 15+ installé et running** (obligatoire)
- [ ] Artefact `INSTALLABLE_CERTIFIED` et code SHA exact vérifiés, aucune installation depuis le dépôt

**Configuration DB :**
- [ ] Role PostgreSQL dédié créé (`cabinet_XXXX_01`)
- [ ] Base cabinet créée (`digitalcrown_cabinet_XXXX_01`)
- [ ] Password fort généré (20+ caractères aléatoires)
- [ ] Permissions GRANT appliquées (roles != postgres)

**Application :**
- [ ] DB synthétique isolée, cible PostgreSQL résolue et droits du rôle vérifiés (secrets jamais exposés)
- [ ] Secrets uniques et protégés présents sur banc, sans exposition GitHub/Notion/logs
- [ ] MEDIA_DIR configuré (`%APPDATA%\DigitalCrown\media`)
- [ ] Serveur S démarre depuis l'artefact certifié, identité release/SHA observée
- [ ] `/api/health` répond sur le schéma réellement configuré : HTTPS pour LAN
- [ ] `/api/health/db` retourne OK
- [ ] Frontend HTTPS :8005 accessible depuis A et B, avec confiance TLS vérifiée individuellement

**Cabinet :**
- [ ] Propriétaire initialisé par le parcours certifié avec permissions vérifiées ; aucun `seed_user` en cabinet réel
- [ ] Premier login réussit
- [ ] Cabinet configuré (logo, adresse, téléphone)
- [ ] Patient purement synthétique créé sur DB de banc isolé, jamais sur cabinet clinique
- [ ] Document de fixture synthétique archivé sans donnée patient réelle

**Backup & Restore :**
- [ ] Backup DB fonctionne (`backup_db.py`)
- [ ] Backup média fonctionne (`backup_media.py`)
- [ ] Restore testé sur DB isolée (jamais vraie DB)
- [ ] Comptages identiques source/restore
- [ ] Procédure rollback imprimée et accessible

**Multi-postes (si applicable) :**
- [ ] IP/DNS LAN de S vérifié, nom/IP correspondant au SAN du certificat et port 8005 testés sur A/B
- [ ] `ALLOWED_ORIGINS` restreint aux origines HTTPS réellement servies, pas aux IP clientes par défaut
- [ ] Deux annexes A et B physiquement/logiquement distinctes rejoignent le bon serveur S en HTTPS avec TLS natif validé séparément
- [ ] Identités et appairages A/B distincts, Station PIN et restrictions vérifiés ; mobile/PWA = test séparé

**Validation finale :**
- [ ] Aucune donnée test dans DB principale
- [ ] Vraie DB `digitalcrown_db` jamais touchée
- [ ] Superadmin réel intact
- [ ] Pas de données patients réels importées (sauf acceptation explicite)
- [ ] Procédure rollback à portée d'équipe

---

## Dépannage

### "Database connection refused"

```bash
# Vérifier PostgreSQL
psql -U postgres -h localhost -c "SELECT 1"

# Si échoue : relancer service
# Windows : Services → PostgreSQL → Restart
# Mac : brew services restart postgresql@15
```

### "Module not found: reportlab"

```bash
pip install reportlab pillow weasyprint
```

### "CORS blocked"

```bash
# Vérifier ALLOWED_ORIGINS dans .env.local
# Inclure l'IP exacte du client
ALLOWED_ORIGINS=https://192.168.1.100:8005
```

### "Patients not showing"

```bash
# Vérifier tenant isolation
# DB doit avoir au moins 1 patient sous le cabinet du user connecté
# Via psql :
SELECT COUNT(*) FROM patients WHERE employer_id = (SELECT id FROM users WHERE email='owner@cabinet.local');
```

---

## Rehearsal E2E isolé (validation avant go-live)

Avant d'installer un vrai cabinet, valider le parcours complet (bootstrap →
login → `/me`) sur une instance PostgreSQL et un port totalement isolés du
cabinet actif, sans jamais toucher `.env.local` ni les variables Windows
persistantes.

### Lancement sécurisé (obligatoire)

Ne jamais lancer le backend rehearsal à la main. Utiliser uniquement :

```powershell
.\backend\scripts\run_rehearsal_backend.ps1
```

Ce script :
- charge `.env.e2e-install-rehearsal` **dans le process courant uniquement**
  (aucune variable persistante modifiée, aucun `setx`)
- exige une `DATABASE_URL` explicitement présente dans le fichier rehearsal et
  calcule une empreinte de la cible ; les alias PostgreSQL équivalents à la
  cible cabinet connue sont refusés par le garde Python
- refuse de démarrer si `ENVIRONMENT` global est `production`/`cabinet`
- refuse de démarrer si `PORT=8005` est défini persistemment (port du
  cabinet réel)
- lance le backend sur `127.0.0.1:8008` (jamais 8005)

### Bootstrap cabinet + owner (jamais SUPERADMIN global)

```bash
export $(grep -v '^#' .env.e2e-install-rehearsal | xargs)
python -m backend.scripts.bootstrap_new_cabinet
```

`backend/scripts/bootstrap_new_cabinet.py` refuse de s'exécuter si la DB
cible correspond à la cible cabinet connue ou si `ENVIRONMENT` n'est pas
rehearsal/test/development. Il crée un owner cabinet avec `role=DENTISTE`
(jamais `ADMIN` global — le superadmin réel reste hors de toute cible rehearsal).

**⚠️ Piège email de test — TLD réservé** : ne jamais utiliser un domaine de
test en `.local` (ex. `owner@test.local`). Le validateur email Pydantic
(`email-validator`) rejette systématiquement les TLD réservés RFC 6761/6762
(`.local`, `.test`, `.example`, `.invalid`, `.localhost`), **indépendamment
du DNS** — l'erreur n'apparaît qu'à la sérialisation de la réponse (ex.
`/api/auth/me`), pas au login lui-même, ce qui la rend trompeuse (elle se
manifeste en 500 sur `/me`, pas en 422 au login). Utiliser un TLD non
réservé, comme les fixtures de test réelles (`backend/tests/conftest.py` →
`@cabinet.ma`). Le script bootstrap utilise `owner.e2e@e2e-rehearsal.ma`.

### Login owner cabinet (format exact)

L'endpoint `/api/auth/login` attend un payload **OAuth2 form-urlencoded**
avec les champs `username`/`password` — **pas** de JSON `{"email": ...}`.

```bash
curl -X POST http://127.0.0.1:8008/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=owner.e2e@e2e-rehearsal.ma&password=<PASSWORD_REHEARSAL>"
```

Réponse attendue (200) :
```json
{"access_token": "...", "refresh_token": "...", "token_type": "bearer"}
```

### Vérification `/me`

```bash
curl http://127.0.0.1:8008/api/auth/me -H "Authorization: Bearer <TOKEN>"
```

Réponse attendue (200) : `role: "DENTISTE"`, `is_superadmin: false`.

### Piège process zombie

Si le login renvoie 500 alors que le code est correct, vérifier qu'aucun
ancien process `uvicorn` ne tourne déjà sur le port 8008 avec du code
obsolète :

```powershell
netstat -ano | findstr ":8008"
taskkill /F /PID <PID>
```

Relancer ensuite exclusivement via `run_rehearsal_backend.ps1`.

### Piège MEDIA_ROOT — isolation du stockage fichier (corrigé)

**Historique du bug** : jusqu'à ce que `MEDIA_ROOT` soit effectivement lu par
le code (`backend/main.py`, `backend/routers/documents.py`,
`backend/routers/patients.py`, `backend/services/archive_service.py`), les
documents générés en rehearsal (ordonnance, certificat) étaient écrits
**physiquement dans le vrai dossier média du cabinet**
(`%APPDATA%/DigitalCrown/media/archives/<patient_id>/...`), même si la DB
restait correctement isolée. La cause : `MEDIA_DIR` était calculé une seule
fois via `AppPaths.get_user_data_dir() / "media"`, sans jamais lire la
variable d'environnement.

**Fix appliqué** : chaque point de calcul de `MEDIA_DIR` lit désormais
`MEDIA_ROOT` si définie, sinon comportement identique à avant (le vrai
cabinet ne définit jamais `MEDIA_ROOT`, donc zéro changement de comportement
en production).

**Vérification obligatoire avant de refaire confiance à l'isolation média** :
après génération d'un document en rehearsal, toujours confirmer physiquement
que le fichier est dans `install_rehearsal_media/` et **absent** de
`%APPDATA%/DigitalCrown/media/`.

### Sécurité MEDIA_ROOT et isolation rehearsal

- `ENVIRONMENT=e2e_install_rehearsal` impose désormais `MEDIA_ROOT`.
- `MEDIA_ROOT` rehearsal doit pointer vers un dossier explicite de répétition
  comme `install_rehearsal_media` : s'il est absent, s'il pointe vers
  `%APPDATA%/DigitalCrown/media`, ou s'il ressemble au dossier média réel,
  le backend et les scripts de backup refusent de démarrer.
- `DIGITALCROWN_ENV_FILE` est obligatoire pour tout backup rehearsal :
  ne jamais laisser `backup_db.py` ou `backup_media.py` recharger
  `backend/.env.local` par-dessus la config rehearsal.
- Le piège historique reste `%APPDATA%/DigitalCrown/media` : c'est le dossier
  réel du cabinet, jamais une cible de rehearsal.

Commande de lancement sûre :

```powershell
.\backend\scripts\run_rehearsal_backend.ps1
```

Commande backup DB sûre :

```powershell
$env:DIGITALCROWN_ENV_FILE = (Resolve-Path .\.env.e2e-install-rehearsal)
.\.venv312\Scripts\python.exe backend\scripts\backup_db.py --dry-run
.\.venv312\Scripts\python.exe backend\scripts\backup_db.py
```

Commande backup média sûre :

```powershell
$env:DIGITALCROWN_ENV_FILE = (Resolve-Path .\.env.e2e-install-rehearsal)
.\.venv312\Scripts\python.exe backend\scripts\backup_media.py --dry-run
.\.venv312\Scripts\python.exe backend\scripts\backup_media.py
```

Checklist avant installateur :

- vérifier que `run_rehearsal_backend.ps1` affiche `ENVIRONMENT=e2e_install_rehearsal`
- vérifier que l'empreinte affichée correspond à la cible isolée attendue et
  que la cible n'est pas la cible cabinet connue
- vérifier que `MEDIA_ROOT` affiché contient `install_rehearsal_media`
- lancer les deux backups en `--dry-run` avec `DIGITALCROWN_ENV_FILE`
- générer un document de test et confirmer qu'aucun fichier nouveau n'apparaît
  dans `%APPDATA%/DigitalCrown/media`

### Piège DATABASE_URL/CABINET_MASTER_KEY_HEX dans les scripts backup/restore

`backup_db.py`, `backup_media.py` et `restore_db.py` appellent
`load_backend_env(override=True)` **sans condition d'environnement**
(contrairement à `main.py`, qui protège les variables déjà injectées via
`override=False` en premier). Si `backend/.env.local` définit
une `DATABASE_URL` issue du fichier cabinet, lancer ces scripts avec seulement
des variables exportées dans le shell **ne suffit pas** — le script écrasera
silencieusement la cible par celle du fichier chargé en priorité.

**Protection obligatoire** : toujours définir `DIGITALCROWN_ENV_FILE` (chemin
absolu vers `.env.e2e-install-rehearsal`) avant d'appeler ces scripts — ce
candidat est prioritaire sur `.env.local` dans `env_loader.py`.

```bash
python -c "
import os
os.environ['DIGITALCROWN_ENV_FILE'] = r'C:\chemin\absolu\.env.e2e-install-rehearsal'
from backend.scripts.backup_db import backup_db
backup_db()
"
```

`.env.e2e-install-rehearsal` doit aussi définir `CABINET_MASTER_KEY_HEX`
(clé hex 32 bytes dédiée rehearsal, générée via `secrets.token_hex(32)` —
**jamais** la clé réelle du cabinet).

**Précision (AUTO-BACKUP-POSTGRES-ROUTING-FIX-1, 2026-07-10)** : ce piège reste
entier pour un usage **CLI** de `backup_db.py` (le `load_backend_env(override=True)`
sous `if __name__ == "__main__":` s'exécute toujours sans condition — protection
`DIGITALCROWN_ENV_FILE` ci-dessus toujours obligatoire). En revanche, `backup_db.py`
est désormais aussi importé comme **librairie** par
`backend/services/backup_service.py` (scheduler automatique du process réel) : dans
ce cas, ni `load_backend_env` ni l'import de `settings` ne s'exécutent au niveau
module — le process appelant (déjà démarré via `main.py`, env déjà chargé
correctement) n'est jamais écrasé. Les deux usages sont maintenant sûrs, mais pour
des raisons différentes : CLI protégé par `DIGITALCROWN_ENV_FILE`, librairie
protégée par le chargement paresseux.

### Login owner cabinet (déjà validé plus haut) → workflow patient/documents

```bash
TOKEN=$(curl -s -X POST http://127.0.0.1:8008/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "username=owner.e2e@e2e-rehearsal.ma" \
  --data-urlencode "password=<PASSWORD_REHEARSAL>" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
```

**Créer un patient test** (payload minimal — `nom`, `prenom`,
`date_naissance`, `sexe` requis, `extra="forbid"` sur le reste) :

```bash
curl -X POST http://127.0.0.1:8008/api/patients/ \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"nom":"INSTALL","prenom":"PatientE2E","date_naissance":"1990-01-01","sexe":"M","telephone":"0600000001"}'
```

**Piège licence** : un owner cabinet fraîchement bootstrappé a
`is_licensed=False` (Firebase injoignable en rehearsal isolé) — toute route
POST/PUT/PATCH/DELETE renvoie 403 `NOT_LICENSED`. Seed `is_licensed=True`
directement dans `bootstrap_new_cabinet.py` (champ `User`, pas de logique de
licence modifiée).

**Générer ordonnance/certificat** (`POST /api/documents/generate`,
`type=ordonnance|certificat`, `patient_id`, `data`) :

```bash
curl -X POST "http://127.0.0.1:8008/api/documents/generate?archive=true" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"type":"ordonnance","patient_id":1,"data":{"medications":[{"nom":"ZAMOX","dosage":"1 g","forme":"Sachets","posologie":"2 fois par jour pendant une semaine"}]}}'
```

**Upload document/média** (`POST /api/documents/archive`, `doc_type` en
MAJUSCULES — voir enum `DocumentType`) :

```bash
curl -X POST "http://127.0.0.1:8008/api/documents/archive?patient_id=1&doc_type=DOCUMENT_LIBRE&title=Test" \
  -H "Authorization: Bearer $TOKEN" -F "file=@test.pdf;type=application/pdf"
```

**Test média protégé** :
```bash
curl http://127.0.0.1:8008/api/documents/{id}/download -H "Authorization: Bearer $TOKEN"  # 200
curl http://127.0.0.1:8008/api/documents/{id}/download                                     # 401
```

**Backup DB + médias rehearsal** (avec protection `DIGITALCROWN_ENV_FILE`
ci-dessus) :

```bash
python -c "... from backend.scripts.backup_db import backup_db; backup_db()"
python -c "... from backend.scripts.backup_media import backup_media; backup_media()"
```

Vérifier que la taille du backup média rehearsal est cohérente avec le
volume de test (quelques Mo), pas avec le volume réel du cabinet
(généralement centaines de Mo) — un backup anormalement gros est un signal
d'alerte d'isolation cassée.

---

## Passage à la production (go-live)

1. ✅ Backups validés (restore testé sur copie)
2. ✅ Patients/documents contents on copie test
3. ✅ Accès LAN testé (tous postes)
4. ✅ PWA mobile testé
5. ✅ PDF rendering (ordonnance, certificat) testé
6. ✅ Offline mode testé
7. ✅ Rollback procedure imprimée et à portée

**Puis :** import des vrais patients (via CSV ou API) et démarrage progressif.

---

**Version** : 2026-07-08
**Auteur** : Claude Code
**Lien CABINET-PATIENT-DATA-SAFETY-1** : cf. docs/PATIENT_DATA_ROLLBACK.md pour urgences
