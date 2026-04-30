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

### 🆕 Onboarding "Zero-Friction" v4.0 (`frontend/src/features/admin/SetupWizard.tsx`)

**Fonctionnement**:
Le Wizard v4.0 est un studio de design immersif permettant d'initialiser le cabinet avec un rendu WYSIWYG instantané.

**Breakthroughs Techniques**:
1. **Dynamic Branding Engine** : Synchronisation temps réel entre le frontend (CSS Variables) et le backend (ReportLab Context).
2. **Architecture Découpée** : `LiveDocumentStudio` mémoïsé pour des performances fluides lors de la saisie (0 lag).
3. **Pied de page Rigoureux** : Centrage géométrique (10.5cm) et typographie premium sur tous les documents.
4. **Bilinguisme Intégral** : Support natif du nom du praticien et des spécialités en arabe avec moteur de prévisualisation dédié.
5. **Icônes Premium** : Agrandissement à 32px pour une interaction tactile optimisée et un visuel "Elite".

---

## 10. Moteur PDF v4.0 (ReportLab Dynamic)

Le système a abandonné les styles statiques au profit d'une injection de contexte via `CabinetConfig`.

**Flux de Génération**:
1. `DocumentFactory` reçoit `db` et `user_id`.
2. Elle récupère la `CabinetConfig` du praticien.
3. Elle injecte la `primary_color`, les logos et les en-têtes bilingues dans les générateurs.
4. `BaseTemplate` dessine dynamiquement les éléments statiques (Header/Footer).

**Règles d'Or**:
- Tout nouveau document DOIT hériter de `BaseTemplate`.
- Les couleurs ne doivent JAMAIS être hardcodées (utiliser `p_color` de la config).
- L'alignement central doit toujours utiliser `10.5*cm` (A4 standard).

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
| **Vision** | `vision_service.py` | SOTA ONNX (38 pts) / PyTorch | Détection 38 landmarks (SOTA) ou 19 landmarks (Standard) |
| **Géométrie** | `cephalo_engine.py` | Python (math) | Calculs angles, normes COM, projections (Synonym Mapping v4.3) |
| **Diagnostic** | `ai_advisor.py` | Ollama/Llama3.2 (SLM) | Diagnostic structuré (squelettique/dentaire/stratégie) |
| **Intelligence** | `clinical_intelligence.py`| Gemini 1.5 Flash | Résumé flash et analyse de cohérence clinique |
| **Prescription** | `prescription_service.py`| Arbre décisionnel (Python) | Résolution contextuelle (Acte > Préférence > Sécurité) |
| **CardExtractor**| `card_extractor.py`      | Gemini 1.5 Flash (Vision)  | Extraction intelligente de cartes de visite (Onboarding) |
| **DocMaster** | `*.md` | Markdown Sync Agent | Actualisation en temps réel des specs, roadmap et journal d'erreurs |
| Documents | Generators/*.py | ReportLab (Stable) | Génération PDF (ordonnances, bilans, devis) |

---

## 👥 Équipe Virtuelle de Sub-Agents

Pour toute intervention, l'agent doit se référer aux spécialités suivantes (voir `TEAM.md`) :
- **Architector** (Backend/BDD) : Priorité à l'intégrité SQL et FastAPI.
- **PixelMaster** (Frontend) : Priorité au design Ghost Elite (React 19).
- **DataPhysicist** (Maths/IA) : Priorité à la précision Cephalo.
- **Financia** (Compta/Docs) : Priorité à la traçabilité financière.

---

## 🛡️ Règles de Sécurité Documentaire (Anti-Doublon)

1. **Doublon de Contenu** : Avant d'archiver, le système compare les `clinical_data`. Si une note identique existe (mêmes actes/montant), l'archivage est bloqué.
2. **Forçage** : L'utilisateur doit explicitement approuver via `force=True` pour enregistrer un doublon réel.
3. **Extraction** : En cas de perte de données, utiliser `PyPDF2` pour reconstruire les métadonnées depuis les fichiers physiques.

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

---

### 🆕 Apprentissage & Habitudes v1.3 (Avril 2026)

1. **Habits Engine (Auto-Learning)** : Déploiement de `DoctorActHabit` permettant au système d'apprendre les actes fréquents du praticien sans saisie manuelle préalable.
2. **Dynamic Quick Acts** : Remplacement des raccourcis statiques par une barre prédictive basée sur la fréquence d'usage réelle.
3. **Save-as-Habit UI** : Intégration d'un bouton de persistance rapide dans le Studio Documentaire pour enregistrer de nouveaux actes personnalisés.
4. **Tri Administratif Avancé** : Support du tri par N° Dossier et Date de création dans la liste des patients.

---

### 🛡️ Smart QR Validation (En cours de Brainstorming)

- **Agent QR** : `qr_service.py` (Projeté)
- **Rôle** : Génération de signatures numériques infalsifiables.
- **Usage** : Validation de l'authenticité des ordonnances et paiements express via QR Code sécurisé.

---

*Document mis à jour le 29 Avril 2026 pour agents IA - Digital Crown v1.3 (Cephalo Ghost Elite Release)*

<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:ca08a54f -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

## Session Completion

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd dolt push
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
<!-- END BEADS INTEGRATION -->
