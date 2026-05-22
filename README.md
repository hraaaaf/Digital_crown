# Digital Crown — SANINOVA Edition
## *L'Intelligence Clinique au service de la Dentisterie Moderne*

![Version](https://img.shields.io/badge/Version-v2.0_Ghost_Hub-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Backend-FastAPI_0.110-green?style=for-the-badge&logo=fastapi)
![React](https://img.shields.io/badge/Frontend-React_19-61DAFB?style=for-the-badge&logo=react)
![Engine](https://img.shields.io/badge/PDF_Engine-ReportLab_Elite-red?style=for-the-badge)
![Intelligence](https://img.shields.io/badge/Intelligence-Ghost_Hub_v2-purple?style=for-the-badge)

---

## Vision du Projet

Digital Crown est une plateforme **Ghost Elite** conçue pour transformer la gestion des cabinets dentaires et orthodontiques. En fusionnant une esthétique ultra-premium avec des algorithmes d'IA de pointe et un moteur d'intelligence proactive, elle permet aux praticiens de se concentrer sur l'essentiel : le diagnostic et le soin.

---

## Breakthroughs Techniques (Mai 2026)

### Ghost Hub Intelligence v2.0 — Moteur Proactif Complet

Le système nerveux central de l'application. Analyse en continu les dossiers patients et génère des alertes actionnables avant même que le praticien ne le demande.

**Catégorie A — Analyse Patient :**
- **A1 Flash Summary** : Résumé IA de dossier en temps réel (antécédents, traitements actifs, solde).
- **A4 Traitement Abandonné** : Détection des devis > 60j sans acte commencé.
- **A5 Suivi Post-Extraction** : Alerte de suivi automatique à J+7.

**Catégorie B — Prédictions Comportementales :**
- **B1 Score No-Show** : Taux d'annulation > 40% sur 6 mois → alerte proactive.
- **B3 Créneau Maudit** : Détection d'un slot horaire annulé 3+ fois consécutives.
- **B4 Progression Ortho** : Estimation % d'avancement du traitement orthodontique.
- **B5 Prédiction Fin Ortho** : Extrapolation de la date de fin via intervalles moyens inter-séances.

**Catégorie C — Finance Prédictive :**
- **C1 Forecast Semaine** : Projection du chiffre d'affaires des 7 prochains jours.
- **C4 Taux de Conversion** : % des devis suivis d'un acte dans les 90 jours.
- **C5 Projection Mensuelle** : Historique 3 mois + forecast 6 mois pondéré par RDV planifiés.

**Catégorie D — Actions Anticipatoires :**
- **D1 Next Best Action (NBA)** : Toast actionnable au départ de la fiche patient.
- **D3 Protocole Auto-suggéré** : Détection du preset d'ordonnance le plus pertinent selon l'acte du jour.
- **D4 Ordonnance Anticipée** : Si RDV dans ≤ 14j, suggestion du protocole à préparer.

**Catégorie E — Scheduler & Notifications :**
- **E1 Daily Scheduler** : Thread daemon récursif — génère les alertes à 10s de démarrage, puis toutes les 24h.
- **E2 ProactiveAlert** : Table SQLite dédiée avec déduplication 24h et expiration 7j.
- **E3 Hub Alertes du Jour** : Widget Dashboard avec navigation directe patient + mark-as-read.
- **E5 Push Mobile FCM** : Notifications push Firebase vers l'app mobile compagnon après génération d'alertes.

---

### Panoramic ELITE Hub v2.0
Diagnostic panoramique haute-fidélité.
- **Taxonomie Clinique** : Groupement des anomalies par spécialité (Endo, Paro, Chirurgie, Prothèse).
- **Multi-Tooth Selection** : Prise en charge native des bridges et zones infectieuses étendues (sélection FDI).
- **Live PDF Engine** : Génération instantanée de bilans structurés par secteur.

### Clinical Intelligence v1.5
- **Flash Summaries** : Diagnostics structurés (Squelettique, Dentaire, Stratégie) via Ollama/Llama3.2 et Gemini 1.5 Flash.
- **EliteAssistant** : Compagnon contextuel avec awareness du module actif, insights cliniques, D4 ordonnance anticipée.

### Studio Documentaire v4.x
- **Ordonnance Zero-Clavier** : Protocoles rapides, suggestion IA, architecture de forme galénique.
- **Devis / Note d'Honoraires** : Odontogramme FDI interactif, archivage automatique, anti-doublon SHA-256.
- **Certificats / Documents Libres** : Templates vectoriels ReportLab Elite.
- **QR E-Verify** : Signature numérique injectée dans chaque ordonnance.

### Ghost Elite UI
- **Backdrop-blur** systématisé, CSS Variables synchronisées avec la BDD.
- **Odontogramme FDI Interactif** : Rendu vectoriel SVG haute fidélité (surfaces M, O, D, MOD).
- **Dynamic Branding v4.6** : 6 thèmes, curseurs couleur avec persistence BDD.

### App Mobile ZKA
- **Onboarding QR** : Appairage Zero-Knowledge via token éphémère.
- **Cockpit Mobile** : Agenda, Performance, Liste Rouge (débiteurs) en temps réel sur LAN.
- **Push FCM (E5)** : Réception des alertes proactives du scheduler quotidien.

---

## Architecture du Système

### Backend (Elite Core)
- **FastAPI** : Performance asynchrone, multi-tenant par `employer_id`.
- **SQLAlchemy 2.0** : Mapped/mapped_column style, `create_all` sans Alembic.
- **Services Intelligence** : `habits_engine.py` (triggers), `daily_scheduler.py` (daemon), `push_service.py` (FCM).
- **Vision Engine** : U-Net CephLD-CCA (PyTorch), 19 landmarks céphalo.
- **PDF Engine** : ReportLab + WeasyPrint (templates dédiés par type de document).

### Frontend (Elite UI)
- **React 19** + **Tailwind CSS 4** + **Framer Motion**.
- **Design System** : `cn()`, CSS Variables, glassmorphism, micro-animations.
- **DocumentHub** : Orchestrateur central du Studio Documentaire.
- **EliteAssistant** : Panneau latéral d'intelligence contextuelle.

---

## Structure du Code

```
DigitalCrown/
├── backend/
│   ├── services/
│   │   ├── habits_engine.py      # Triggers proactifs (15 règles A/B/C/D)
│   │   ├── daily_scheduler.py    # Daemon 24h — génère les ProactiveAlerts
│   │   ├── push_service.py       # FCM multicast — E5 notifications mobiles
│   │   ├── elite_manager.py      # Intelligence patient complète
│   │   ├── vision_service.py     # IA Vision (PyTorch)
│   │   ├── cephalo_engine.py     # Maths & Géométrie orthodontique
│   │   └── generators/           # Moteurs ReportLab dédiés
│   └── routers/
│       ├── intelligence.py       # Endpoints Ghost Hub (C/D/E)
│       ├── mobile.py             # API Mobile ZKA + device token
│       └── ...                   # Autres modules métier
├── frontend/src/
│   ├── features/
│   │   ├── admin/DocumentStudio/ # Studio documentaire (Ordonnance, Devis, etc.)
│   │   ├── patients/             # Dossiers patients, fiche, archives
│   │   └── ortho/                # Céphalométrie COM
│   ├── pages/Dashboard.tsx       # Ghost Hub Dashboard (widgets A/B/C/D/E)
│   └── services/api.ts           # Client Elite Axios
├── SKILLS.md                     # Guide agents IA
├── ROADMAP.md                    # Fonctionnalités déployées & prévues
└── SESSION.md                    # Journal de sessions
```

---

## Installation & Démarrage

### Windows (Quick Launch)
```powershell
./Start_DigitalCrown.bat
```

### Développement
```bash
# Backend
venv\Scripts\activate
uvicorn backend.main:app --reload --port 8000

# Frontend
cd frontend && npm run dev
```

API Docs : `http://localhost:8000/docs`  
App : `http://localhost:5173`

---

## Sécurité & Éthique
- **Zéro Data Leak** : Validation Pydantic stricte, multi-tenant isolé par `employer_id`.
- **Archivage Immuable** : SHA-256 anti-doublon sur tous les documents cliniques.
- **Local-First AI** : SLM local (Ollama) pour confidentialité maximale des données patient.
- **License System** : Coffre-fort chiffré AES-256 + anti-rollback temporel + grâce 72h offline.

---

## Équipe & Version
**Staff Engineering — Digital Crown SANINOVA**  
*Dernière mise à jour : 21 Mai 2026 — Ghost Hub v2.0 (115 pts déployés)*
