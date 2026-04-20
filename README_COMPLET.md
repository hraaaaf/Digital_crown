# Digital Crown - Documentation Complète

> **Version**: 2026.04 (v4.0)  
> **Projet**: Cabinet dentaire/orthodontique avec IA intégrée  
> **Stack**: FastAPI + React 19 + PostgreSQL + PyTorch + ReportLab Vectorial

---

## 🎯 Vue d'ensemble

Digital Crown est une application full-stack de gestion de cabinet dentaire intégrant :
- **Analyse céphalométrique assistée par IA** (détection automatique des landmarks)
- **Protocole COM** (Centre d'Orthodontie Moderne) pour le diagnostic
- **Génération de documents médicaux** (ordonnances, certificats, devis)
- **Setup Wizard & Branding v4.0** : Onboarding immersif piloté par State Machine (6 étapes) avec le **Crown Guide** (assistance IA contextuelle) et prévisualisation Triple Colonne (FR/Logo/AR). Thémisation dynamique (Elite, Emerald, Prestige).
- **Master Template PDF v4.0** : Moteur de rendu 100% vectoriel natif (Vector-First). Suppression des letterheads images pour une netteté absolue. Injection automatique des identifiants légaux (ICE, IF, INPE) sur les flux financiers.
- **Odontogramme Interactif** : Interface graphique de suivi patient avec nomenclature FDI.

---

## 🤖 Intelligence Artificielle

### 1. Analyse Céphalométrique - Moteur IA

**Architecture**: CephLD-CCA (U-Net with Cartesian SE)
```
Backend: backend/services/vision_service.py
Modèle: backend/ai_models/cephld_cca/ceph_weights.pth
```

**Fonctionnement**:
- **Entrée**: Radiographie céphalométrique (JPEG/PNG)
- **Sortie**: 19 points anatomiques + 2 apex dentaires
  - S (Sella), N (Nasion), Po (Porion), Or (Orbitaire)
  - A, B (points maxillaire et mandibulaire)
  - Go (Gonion), Me (Menton)
  - U1_incisal, U1_apex (incisive supérieure)
  - L1_incisal, L1_apex (incisive inférieure)
  
**Calculs automatiques**:
- Angles: Tweed, IMPA, I/Francfort, ANB, SNA, SNB
- Projections A', B', N' sur plan de Francfort
- DDM Céphalo: (IMPA - 90°) / 2.5

**Agents utilisés**:
- **PyTorch** (inférence CPU/GPU)
- **OpenCV** (prétraitement d'image)
- **Fallback**: Mode MOCK si modèle indisponible (points aléatoires)

### 2. Diagnostic IA - SLM (Small Language Model)

**Fichier**: `backend/services/ai_advisor.py`

**Connecteur**:
```python
# Primaire: Ollama (Llama3.2) sur port 11434
# Fallback: Heuristique déterministe si SLM indisponible
```

**Sortie structurée**:
- Diagnostic squelettique (Classe I/II/III)
- Analyse dentaire (compensations)
- Stratégie thérapeutique (extraction vs chirurgie)

### 3. Suggestions intelligentes

- **Ordonnances**: Protocoles par catégorie (extraction, abcès, etc.)
- **Actes cliniques**: Auto-complétion depuis catalogue CCAM
- **Odontogramme**: Suggestions contextuelles selon la dent cliquée

---

## 🏗️ Architecture Technique

### Backend (FastAPI)

```
backend/
├── main.py                    # Routes API REST
├── models.py                  # SQLAlchemy (PostgreSQL)
├── schemas.py                 # Pydantic (validation)
├── services/
│   ├── vision_service.py      # IA Céphalo (PyTorch)
│   ├── cephalo_engine.py      # Calculs géométriques COM
│   ├── ai_advisor.py          # Diagnostic SLM
│   ├── archive_service.py     # Gestion documents
│   ├── document_factory.py    # Façade PDF
│   └── generators/
│       ├── ordonnance_gen.py
│       ├── certificat_gen.py
│       ├── accounting_gen.py  # Devis & Notes
│       └── cephalo_gen.py
└── ai_models/
    └── cephld_cca/
        └── ceph_weights.pth   # Poids du modèle
```

### Frontend (React 19 + Vite)

```
frontend/src/
├── components/
│   └── odontogram/            # Odontogramme FDI
│       ├── Odontogram.tsx
│       ├── OdontogramSVG.tsx
│       ├── TreatmentSelector.tsx
│       └── types.ts
├── features/
│   ├── patients/              # CRUD patients
│   ├── ortho/                 # Analyse céphalo
│   └── admin/
│       └── DocumentHub.tsx    # Génération documents
└── services/api.ts            # Client Axios
```

---

## 🦷 Odontogramme Interactif (Nouveau)

### Système FDI (ISO 3950)

```
Quadrant 1 (Haut droit) : 18 → 11  (3ème molaire → incisive)
Quadrant 2 (Haut gauche): 21 → 28  (incisive → 3ème molaire)
Quadrant 3 (Bas gauche) : 38 → 31  (3ème molaire → incisive)
Quadrant 4 (Bas droit)  : 41 → 48  (incisive → 3ème molaire)
```

### Bibliothèque de traitements (40+ actes)

| Catégorie | Exemples |
|-----------|----------|
| **Conservatrice** | Composite 1/2/3 surfaces, Amalgame |
| **Endodontie** | Traitement canalaire, Reprise, Pulpotomie |
| **Chirurgie** | Extraction simple/chirurgicale, Séparation radiculaire |
| **Prothèse** | Couronne CCM/Zircone/E-Max, Bridge, Inlay |
| **Implants** | Pose d'implant, Sinus lift, Greffe osseuse |
| **Prévention** | Détartrage, Sceaugment, Fluorisation |

### Workflow

1. Cliquer sur une dent dans le schéma anatomique
2. Sélectionner le traitement (suggestions intelligentes)
3. **Saisir le prix en MAD** (libre, pas de défaut)
4. Choisir les surfaces (M, O, D, MOD...)
5. La ligne s'ajoute automatiquement au devis/note

---

## 📊 Protocole COM (Diagnostic)

### Étape 1: Tracing Céphalométrique
- Upload radiographie
- IA détecte 19 points automatiquement
- Calibration mm/pixel (clic sur image)
- Repositionnement des apex (IMPA 90°, I/F 107°)

### Étape 2: Moulages + Examen Occlusal
- DDM par arcade (maxillaire/mandibulaire)
- Classe d'Angle (I, II, III) par côté
- Division (1 ou 2) pour Classe II
- Type d'arcade (I, II, III)

### Étape 3: Diagnostic COM
**Auto-remplissage** depuis anglesData:
- Analyse dentaire: IMPA, I/F, Surplomb, Recouvrement
- Analyse osseuse: Tweed, ANB, SNA, SNB, Profondeur faciale
- CVM estimé automatiquement (Baccetti tables)
- DDM calculée: Clinique + Céphalo

**Classification**:
- Sagittal: Classe I/II/III selon ANB
- Vertical: Hypo/Normo/Hyperdivergent (Tweed)
- Transversal: Symétrique/Asymétrique
- Espace DDM: Déficit léger/modéré/sévère

### Étape 4: Génération PDF
- 8 slots photos (optionnels)
- Résumé diagnostic
- Plan de traitement
- Signature électronique

---

## 📁 Archivage Documentaire

### Table `document_archives`

```sql
- id, patient_id, document_type
- file_hash (SHA-256, détection doublons)
- document_group_id (versioning)
- version_number, is_latest_version
- file_path, file_size
- status: ACTIF | SUPPRIME | ARCHIVE
- deleted_at, permanent_delete_at (+1 an)
```

### Fonctionnalités

- **Versioning**: Nouvelle version = même document_group_id
- **Corbeille**: Récupération possible pendant 1 an
- **Détection doublons**: Hash du fichier + même nom/jour
- **Modal de conflit**: Garder les deux / Écraser / Créer version

---

## 👥 Gestion des Patients

### Anti-doublons

Vérification avant création:
- Nom (insensible à la casse)
- Prénom (insensible à la casse)
- Date de naissance

Normalisation:
- Nom → MAJUSCULES
- Prénom → Capitalize

### Workflow création patient

1. Saisie nom/prénom/date
2. Pré-vérification `/patients/check-duplicate`
3. Si doublon → Modal avec options:
   - Ouvrir dossier existant
   - Créer quand même (jumeaux/homonymes)
   - Modifier informations

---

## 🎨 Interface Utilisateur

### Design System

- **Couleur principale**: `#003380` (Bleu marine)
- **Glassmorphism**: backdrop-blur, transparence
- **Bordures arrondies**: `rounded-[2.5rem]` pour les cards
- **Ombres**: `shadow-[0_8px_30px_rgb(0,0,0,0.04)]`

### Animations (Framer Motion)

- Transitions entre étapes
- Hover des dents (scale 1.08)
- Apparition modaux (fade + scale)
- Tooltips et notifications

---

## 🔌 API Endpoints Principaux

### Patients
```
GET    /patients/
POST   /patients/              (avec check doublons)
POST   /patients/check-duplicate
GET    /patients/{id}
PUT    /patients/{id}
```

### Analyse Céphalo
```
POST   /patients/{id}/upload-radio   # + analyse IA
PUT    /analyses/{id}               # Mise à jour landmarks
POST   /analyses/{id}/calibrate     # Calibration mm/px
POST   /patients/{id}/pdf           # Génération PDF
GET    /patients/{id}/ai-diagnostic # Diagnostic SLM
```

### Documents
```
POST   /documents/generate          # Ordonnance, certificat, devis...
POST   /documents/archive           # Avec versioning
GET    /documents                   # Liste avec filtres
POST   /documents/{id}/trash        # Corbeille
POST   /documents/{id}/restore      # Restaurer
DELETE /documents/{id}              # Suppression définitive
POST   /admin/cleanup-trash         # Cron job (1 an)
```

### Odontogramme
```
GET    /patients/{id}/odontogramme
POST   /patients/{id}/odontogramme/tooth/{number}
```

---

## ⚙️ Configuration

### Variables d'environnement
```env
DATABASE_URL=postgresql://postgres:admin@localhost/digitalcrown_db
# ou SQLite: sqlite:///./digital_crown.db
CRON_SECRET_KEY=change-me-in-production
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Lancement

**Windows** (rapide):
```bash
Start_DigitalCrown.bat
```

**Manuel**:
```bash
# Terminal 1 - Backend
venv\Scripts\activate
uvicorn backend.main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

Accès:
- Frontend: http://localhost:5173
- API: http://localhost:8000
- Docs: http://localhost:8000/docs

---

## 📦 Dépendances Principales

### Backend
- FastAPI 0.110.0
- SQLAlchemy 2.0.28 (ORM)
- PyTorch (vision service)
- ReportLab (PDF)
- python-magic (validation fichiers)

### Frontend
- React 19.2.0
- TypeScript 5.9.3
- Vite 7.3.1
- Tailwind CSS 4.1.18
- Framer Motion (animations)
- Axios (HTTP)
- Lucide React (icônes)

---

## 🔒 Sécurité

- **Clés API**: En `.env` (développement uniquement)
- **CORS**: Restreint par `ALLOWED_ORIGINS`
- **Upload**: Validation MIME + magic numbers
- **Authentification**: Non implémentée (système en dev)

---

## 🗺️ Roadmap / Idées Futures

- [ ] Authentification JWT (Dentiste/Admin/Secrétaire)
- [ ] Vue 3D de l'odontogramme (Three.js)
- [ ] Synchronisation photos intra-orales
- [ ] Historique temporel des traitements
- [ ] IA prédiction résultat orthodontique
- [ ] Application mobile (React Native)
- [ ] Télémédecine (vidéo consultation)

---

## 👨‍💻 Développeur

**SANINOVA** - 2026

Contact: [à définir]

---

*Document généré le 2026-03-05 - Version complète incluant odontogramme et archivage*
