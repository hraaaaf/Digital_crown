# Digital Crown — SANINOVA Edition
## *Plateforme de gestion dentaire & orthodontique — Local-First, Production-Ready*

![Version](https://img.shields.io/badge/Version-v4.0_hardened-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Backend-FastAPI_0.110-green?style=for-the-badge&logo=fastapi)
![React](https://img.shields.io/badge/Frontend-React_19_TypeScript-61DAFB?style=for-the-badge&logo=react)
![Database](https://img.shields.io/badge/Database-PostgreSQL_18.2-336791?style=for-the-badge&logo=postgresql)
![AI](https://img.shields.io/badge/IA-Ollama_Local--First-orange?style=for-the-badge)
![Security](https://img.shields.io/badge/Security-Hardened_S0--S9-red?style=for-the-badge)

---

## Vue d'ensemble

Digital Crown est une application de gestion de cabinet dentaire et orthodontique **multi-tenant**, déployée en local (réseau LAN du cabinet). Elle gère des données patients réelles (197+ patients en production), couvre le cycle clinique complet — agenda, dossiers, céphalométrie, panoramique, ordonnances, comptabilité — et expose une API REST sécurisée pour une app mobile compagnon (PWA + native).

> **Base de données active** : PostgreSQL 18.2 `digitalcrown_db` (localhost)  
> **Environnement** : `ENVIRONMENT=development` sur le poste du praticien  
> **Pas de cloud** : toutes les données cliniques restent sur la machine du cabinet
> **Firebase** : licence/identité uniquement — jamais patients/documents/données cliniques

**🔒 Doctrine base de données :**
- ✅ PostgreSQL 15+ obligatoire pour toute installation cabinet/client
- ✅ SQLite réservé aux tests/développement (jamais production)
- ✅ Firebase gère uniquement la licence et l'authentification
- ❌ Zéro donnée patient ou clinique dans le cloud

---

## Architecture technique

```
Backend  FastAPI :8005     →  PostgreSQL 18.2 (digitalcrown_db)
                            →  SQLAlchemy ORM (multi-tenant employer_id)
                            →  ReportLab (PDF génération Elite)
                            →  ONNX YOLO11x (analyse panoramique)
                            →  Ollama local-first (LLM, fallback cloud opt-in)
                            →  Firebase (push FCM mobile uniquement)

Frontend React/Vite :5173  →  Zustand (état global)
                            →  Axios (API client, refresh JWT auto)
                            →  Framer Motion + TailwindCSS
                            →  Vite PWA (Service Worker offline)

Mobile (PWA LAN)           →  App compagnon sur réseau local
                            →  ZKA : appairage ECDH P-256, masterKey jamais en clair
```

### Multi-tenant
Toutes les données cliniques sont isolées par `employer_id`. Chaque requête vérifie l'appartenance via `assert_patient_access(patient_id, user, db)`. Aucun fichier patient n'est accessible sans authentification JWT.

---

## Modules fonctionnels

### Agenda & Patients
- Agenda multi-praticien avec gestion des statuts RDV
- Dossiers patients complets (anamnèse, actes, prescriptions, documents)
- Scoring patient (prédiction no-show, B1/B3/B4/B5)
- Ghost Hub proactif : alertes cliniques quotidiennes (traitements abandonnés, suivi post-extraction, etc.)

### Studio Céphalométrique (Step 1→4)
- **Étape 1** : Upload radio + placement landmarks (36 points requis) + calibration mm/px
- **Étape 2** : Examen occlusal (classe molaire/canine, type d'arcade)
- **Étape 3** : Calcul automatique SNA/SNB/ANB/IMPA/I-Francfort/Inter-incisif/Nasolabial (3 analyses : COM / Steiner / Tweed) + diagnostic textuel
- **Étape 4 (M3)** : Interface structurée en 4 sections — synthèse angles (7 cards code couleur), checklist validation live, plan de traitement, 3 boutons (Prévisualiser / Brouillon PDF / Valider & Archiver)
- **CephaloConsistencyValidator** : validation clinique avant PDF — erreurs fatales bloquantes (bornes physiologiques, SNA-SNB≠ANB, contradiction de classe) + warnings non-bloquants
- **Endpoint** `GET /patients/{id}/cephalo-validation` pour pré-validation frontend

### Panoramique ELITE
- **IA** : ONNX YOLO11x — détecte les dents uniquement (0 pathologie auto-diagnostiquée)
- **Annotation manuelle** : taxonomie clinique (Endo, Paro, Chirurgie, Prothèse, dent_absente, appareil) + constats généraux (lyse, parodontite, édentement)
- **Bilan 100% déterministe** sans LLM : phrases cliniques, CCAM, conduite à tenir, normalité conditionnelle
- **Preview + édition** : visualisation et modification ligne par ligne avant archivage

### CrownBot — Assistant Conversationnel IA
- Intent parser hybride (regex + Ollama fallback)
- **Pending actions server-side** : le LLM propose → action stockée en DB avec UUID + TTL 30 min → seul l'UUID est renvoyé au client → exécution uniquement sur confirmation avec UUID
- Action dispatcher : prise de RDV, fiche patient, solde, ouverture ordonnance/devis
- Contexte LLM anonymisé (data_sanitizer) — aucune PII dans le prompt

### Document Studio
- **Ordonnances** : protocoles rapides, suggestion IA, architecture galénique, QR e-verify
- **Devis / Honoraires** : odontogramme FDI SVG, archivage anti-doublon SHA-256
- **Échéancier** : plan de paiement A5, statuts CheckBox, rappels WhatsApp
- **Bilan orthodontique** : PDF Elite avec disclaimer praticien obligatoire

### Comptabilité & Finance
- Tableau de bord recettes/dépenses, trésorerie, projection mensuelle
- Forecast semaine (C1), taux de conversion devis (C4)
- Export PDF comptable

### Équipe & Plans d'abonnement
| Plan | Dentistes | Assistantes |
|------|-----------|-------------|
| GOLD | 1 (owner) | 2 |
| PREMIUM | 2 | 6 |
| ELITE | Illimité | Illimité |

- Workflow d'approbation : création → `PENDING` (login bloqué) → `APPROVED/REJECTED` par le praticien propriétaire
- `GET /team/quota` · `POST /team/{id}/approve` · `POST /team/{id}/reject`

### App Mobile (ZKA)
- Appairage QR : ECDH secp256r1 → masterKey chiffrée AES-256-GCM (jamais en clair sur le réseau)
- Cockpit : agenda, performance, finance, labo, sécurité
- Push FCM, offline queue (Workbox Background Sync)

---

## Sécurité (Sprint S0–S9)

| Domaine | Mesure |
|---------|--------|
| **Télémétrie** | `TELEMETRY_ENABLED=False` par défaut — opt-in explicite |
| **Fichiers patients** | Auth JWT obligatoire sur toutes les routes `/uploads/`, `/archives/`, `/documents/` |
| **Cross-tenant** | `assert_patient_access` sur chaque endpoint patient · guard `_assert_media_tenant` sur les routes statiques |
| **Permissions** | RBAC 9 permissions · fail-closed sur type inconnu · guards serrés sur prescriptions/actes/accounting/cephalo |
| **Cloud IA** | `CLOUD_AI_ENABLED=False` par défaut · AI Gateway (`ai_gateway.py`) local-first avec résolution d'URL d'egress |
| **ZKA Mobile** | ECDH P-256 + HKDF-SHA256 + AES-256-GCM · masterKey jamais en clair · `get_mobile_role` fail-closed |
| **Bot** | Pending actions en DB (UUID + TTL) · tenant-check avant exécution · allowlist d'actions explicite |
| **Audit** | `AuditLog` par cabinet (employer_id) · EXPORT_DB/MOBILE_PAIRING/BOT_EXECUTE tracés |
| **Prod gate** | `prod_safety_check.py` + CI GitHub Actions · invariants fail-fast au démarrage |

---

## Migrations disponibles

```bash
# Table pending actions bot
python scripts/migrate_bot_pending_actions.py

# Colonnes plans / approbation équipe
python scripts/migrate_m1_subscription_plans.py

# Contrainte unique multi-tenant numero_dossier
python scripts/migrate_p04_numero_dossier_tenant.py

# Audit read-only (baseline counts)
python scripts/preflight_data_audit.py

# Vérification config production
python scripts/prod_safety_check.py
```

Toutes les migrations sont **idempotentes** et vérifient `count_before == count_after` (patients, documents).

---

## Installation & Démarrage

### Prérequis
- Python 3.11+ avec `venv`
- PostgreSQL 18.2 (base `digitalcrown_db`)
- Node.js 20+ / npm
- Ollama (LLM local, modèle `llama3.2` recommandé)

### Démarrage rapide (Windows)
```powershell
./Start_DigitalCrown.bat
```

### Développement manuel
```bash
# Backend
venv\Scripts\activate
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8005

# Frontend (autre terminal)
cd frontend && npm run dev
```

### Variables d'environnement clés (`.env`)
```env
DATABASE_URL=postgresql://user:password@localhost/digitalcrown_db
SECRET_KEY=<clé 32+ caractères aléatoires>
ENVIRONMENT=development        # production active les fail-fast guards
TELEMETRY_ENABLED=false
CLOUD_AI_ENABLED=false         # opt-in cloud LLM
OLLAMA_URL=http://localhost:11434
```

### Accès
| Service | URL |
|---------|-----|
| Application | `http://localhost:5173` |
| API + Swagger | `http://localhost:8005/docs` |
| Mobile (LAN) | `http://<ip-locale>:5173` |

---

## Tests & CI

```bash
# Commandes frontend officielles depuis la racine
npm test
npm run build

# Suite de tests backend
pytest backend/tests/

# Vérification TypeScript frontend
cd frontend && npx tsc --noEmit

# Équivalents directs frontend
npm --prefix frontend test
npm --prefix frontend run build

# Gate de sécurité production
python scripts/prod_safety_check.py
```

Pipeline CI (`.github/workflows/ci.yml`) : install → prod_safety_check → pytest → test négatif garde prod.

---

## Contraintes non-négociables (données patients)

- Ne **jamais** supprimer / réinitialiser / recréer des données patients
- Ne **jamais** dropper la table `patients` ni régénérer `numero_dossier`
- Toute migration : `count_before == count_after` prouvé par `preflight_data_audit.py`
- Backend = seule autorité · Frontend = non fiable · LLM = non fiable (capsule confinée)
- Aucune sortie IA clinique sans validation praticien
- `masterKey` jamais en clair sur le réseau

---

## Équipe & Version

**Staff Engineering — Digital Crown SANINOVA**  
*Dernière mise à jour : 17 Juin 2026 — v4.0 hardened (S0–S9 + M1/M2/M3/M4 cephalo + panoramique déterministe)*
