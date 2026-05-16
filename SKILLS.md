# 🛠️ Digital Crown - AI Agent Skills

This document defines the core recurring workflows, procedures, and rules for agents operating on the Digital Crown codebase.

## 1. Ghost Elite UI Implementation
**Trigger**: Creating or modifying UI components, modals, pages, or styling elements.
**Steps**:
1. Use React 19, Tailwind CSS 4, and Framer Motion.
2. Structure layout atomically. Use `cn()` for conditional class merging.
3. Apply "Ghost Elite" aesthetics: backdrop-blur (`bg-white/40`), subtle shadows, and CSS variables (`--primary`, `--secondary`) synced with `CabinetConfig`.
4. Define complex sub-components outside the main component body (use `React.memo` if necessary).
5. Ensure navigation elements (Sidebar) maintain extreme z-index (`z-[10000]`).
6. **EliteDock Centralization**: All clinical intelligence orbs (Brain, Guide) must be grouped in the `EliteDock` (`z-[10001]`) to avoid UI clutter and ensure platform-wide accessibility.
**Output**: A highly responsive, visually premium, and optimized React component.
**Rules**:
- NEVER define a React component inside another component's render body.
- NEVER use low-contrast text (e.g., `text-slate-900` on translucent backgrounds); prefer `text-primary` or pure black on pure white for financial data.
- NEVER add redundant visual labels ("Posologie :") if typography and layout can provide context.
- NEVER duplicate clinical assistants in the Header; use the centralized `EliteDock`.

## 2. Massive Code Replacement Protocol
**Trigger**: Executing `replace_file_content` or `multi_replace_file_content` for large blocks (> 50 lines).
**Steps**:
1. Visually scan the file to capture exact context and line numbers.
2. Apply the specific diffs atomically.
3. Verify opening/closing coherence (`{}`, `()`, `</>`).
4. Ensure React hooks (`useState`, `useEffect`) remain correctly scoped at the top of the function body.
5. Verify all newly declared variables or destructured props are actually utilized.
6. Run `npm run build` or `npx tsc --noEmit` locally to validate type integrity and catch unused variables.
**Output**: A clean, syntactically perfect, production-ready code replacement.
**Rules**:
- NEVER trust a blind replace; always double-check the first and last lines of the targeted block.
- NEVER leave unused imports or variables (treated as compilation errors).
- NEVER place hooks outside the functional component body or conditionally call them.

## 3. Backend Modification & Integrity
**Trigger**: Modifying FastAPI endpoints, SQLAlchemy models, background services, or database schemas.
**Steps**:
1. Check `git status` to ensure a clean working tree before major changes.
2. Formulate an atomic execution plan based on `models.py`, `schemas.py`, and the target `service.py`.
3. Apply changes and strictly verify the first line of the file (to avoid truncation errors like `mport os`).
4. Validate Pydantic schemas (ensure missing fields are Optional or have defaults).
5. Restart `uvicorn` and check server logs for startup crashes or syntax errors.
**Output**: A stable, performant, and secure backend module.
**Rules**:
- NEVER inject large CSS/JS code blocks into Python using multi-line f-strings (use list-based `"\n".join()`).
- NEVER leave a corrupted import statement.
- NEVER assume a third-party library or package is installed without verifying `requirements.txt`.

## 4. Elite PDF Document Generation
**Trigger**: Creating or updating ReportLab or WeasyPrint PDF generators (Ordonnances, Devis, Certificats).
**Steps**:
1. Inherit from `BaseTemplate` or the standard PDF architecture.
2. Inject `CabinetConfig` to fetch dynamic branding (primary_color, logos, fonts).
3. Use absolute positioning for static elements (e.g., anchoring footers at `3.2cm` from the bottom, or central alignment at `10.5*cm`).
4. Apply Google Fonts (Outfit, Inter) and scale text (+1pt) for "Medical Premium" readability.
5. Inject legal identifiers (ICE, IF, INPE) dynamically for financial documents.
**Output**: A pixel-perfect, vector-based PDF document perfectly aligned with the clinic's visual identity.
**Rules**:
- NEVER hardcode brand colors (always use `p_color` from config).
- NEVER include the anatomical Odontogram on patient-facing A5 PDFs unless explicitly overridden.
- NEVER duplicate financial totals; present legal closings in text/letters cleanly.

## 5. Clinical Coherence Triple-Check
**Trigger**: Developing or refining medical rules, alert systems, or AI-driven diagnostics (SLM/Gemini).
**Steps**:
1. Implement the deterministic rule (e.g., safety filters for allergies, pediatrics) in the backend.
2. Add semantic analysis via LLM/SLM as a secondary intelligence layer (explain with 🤖 prefix).
3. Validate Backend Integrity (schema responses, timeouts).
4. Validate API Synchronization (zero-loss data transfer to frontend).
5. Simulate real-case UI scenarios in the Document Studio to ensure alerts (Warning, Critical) correctly block or inform the user.
**Output**: A robust, fail-safe clinical alert or diagnostic suggestion.
**Rules**:
- NEVER rely solely on an AI model for critical medical safety (always have a deterministic fallback).
- NEVER allow a document with a "Critical" alert to be printed without explicit user acknowledgment/override.

## 6. AI Vision & Landmark Calibration
**Trigger**: Updating PyTorch CephLD-CCA endpoints, cephalometric mappings, or panoramic inference thresholds.
**Steps**:
1. Ensure explicit and normalized naming conventions between frontend and backend (e.g., `Pog_soft` vs `stPog`).
2. Map outputs strictly to official challenge tables (e.g., MICCAI 2023) without assuming standard order.
3. Calibrate panoramic thresholds adaptively (compensating for lateral stretching on X-axis).
4. Lower confidence thresholds specifically for subtle periapical lesions.
**Output**: Accurate coordinate matrices and geometrical calculations (Tweed, COM).
**Rules**:
- NEVER filter out soft-tissue or specific points from the interactive frontend layer.
- NEVER prevent the practitioner from manually adjusting AI-detected landmarks.

## 7. Anti-Doublon & Security Enforcement
**Trigger**: Creating logic for patient creation, document archiving, or clinical act recording.
**Steps**:
1. Normalize inputs (strip whitespace, uppercase names, title-case surnames).
2. Query the database using case-insensitive comparisons and identical timestamps/dates.
3. For files, generate and compare SHA-256 hashes.
4. If a duplicate is detected, block the action and present a conflict modal (Keep/Overwrite/New Version).
**Output**: Secure database transactions ensuring zero silent data duplication.
**Rules**:
- NEVER silently overwrite existing clinical data.
- NEVER bypass the `force=True` explicit user requirement to save a confirmed duplicate.

## 8. Session Completion Protocol (Beads Tracker)
**Trigger**: Concluding a task, feature implementation, or ending an interactive session.
**Steps**:
1. File issues for remaining/future work using `bd` commands.
2. Run quality gates: linters (`npx tsc --noEmit`), builds (`npm run build`).
3. Update issue status (`bd close <id>`).
4. Execute mandatory remote sync:
   - `git pull --rebase`
   - `bd dolt push`
   - `git push`
   - `git status` (must be clean).
5. Hand off context for the next session.
**Output**: A synchronized, tracked, and safely pushed repository state.
**Rules**:
- NEVER stop working before a successful `git push` completes.
- NEVER use Markdown TODO lists (`TODO.md`, `MEMORY.md`) for task tracking; strictly use `bd`.

## 9. Technical Specifications Reference

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
- **Moteur d'Habitudes (v1.3)** : Table `doctor_act_habits` pour l'apprentissage des actes fréquents. Suggerre automatiquement le "Top 8" dans l'interface.

### 👥 Gestion des Patients
- **Tri Avancé** : Support du tri par `numero_dossier` (alphanumérique) et `created_at` (temporel) pour faciliter la gestion administrative des flux importants.

### 🦷 Hub Panoramique ELITE v2.0
- **Interaction FDI** : Canevas interactif avec sélection de zone (range FDI) pour les bridges et pathologies étendues.
- **Taxonomie Spécialisée** : Classification structurée des anomalies en 6 spécialités cliniques (Conservatrice, Endo, Paro, Chirurgie, Prothèse, ATM).
- **Moteur de Rapport** : Hybridation déterministe entre détection IA YOLOv11 (ONNX) et annotations manuelles. Génération PDF structurée par secteurs.

### 🧠 Intelligence Artificielle Cephalo
- **Vision Engine** : U-Net CephLD-CCA (PyTorch).
- **Géométrie** : Moteur Python pur pour les calculs d'angles (Tweed, Steiner, Normes COM).
- **Advising** : SLM (Small Language Model - Llama 3.2 via Ollama) pour le diagnostic structuré.

### 🎨 Frontend Ghost Elite & Branding Engine v4.6
- **Design System** : React 19 + Tailwind CSS 4 + Framer Motion.
- **Branding Engine v4.6** : 
    - Typographie **Medical Premium** : Intégration native Google Fonts (Outfit & Inter) via WeasyPrint.
    - Forçage Branding : Couleur primaire forcée sur 100% du contenu textuel.
    - Live Studio WYSIWYG : Prévisualisation ultra-fidèle en temps réel.
- **Esthétique** : Fond Glassmorphism dynamique, animations fluides, micro-interactions 3D.

### 🛡️ Sécurité & Validation (En cours)
- **Smart QR Validation** : Génération de signatures numériques QR sur les documents cliniques pour authentification auprès des tiers (pharmacies, assurances).
- **Archivage Robuste** : Versioning et corbeille 1 an.
- **Cascade de Résolution** :
    1. `Doctor Surcharge` : Recherche d'une préférence explicite du praticien (Table `DoctorPrescriptionPreference`).
    2. `System Protocol` : Fallback sur le protocole standard lié à l'acte gâchette détecté (EXTRACTION, IMPLANT, etc.).
    3. `Safety Filter` : Application systématique et immuable des règles d'allergie (Substitution Pénicilline) et des doses pédiatriques (Adaptation mg/kg).
- **Interface Zero-Clavier** : Capture automatique du contexte clinique via les rendez-vous du jour pour proposer l'ordonnance idéale avant même la première frappe.
