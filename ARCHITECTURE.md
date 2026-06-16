# Architecture — Digital Crown

> Dernière mise à jour : 2026-06-12
> Branche active : `crownbot`

---

## Stack technique

| Couche | Technologie |
|---|---|
| **Backend** | FastAPI (Python 3.11+), SQLAlchemy ORM, Alembic migrations, ReportLab PDF |
| **Base de données** | SQLite (local, fichier `digital_crown.db`) |
| **Frontend** | React 18 + TypeScript, Vite, TailwindCSS, Zustand, Framer Motion, Recharts |
| **Mobile** | PWA (Progressive Web App) + Service Worker offline-first |
| **IA / ML** | ONNX Runtime (panoramique), Ollama/LLM local (ordonnances, bot), CephMark (céphalo) |
| **Auth** | JWT (access + refresh token), OAuth2 Google, Zero-Knowledge Architecture (ZKA) |
| **PDF** | ReportLab (backend), LibreOffice headless (fallback) |
| **Desktop** | PyInstaller (DigitalCrown.exe) + Tauri (expérimental) |
| **CI/Déploiement** | ecosystem.config.js (PM2), Dockerfile |

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
├── alembic/                           # Migrations de schéma DB
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── 0ac66fa0bdb8_remove_color_ref_and_init_lab_jobs.py
│       ├── 2872d2ae6349_add_superadmin_features.py
│       ├── 74e675197637_add_medical_library_models.py
│       └── 8f6465e49d90_sync_db_and_models_after_god_file_split_.py
│
├── artifacts/                         # Sorties de tests / docs générés
│
├── backend/                           # API FastAPI
│   ├── __init__.py
│   ├── config.py                      # Settings (env, chemins, flags)
│   ├── database.py                    # Engine SQLAlchemy + session
│   ├── main.py                        # App FastAPI, montage des routers
│   ├── models.py                      # Tous les modèles ORM SQLAlchemy
│   ├── security.py                    # JWT, hashing, dépendances auth
│   ├── requirements.txt               # Dépendances Python backend
│   │
│   ├── .env                           # Variables d'environnement (ignoré git)
│   ├── .env.development
│   ├── .env.example
│   │
│   ├── ai_models/                     # Modèles ML embarqués
│   │   ├── audit_model.py             # Wrapper audit ONNX
│   │   ├── best.onnx                  # Modèle panoramique ONNX
│   │   ├── best.pt                    # Modèle panoramique PyTorch
│   │   ├── panoramic_model.onnx
│   │   ├── panoramic_model.pt
│   │   ├── panoramic_model.pth
│   │   ├── cephalometric-master/      # Lib céphalo JS (référence)
│   │   ├── cephld_cca/                # Modèle CCA détection landmarks
│   │   ├── cephmark/                  # Moteur céphalométrie principal
│   │   └── CL-Detection2023/          # Détection contours céphalométriques
│   │
│   ├── core/
│   │   └── paths.py                   # AppPaths : résolution chemins AppData/media
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
│   │   ├── ia.py                      # /ia — analyses IA (panoramique, céphalométrie)
│   │   ├── installments.py            # /installments — plans de paiement échelonné
│   │   ├── intelligence.py            # /intelligence — moteur règles cliniques
│   │   ├── lab_jobs.py                # /lab — travaux laboratoire
│   │   ├── medical_library.py         # /library — bibliothèque médicale
│   │   ├── mobile.py                  # /mobile — endpoints dédiés PWA mobile
│   │   ├── patients.py                # /patients — CRUD patients
│   │   ├── prescriptions.py           # /prescriptions — ordonnances
│   │   ├── stats.py                   # /stats — statistiques cabinet
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
│   │   ├── branding.py
│   │   ├── cabinet.py
│   │   ├── catalog.py
│   │   ├── clinical.py
│   │   ├── documents.py
│   │   ├── installments.py
│   │   ├── panoramic.py
│   │   ├── patient.py
│   │   ├── payments.py
│   │   └── superadmin.py
│   │
│   ├── services/                      # Logique métier
│   │   ├── __init__.py
│   │   ├── accounting_service.py      # KPIs financiers, soldes, caisse
│   │   ├── ai_advisor.py              # Conseils IA cliniques contextuels
│   │   ├── ai_coherence.py            # Vérification cohérence IA
│   │   ├── anonymizer.py              # Anonymisation données patients (RGPD)
│   │   ├── archive_service.py         # Archivage documents générés
│   │   ├── audit_service.py           # Audit sécurité et accès
│   │   ├── backup_service.py          # Sauvegardes automatiques DB
│   │   ├── base_template.py           # Template ReportLab de base (entête cabinet)
│   │   ├── bilan_ortho_engine.py      # Moteur bilan orthodontique
│   │   ├── calibration_service.py     # Calibration images radio (px→mm)
│   │   ├── card_extractor.py          # Extraction carte CIN/assurance
│   │   ├── cephalo_engine.py          # Pipeline détection landmarks céphalo
│   │   ├── cephalo_service.py         # Service céphalométrie (VTO, analyses)
│   │   ├── clinical_coherence.py      # Règles cohérence clinique
│   │   ├── clinical_intelligence.py   # Intelligence clinique (suggestions)
│   │   ├── clinical_rules_engine.py   # Moteur règles QCM/protocoles
│   │   ├── cmo_agent_service.py       # Agent CMO (Chief Medical Officer IA)
│   │   ├── css_generator.py           # Génération CSS dynamique branding
│   │   ├── daily_scheduler.py         # Tâches planifiées journalières
│   │   ├── document_factory.py        # Factory de génération PDF
│   │   ├── elite_manager.py           # Gestion features Elite / licence
│   │   ├── file_validator.py          # Validation fichiers uploadés
│   │   ├── firebase_sync_service.py   # Sync Firebase (multi-device)
│   │   ├── fts_indexer.py             # Full-text search SQLite FTS5
│   │   ├── ghost_memory_service.py    # Mémoire contextuelle IA (Ghost Brain)
│   │   ├── habits_engine.py           # Moteur habitudes/protocoles cabinet
│   │   ├── holiday_engine.py          # Gestion jours fériés Maroc
│   │   ├── license_service.py         # Validation licence (Firebase + local)
│   │   ├── llm_cache.py               # Cache réponses LLM (Redis-like en mémoire)
│   │   ├── logo_processor.py          # Traitement logo cabinet (recadrage, format)
│   │   ├── notification_service.py    # Notifications push (FCM)
│   │   ├── panoramic_ai_advisor.py    # Conseiller IA panoramique
│   │   ├── panoramic_expert_engine.py # Moteur expert interprétation panoramique
│   │   ├── panoramic_report_engine.py # Génération rapport panoramique
│   │   ├── panoramic_service.py       # Service orchestration panoramique
│   │   ├── panoramic_vision_service.py# Vision ONNX inference panoramique
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
│   ├── static/                        # Fichiers statiques servis par FastAPI
│   │   ├── archives/                  # Archives PDF par patient/cabinet
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
│   ├── tests/                         # Suite de tests backend (pytest)
│   │   ├── conftest.py
│   │   ├── smoke_test_elite.py
│   │   ├── test_access_control.py
│   │   ├── test_accounting_gen.py
│   │   ├── test_auth.py
│   │   ├── test_backups.py
│   │   ├── test_clinical_v4.py
│   │   ├── test_ddi.py
│   │   ├── test_health_and_pagination.py
│   │   ├── test_honoraires_archive.py
│   │   ├── test_license.py
│   │   ├── test_notifications.py
│   │   ├── test_patients.py
│   │   ├── test_prescription_safety_crosscheck.py
│   │   ├── test_security.py
│   │   └── test_studio_v4.py
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
│   │   │   ├── DayOneTour.tsx         # Tour guidé Joyride (premier lancement)
│   │   │   ├── DigitalCrownLoader.tsx # Splash screen chargement
│   │   │   ├── EliteGhostLoader.tsx   # Loader Elite avec Ghost Brain
│   │   │   ├── ErrorBoundary.tsx      # Boundary React erreurs critiques
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
│   │   ├── features/                  # Modules fonctionnels (par domaine)
│   │   │   │
│   │   │   ├── admin/                 # Module administratif / document studio
│   │   │   │   ├── AccountingStudio.tsx       # Studio comptabilité
│   │   │   │   ├── DocumentHub.tsx            # Hub central documents (orchestrateur)
│   │   │   │   ├── TeamManager.tsx            # Gestion équipe cabinet
│   │   │   │   ├── TemplateBuilder.tsx        # Constructeur modèles documents
│   │   │   │   │
│   │   │   │   ├── components/
│   │   │   │   │   ├── ArabicKeyboard.tsx     # Clavier arabe virtuel
│   │   │   │   │   ├── CrownGuide.tsx         # Guide contextuel IA
│   │   │   │   │   ├── LiveDocumentStudio.tsx # Prévisualisation live document
│   │   │   │   │   └── settings/              # Sous-composants settings
│   │   │   │   │
│   │   │   │   ├── DocumentStudio/            # Studio de génération documents
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
│   │   │   │   │   ├── DiagnosticEngine.ts    # Moteur diagnostic frontend
│   │   │   │   │   │
│   │   │   │   │   └── Forms/
│   │   │   │   │       ├── CertificateForm.tsx        # Formulaire certificat
│   │   │   │   │       ├── InstallmentStudio.tsx       # Studio échéancier paiement
│   │   │   │   │       ├── LibreForm.tsx               # Formulaire document libre
│   │   │   │   │       ├── PrescriptionAgenticStudio.tsx # Ordonnance IA agentique
│   │   │   │   │       └── PrescriptionForm.tsx        # Formulaire ordonnance classique
│   │   │   │   │
│   │   │   │   ├── Security/
│   │   │   │   │   └── MobileSecurity.tsx     # Paramètres sécurité mobile (PIN, biométrie)
│   │   │   │   │
│   │   │   │   ├── Settings/                  # Module paramètres cabinet
│   │   │   │   │   ├── SettingsContainer.tsx  # Conteneur principal settings
│   │   │   │   │   └── tabs/
│   │   │   │   │       ├── AgendaTab.tsx      # Config agenda (créneaux, durées)
│   │   │   │   │       ├── BrandingTab.tsx    # Branding (logo, couleurs, thème)
│   │   │   │   │       ├── CatalogTab.tsx     # Catalogue actes dentaires
│   │   │   │   │       ├── IATab.tsx          # Paramètres IA (modèle, seuils)
│   │   │   │   │       ├── ProfileTab.tsx     # Profil praticien
│   │   │   │   │       ├── SecurityTab.tsx    # Sécurité (2FA, sessions)
│   │   │   │   │       └── branding/
│   │   │   │   │           ├── AmbiancePill.tsx   # Sélecteur ambiance visuelle
│   │   │   │   │           ├── PresetsModal.tsx   # Modal presets thèmes
│   │   │   │   │           ├── StudioControls.tsx # Contrôles branding avancés
│   │   │   │   │           └── StudioPreview.tsx  # Prévisualisation branding live
│   │   │   │   │
│   │   │   │   ├── SetupWizard/               # Wizard configuration initiale
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
│   │   │   │   ├── GoogleImportModal.tsx      # Import depuis Google Calendar
│   │   │   │   ├── MonthlyView.tsx            # Vue mensuelle
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
│   │   │   │   └── useClinicalRef.ts          # Hook données référentiel
│   │   │   │
│   │   │   ├── mobile/                        # Module PWA mobile
│   │   │   │   ├── Dashboard/
│   │   │   │   │   ├── MobileDashboard.tsx    # Dashboard principal mobile
│   │   │   │   │   ├── components/
│   │   │   │   │   │   ├── AddApptModal.tsx   # Modal ajout RDV mobile
│   │   │   │   │   │   ├── ApptCard.tsx       # Carte RDV
│   │   │   │   │   │   ├── DraggableApptCard.tsx # Carte RDV draggable
│   │   │   │   │   │   ├── DroppableDay.tsx   # Zone drop agenda
│   │   │   │   │   │   ├── MobileBottomNav.tsx   # Navigation bas mobile
│   │   │   │   │   │   ├── MobileHeader.tsx   # Header mobile
│   │   │   │   │   │   ├── SignatureModal.tsx  # Modal signature électronique
│   │   │   │   │   │   ├── SignaturePad.tsx    # Pad signature tactile
│   │   │   │   │   │   └── WhatsAppModal.tsx  # Modal envoi WhatsApp
│   │   │   │   │   └── views/
│   │   │   │   │       ├── AgendaView.tsx     # Vue agenda mobile
│   │   │   │   │       ├── BotView.tsx        # Vue bot mobile
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
│   │   │   │   ├── EditPatientForm.tsx        # Formulaire édition patient
│   │   │   │   ├── PatientDetails.tsx         # Fiche patient complète
│   │   │   │   ├── PatientDocuments.tsx       # Documents archivés du patient
│   │   │   │   ├── PatientList.tsx            # Liste patients (search + filtres)
│   │   │   │   └── components/
│   │   │   │       ├── ClinicalHub.tsx        # Hub clinique patient
│   │   │   │       ├── MotifSelector.tsx      # Sélecteur motif consultation
│   │   │   │       ├── PatientScoreBadge.tsx  # Badge score risque patient
│   │   │   │       ├── PatientSummaryHoverCard.tsx # Hover card résumé patient
│   │   │   │       ├── PatientTracking.tsx    # Suivi traitement / jalons
│   │   │   │       ├── QuickPayModal.tsx      # Paiement rapide inline
│   │   │   │       └── wizards/               # Assistants cliniques par spécialité
│   │   │   │           ├── AssistantATM.tsx
│   │   │   │           ├── AssistantChirurgie.tsx
│   │   │   │           ├── AssistantEndo.tsx
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
│   │   │   ├── AgendaPage.tsx                 # Page agenda
│   │   │   ├── Analytics.tsx                  # Page analytics / statistiques
│   │   │   ├── Dashboard.tsx                  # Dashboard principal
│   │   │   ├── ForgotPasswordPage.tsx         # Page mot de passe oublié
│   │   │   ├── LicenseStatusPage.tsx          # Page statut licence
│   │   │   ├── LoginPage.tsx                  # Page connexion (email + Google)
│   │   │   ├── RegisterPage.tsx               # Page inscription
│   │   │   ├── Settings.tsx                   # Page paramètres
│   │   │   └── WelcomeScreen.tsx              # Écran d'accueil premier lancement
│   │   │
│   │   ├── services/                          # Clients API et services frontend
│   │   │   ├── api.ts                         # Instance Axios (baseURL, intercepteurs JWT)
│   │   │   ├── auth.ts                        # authService (login, logout, refresh, me)
│   │   │   ├── cephaloRepository.ts           # Repo céphalo (fetch/save analyses)
│   │   │   ├── labJobService.ts               # Service travaux labo
│   │   │   ├── paymentApi.ts                  # API paiements / encaissements
│   │   │   ├── templateApi.ts                 # API modèles documents
│   │   │   ├── whatsappService.ts             # Ouverture liens WhatsApp
│   │   │   └── zka/                           # Zero-Knowledge Architecture
│   │   │       ├── AdminStorage.ts            # Stockage chiffré admin
│   │   │       ├── CryptoService.ts           # AES-GCM, dérivation clé
│   │   │       ├── MobileStorage.ts           # Stockage chiffré mobile
│   │   │       ├── supabaseClient.ts          # Client Supabase (sync cloud ZKA)
│   │   │       └── zka-engine.ts              # Moteur ZKA complet
│   │   │
│   │   ├── stores/                            # Stores globaux Zustand
│   │   │   ├── useAuthStore.ts                # Authentification (user, token, rôle)
│   │   │   ├── useEliteStore.ts               # Features Elite (flags, limites)
│   │   │   └── usePatientStore.ts             # Patient sélectionné courant
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
│       ├── Cargo.toml
│       ├── tauri.conf.json
│       └── src/
│           ├── lib.rs
│           └── main.rs
│
├── scratch/                                   # Scripts ponctuels / expérimentaux
│   ├── test_calibration.py
│   ├── test_cephalo_pipeline.py
│   ├── test_pano.py
│   ├── zka_test_vector.py
│   └── vibecode-kit/                          # Outils Vibecode (agents CLI)
│
└── static/                                    # Dossier statique legacy (racine)
    ├── archives/
    ├── backups/
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
| **Branche active** | `crownbot` — merge vers `master` par PR |
