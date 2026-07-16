# Architecture — Digital Crown

> Dernière mise à jour : 2026-07-14 (arborescence complète régénérée depuis le dépôt réel)
> Branche active : `master`
>
> L'arborescence ci-dessous a été vérifiée fichier par fichier le 2026-07-14
> (routers, services, schemas, scripts, tests backend ; components, features,
> pages, services, stores, hooks, data frontend). Deux raccourcis Windows
> parasites (`features - Raccourci*.lnk` dans `frontend/src/`, `services -
> Raccourci.lnk` dans `backend/`) et un dossier vide résiduel
> (`backend/ai_models/dentex/`) existent sur le disque mais sont volontairement
> omis ci-dessous (junk non versionné/non utilisé). Les scripts ponctuels de
> debug/migration à la racine de `backend/` (`seed_*.py`, `migrate_*.py`,
> `alter_db.py`, `download_fonts*.py`, `test_sanitizer.py`) sont résumés par
> catégorie plutôt qu'énumérés un par un.

---

## Stack technique

| Couche | Technologie |
|---|---|
| **Backend** | FastAPI (Python 3.11+), SQLAlchemy ORM, Alembic migrations, ReportLab PDF |
| **Base de données** | **PostgreSQL 15+** (obligatoire production) — SQLite réservé aux tests/dev |
| **Frontend** | React 19 + TypeScript, Vite, TailwindCSS, Zustand, Framer Motion, Recharts |
| **Mobile** | PWA (Progressive Web App) + Service Worker offline-first |
| **IA / ML** | ONNX Runtime (panoramique), Ollama/LLM local (ordonnances, bot), CephMark (céphalo) |
| **Auth** | JWT (access + refresh token), OAuth2 Google, Zero-Knowledge Architecture (ZKA) |
| **PDF** | ReportLab (backend), LibreOffice headless (fallback) |
| **Desktop** | PyInstaller (DigitalCrown.exe) + Tauri (expérimental) |
| **CI/Déploiement** | ecosystem.config.js (PM2), Dockerfile |

---

## 🗄️ Doctrine Base de Données

**Deux modes de production légitimes (`ENVIRONMENT`, voir `CLAUDE.md`) :**
- ✅ **Cabinet solo** (`ENVIRONMENT=cabinet`) : SQLite/SQLCipher chiffré
  AES-256 local — c'est le mode de l'installeur un clic
  (`installer/DigitalCrown.iss`), zéro serveur DB externe à installer
- ✅ **Cabinet multi-postes** (`ENVIRONMENT=cabinet` ou `production`) :
  PostgreSQL 15+, une DB + un utilisateur PostgreSQL dédié par cabinet
  (jamais le superuser `postgres`)
- ❌ `ENVIRONMENT=production` refuse SQLite (PostgreSQL obligatoire dans ce
  mode précis) — mais `production` n'est pas le seul mode de prod légitime,
  voir `cabinet` ci-dessus
- ❌ SQLite **non chiffré** (`ENVIRONMENT=development/local/test`) reste
  réservé aux tests unitaires et au développement local, jamais un cabinet réel

**Firebase (optionnel, hors-ligne supporté) :**
- ✅ Gère : licence, identité cabinet, abonnement, grâce hors-ligne
- ❌ Ne stocke jamais : patients, documents, radios, ordonnances, agenda, actes, données cliniques

---

## Arborescence complète

```
DigitalCrown/
├── .gitignore
├── alembic.ini                        # Config migrations Alembic
├── clinical_vault.db                  # DB clinique (vault chiffré)
├── digital_crown.db                   # Base SQLite principale
├── DigitalCrown.spec                  # Spec PyInstaller (build .exe)
├── Dockerfile                         # Image Docker production
├── ecosystem.config.js                # Config PM2 (process manager prod)
├── migrate.py                         # Script migration ponctuel
├── package.json                       # Scripts npm racine (run frontend)
├── pytest.ini                         # Config tests Python
├── README.md
├── requirements.txt                   # Dépendances Python racine
├── restore_cabinet.py                 # Outil restauration données cabinet
├── run.py                             # Point d'entrée dev (uvicorn + vite)
├── SESSION.md                         # Suivi de session en cours
├── Start_DigitalCrown.bat             # Lanceur Windows dev
├── Start_PROD.bat                     # Lanceur Windows production
├── STATE.md                           # État courant du sprint
│
├── .vscode/
│   └── settings.json
│
├── alembic/                           # Migrations de schéma DB (jamais auto-appliquées, voir CLAUDE.md)
│   ├── env.py
│   ├── script.py.mako
│   └── versions/                      # 6 migrations (+ __pycache__), ex. :
│       ├── 0ac66fa0bdb8_remove_color_ref_and_init_lab_jobs.py
│       ├── 2872d2ae6349_add_superadmin_features.py
│       ├── 74e675197637_add_medical_library_models.py
│       ├── 8f6465e49d90_sync_db_and_models_after_god_file_split_.py
│       ├── a1b2c3d4e5f6_add_user_id_to_bot_sessions.py
│       └── b2c3d4e5f6a7_add_patient_id_to_bot_sessions.py
│
├── artifacts/                         # Sorties de tests / docs générés
│
├── backend/                           # API FastAPI
│   ├── __init__.py
│   ├── config.py                      # Settings (env, chemins, flags)
│   ├── database.py                    # Engine SQLAlchemy + session
│   ├── env_loader.py                  # load_backend_env() — override=False, sauf dev/local/test
│   ├── main.py                        # App FastAPI, montage des routers
│   ├── models.py                      # Tous les modèles ORM SQLAlchemy
│   ├── security.py                    # JWT, hashing, dépendances auth
│   ├── requirements.txt               # Dépendances Python backend
│   │
│   │   # Scripts ponctuels de debug/migration/seed à la racine (non organisés en
│   │   # module) — alter_db.py, download_fonts.py, download_fonts_from_css.py,
│   │   # migrate_patients.py, migrate_scheduling.py, seed.py, seed_catalog.py,
│   │   # seed_clinical.py, seed_clinical_rules.py, seed_demo.py,
│   │   # seed_medical_library.py, seed_presets.py, seed_templates.py, seed_user.py,
│   │   # test_sanitizer.py
│   │
│   ├── .env                           # Variables d'environnement (ignoré git)
│   ├── .env.development
│   ├── .env.example
│   │   # + .env.local, .env.install_test, .env.treatment-journey-rehearsal
│   │   # (ignorés git, présents localement pour des scénarios de test spécifiques)
│   │
│   ├── ai_models/                     # Modèles ML embarqués (~1,9 Go réel — voir DigitalCrown.spec)
│   │   ├── audit_model.py             # Wrapper audit ONNX
│   │   ├── best.onnx                  # Modèle céphalo landmarks ONNX (chargé au runtime)
│   │   ├── best.pt                    # Modèle céphalo landmarks PyTorch (chargé au runtime)
│   │   ├── panoramic_model.onnx       # Modèle panoramique ONNX (chargé au runtime)
│   │   ├── panoramic_model.pt         # Modèle panoramique PyTorch (chargé au runtime)
│   │   ├── panoramic_model.pth
│   │   └── cephld_cca/                # Repo vendored RÉELLEMENT utilisé (vision_service.py
│   │       │                         # y injecte sys.path pour importer U_Net_w_Cartesian_SE)
│   │       ├── ceph_weights.pth       # Seul poids réellement chargé (35 Mo)
│   │       ├── models/                # Code source du modèle (nécessaire à l'import)
│   │       └── model/                 # ⚠️ 774 Mo de checkpoints d'entraînement jamais
│   │                                 # chargés — exclu du packaging EXE (DigitalCrown.spec)
│   │
│   │   # Dossiers vendored NON utilisés au runtime (vérifiés par grep, zéro
│   │   # référence dans backend/services|routers), exclus du packaging EXE
│   │   # mais toujours présents dans le dépôt Git — voir le commentaire en
│   │   # tête de DigitalCrown.spec pour le détail de chaque vérification :
│   │   # CLdetection2023-master/, dentex_repo/, CL-Detection2023/,
│   │   # cephalometric-master/, cephmark/
│   │
│   ├── core/
│   │   ├── media_paths.py             # Résolution chemins médias, isolation runtime réel/rehearsal
│   │   └── paths.py                   # AppPaths : résolution chemins AppData/media
│   │
│   ├── data/
│   │   └── medications_ma.json        # Référentiel national médicaments (CNOPS, Open Data)
│   │
│   ├── deprecated/                    # Scripts de migration/debug archivés
│   │
│   ├── repositories/
│   │   └── cephalo_repository.py      # Accès données analyses céphalométriques
│   │
│   ├── routers/                       # Points d'entrée API REST
│   │   ├── __init__.py
│   │   ├── accounting.py              # /accounting — recettes, dépenses, caisse
│   │   ├── admin.py                   # /admin — dashboard stats, cabinet
│   │   ├── agenda_settings.py         # /agenda/settings — config créneaux
│   │   ├── ai_feedback.py             # /ai/feedback — feedback modèles IA
│   │   ├── analytics.py               # /analytics — KPIs avancés
│   │   ├── appointments.py            # /appointments — RDV agenda
│   │   ├── auth.py                    # /auth — login, refresh, logout, Google OAuth
│   │   ├── bot.py                     # /bot — CrownBot chat (intent + LLM)
│   │   ├── catalog.py                 # /catalog — catalogue actes dentaires
│   │   ├── clinical.py                # /clinical — dossier clinique patient
│   │   ├── clinical_data.py           # /clinical/data — données de référence
│   │   ├── clinics.py                 # /clinics — gestion multi-cabinet
│   │   ├── documents.py               # /documents — génération PDF (devis, honoraires…)
│   │   ├── frontdesk.py               # /frontdesk — demandes de RDV accueil (FRONTDESK-AGENDA-MVP-1)
│   │   ├── ia.py                      # /ia — analyses IA (panoramique, céphalométrie)
│   │   ├── installments.py            # /installments — plans de paiement échelonné
│   │   ├── intelligence.py            # /intelligence — moteur règles cliniques
│   │   ├── lab_jobs.py                # /lab — travaux laboratoire
│   │   ├── medical_library.py         # /library — bibliothèque médicale
│   │   ├── medications.py             # /medications — dictionnaire national médicaments (Maroc)
│   │   ├── mobile.py                  # /mobile — endpoints dédiés PWA mobile
│   │   ├── patients.py                # /patients — CRUD patients
│   │   ├── prescriptions.py           # /prescriptions — ordonnances
│   │   ├── public.py                  # routes publiques sans auth — landing page, demandes démo
│   │   ├── stats.py                   # /stats — statistiques cabinet
│   │   ├── stock.py                   # /stock — inventaire consommables cabinet
│   │   ├── superadmin.py              # /superadmin — gestion multi-tenant
│   │   ├── team.py                    # /team — membres équipe cabinet
│   │   ├── templates.py               # /templates — modèles de documents
│   │   └── verification.py            # /verification — vérification licences
│   │
│   ├── schemas/                       # Pydantic schemas (validation I/O)
│   │   ├── __init__.py
│   │   ├── agenda.py
│   │   ├── appointments.py
│   │   ├── auth.py
│   │   ├── base.py
│   │   ├── bot.py                     # Schemas requêtes/réponses CrownBot (execute action)
│   │   ├── branding.py
│   │   ├── cabinet.py
│   │   ├── catalog.py
│   │   ├── clinical.py
│   │   ├── documents.py
│   │   ├── installments.py
│   │   ├── journey.py                 # Schemas Treatment Journey (MilestoneType, timeline)
│   │   ├── panoramic.py
│   │   ├── patient.py
│   │   ├── payments.py
│   │   ├── rvg.py                     # Schemas upload/affichage RVG (radio intra-orale)
│   │   └── superadmin.py
│   │
│   ├── services/                      # Logique métier
│   │   ├── __init__.py
│   │   ├── accounting_service.py      # KPIs financiers, soldes, caisse
│   │   ├── acte_classification.py     # Classification libellé facturé → ActeType (fonction pure)
│   │   ├── ai_advisor.py              # Conseils IA cliniques contextuels
│   │   ├── ai_coherence.py            # Vérification cohérence IA
│   │   ├── ai_gateway.py              # Point de contrôle unique sorties LLM (local-first, egress IA)
│   │   ├── anonymizer.py              # Anonymisation données patients (RGPD)
│   │   ├── archive_service.py         # Archivage documents générés
│   │   ├── audit_service.py           # Audit sécurité et accès
│   │   ├── backup_service.py          # Sauvegardes automatiques DB (routage par moteur actif)
│   │   ├── base_template.py           # Template ReportLab de base (entête cabinet)
│   │   ├── bilan_ortho_engine.py      # Moteur bilan orthodontique
│   │   ├── calibration_service.py     # Calibration images radio (px→mm)
│   │   ├── card_extractor.py          # Extraction carte CIN/assurance
│   │   ├── cephalo_consistency_validator.py # Validateur cohérence céphalo (FATAL/WARNING) avant PDF
│   │   ├── cephalo_engine.py          # Pipeline détection landmarks céphalo
│   │   ├── cephalo_measure_registry.py # Source unique de vérité unités métriques céphalo
│   │   ├── cephalo_service.py         # Service céphalométrie (VTO, analyses)
│   │   ├── clinical_coherence.py      # Règles cohérence clinique
│   │   ├── clinical_intelligence.py   # Intelligence clinique (suggestions)
│   │   ├── clinical_rules_engine.py   # Moteur règles QCM/protocoles
│   │   ├── cmo_agent_service.py       # Agent CMO (Chief Medical Officer IA)
│   │   ├── css_generator.py           # Génération CSS dynamique branding
│   │   ├── daily_scheduler.py         # Tâches planifiées journalières
│   │   ├── document_factory.py        # Factory de génération PDF
│   │   ├── elite_manager.py           # Gestion features Elite / licence
│   │   ├── email_service.py           # Envoi emails SMTP (notifications, demandes démo)
│   │   ├── file_validator.py          # Validation fichiers uploadés
│   │   ├── firebase_sync_service.py   # Sync Firebase (multi-device)
│   │   ├── fts_indexer.py             # Full-text search SQLite FTS5
│   │   ├── ghost_memory_service.py    # Mémoire contextuelle IA (Ghost Brain)
│   │   ├── habits_engine.py           # Moteur habitudes/protocoles cabinet
│   │   ├── holiday_engine.py          # Gestion jours fériés Maroc
│   │   ├── license_service.py         # Validation licence (Firebase + local)
│   │   ├── llm_cache.py               # Cache réponses LLM (Redis-like en mémoire)
│   │   ├── logo_processor.py          # Traitement logo cabinet (recadrage, format)
│   │   ├── medication_dict.py         # Dictionnaire national médicaments (référentiel CNOPS)
│   │   ├── notification_service.py    # Notifications push (FCM)
│   │   ├── panoramic_ai_advisor.py    # Conseiller IA panoramique
│   │   ├── panoramic_expert_engine.py # Moteur expert interprétation panoramique
│   │   ├── panoramic_report_engine.py # Génération rapport panoramique
│   │   ├── panoramic_service.py       # Service orchestration panoramique
│   │   ├── panoramic_vision_service.py# Vision ONNX inference panoramique
│   │   ├── patient_journey_service.py # Agrégation lecture seule parcours patient (9 sources)
│   │   ├── patient_scoring_service.py # Score risque patient
│   │   ├── pii_masker.py              # Masquage PII dans logs/LLM
│   │   ├── prescription_agentic_service.py # Ordonnances IA (agent LLM)
│   │   ├── prescription_service.py    # Génération ordonnances classiques
│   │   ├── push_service.py            # Service push notifications
│   │   ├── qr_service.py              # Génération QR code documents
│   │   ├── rag_context.py             # RAG (retrieval-augmented generation)
│   │   ├── sota_panoramic_service.py  # SOTA pipeline panoramique avancé
│   │   ├── sota_vision_service.py     # SOTA vision service
│   │   ├── state_extractor.py         # Extraction état clinique patient
│   │   ├── sync_manager.py            # Gestionnaire sync multi-device
│   │   ├── telemetry.py               # Télémétrie usage (anonymisée)
│   │   ├── template_engine.py         # Moteur templates documents
│   │   ├── temporal_comparator.py     # Comparaison temporelle analyses
│   │   ├── treatment_plan_engine.py   # Moteur plan de traitement
│   │   ├── vision_service.py          # Service vision générique
│   │   ├── zka_crypto.py              # Cryptographie ZKA (AES-GCM)
│   │   ├── zka_service.py             # Service Zero-Knowledge Architecture
│   │   │
│   │   ├── bot/                       # CrownBot — moteur conversationnel
│   │   │   ├── __init__.py
│   │   │   ├── action_dispatcher.py   # Dispatch actions selon intent
│   │   │   ├── intent_parser.py       # Parser d'intentions (regex + LLM)
│   │   │   ├── intents_config.py      # Configuration des intents
│   │   │   ├── knowledge_base.py      # Base de connaissances cabinet
│   │   │   └── llm_parser.py          # Parser LLM (Ollama)
│   │   │
│   │   ├── generators/                # Générateurs PDF ReportLab
│   │   │   ├── accounting_gen.py      # Note comptable / journal de caisse
│   │   │   ├── bilan_gen.py           # Bilan clinique général
│   │   │   ├── bilan_ortho_gen.py     # Bilan orthodontique complet
│   │   │   ├── cephalo_gen.py         # Rapport céphalométrique
│   │   │   ├── certificat_gen.py      # Certificat médical
│   │   │   ├── document_layout_safety.py # join_unbreakable(), protect_unit_patterns()
│   │   │   ├── document_typography.py # Constantes taille (TITLE_SIZE, PRESCRIPTION_*…)
│   │   │   ├── installment_gen.py     # Plan de paiement échelonné (ancienne version)
│   │   │   ├── installment_receipt_gen.py # Reçu/aperçu échéancier (A5, ReportLab)
│   │   │   ├── libre_gen.py           # Document libre personnalisé
│   │   │   ├── ordonnance_gen.py      # Ordonnance médicale
│   │   │   ├── panoramic_elite_gen.py # Rapport panoramique Elite (multi-page)
│   │   │   ├── panoramic_gen.py       # Rapport panoramique standard
│   │   │   └── report_gen.py          # Rapport générique
│   │   │
│   │   └── security/
│   │       ├── __init__.py
│   │       └── data_sanitizer.py      # Sanitisation entrées (XSS, injection)
│   │
│   ├── scripts/                       # Scripts opérationnels (backup/restore/bootstrap)
│   │   ├── backup_db.py               # Backup DB chiffré (pg_dump PostgreSQL / Fernet)
│   │   ├── backup_media.py            # Backup chiffré dossier média (radios, RVG, archives)
│   │   ├── backup_offsite.py          # Copie best-effort backups déjà chiffrés vers hors-machine
│   │   ├── bootstrap_new_cabinet.py   # Bootstrap nouveau cabinet + admin propriétaire
│   │   ├── count_records.py           # Comptage enregistrements avant/après sécurisation médias
│   │   ├── create_backup_release.ps1  # Release immuable dédiée au backup planifié (git archive)
│   │   ├── create_release.ps1         # Snapshot immuable runtime réel (hors dépôt de travail)
│   │   ├── migrate_qr_style.py        # Migration ponctuelle style QR code
│   │   ├── panoramic_export.py        # Export modèle panoramique (YOLO)
│   │   ├── recover_documents.py       # Récupération documents orphelins depuis clinical_data
│   │   ├── reorganize_archives.py     # Réorganisation structure archives statiques
│   │   ├── restore_db.py              # Restauration backup DB chiffré (jamais sur DB principale sans confirmation)
│   │   ├── run_real_backend.ps1       # Lanceur UNIQUE runtime cabinet réel (jamais --reload)
│   │   ├── run_rehearsal_backend.ps1  # Lanceur backend rehearsal isolé (variables process only)
│   │   ├── run_scheduled_backup.ps1   # Lanceur tâche planifiée Windows (exécute la release backup)
│   │   ├── scheduled_backup.py        # Orchestrateur backup planifié DB+médias (préflight→verrou→retention)
│   │   └── seed_demo_mo.py            # Seed démo cabinet marocain (patients/RDV/actes fictifs)
│   │
│   ├── static/                        # Fichiers statiques servis par FastAPI
│   │   ├── archive/                   # Archives PDF (variante ancienne, par ID)
│   │   ├── archives/                  # Archives PDF par patient/cabinet
│   │   ├── assets/                    # Assets partagés génération PDF (fonts, logo, header_bg)
│   │   ├── backups/                   # Sauvegardes DB
│   │   ├── documents/                 # PDFs générés (non archivés)
│   │   ├── models/                    # Modèles ML statiques
│   │   ├── patients/                  # Dossiers patients (radios, docs)
│   │   ├── reports/                   # Rapports générés
│   │   └── uploads/                   # Fichiers uploadés (logos, radios)
│   │       ├── clinics/
│   │       ├── panoramic/
│   │       └── radios/
│   │
│   ├── templates/                     # Templates HTML (LibreOffice/WeasyPrint, legacy)
│   │   ├── base_elite.html
│   │   ├── bilan_ortho_elite.html
│   │   ├── cephalo_report_elite.html
│   │   ├── certificat_elite.html
│   │   ├── ordonnance_elite.html      # Code mort — aucune référence Python, voir CLAUDE.md
│   │   └── panoramic_elite.html
│   │
│   ├── tests/                         # Suite de tests backend (pytest) — 108 fichiers, ~2200+ tests
│   │   ├── conftest.py                # Fixtures réelles : db, dentiste, auth_headers, client, make_user()
│   │   ├── smoke_test_elite.py
│   │   ├── test_access_control.py
│   │   ├── test_auth.py
│   │   ├── test_frontdesk.py          # Tests router /frontdesk
│   │   ├── test_patients.py
│   │   ├── test_rvg.py                # Tests upload/affichage RVG
│   │   ├── test_scheduled_backup.py   # Tests orchestrateur backup planifié
│   │   ├── test_services_unit2.py … test_services_unit26.py # Suite de tests unitaires services (25 fichiers)
│   │   └── … (voir répertoire pour la liste complète)
│   │
│   └── utils/
│       ├── access_control.py          # Contrôle d'accès RBAC
│       ├── accounting_utils.py        # Helpers calculs comptables
│       └── rate_limit.py              # Rate limiting endpoints sensibles
│
├── build/                             # Build PyInstaller (binaire Windows)
│   └── DigitalCrown/
│       └── DigitalCrown.exe
│
├── certs/                             # Certificats TLS auto-signés (dev HTTPS)
│   ├── cert.pem
│   └── key.pem
│
├── frontend/                          # Application React/TypeScript
│   ├── package.json
│   ├── vite.config.ts                 # Config Vite (proxy → :8005, PWA)
│   ├── tsconfig.app.json
│   ├── postcss.config.js
│   ├── eslint.config.js
│   │
│   ├── src/
│   │   ├── App.tsx                    # Router principal (React Router v6)
│   │   ├── main.tsx                   # Entrée React, providers globaux
│   │   ├── index.css                  # Styles globaux + variables CSS
│   │   │
│   │   ├── components/                # Composants partagés
│   │   │   ├── AnimatedBackground.tsx # Fond animé page login
│   │   │   ├── AppLoader.tsx          # Loader init app (auth check)
│   │   │   ├── AssuranceBadge.tsx     # Badge organisme d'assurance (CNOPS/CNSS/mutuelle)
│   │   │   ├── ComingSoon.tsx         # Placeholder feature à venir
│   │   │   ├── DayOneTour.tsx         # Tour guidé Joyride (premier lancement)
│   │   │   ├── DigitalCrownLoader.tsx # Splash screen chargement
│   │   │   ├── EliteGhostLoader.tsx   # Loader Elite avec Ghost Brain
│   │   │   ├── ErrorBoundary.tsx      # Boundary React erreurs critiques
│   │   │   ├── ErrorBoundary.test.tsx # Tests ErrorBoundary
│   │   │   ├── GhostBrainWidget.tsx   # Widget mémoire contextuelle IA
│   │   │   ├── Header.tsx             # Header desktop (profil, notifs, bot)
│   │   │   ├── LabJobsBoard.tsx       # Tableau bord travaux labo
│   │   │   ├── LicenseBanner.tsx      # Bandeau licence expirée/essai
│   │   │   ├── PWAInstallPrompt.tsx   # Prompt installation PWA
│   │   │   ├── Sidebar.tsx            # Navigation latérale desktop
│   │   │   ├── TrustBadge.tsx         # Badge conformité/sécurité
│   │   │   │
│   │   │   ├── Analysis/
│   │   │   │   ├── AnalysisStudio.tsx # Studio analyse céphalométrique
│   │   │   │   └── CephaloStudio.tsx  # Workspace céphalométrie interactif
│   │   │   │
│   │   │   ├── Auth/
│   │   │   │   └── LicenseGuard.tsx   # Guard route (vérif licence)
│   │   │   │
│   │   │   ├── clinical/
│   │   │   │   └── FlashSummary.tsx   # Résumé clinique flash patient
│   │   │   │
│   │   │   ├── CrownBot/
│   │   │   │   ├── ChatMessage.tsx    # Bulle message bot
│   │   │   │   └── CrownBotChat.tsx   # Interface chat CrownBot
│   │   │   │
│   │   │   ├── GuidedTour/
│   │   │   │   ├── GuidedTour.tsx     # Tour guidé custom (overlay steps)
│   │   │   │   ├── GuideTower.tsx     # Tour version compacte
│   │   │   │   ├── tourConfig.ts      # Config steps + TOUR_STORAGE_KEY/VERSION
│   │   │   │   └── TourLauncher.tsx   # Bouton flottant + auto-lancement J+1
│   │   │   │
│   │   │   ├── Layout/
│   │   │   │   ├── MainLayout.tsx     # Layout principal (sidebar + contenu)
│   │   │   │   └── ProtectedRoute.tsx # Route protégée (auth required)
│   │   │   │
│   │   │   ├── mobile/
│   │   │   │   └── OfflineQueueViewer.tsx # Visualiseur file d'attente offline
│   │   │   │
│   │   │   └── odontogram/
│   │   │       ├── DocumentWithOdontogram.tsx # Document + odontogramme intégré
│   │   │       ├── Odontogram.tsx             # Odontogramme interactif FDI
│   │   │       ├── OdontogramSVG.tsx          # SVG dents (32 dents, états)
│   │   │       ├── PriceBrain.ts              # Ghost Brain tarification (mémoire IA)
│   │   │       ├── TreatmentSelector.tsx      # Sélecteur actes sur dent
│   │   │       └── types.ts
│   │   │
│   │   ├── data/                      # Données statiques front (contenus éditoriaux)
│   │   │   ├── clinical_tips.ts       # Textes des bulles conseil clinique contextuel
│   │   │   ├── motifsDictionary.ts    # Dictionnaire motifs de consultation
│   │   │   ├── science_articles.ts    # Articles bibliothèque science dentaire (Elite)
│   │   │   └── clinical-protocols/    # ~50 fiches protocole clinique (JSON, un fichier par acte)
│   │   │       ├── index.ts           # Registre/typage des protocoles
│   │   │       ├── pose-implant.json
│   │   │       ├── traitement-endodontique.json
│   │   │       └── … (48 autres fiches, ex. detartrage-surfacage.json, sinus-lift.json)
│   │   │
│   │   ├── hooks/                     # Hooks React partagés (hors feature spécifique)
│   │   │   ├── useAuthenticatedImage.ts # Fetch image protégée (Bearer) → Object URL
│   │   │   ├── useEscapeKey.ts        # Fermeture modal/panel sur touche Échap
│   │   │   ├── useLocalStorage.ts     # State synchronisé avec localStorage
│   │   │   ├── useOfflineQueue.ts     # File d'actions en attente (mobile offline-first)
│   │   │   └── usePWAInstall.ts       # Détection/déclenchement prompt installation PWA
│   │   │
│   │   ├── features/                  # Modules fonctionnels (par domaine)
│   │   │   │
│   │   │   ├── admin/                 # Module administratif / document studio
│   │   │   │   ├── AccountingStudio.tsx       # Studio comptabilité
│   │   │   │   ├── constants.ts               # Constantes partagées admin (icônes, presets branding)
│   │   │   │   ├── DocumentHub.tsx            # Hub central documents (orchestrateur)
│   │   │   │   ├── TeamManager.tsx            # Gestion équipe cabinet
│   │   │   │   ├── TemplateBuilder.tsx        # Constructeur modèles documents
│   │   │   │   ├── types.ts                   # Types partagés module admin (IdentityState…)
│   │   │   │   │
│   │   │   │   ├── components/
│   │   │   │   │   ├── ArabicKeyboard.tsx     # Clavier arabe virtuel
│   │   │   │   │   ├── CrownGuide.tsx         # Guide contextuel IA
│   │   │   │   │   └── LiveDocumentStudio.tsx # Prévisualisation live document
│   │   │   │   │
│   │   │   │   ├── DocumentStudio/            # Studio de génération documents
│   │   │   │   │   ├── DiagnosticEngine.ts    # Moteur diagnostic frontend
│   │   │   │   │   ├── EliteAssistant.tsx     # Assistant IA inline
│   │   │   │   │   ├── EliteDock.tsx          # Dock actions rapides
│   │   │   │   │   ├── HouseWizard.tsx        # Wizard configuration cabinet
│   │   │   │   │   ├── LivePreview.tsx        # Aperçu PDF en temps réel
│   │   │   │   │   ├── StudioFooter.tsx       # Footer (Aperçu/Enregistrer/Imprimer)
│   │   │   │   │   ├── StudioHeader.tsx       # Header (patient, date, actions)
│   │   │   │   │   ├── StudioTabs.tsx         # Onglets types de documents
│   │   │   │   │   ├── TreatmentPlanStudio.tsx# Studio plan de traitement
│   │   │   │   │   ├── useDocumentGenerator.ts# Hook orchestration génération PDF
│   │   │   │   │   ├── VigilanceRadar.tsx     # Radar alertes cliniques
│   │   │   │   │   ├── clinical_rules.ts      # Règles cliniques frontend
│   │   │   │   │   │
│   │   │   │   │   └── Forms/
│   │   │   │   │       ├── CertificateForm.tsx        # Formulaire certificat
│   │   │   │   │       ├── DrugRow.tsx                # Ligne médicament ordonnance (dosage, posologie)
│   │   │   │   │       ├── DrugRow.test.tsx           # Tests DrugRow
│   │   │   │   │       ├── InstallmentStudio.tsx       # Studio échéancier paiement
│   │   │   │   │       ├── LibreForm.tsx               # Formulaire document libre
│   │   │   │   │       ├── PrescriptionAgenticStudio.tsx # Ordonnance IA agentique
│   │   │   │   │       ├── PrescriptionForm.tsx        # Formulaire ordonnance classique
│   │   │   │   │       ├── PrescriptionGuideModal.tsx  # Modal guide posologie pédiatrique/adulte
│   │   │   │   │       ├── prescriptionTypes.tsx       # Types DrugItem + icônes formes galéniques
│   │   │   │   │       ├── QuickEntryBar.tsx           # Barre saisie rapide médicament (dictionnaire national)
│   │   │   │   │       └── QuickEntryBar.test.tsx      # Tests QuickEntryBar
│   │   │   │   │
│   │   │   │   ├── Security/
│   │   │   │   │   ├── AuditLogViewer.tsx     # Visualiseur journal d'audit (filtres, pagination)
│   │   │   │   │   └── MobileSecurity.tsx     # Paramètres sécurité mobile (PIN, biométrie)
│   │   │   │   │
│   │   │   │   ├── Settings/                  # Module paramètres cabinet
│   │   │   │   │   ├── index.ts               # Barrel export (Settings, types, useSettingsStore)
│   │   │   │   │   ├── SettingsContainer.tsx  # Conteneur principal settings
│   │   │   │   │   ├── types.ts               # Types settings (ContactInfo…)
│   │   │   │   │   ├── components/
│   │   │   │   │   │   └── SharedUI.tsx       # Classes/styles partagés inputs settings
│   │   │   │   │   ├── hooks/
│   │   │   │   │   │   ├── useCatalogStore.ts # État catalogue actes (Zustand)
│   │   │   │   │   │   └── useSettingsStore.ts# État global settings (Zustand)
│   │   │   │   │   └── tabs/
│   │   │   │   │       ├── AgendaTab.tsx      # Config agenda (créneaux, durées)
│   │   │   │   │       ├── BrandingTab.tsx    # Branding (logo, couleurs, thème)
│   │   │   │   │       ├── CatalogTab.tsx     # Catalogue actes dentaires
│   │   │   │   │       ├── IATab.tsx          # Paramètres IA (modèle, seuils)
│   │   │   │   │       ├── ProfileTab.tsx     # Profil praticien
│   │   │   │   │       ├── SecurityTab.tsx    # Sécurité (2FA, sessions)
│   │   │   │   │       └── branding/
│   │   │   │   │           ├── AmbiancePill.tsx   # Sélecteur ambiance visuelle
│   │   │   │   │           ├── presets.ts         # Données presets thèmes (BRAND_IDENTITIES)
│   │   │   │   │           ├── PresetsModal.tsx   # Modal presets thèmes
│   │   │   │   │           ├── StudioControls.tsx # Contrôles branding avancés
│   │   │   │   │           ├── StudioPreview.tsx  # Prévisualisation branding live
│   │   │   │   │           └── types.ts           # Types branding (Density, Scope, Preset)
│   │   │   │   │
│   │   │   │   ├── SetupWizard/               # Wizard configuration initiale
│   │   │   │   │   ├── index.ts               # Barrel export SetupWizard
│   │   │   │   │   ├── SetupWizard.tsx
│   │   │   │   │   ├── steps/
│   │   │   │   │   │   ├── Step1Identity.tsx  # Identité praticien
│   │   │   │   │   │   ├── Step2Specialties.tsx # Spécialités
│   │   │   │   │   │   ├── Step3Contacts.tsx  # Coordonnées cabinet
│   │   │   │   │   │   ├── Step5Design.tsx    # Design / logo
│   │   │   │   │   │   ├── Step6Theme.tsx     # Thème couleurs
│   │   │   │   │   │   ├── Step7Confirmation.tsx
│   │   │   │   │   │   └── StepQR.tsx         # QR code mobile
│   │   │   │   │   └── store/
│   │   │   │   │       └── useSetupStore.ts   # État wizard (Zustand)
│   │   │   │   │
│   │   │   │   └── store/
│   │   │   │       ├── useAccountingStore.ts  # État comptabilité (Zustand)
│   │   │   │       ├── useClinicalStore.ts    # État clinique courant
│   │   │   │       └── useDocumentStore.ts    # État studio documents
│   │   │   │
│   │   │   ├── agenda/                        # Module agenda / RDV
│   │   │   │   ├── AgendaModal.tsx            # Modal création/édition RDV
│   │   │   │   ├── AgendaStudio.tsx           # Studio agenda complet
│   │   │   │   ├── DailyView.tsx              # Vue journalière
│   │   │   │   ├── FrontdeskModal.tsx         # Modal création demande RDV accueil
│   │   │   │   ├── FrontdeskModal.test.tsx    # Tests FrontdeskModal
│   │   │   │   ├── GoogleImportModal.tsx      # Import depuis Google Calendar
│   │   │   │   ├── MonthlyView.tsx            # Vue mensuelle
│   │   │   │   ├── PendingRequestCard.tsx     # Carte demande RDV accueil en attente
│   │   │   │   ├── PendingRequestCard.test.tsx# Tests PendingRequestCard
│   │   │   │   └── WeeklyView.tsx             # Vue hebdomadaire
│   │   │   │
│   │   │   ├── analytics/
│   │   │   │   └── AnalyticsCharts.tsx        # Graphiques tendances semaine (données réelles)
│   │   │   │
│   │   │   ├── clinical_tips/
│   │   │   │   └── components/
│   │   │   │       └── ClinicalTipBubble.tsx  # Bulle conseil clinique contextuel
│   │   │   │
│   │   │   ├── clinical-ref/                  # Référentiel clinique
│   │   │   │   ├── ClinicalRefContent.tsx     # Contenu article référentiel
│   │   │   │   ├── ClinicalRefSidebar.tsx     # Sidebar navigation référentiel
│   │   │   │   ├── ClinicalRefTabs.tsx        # Onglets spécialités
│   │   │   │   ├── ClinicalSoinMode.tsx       # Mode soin (checklist procédure)
│   │   │   │   ├── EliteLibrary.tsx           # Bibliothèque Elite (articles premium)
│   │   │   │   ├── EliteScienceHub.tsx        # Hub science dentaire
│   │   │   │   ├── types.ts                   # Types référentiel clinique
│   │   │   │   └── useClinicalRef.ts          # Hook données référentiel
│   │   │   │
│   │   │   ├── mobile/                        # Module PWA mobile
│   │   │   │   ├── Dashboard/
│   │   │   │   │   ├── MobileDashboard.tsx    # Dashboard principal mobile
│   │   │   │   │   ├── types.tsx              # Types Tab/SyncStatus dashboard mobile
│   │   │   │   │   ├── utils.ts               # Helpers (greeting()…) dashboard mobile
│   │   │   │   │   ├── components/
│   │   │   │   │   │   ├── AddApptModal.tsx   # Modal ajout RDV mobile
│   │   │   │   │   │   ├── ApptCard.tsx       # Carte RDV
│   │   │   │   │   │   ├── DraggableApptCard.tsx # Carte RDV draggable
│   │   │   │   │   │   ├── DroppableDay.tsx   # Zone drop agenda
│   │   │   │   │   │   ├── MobileBottomNav.tsx   # Navigation bas mobile
│   │   │   │   │   │   ├── MobileHeader.tsx   # Header mobile
│   │   │   │   │   │   ├── SignatureModal.tsx  # Modal signature électronique
│   │   │   │   │   │   ├── SignaturePad.tsx    # Pad signature tactile
│   │   │   │   │   │   ├── Skeleton.tsx        # Placeholder chargement (pulse)
│   │   │   │   │   │   └── WhatsAppModal.tsx  # Modal envoi WhatsApp
│   │   │   │   │   ├── hooks/
│   │   │   │   │   │   └── useMobileDashboard.ts # Hook orchestration état dashboard mobile
│   │   │   │   │   └── views/
│   │   │   │   │       ├── AgendaView.tsx     # Vue agenda mobile
│   │   │   │   │       ├── BotView.tsx        # Vue bot mobile
│   │   │   │   │       ├── DentistsView.tsx   # Vue sélection/gestion dentistes mobile
│   │   │   │   │       ├── FinanceView.tsx    # Vue finance mobile
│   │   │   │   │       ├── LabView.tsx        # Vue labo mobile
│   │   │   │   │       └── SecuriteView.tsx   # Vue sécurité / PIN mobile
│   │   │   │   └── Onboarding/
│   │   │   │       └── OnboardingScanner.tsx  # Scanner QR onboarding mobile
│   │   │   │
│   │   │   ├── ortho/                         # Module orthodontie / céphalométrie
│   │   │   │   ├── CephaloHistory.tsx         # Historique analyses céphalo
│   │   │   │   ├── CephaloWorkspace.tsx       # Workspace céphalo principal
│   │   │   │   ├── CephaloTracingLayer.tsx    # Calque tracé landmarks
│   │   │   │   ├── CephaloStatsTable.tsx      # Tableau mesures normatives
│   │   │   │   ├── DocumentArchiveManager.tsx # Gestion archives documents ortho
│   │   │   │   ├── orthoExpertSystem.ts       # Système expert orthodontique
│   │   │   │   ├── cephaloMath.ts             # Calculs angulaires/linéaires
│   │   │   │   ├── cephaloTypes.ts            # Types TypeScript céphalo
│   │   │   │   ├── cephaloUtils.ts            # Utilitaires céphalo
│   │   │   │   ├── cephaloTheme.ts            # Thème couleurs landmarks
│   │   │   │   ├── cephaloShared.ts           # Constantes partagées
│   │   │   │   ├── cephaloRepository.ts       # Accès données céphalo (frontend)
│   │   │   │   ├── components/
│   │   │   │   │   ├── AnatomicalTooth.tsx    # Dent anatomique SVG
│   │   │   │   │   ├── Step1Cephalo.tsx       # Étape 1 : radio + landmarks
│   │   │   │   │   ├── Step2Occlusal.tsx      # Étape 2 : analyse occlusale
│   │   │   │   │   ├── Step3Clinical.tsx      # Étape 3 : examen clinique
│   │   │   │   │   ├── Step4Documents.tsx     # Étape 4 : génération docs
│   │   │   │   │   ├── Step2BlockerModal.tsx  # Modal blocage étape 2
│   │   │   │   │   ├── StepTab.tsx            # Onglet étape
│   │   │   │   │   ├── SyncBadge.tsx          # Badge synchronisation cloud
│   │   │   │   │   └── WedgeZone.tsx          # Zone coin occlusal
│   │   │   │   ├── hooks/
│   │   │   │   │   └── useCephaloPersistence.ts # Hook sauvegarde/chargement analyse céphalo
│   │   │   │   └── stores/
│   │   │   │       └── useOrthoStore.ts       # État orthodontie (Zustand)
│   │   │   │
│   │   │   ├── panoramic/                     # Module radiographie panoramique
│   │   │   │   ├── PanoramicHistory.tsx       # Historique radios panoramiques
│   │   │   │   ├── PanoramicStudio.tsx        # Studio analyse panoramique
│   │   │   │   ├── PanoramicWorker.ts         # Web Worker inference ONNX
│   │   │   │   ├── ReportViewer.tsx           # Visionneuse rapport panoramique
│   │   │   │   ├── XRayCanvas.tsx             # Canvas SVG radio + numéros FDI + anomalies
│   │   │   │   └── stores/
│   │   │   │       └── usePanoramicStore.ts   # État panoramique + taxonomie anomalies
│   │   │   │
│   │   │   ├── patients/                      # Module gestion patients
│   │   │   │   ├── AddPatientForm.tsx         # Formulaire nouveau patient
│   │   │   │   ├── CsvImportModal.tsx         # Modal import patients depuis CSV
│   │   │   │   ├── EditPatientForm.tsx        # Formulaire édition patient
│   │   │   │   ├── PatientDetails.tsx         # Fiche patient complète
│   │   │   │   ├── PatientDocuments.tsx       # Documents archivés du patient
│   │   │   │   ├── PatientList.tsx            # Liste patients (search + filtres)
│   │   │   │   └── components/
│   │   │   │       ├── ClinicalHub.tsx        # Hub clinique patient
│   │   │   │       ├── InstallmentPlanModal.tsx # Modal création plan de paiement échelonné
│   │   │   │       ├── LegacyActeNotes.tsx    # Notes/pièces jointes Acte, partagé par PatientJourney
│   │   │   │       ├── MotifSelector.tsx      # Sélecteur motif consultation
│   │   │   │       ├── PatientFinances.tsx    # Onglet finances patient (soldes, paiements)
│   │   │   │       ├── PatientJourney.tsx     # Fil chronologique patient (remplace PatientTracking.tsx, supprimé)
│   │   │   │       ├── PatientJourney.test.tsx# Tests PatientJourney
│   │   │   │       ├── PatientScoreBadge.tsx  # Badge score risque patient
│   │   │   │       ├── PatientSummaryHoverCard.tsx # Hover card résumé patient
│   │   │   │       ├── PayActeModal.tsx       # Modal encaissement d'un acte
│   │   │   │       ├── QuickPayModal.tsx      # Paiement rapide inline
│   │   │   │       ├── RvgCard.tsx            # Carte document RVG (radio intra-orale)
│   │   │   │       ├── RvgUploadModal.tsx     # Modal upload RVG
│   │   │   │       └── wizards/               # Assistants cliniques par spécialité
│   │   │   │           ├── AssistantATM.tsx
│   │   │   │           ├── AssistantChirurgie.tsx
│   │   │   │           ├── AssistantEndo.tsx
│   │   │   │           ├── AssistantExamenComplet.tsx
│   │   │   │           ├── AssistantGeneral.tsx
│   │   │   │           ├── AssistantOrtho.tsx
│   │   │   │           ├── AssistantParo.tsx
│   │   │   │           ├── AssistantPatho.tsx
│   │   │   │           ├── AssistantPedo.tsx
│   │   │   │           └── AssistantProthese.tsx
│   │   │   │
│   │   │   └── superadmin/
│   │   │       └── SuperAdminDashboard.tsx    # Dashboard super-admin multi-tenant
│   │   │
│   │   ├── pages/                             # Pages React (routes top-level)
│   │   │   ├── AccountingPage.tsx             # Page comptabilité
│   │   │   ├── ActivateTrialPage.tsx          # Page activation licence d'essai
│   │   │   ├── AgendaPage.tsx                 # Page agenda
│   │   │   ├── Analytics.tsx                  # Page analytics / statistiques
│   │   │   ├── Dashboard.tsx                  # Dashboard principal
│   │   │   ├── DownloadPage.tsx               # Page téléchargement app desktop/mobile
│   │   │   ├── ForgotPasswordPage.tsx         # Page mot de passe oublié
│   │   │   ├── LandingPage.tsx                # Page vitrine publique (marketing)
│   │   │   ├── LegalPage.tsx                  # Page mentions légales / CGU
│   │   │   ├── LicenseStatusPage.tsx          # Page statut licence
│   │   │   ├── LoginPage.tsx                  # Page connexion (email + Google)
│   │   │   ├── RegisterPage.tsx               # Page inscription
│   │   │   ├── Settings.tsx                   # Page paramètres
│   │   │   ├── StockPage.tsx                  # Page gestion stock/inventaire cabinet
│   │   │   ├── WaitingRoomPage.tsx            # Page salle d'attente (suivi patients du jour)
│   │   │   └── WelcomeScreen.tsx              # Écran d'accueil premier lancement
│   │   │
│   │   ├── services/                          # Clients API et services frontend
│   │   │   ├── api.ts                         # Instance Axios (baseURL, intercepteurs JWT)
│   │   │   ├── auth.ts                        # authService (login, logout, refresh, me)
│   │   │   ├── botService.test.ts             # Tests service bot
│   │   │   ├── cephaloRepository.ts           # Repo céphalo (fetch/save analyses)
│   │   │   ├── labJobService.ts               # Service travaux labo
│   │   │   ├── paymentApi.ts                  # API paiements / encaissements
│   │   │   ├── rvgService.ts                  # API upload/fetch RVG (radio intra-orale)
│   │   │   ├── templateApi.ts                 # API modèles documents
│   │   │   ├── whatsappService.ts             # Ouverture liens WhatsApp
│   │   │   └── zka/                           # Zero-Knowledge Architecture
│   │   │       ├── AdminStorage.ts            # Stockage chiffré admin
│   │   │       ├── CryptoService.ts           # AES-GCM, dérivation clé
│   │   │       ├── ecdhPairing.ts             # Appairage ECDH mobile (QR, HKDF, AES-GCM)
│   │   │       ├── ecdhPairing.test.ts        # Tests appairage ECDH
│   │   │       ├── MobileStorage.ts           # Stockage chiffré mobile
│   │   │       ├── supabaseClient.ts          # Client Supabase (sync cloud ZKA)
│   │   │       └── zka-engine.ts              # Moteur ZKA complet
│   │   │
│   │   ├── stores/                            # Stores globaux Zustand
│   │   │   ├── useAuthStore.ts                # Authentification (user, token, rôle)
│   │   │   ├── useEliteStore.ts               # Features Elite (flags, limites)
│   │   │   ├── usePatientScoresStore.ts       # Cache scores de risque patients
│   │   │   └── usePatientStore.ts             # Patient sélectionné courant
│   │   │
│   │   ├── test/
│   │   │   └── setup.ts                       # Setup global tests Vitest
│   │   │
│   │   ├── types/                             # Types TypeScript partagés
│   │   │   ├── index.ts
│   │   │   ├── labJob.ts
│   │   │   └── template.ts
│   │   │
│   │   └── utils/
│   │       ├── cn.ts                          # clsx + tailwind-merge
│   │       └── icsParser.ts                   # Parser fichiers .ics (iCal)
│   │
│   └── src-tauri/                             # Wrapper Tauri (desktop natif, expérimental)
│       ├── build.rs
│       ├── Cargo.toml
│       ├── tauri.conf.json
│       ├── capabilities/
│       │   └── default.json
│       ├── icons/                             # Icônes desktop (toutes tailles/plateformes)
│       └── src/
│           ├── lib.rs
│           └── main.rs
│
├── scratch/                                   # Scripts ponctuels / expérimentaux (usage jetable, non testés)
│   ├── check_db_schema.py
│   ├── check_doc_types.py
│   ├── check_weasyprint.py
│   ├── fix_paths.py / fix_paths_v2.py / fix_paths.ps1
│   ├── get_clinic_name.py
│   ├── migrate_license.py
│   ├── migrate_patients.py
│   ├── test_calibration.py
│   ├── test_cephalo_mapping.py
│   ├── test_cephalo_pipeline.py
│   ├── test_pano.py
│   ├── test_preview.py
│   ├── test_qcm_rules.py
│   ├── test_sync.py
│   ├── win-install.mjs
│   ├── zka_test_vector.py
│   └── vibecode-kit/                          # Outils Vibecode (agents CLI)
│
└── static/                                    # Dossier statique legacy (racine, distinct de backend/static/)
    ├── documents/
    └── reports/
```

---

## Flux de données principaux

### Génération PDF (Document Studio)
```
DocumentHub.tsx
  → StudioTabs (sélection type)
  → [Form] (InstallmentStudio / PrescriptionAgenticStudio / CertificateForm…)
  → StudioFooter (Aperçu / Enregistrer / Imprimer)
  → useDocumentGenerator.ts (hook)
  → POST /api/documents/generate (ou /installments/generate-preview)
  → backend/services/generators/[type]_gen.py (ReportLab)
  → fichier PDF dans AppData/media/documents/
  → URL normalisée "static/documents/…"
  → GET /api/static/documents/…
  → Blob URL affiché dans LivePreview.tsx
```

### Authentification
```
LoginPage.tsx
  → authService.login() (URLSearchParams → OAuth2PasswordRequestForm)
  → POST /api/auth/login
  → JWT access_token + refresh_token → localStorage
  → AppLoader.tsx vérifie token à chaque chargement
  → intercepteur Axios (api.ts) : refresh auto si 401
```

### Analyse panoramique
```
PanoramicStudio.tsx → upload radio
  → POST /api/ia/panoramic/analyze
  → backend/services/panoramic_service.py
  → PanoramicWorker.ts (ONNX inference Web Worker)
  → XRayCanvas.tsx (SVG overlay : numéros FDI + bounding boxes anomalies)
  → usePanoramicStore (annotations manuelles par dent)
```

### CrownBot
```
CrownBotChat.tsx → saisie utilisateur
  → POST /api/bot/message
  → backend/routers/bot.py
  → intent_parser.py (regex) → llm_parser.py (Ollama si ambigu)
  → action_dispatcher.py → réponse structurée + actions
  → ChatMessage.tsx (rendu markdown + cartes action)
```

---

## Conventions

| Sujet | Convention |
|---|---|
| **API base URL** | `http://localhost:8005` (dev) — proxy Vite `/api` → backend |
| **Auth header** | `Authorization: Bearer <access_token>` |
| **Fichiers statiques** | montés sur `/api/static` → `AppData/.../media/` |
| **Nommage routes** | `/api/{domaine}/{ressource}` |
| **Stores Zustand** | `use[Nom]Store.ts` dans `features/[module]/store/` |
| **Générateurs PDF** | tous dans `backend/services/generators/`, format A4 ou A5 ReportLab |
| **Branche active** | `master` |
