# Digital Crown — Runbook Pré-production

Document opérationnel minimal pour exploiter, surveiller, sauvegarder et
revenir en arrière sur l'environnement pré-production.

---

## 1. Health checks

| Route | Usage |
|---|---|
| `GET /api/health` | Statut global : `status`, `database`, `environment`, `version` (hash git court), `timestamp` |
| `GET /api/health/db` | Vérifie uniquement la connexion DB (`SELECT 1`) |
| `GET /api/health/storage` | Vérifie que le dossier média est accessible en écriture |
| `GET /health` | Health check historique (conservé pour compatibilité, ne pas retirer) |

```bash
curl -s http://<host>:<port>/api/health
```

Réponse HTTP 200 si `database == "ok"`, 503 sinon (dégradé).

---

## 2. Logs applicatifs et sécurité

Tous les événements sensibles passent par `audit_service.log()` (table `audit_logs` :
`timestamp`, `user_id`, `employer_id`, `action`, `resource_type`, `resource_id`, `severity`, `details`).

### Événements couverts

| Événement | Action loggée | Fichier |
|---|---|---|
| Connexion réussie | `LOGIN_SUCCESS` | `routers/auth.py` |
| Connexion échouée | `LOGIN_FAIL` | `routers/auth.py` |
| Accès média refusé (cross-tenant) | `MEDIA_ACCESS_DENIED` / `ACCESS_DENIED` | `main.py::_assert_media_tenant`, `utils/access_control.py` |
| Accès média accordé | `MEDIA_ACCESS_GRANTED` | `routers/documents.py::download_document` |
| Demande Frontdesk créée | `FRONTDESK_REQUEST_CREATED` | `routers/frontdesk.py` |
| Confirmation Frontdesk demandée | `FRONTDESK_CONFIRMATION_REQUESTED` | `routers/frontdesk.py` |
| RDV Frontdesk confirmé | `FRONTDESK_APPOINTMENT_CONFIRMED` | `routers/frontdesk.py` |
| RDV Frontdesk refusé | `FRONTDESK_APPOINTMENT_REJECTED` | `routers/frontdesk.py` |
| RDV Frontdesk expiré | `FRONTDESK_APPOINTMENT_EXPIRED` | `routers/frontdesk.py` |
| RVG uploadée | `RVG_UPLOAD` | `routers/documents.py` |
| Document générique uploadé | `DOCUMENT_UPLOADED` | `routers/documents.py::archive_document` |
| Action Crown Bot exécutée | `BOT_EXECUTE` (severity INFO) | `routers/bot.py` |
| Action Crown Bot rejetée (409/410/403) | `CROWN_BOT_ACTION_REJECTED` | `routers/bot.py` |
| PDF céphalo bloqué (données incohérentes) | `CEPHALO_PDF_BLOCKED` | `routers/documents.py::generate_patient_report` |
| PDF céphalo généré | `CEPHALO_PDF_GENERATED` | `routers/documents.py::generate_patient_report` |

### Ne jamais logger

Mot de passe, token JWT complet, `CABINET_MASTER_KEY_HEX`, `masterKey` ZKA,
contenu complet d'un document/radio, toute donnée médicale au-delà de l'ID
de ressource nécessaire au diagnostic.

### Consulter les logs

```sql
SELECT timestamp, user_id, employer_id, action, resource_type, resource_id, severity, details
FROM audit_logs
WHERE severity IN ('WARNING', 'ERROR')
ORDER BY timestamp DESC
LIMIT 100;
```

Filtrer par cabinet en cas d'incident signalé par un client :

```sql
SELECT * FROM audit_logs WHERE employer_id = <id_cabinet> ORDER BY timestamp DESC LIMIT 50;
```

---

## 3. Backups

### DB PostgreSQL (chiffrée, Fernet dérivé de `CABINET_MASTER_KEY_HEX`)

```bash
python -m backend.scripts.backup_db
# -> backend/backups/backup_<timestamp>.sql.enc
```

### Média (radios, RVG, documents archivés — chiffré)

```bash
python -m backend.scripts.backup_media
# -> backend/backups/media_backup_<timestamp>.zip.enc
```

**Avant tout backup** : vérifier l'espace disque disponible (`Get-PSDrive C`
sous Windows / `df -h` sous Linux). Un backup média peut représenter
plusieurs centaines de Mo selon le nombre de radios/RVG stockées.

### Restore DB

```bash
python -m backend.scripts.restore_db backend/backups/backup_<timestamp>.sql.enc --yes
```

⚠️ **Destructif** — écrase la base ciblée par `DATABASE_URL`. Toujours faire
un `backup_db.py` de l'état actuel juste avant de restaurer, même en cas
d'urgence.

### Restore média

Pas de script dédié (volume + complexité chiffrement ne le justifient pas
pour l'instant) — procédure manuelle :

```bash
python -c "
from backend.scripts.backup_db import get_cipher
cipher = get_cipher()
data = cipher.decrypt(open('backend/backups/media_backup_<timestamp>.zip.enc', 'rb').read())
open('restored_media.zip', 'wb').write(data)
"
# Puis dézipper restored_media.zip dans %APPDATA%/DigitalCrown/media
# (sauvegarder l'ancien dossier média avant d'écraser)
```

---

## 4. Checklist rollback

Ne jamais faire de rollback automatique. Toujours suivre ces étapes dans l'ordre :

1. **Identifier le commit déployé actuellement**
   ```bash
   curl -s http://<host>/api/health | grep version
   # ou directement sur le serveur : git rev-parse --short HEAD
   ```
2. **Identifier le dernier commit stable connu** (`git log --oneline -20`,
   se référer au dernier tag/commit validé par une session GO pré-prod)
3. **Sauvegarder DB et média AVANT tout rollback**
   ```bash
   python -m backend.scripts.backup_db
   python -m backend.scripts.backup_media
   ```
4. **Rollback de l'application**
   ```bash
   git checkout <commit_stable>
   # redéployer / relancer le service applicatif
   ```
5. **Vérifier que les migrations ne sont pas destructives dans le sens du
   rollback** — `create_all()` ne supprime jamais de colonnes/tables ; un
   rollback vers un commit antérieur peut laisser des colonnes/enum ajoutées
   par une version plus récente encore présentes en DB (inoffensif, juste
   inutilisées). Ne JAMAIS `DROP` manuellement une colonne/table pour
   "nettoyer" après un rollback sans vérifier qu'aucune donnée réelle n'y est
   stockée.
6. **Relancer les smoke tests** (section 5 ci-dessous)
7. **Vérifier les logs d'erreur** post-rollback :
   ```sql
   SELECT * FROM audit_logs WHERE severity = 'ERROR' AND timestamp > NOW() - INTERVAL '10 minutes';
   ```

---

## 5. Smoke tests post-déploiement

Checklist courte à exécuter après CHAQUE déploiement (pré-prod ou prod) :

| # | Test | Attendu |
|---|---|---|
| 1 | Login cabinet | 200 + access_token |
| 2 | Liste patients | 200 |
| 3 | Dossier patient | 200 |
| 4 | Upload/lecture document | 200 (upload) + 200 (download) |
| 5 | Upload/lecture RVG | 200 (upload) + 200 (download) |
| 6 | Frontdesk créer → confirmer | `EN_ATTENTE_DEMANDE` → `CONFIRMÉ` |
| 7 | Crown Bot `pending_action_id` only | 422 si champ extra, 404 si ID inconnu |
| 8 | Céphalo pré-bilan + blocage incohérent | 422 sur données hors bornes |
| 9 | Panoramique — auth requise | 401 sans token |
| 10 | Accès anonyme média | 401 sur toutes les routes documents/RVG |

Ces 10 points ont été exécutés en live lors de PREPROD-DEPLOY-1 (10/10 PASS)
contre une base PostgreSQL fraîche créée à partir de zéro — la procédure est
reproductible.

---

## 6. Seed cabinet démo

```bash
python -m backend.seed_demo
```

- **Idempotent** : relancer ne recrée rien si le cabinet démo existe déjà
  (vérifié par email du dentiste).
- **Ne supprime rien, ne modifie aucun cabinet réel** (crée uniquement de
  nouveaux enregistrements, jamais de update/delete sur l'existant).
- Crée : 1 cabinet, 1 dentiste (compte principal), 1 assistante (sous-compte
  lié via `employer_id`).

**Identifiants de test (démo uniquement, ne jamais utiliser en prod réelle) :**

```
Cabinet    : Cabinet Dentaire Digital Crown — Démo
Dentiste   : demo.dentiste@digitalcrown.ma / DemoCrown2026!
Assistante : demo.assistante@digitalcrown.ma / DemoCrown2026!
```

Un script similaire pré-existant, `backend/scripts/seed_demo_mo.py`, seed un
autre cabinet démo (`mo@digitalcrown.com`) avec des données patients/RDV
d'exemple plus étoffées — les deux coexistent sans conflit (comptes distincts).

---

## 7. Points de vigilance connus

- **Espace disque** : vérifier avant tout backup média (peut représenter
  plusieurs centaines de Mo).
- **`load_backend_env(override=True)`** : `backend/.env.local` écrase
  toujours les variables d'environnement déjà présentes dans le shell/l'OS
  au démarrage. Un déploiement via variables d'environnement injectées par
  un orchestrateur (Docker/systemd/k8s secrets) serait silencieusement
  ignoré si un fichier `.env.local` traîne dans l'image — à vérifier avant
  un déploiement remote réel.
- **`CephaloPDFRequest.archive`** : champ de schéma présent mais jamais lu
  par la route — aucun impact actuel (non appelé par le frontend), mais à
  garder en tête si quelqu'un l'utilise un jour en supposant qu'il archive
  le PDF généré.
