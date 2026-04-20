# 📝 Spécifications Techniques - Digital Crown

### 📊 Système Comptable & Documentaire
- **Archivage** : Table `document_archives` (SQLAlchemy). 
- **Types supportés** : ORDONNANCE, CERTIFICAT, DEVIS, NOTE_HONORAIRES, DOCUMENT_LIBRE.
- **Cycle de vie** : `ACTIF` -> `SUPPRIME` (Corbeille pendant 1 an).
- **Anti-Doublon** : 
    - Niveau 1 : Hash SHA-256 du fichier physique.
    - Niveau 2 : Comparaison logique (Patient + Date + Montant).
    - Validation : Autorisation par le praticien via `force=True` en cas de doublon de contenu détecté.
- **Extraction historique** : Utilisation de `PyPDF2` pour scanner les PDFs "Legacy" et reconstruire la table comptable.

### 🦷 Odontogramme & Actes
- **Système FDI** : Gestion des 32 dents adultes (11-48).
- **Format de données** : JSON structuré (`teeth_data`).
- **Lien Clinique** : Les actes sélectionnés sur l'odontogramme sont automatiquement injectés dans les Devis et Notes d'honoraires.

### 🧠 Intelligence Artificielle Cephalo
- **Vision Engine** : U-Net CephLD-CCA (PyTorch).
- **Géométrie** : Moteur Python pur pour les calculs d'angles (Tweed, Steiner, Normes COM).
- **Advising** : SLM (Small Language Model - Llama 3.2 via Ollama) pour le diagnostic structuré.

### 🎨 Frontend Ghost Elite & Branding Engine v2.0
- **Design System** : React 19 + Tailwind CSS 4 + Framer Motion.
- **Setup Machine** : Onboarding piloté par état (Zéro Friction) avec assistance interactive du **Crown Guide**.
- **Branding Engine** : 
    - Header Triple Colonne (Reférence Royale) : Français | Logo | Arabe.
    - 4 Variantes : `classic`, `elite`, `prestige`, `minimal`.
    - Live Studio WYSIWYG : Prévisualisation ultra-fidèle en temps réel.
- **Esthétique** : Fond Glassmorphism dynamique (Pilotage par `data-theme`), animations fluides, micro-interactions 3D.

### 💊 Ordonnance Smart (Moteur Déterministe)
- **Cascade de Résolution** :
    1. `Doctor Surcharge` : Recherche d'une préférence explicite du praticien (Table `DoctorPrescriptionPreference`).
    2. `System Protocol` : Fallback sur le protocole standard lié à l'acte gâchette détecté (EXTRACTION, IMPLANT, etc.).
    3. `Safety Filter` : Application systématique et immuable des règles d'allergie (Substitution Pénicilline) et des doses pédiatriques (Adaptation mg/kg).
- **Interface Zero-Clavier** : Capture automatique du contexte clinique via les rendez-vous du jour pour proposer l'ordonnance idéale avant même la première frappe.
