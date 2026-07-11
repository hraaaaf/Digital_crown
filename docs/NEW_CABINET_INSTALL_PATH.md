# Digital Crown — Guide d'installation pour nouveau cabinet

## Vue d'ensemble

Digital Crown est une application **on-premise**, tournant localement dans le cabinet dentaire (pas de serveur distant). Chaque installation est isolée, avec sa propre base de données et ses médias.

**Architecture :**
- Backend : FastAPI + SQLAlchemy
- Frontend : React 19 + Vite 7
- Base de données : **PostgreSQL 15+ (obligatoire pour installation client)**
- Médias : stockés localement, servis par routes authentifiées
- Identité/Licence : Firebase (optionnel, hors-ligne supporté)

**⚠️ IMPORTANT : PostgreSQL est le standard obligatoire**

SQLite n'est accepté que pour :
- ✓ Développement local
- ✓ Tests unitaires
- ✓ Démo / Formation

Pour toute installation cabinet client, **PostgreSQL est obligatoire**.

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
│  └─ Frontend PWA (http://192.168.x.1:8005)
│
└─ PC Salle Attente
   └─ Frontend PWA (http://192.168.x.1:8005)
```

### Clinique (10+ postes)

```
┌─ Serveur dédié
│  ├─ PostgreSQL (serveur.local)
│  ├─ Backend FastAPI (port 8005)
│  └─ Backup quotidien
│
├─ Poste 1..N
│  └─ Frontend PWA (http://serveur.local:8005)
```

---

## 1. Prérequis

### Windows 10/11 Pro ou Mac

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

## 2. Installation PostgreSQL (recommandé)

### Windows

```bash
# Télécharger PostgreSQL 15+ depuis https://www.postgresql.org/download/windows/
# Installer avec password root = 'admin' (peut être changé après)
# Vérifier :
psql --version
psql -U postgres -h localhost -c "SELECT version();"
```

### Mac

```bash
# Homebrew
brew install postgresql@15
brew services start postgresql@15
psql -U postgres -c "SELECT version();"
```

### Mode Solo (cabinet seul)

Même en mode solo (un seul poste), PostgreSQL est obligatoire :
- Simplifie le support et les migrations futures
- Facilite l'ajout de postes supplémentaires sans refonte DB
- Offre des garanties ACID meilleures que SQLite
- PostgreSQL peut tourner sur le même PC que l'application

---

## 3. Modèle DB standard : utilisateur dédié par cabinet

**Principe :** chaque cabinet a un utilisateur PostgreSQL dédié, jamais le superuser `postgres`.

```bash
# Connexion PostgreSQL (Windows / Mac / Linux)
psql -U postgres -h localhost

# Dans psql :
CREATE DATABASE digitalcrown_cabinet_2024_01;
CREATE ROLE cabinet_2024_01 WITH LOGIN PASSWORD 'XyZ9pQ2kL5mN8vB3wE7rT';
GRANT ALL PRIVILEGES ON DATABASE digitalcrown_cabinet_2024_01 TO cabinet_2024_01;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO cabinet_2024_01;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO cabinet_2024_01;
\q
```

**Résultat :**
- DB : `digitalcrown_cabinet_2024_01`
- User : `cabinet_2024_01` (dédié, pas postgres)
- Password : `XyZ9pQ2kL5mN8vB3wE7rT` (généré aléatoire)

**Sécurité (OBLIGATOIRE) :**
- ❌ Ne JAMAIS utiliser `postgres` superuser dans l'application
- ❌ Ne JAMAIS hardcoder le mot de passe en clair
- ❌ Ne JAMAIS logger la `DATABASE_URL` complète (masquer password)
- ✓ Stocker password dans un fichier `.env` local protégé (chmod 600)
- ✓ Générer password aléatoire (min. 20 caractères, alphanumériques + spéciaux)

---

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
ALLOWED_ORIGINS=http://127.0.0.1:8005,http://192.168.x.x:8005

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
python -c "import secrets; print(secrets.token_hex(16))"
```

---

## 5. Créer le superadmin cabinet

```bash
cd C:\chemin\vers\DigitalCrown

# Créer le premier utilisateur admin
python -m backend.seed_user --email owner@cabinet.local --password "SecurePass123!" --role ADMIN
```

**Résultat :**
- Email : `owner@cabinet.local`
- Password : `SecurePass123!` (à changer après premier login)
- Rôle : ADMIN (accès complet)

---

## 6. Lancer le backend

**⚠️ Ne jamais lancer `uvicorn --reload` sur le port réel du cabinet.** Un `--reload` recharge
le process à chaque édition de fichier Python du dépôt — y compris du code non terminé — sans
déploiement explicite. Incident réel documenté dans `CLAUDE.md` (P0-TREATMENT-JOURNEY-1, 2026-07-10).

**Procédure recommandée (dépôt de dev, avant packaging EXE) :**
```powershell
# 1. Construire une release immuable (copie hors du dépôt, backend/ + frontend/dist)
cd backend\scripts
.\create_release.ps1

# 2. Démarrer depuis cette release, jamais depuis le dépôt directement
.\run_real_backend.ps1 -ReleaseId <release_id_affiche> -ConfirmRealActivation "YES"
```

`run_real_backend.ps1` refuse tout `--reload`, toute config ressemblant à du rehearsal
(DATABASE_URL, ENVIRONMENT, MEDIA_ROOT), et exige un manifeste de release valide. Voir
`docs/CABINET_ONPREM_GUIDE.md` section 2 pour le détail de la doctrine.

**Commande brute équivalente (sans les garde-fous — déconseillée sauf test isolé, jamais sur le
poste cabinet réel) :**
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8005
```

**Résultat attendu :**
```
Uvicorn running on http://0.0.0.0:8005
Application startup complete
```

Health check :
```bash
curl http://127.0.0.1:8005/api/health
# Résultat : {"status":"ok","database":"ok",...}
```

---

## 7. Lancer le frontend

Commandes frontend officielles depuis la racine du repo :

```bash
npm test
npm run build
```

Equivalents directs si vous voulez cibler explicitement le sous-projet :

```bash
npm --prefix frontend test
npm --prefix frontend run build
```

```bash
cd frontend

# Mode développement (test)
npm run dev --host 0.0.0.0

# Mode production (packagé avec backend)
npm run build
# → distill dans frontend/dist/, servi par backend.main
```

**Accès :**
- Dev : http://localhost:5173
- Prod : http://127.0.0.1:8005

---

## 8. Premier login et configuration

1. Ouvrir http://127.0.0.1:8005
2. Email : `owner@cabinet.local` / Password : `SecurePass123!`
3. Changer le mot de passe (Settings → Profile)
4. Configurer le cabinet :
   - Logo
   - Adresse
   - Téléphone
   - QR code (généré automatiquement)

---

## 9. Accès depuis d'autres postes du réseau

**Prerequis :**
- Tous les postes sur le même LAN
- Machine cabinet : IP fixe (ex. 192.168.1.100)

**Configuration :**
1. Dans `backend/.env.local` :
   ```env
   ALLOWED_ORIGINS=http://192.168.1.100:8005,http://192.168.1.101:8005
   ```
2. Relancer backend
3. Autre poste : http://192.168.1.100:8005
4. Login avec le même compte

**Mobile PWA :**
1. Ouvrir http://192.168.1.100:8005 sur téléphone
2. Menu → "Ajouter à l'écran d'accueil"
3. Accès offline avec QR-pairing

---

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
- [ ] Python 3.12 installé
- [ ] **PostgreSQL 15+ installé et running** (obligatoire)
- [ ] Git installé

**Configuration DB :**
- [ ] Role PostgreSQL dédié créé (`cabinet_XXXX_01`)
- [ ] Base cabinet créée (`digitalcrown_cabinet_XXXX_01`)
- [ ] Password fort généré (20+ caractères aléatoires)
- [ ] Permissions GRANT appliquées (roles != postgres)

**Application :**
- [ ] `.env.local` configuré avec DATABASE_URL du role dédié
- [ ] `.env.local` contient SECRET_KEY (32+ caractères)
- [ ] MEDIA_DIR configuré (`%APPDATA%\DigitalCrown\media`)
- [ ] Backend démarre sans erreur
- [ ] `/api/health` retourne OK
- [ ] `/api/health/db` retourne OK
- [ ] Frontend accessible (http://127.0.0.1:8005)

**Cabinet :**
- [ ] Premier superadmin créé (via seed_user)
- [ ] Premier login réussit
- [ ] Cabinet configuré (logo, adresse, téléphone)
- [ ] Au moins 1 patient test créé
- [ ] Au moins 1 document test généré (ordonnance/certificat)

**Backup & Restore :**
- [ ] Backup DB fonctionne (`backup_db.py`)
- [ ] Backup média fonctionne (`backup_media.py`)
- [ ] Restore testé sur DB isolée (jamais vraie DB)
- [ ] Comptages identiques source/restore
- [ ] Procédure rollback imprimée et accessible

**Multi-postes (si applicable) :**
- [ ] Machine cabinet : IP fixe configurée
- [ ] ALLOWED_ORIGINS mis à jour dans .env
- [ ] Au moins 1 poste secondaire accède au cabinet via LAN
- [ ] PWA ajoutée à téléphone/autres appareils

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
ALLOWED_ORIGINS=http://192.168.1.100:8005
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
- refuse de démarrer si `DATABASE_URL` contient `digitalcrown_db`
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
cible est `digitalcrown_db` ou si `ENVIRONMENT` n'est pas
rehearsal/test/development. Il crée un owner cabinet avec `role=DENTISTE`
(jamais `ADMIN` global — le seul superadmin global reste
`benmoussa.achraf@gmail.com` sur `digitalcrown_db`).

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
- vérifier que la DB affichée n'est pas `digitalcrown_db`
- vérifier que `MEDIA_ROOT` affiché contient `install_rehearsal_media`
- lancer les deux backups en `--dry-run` avec `DIGITALCROWN_ENV_FILE`
- générer un document de test et confirmer qu'aucun fichier nouveau n'apparaît
  dans `%APPDATA%/DigitalCrown/media`

### Piège DATABASE_URL/CABINET_MASTER_KEY_HEX dans les scripts backup/restore

`backup_db.py`, `backup_media.py` et `restore_db.py` appellent
`load_backend_env(override=True)` **sans condition d'environnement**
(contrairement à `main.py`, qui protège les variables déjà injectées via
`override=False` en premier). Si `backend/.env.local` définit
`DATABASE_URL=...digitalcrown_db`, lancer ces scripts avec seulement des
variables exportées dans le shell **ne suffit pas** — le script écrasera
silencieusement `DATABASE_URL` par celui du vrai cabinet.

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
