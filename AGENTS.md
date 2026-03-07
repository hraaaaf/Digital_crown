# Digital Crown - Guide pour Agents de Code IA

> **Projet**: Digital Crown - SANINOVA Edition  
> **Domaine**: Logiciel de gestion de cabinet dentaire/orthodontique avec IA intégrée  
> **Langue principale**: Français (code, commentaires, documentation)  
> **Date d'analyse**: 2026-03-01

---

## 1. Vue d'ensemble du projet

Digital Crown est une application full-stack de gestion de cabinet dentaire intégrant des capacités d'intelligence artificielle pour l'analyse céphalométrique (radiographies orthodontiques). Le système permet la gestion des patients, la génération de documents médicaux (ordonnances, certificats, devis), et fournit un diagnostic assisté par IA.

### Architecture générale

```
DigitalCrown/
├── backend/                    # API FastAPI (Python)
│   ├── main.py                 # Point d'entrée API (routes REST)
│   ├── models.py               # Modèles SQLAlchemy (ORM)
│   ├── schemas.py              # Schémas Pydantic (validation)
│   ├── database.py             # Configuration PostgreSQL
│   ├── seed.py                 # Injection données initiales
│   ├── services/               # Logique métier et IA
│   │   ├── vision_service.py   # Détection landmarks (PyTorch/CephLD-CCA)
│   │   ├── cephalo_engine.py   # Calculs céphalométriques COM-Skeletal V4
│   │   ├── ai_advisor.py       # Diagnostic IA (SLM/heuristique)
│   │   ├── document_factory.py # Façade génération documents
│   │   ├── file_validator.py   # Validation fichiers uploadés
│   │   ├── pdf_generator.py    # Générateur PDF legacy
│   │   └── generators/         # Générateurs PDF spécialisés
│   │       ├── ordonnance_gen.py
│   │       ├── certificat_gen.py
│   │       ├── accounting_gen.py
│   │       ├── cephalo_gen.py
│   │       └── libre_gen.py
│   └── ai_models/              # Modèles de deep learning
│       ├── cephld_cca/         # Architecture CephLD-CCA (U-Net)
│       │   ├── ceph_weights.pth
│       │   ├── models/unet_w_cartesian_se.py
│       │   └── data/           # Dataset radiographies (train/test)
│       └── cephalometric-master/  # Référence implémentation TypeScript
├── frontend/                   # Application React 19 (TypeScript)
│   ├── src/
│   │   ├── components/         # Composants réutilisables
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Layout/MainLayout.tsx
│   │   │   └── Analysis/
│   │   │       ├── AnalysisStudio.tsx
│   │   │       └── CephaloStudio.tsx
│   │   ├── features/           # Modules fonctionnels
│   │   │   ├── patients/       # CRUD patients + fiche complète
│   │   │   ├── ortho/          # Analyses céphalométriques
│   │   │   └── admin/          # Administration
│   │   ├── pages/              # Pages principales
│   │   │   ├── Dashboard.tsx
│   │   │   └── Settings.tsx
│   │   ├── services/api.ts     # Client API (axios)
│   │   ├── types/index.ts      # Types TypeScript
│   │   └── utils/cn.ts         # Merge classes Tailwind
│   └── package.json
├── Start_DigitalCrown.bat      # Script de lancement Windows
└── requirements.txt            # Dépendances Python
```

---

## 2. Stack technique

### Backend
| Composant | Technologie | Version |
|-----------|-------------|---------|
| Framework | FastAPI | 0.110.0 |
| Serveur | Uvicorn | 0.27.1 |
| ORM | SQLAlchemy | 2.0.28 |
| Validation | Pydantic | 2.6.3 |
| Base de données | PostgreSQL | (via psycopg2-binary 2.9.9) |
| IA/Vision | PyTorch, TensorFlow, OpenCV | latest |
| IA/Générative | Google Generative AI (Gemini) | latest |
| Génération PDF | ReportLab | (dans generators/) |
| Sécurité fichiers | python-magic | 0.4.27 |

### Frontend
| Composant | Technologie | Version |
|-----------|-------------|---------|
| Framework | React | 19.2.0 |
| Langage | TypeScript | 5.9.3 |
| Build tool | Vite | 7.3.1 |
| Styling | Tailwind CSS | 4.1.18 |
| Routing | React Router DOM | 7.13.0 |
| HTTP Client | Axios | 1.13.5 |
| UI/Animation | Framer Motion | 12.34.x |
| Icons | Lucide React | 0.575.0 |
| Markdown | react-markdown | 10.1.0 |

---

## 3. Configuration et démarrage

### Prérequis
- Python 3.12+ (éviter 3.14 qui peut causer des incompatibilités)
- Node.js 20+
- PostgreSQL (local avec identifiants: postgres/admin)
- Windows (scripts optimisés pour PowerShell/CMD)

### Installation initiale

```bash
# 1. Backend - Création environnement virtuel
python -m venv venv
venv\Scripts\activate.bat

# Installation des dépendances
pip install -r requirements.txt

# 2. Frontend
cd frontend
npm install
```

### Démarrage de l'application

**Méthode rapide (Windows)**:
```bash
# Double-cliquer sur ou exécuter:
Start_DigitalCrown.bat
```

**Manuellement**:
```bash
# Terminal 1 - Backend (depuis la racine)
venv\Scripts\activate
uvicorn backend.main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

L'application sera accessible sur:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Documentation API: http://localhost:8000/docs (Swagger UI)

### Configuration base de données

Le fichier `backend/database.py` contient la configuration PostgreSQL:
```python
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:admin@localhost/digitalcrown_db"
```

Alternative via SQLite (modifier `.env`):
```
DATABASE_URL=sqlite:///./digital_crown.db
```

### Seeding des données

Pour injecter les données initiales (catégories cliniques, médicaments, protocoles):
```bash
venv\Scripts\activate
python backend/seed.py
```

---

## 4. Structure du code

### Backend - Organisation

**Modèles (`models.py`)**:
- `User`: Utilisateurs (Dentiste, Admin, Secrétaire)
- `Patient`: Dossiers patients
- `DossierClinique`: Informations cliniques par patient
- `Acte`: Actes médicaux réalisés
- `CephaloAnalysis`: Analyses céphalométriques (résultats IA)
- `Medication`: Base de connaissance médicaments
- `ClinicalCategory` / `ClinicalProtocol`: Protocoles de prescription
- `ClinicalActCatalog`: Catalogue d'actes pour facturation
- `DocumentArchive`: Archivage avec versioning et corbeille
- `PatientDentition`: Odontogramme (FDI 11-48)

**Services (`services/`)**:
- `vision_service.py`: Moteur PyTorch pour détection des 19 points céphalométriques (architecture CephLD-CCA U-Net + Cartesian SE)
- `cephalo_engine.py`: Calculs géométriques COM (Centre d'Orthodontie Moderne), normes âge-spécifiques
- `ai_advisor.py`: Interface avec SLM local (Ollama/Llama3.2) ou fallback heuristique
- `document_factory.py`: Façade pour génération de documents PDF
- `generators/`: Implémentations spécifiques par type de document

**Routes API principales (`main.py`)**:
- `GET /dashboard/stats`: Statistiques temps réel
- `POST /patients/`: Création patient
- `GET/PUT /patients/{id}`: Gestion patient
- `POST /patients/{id}/upload-radio`: Upload + analyse IA
- `PUT /analyses/{id}`: Mise à jour analyse avec recalcul
- `POST /analyses/{id}/calibrate`: Calibration mm/pixel
- `POST /patients/{id}/pdf`: Génération rapport céphalo PDF
- `POST /documents/generate`: Génération documents (ordonnance, certificat...)
- `GET /prescriptions/*`: Gestion prescriptions intelligentes
- `GET /actes/catalog/*`: Catalogue actes cliniques
- `GET /admin/export-db`: Backup base de données

### Frontend - Organisation

**Architecture par fonctionnalités**:
```
src/
├── components/          # Composants transversaux
│   ├── Header.tsx
│   ├── Sidebar.tsx
│   └── Layout/MainLayout.tsx  # Layout glassmorphism
├── features/           # Modules métier autonomes
│   ├── patients/       # Gestion patients (CRUD + détails)
│   ├── ortho/          # Analyses céphalométriques
│   └── admin/          # Administration
├── pages/              # Pages routeur
│   ├── Dashboard.tsx
│   └── Settings.tsx
├── services/           # API client
│   └── api.ts          # Axios configuré
├── types/              # TypeScript definitions
│   └── index.ts
└── utils/              # Utilitaires
    └── cn.ts           # Merge classes Tailwind
```

**Routes principales** (`App.tsx`):
- `/dashboard`: Tableau de bord
- `/patients`: Liste des patients
- `/patients/new`: Création patient
- `/patients/:id`: Fiche patient complète (onglets multiples)
- `/patients/:id/edit`: Édition patient
- `/patients/:id/archives`: Documents archivés
- `/settings`: Paramètres cabinet

---

## 5. Conventions de code

### Python (Backend)

**Style**:
- PEP 8 respecté
- Docstrings en français pour la logique métier
- Commentaires techniques en français (projet francophone)
- Type hints optionnels mais appréciés
- Noms de variables en français métier (pas de traduction)

**Patterns**:
- Architecture Singleton pour les moteurs IA (`vision_engine`, `cephalo_engine`, `ai_advisor`)
- Injection de dépendances FastAPI pour la BDD (`get_db()`)
- Schémas Pydantic pour validation entrées/sorties API
- Gestion des erreurs avec fallback (mode MOCK si modèle IA indisponible)

**Exemple**:
```python
class CephaloEngine:
    """
    Moteur géométrique COM-Skeletal V4.
    Orchestre les calculs COM, le morphing T1, le diagnostic SLM.
    """
    def calculate_metrics(self, raw_points: Dict, ...) -> Dict:
        # ...
        pass

# Instance singleton
cephalo_engine = CephaloEngine()
```

### TypeScript/React (Frontend)

**Style**:
- Fonctions composants avec arrow functions
- Props typées via interfaces
- Nommage: PascalCase pour composants, camelCase pour variables/fonctions
- Classes Tailwind avec `cn()` pour merge conditionnel
- Commentaires en français

**Patterns**:
- React Hooks (useState, useEffect)
- React Router pour navigation
- Axios interceptors pour gestion erreurs globale
- Fallback data pour continuité de service

**Exemple**:
```tsx
interface Patient {
  id?: number;
  nom: string;
  prenom: string;
  // ...
}

export const PatientList: React.FC = () => {
  const [patients, setPatients] = useState<Patient[]>([]);
  // ...
};
```

---

## 6. Tests

### État actuel
Le projet ne contient pas de suite de tests automatisés dédiée. Les tests sont effectués manuellement via:
- L'interface Swagger UI (`/docs`) pour l'API
- Le navigateur pour le frontend

### Stratégie recommandée
Si vous ajoutez des tests:
- **Backend**: pytest avec fixtures SQLAlchemy pour tests d'intégration
- **Frontend**: Vitest (déjà inclus via Vite) + React Testing Library

---

## 7. Considérations de sécurité

### Points critiques identifiés

1. **Clés API**: La clé Gemini est présente en clair dans `backend/.env` (usage développement uniquement)
2. **CORS**: Configuré en mode restreint via variable d'environnement `ALLOWED_ORIGINS`
3. **Authentification**: Non implémentée (système en développement actif)
4. **Upload fichiers**: Validation par content-type ET python-magic (magic numbers)

### Bonnes pratiques pour contributions
- Ne jamais commiter de données patient réelles
- Utiliser des variables d'environnement pour les secrets
- Sanitiser les entrées utilisateur (Pydantic le fait en partie)
- Limiter la taille des uploads d'images

---

## 8. Fonctionnalités IA clés

### 1. Détection landmarks (`vision_service.py`)
- Modèle: U-Net avec Cartesian SE (CephLD-CCA)
- Entrée: Radiographie céphalométrique (JPEG/PNG)
- Sortie: 19 points anatomiques (S, N, Or, Po, A, B, etc.) + 2 apex dentaires
- Fallback: Mode MOCK si le modèle n'est pas disponible
- Poids: `backend/ai_models/cephld_cca/ceph_weights.pth`

### 2. Analyse géométrique (`cephalo_engine.py`)
- Calcul des angles céphalométriques standards (Tweed, IMPA, I/Francfort, etc.)
- Normes COM (Centre d'Orthodontie Moderne) intégrées
- Normes âge-spécifiques (Enfant 9 ans vs Adulte)
- Gestion des plages de compensation
- Projection morphologique T1 (croissance)
- Calcul DDM Réelle: DDM Clinique + DDM Céphalo ((IMPA - 90) / 2.5)

### 3. Diagnostic IA (`ai_advisor.py`)
**Agent**: Ollama/Llama3.2 (SLM local sur port 11434)
- Fallback heuristique déterministe si SLM indisponible (mode par défaut)
- Génération de prescriptions médicamenteuses
- Diagnostic structuré (squelettique, dentaire, stratégie)

**Agents utilisés**:
| Agent | Rôle | Technologie |
|-------|------|-------------|
| Vision | Détection landmarks | PyTorch + CephLD-CCA |
| Géométrie | Calculs céphalométriques | Python pur (math) |
| Diagnostic | Analyse IA | Ollama/Llama3.2 (SLM) |
| Documents | Génération PDF | ReportLab |

### 🆕 Calculs COM Auto-populés

**Étape 3 (Diagnostic)** reçoit automatiquement:
- Angles: Tweed, IMPA, I/F, Surplomb, Recouvrement
- Osseux: ANB, SNA, SNB, Profondeur faciale
- CVM: Estimation via tables Baccetti (âge + sexe)
- DDM: DDM Clinique + DDM Céphalo ((IMPA - 90) / 2.5)

---

## 9. Génération de documents

Le système génère des PDF via la `DocumentFactory`:

| Type | Classe | Description |
|------|--------|-------------|
| Ordonnance | `OrdonnanceGenerator` | Prescription médicale |
| Certificat | `CertificatGenerator` | Arrêt de travail, etc. |
| Devis | `AccountingGenerator` | Devis avec odontogramme intégré |
| Note honoraires | `AccountingGenerator` | Facture patient |
| Bilan céphalo | `CephaloPDFGenerator` | Rapport analyse IA |
| Document libre | `LibreGenerator` | Modèle personnalisable |

### 🆕 Odontogramme Interactif (`frontend/src/components/odontogram/`)

**Système FDI (ISO 3950)**:
```
Q1 (Haut droit) : 18,17,16,15,14,13,12,11  (droite → gauche)
Q2 (Haut gauche): 21,22,23,24,25,26,27,28  (gauche → droite)
Q3 (Bas gauche) : 38,37,36,35,34,33,32,31  (droite → gauche)
Q4 (Bas droit)  : 41,42,43,44,45,46,47,48  (gauche → droite)
```

**Features**:
- SVG interactif avec couronnes/racines anatomiques
- 40+ traitements répartis en 7 catégories (conservatrice, endo, chir, prothèse, implant, prévention, ortho)
- Prix saisis librement en MAD (pas de prix prédéfinis)
- Sélection de surfaces (M, O, D, MOD...)
- Intégration directe dans les Devis/Notes d'honoraires

### 🆕 Archivage Documentaire (`backend/services/archive_service.py`)

**Modèle `DocumentArchive`**:
- **Versioning**: `document_group_id` + `version_number`
- **Corbeille**: `status=SUPPRIME` + `permanent_delete_at` (1 an)
- **Détection doublons**: `file_hash` (SHA-256)
- **Modal conflit**: Garder/Ecraser/Nouvelle version

**Service de nettoyage**:
```bash
# Cron job mensuel ou manuel
POST /admin/cleanup-trash
Header: X-Admin-Key: CRON_SECRET_KEY
```

### 🆕 Anti-doublons Patients

**Algorithme**:
```python
# Normalisation
nom = nom.strip().upper()        # DUPONT
prenom = prenom.strip().title()  # Jean

# Vérification insensible à la casse
existing = query.filter(
    func.lower(Patient.nom) == nom.lower(),
    func.lower(Patient.prenom) == prenom.lower(),
    Patient.date_naissance == date_naissance
).first()
```

**Modal de conflit**:
- Ouvrir dossier existant
- Créer quand même (jumeaux)
- Modifier informations

---

## 10. Dépannage courant

### Erreur "Module not found" sur backend
```bash
# Vérifier que le venv est activé et reinstaller
venv\Scripts\activate
pip install -r requirements.txt
```

### Port 8000 déjà utilisé
```bash
# Trouver et tuer le processus
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### PyTorch/CUDA non disponible
Le système bascule automatiquement sur CPU. Vérifier dans les logs:
```
VisionEngine : Modèle PyTorch chargé avec succès sur [CPU]
```

### Frontend ne se lance pas
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Erreur PostgreSQL (encodage)
Le fichier `database.py` inclut déjà `client_encoding: "utf8"` pour Windows.

---

## 11. Contact et contribution

Ce projet est développé par SANINOVA. Pour toute contribution:
- Respecter les conventions de nommage existantes
- Maintenir la documentation à jour
- Tester manuellement les fonctionnalités avant commit

---

*Document généré le 2026-03-05 pour agents IA - Digital Crown v1.1*

## Résumé des Agents IA Utilisés

| Agent IA | Fichier | Technologie | Rôle |
|----------|---------|-------------|------|
| **Vision** | `vision_service.py` | PyTorch + CephLD-CCA U-Net | Détection 19 landmarks céphalo + 2 apex |
| **Géométrie** | `cephalo_engine.py` | Python (math) | Calculs angles, normes COM, projections |
| **Diagnostic** | `ai_advisor.py` | Ollama/Llama3.2 (SLM) | Diagnostic structuré (squelettique/dentaire/stratégie) |
| **Suggérer** | `ai_advisor.py` | Heuristique + API externe | Suggestions ordonnances, actes cliniques |
| **Documents** | `generators/*.py` | ReportLab | Génération PDF (ordonnances, bilans, devis) |

**Architecture**:
```
Radiographie JPEG/PNG
         ↓
    [VisionAgent]
    PyTorch U-Net
         ↓
    19 points (x,y)
         ↓
    [GeometryAgent]
    Calculs géométriques
         ↓
    Angles (Tweed, ANB...)
         ↓
    [DiagnosticAgent]
    SLM Ollama (fallback heuristique)
         ↓
    Diagnostic structuré
         ↓
    [DocumentAgent]
    ReportLab PDF
         ↓
    Rapport céphalo PDF
```
