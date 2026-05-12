# 👑 Digital Crown - SANINOVA Edition
## *L'Intelligence Clinique au service de l'Orthodontie Moderne*

![Version](https://img.shields.io/badge/Version-v1.3_Elite_Panoramic-blue?style=for-the-badge)

![Python](https://img.shields.io/badge/Backend-FastAPI_0.110-green?style=for-the-badge&logo=fastapi)
![React](https://img.shields.io/badge/Frontend-React_19-61DAFB?style=for-the-badge&logo=react)
![Engine](https://img.shields.io/badge/PDF_Engine-ReportLab_Elite-red?style=for-the-badge)

---

## 🎯 Vision du Projet
Digital Crown est une plateforme **Ghost Elite** conçue pour transformer la gestion des cabinets dentaires et orthodontiques. En fusionnant une esthétique ultra-premium avec des algorithmes d'IA de pointe, elle permet aux praticiens de se concentrer sur l'essentiel : le diagnostic et le soin.

---

## 🚀 Breakthroughs Techniques (Mai 2026)

### 🦷 Panoramic ELITE Hub v2.0
Diagnostic panoramique haute-fidélité.
- **Taxonomie Clinique** : Groupement des anomalies par spécialité (Endo, Paro, Chirurgie, Prothèse).
- **Multi-Tooth Selection** : Prise en charge native des bridges et des zones infectieuses étendues (sélection de plage FDI).
- **Live PDF Engine** : Génération instantanée de bilans structurés par secteur avec prévisualisation dynamique.

### 💡 Elite Clinical Insights
Le système d'assistance cognitive le plus discret au monde.
- **Auto-Hide Tips** : Conseils cliniques apparaissant en haut à gauche pendant 2 secondes pour une concentration maximale.
- **Predictive Habits** : Suggestions de prescriptions basées sur les habitudes cliniques réelles du praticien.

### 🧠 Clinical Intelligence v1.2

Le cerveau de l'application. Plus qu'un simple gestionnaire, Digital Crown analyse le dossier patient en temps réel pour générer des **Flash Summaries** et des diagnostics structurés (Squelettique, Dentaire, Stratégie) via des modèles SLM locaux (Ollama/Llama3.2) et Gemini 1.5 Flash.

### 💎 Ghost Elite UI
Une interface fluide, transparente et immersive. 
- **Backdrop-blur** systématisé.
- **Dynamic Branding** : Thémisation instantanée via CSS Variables synchronisées avec la base de données.
- **Odontogramme FDI Interactif** : Rendu vectoriel SVG haute fidélité avec sélection de surfaces (M, O, D, MOD).

### 📄 Moteur PDF Elite (ReportLab Stable)
Abandon des moteurs instables pour une robustesse maximale.
- **Rendu Vectoriel Natif** : Documents ultra-légers et nets.
- **Auto-Open UX** : Ouverture instantanée du PDF après génération.
- **Branding Forcing** : Application stricte de la charte graphique du cabinet sur 100% des documents.

---

## 🏗️ Architecture du Système

### 🔙 Backend (Elite Core)
- **FastAPI** : Performance asynchrone.
- **SQLAlchemy 2.0** : Intégrité des données et archivage avec versioning.
- **Vision Engine** : Détection de 19 landmarks céphalo via PyTorch (U-Net + Cartesian SE).
- **Geometry Engine** : Calculs COM-Skeletal V4 et normes âge-spécifiques.

### 🔜 Frontend (Elite UI)
- **React 19** : Gestion d'état optimisée (Zero-Lag).
- **Tailwind CSS 4** : Design atomique ultra-rapide.
- **Framer Motion** : Micro-animations pour une expérience "Premium".

---

## 📁 Structure du Code

```
DigitalCrown/
├── backend/                    # API & Intelligence
│   ├── services/
│   │   ├── vision_service.py   # IA Vision (PyTorch)
│   │   ├── cephalo_engine.py   # Maths & Géométrie
│   │   ├── ai_advisor.py       # Diagnostic IA (SLM)
│   │   ├── document_factory.py # Orchestrateur PDF
│   │   └── generators/         # Moteurs ReportLab dédiés
│   └── routers/                # Endpoints modulaires
├── frontend/                   # Interface Utilisateur
│   ├── src/
│   │   ├── features/           # Modules métier (Ortho, Admin, Patients)
│   │   ├── components/         # Design System Atomique
│   │   └── services/api.ts     # Client Elite Axios
└── SKILLS.md                   # Guide pour les agents IA
```

---

## 🛠️ Installation & Démarrage rapide

### Windows (Quick Launch)
Lancez simplement le script à la racine :
```powershell
./Start_DigitalCrown.bat
```

### Manuel (Développement)
1. **Backend** :
   ```bash
   venv\Scripts\activate
   uvicorn backend.main:app --reload --port 8000
   ```
2. **Frontend** :
   ```bash
   cd frontend
   npm run dev
   ```

Accès API : `http://localhost:8000/docs`
Accès App : `http://localhost:5173`

---

## 🛡️ Sécurité & Éthique
- **Zéro Data Leak** : Validation Pydantic stricte.
- **Archivage Immuable** : Système de hashage (SHA-256) pour détecter les doublons documentaires.
- **Local-First AI** : Diagnostic via SLM local pour la confidentialité maximale.

---

## 👨‍💻 Développement
**Équipe Staff Engineering - Digital Crown**
*Dernière mise à jour : 12 Mai 2026 (Elite Panoramic Release v1.3)*

