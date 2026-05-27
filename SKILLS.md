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
6. **Header Centralization**: All clinical intelligence orbs (Ghost Brain) and contextual help (Guide Tower) must be placed in the `Header` next to the Settings icon to ensure a unified navigation experience across the platform.
**Output**: A highly responsive, visually premium, and optimized React component.
**Rules**:
- NEVER define a React component inside another component's render body.
- NEVER use low-contrast text (e.g., `text-slate-900` on translucent backgrounds); prefer `text-primary` or pure black on pure white for financial data.
- NEVER add redundant visual labels ("Posologie :") if typography and layout can provide context.
- NEVER use floating orbs for global tools; keep them in the `Header` next to settings and notifications.

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

## 8. Ghost Hub Intelligence — Pattern de Développement
**Trigger**: Ajouter un nouveau trigger proactif, endpoint d'intelligence, ou widget de Dashboard.

**Architecture à respecter :**
1. **Trigger** → `backend/services/habits_engine.py` → méthode `check_proactive_triggers()` → `triggers.append({type, title, message, action})`.
2. **Stockage** → `backend/services/daily_scheduler.py` → déduplication 24h, expiration 7j, comptage par `employer_id`.
3. **Push** → `backend/services/push_service.py` → `send_push_to_employer()` appelé après `db.commit()`.
4. **API** → `backend/routers/intelligence.py` → préfixe `/intelligence/`, guard `require_permission("patients")`, `assert_patient_access()` pour les routes par patient.
5. **Frontend** → Widget dans `Dashboard.tsx` (hooks dans `useEffect` du premier chargement) **OU** card dans `EliteAssistant.tsx` (hook sur `lastPatientId`).

**Règles :**
- NEVER re-initialiser Firebase — `license_service.py` initialise l'app par défaut ; utiliser `firebase_admin.messaging` directement.
- NEVER dupliquer une alerte dans les 24h — vérifier `ProactiveAlert.created_at >= now - 24h` avant insert.
- Routes statiques (`/forecast-semaine`, `/alerts/today`) TOUJOURS avant routes paramétrisées (`/{patient_id}`) dans le router FastAPI.

## 9. Session Completion Protocol (Beads Tracker)
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

### 🦷 Bilan Parodontal Clinique Graphique v2.0
- **Sondage 6 points & Mobilité** : Saisie interactive et graphique des profondeurs de poches (PD), récessions (GR), saignements (BOP) et indice de plaque (PLQ) sur 6 points par dent, avec indices de mobilité (0-3) et atteintes de furcation (0-3).
- **Moteur Diagnostique Déterministe EFP/AAP 2017** : Calcul du CAL ($CAL = PD + GR$) maximal global pour déterminer le *Staging* (I à IV), croisé avec les toggles réactifs de facteurs de risques (tabagisme, diabète HbA1c $\ge 7.0\%$) pour évaluer le *Grading* (A à C).
- **Prescription d'Ordonnance Intégrée (1 Clic)** : Recommandation automatique de la bi-antibiothérapie d'accompagnement HAS (Amoxicilline 500mg + Métronidazole 500mg) en cas de Grade C actif de parodontite, avec bouton d'édition instantanée lié au dossier.

### 🧠 Intelligence Artificielle Cephalo
- **Vision Engine** : U-Net CephLD-CCA (PyTorch).
- **Géométrie** : Moteur Python pur pour les calculs d'angles (Tweed, Steiner, Normes COM).
- **Advising** : SLM (Small Language Model - Llama 3.2 via Ollama) pour le diagnostic structuré.

### 🧠 Moteur d'Intelligence Clinique & Logistique (Ghost Hub - Elite Core)
- **Calculateur d'Intelligence Patient (Score 0-100)** : Évalue instantanément la complétude du dossier patient (antécédents, radiographies, données cliniques).
- **Vigilance Financière Active (Pénalité Solvabilité)** : Soustrait automatiquement `-15 points` du score d'intelligence patient en cas de dettes échues non réglées ($\ge 1000$ MAD) sur les actes cliniques finalisés, protégeant la trésorerie du cabinet.
- **Pharmacologie Clinique Odontologique (Rules Engine v1.5)** :
    - *Anticipation Grossesse* : Détection résiliente de l'état de grossesse (enceinte, grossesse, maternité). Blocage strict des AINS et des Tétracyclines avec avertissements enrichis sur les risques fœtaux (toxicité cardiopulmonaire, coloration permanente des dents).
    - *Protection Gastro-intestinale* : Blocage strict des AINS et Corticoïdes (Prednisolone) pour tout patient ayant des antécédents d'ulcère ou de gastrite pour prévenir toute hémorragie active.
    - *Préservation de la Flore Digestive* : Co-prescription automatique d'Ultra-Levure (Saccharomyces Boulardii 250mg) pour toute prescription d'antibiotiques à large spectre (Augmentin, Amoxicilline) afin d'éviter la diarrhée post-antibiotique.
- **Fusion Vision Cognitive & Chiffrage Marocain (Treatment Plan Engine)** : Traduction automatique des détections de la radio panoramique en un plan de traitement structuré en 5 phases avec tarification marocaine de référence (MAD) et devis en 1 clic.
- **Anticipation Logistique & Gestion Prédictive des Stocks** : Assistant confrère virtuel analysant l'agenda de la semaine à venir pour alerter sur les besoins de stocks requis (limes endodontiques rotatives, diamètres d'implants, carpules anesthésiques, sutures résorbables) avant chaque séance.

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

## 10. Clinical Prescribing Principles & Dental Protocols (Virtual Dentist Curriculum)

Cette section définit le référentiel de connaissances académiques et cliniques (recommandations HAS, ANSM et standards odontologiques internationaux) pour l'agent d'aide à la décision thérapeutique.

### 🛡️ A. Sécurisation de l'Antibiothérapie & Prophylaxie
1. **Rationnalisation & Diagnostic** : Un antibiotique ne guérit pas une douleur d'origine mécanique ou inflammatoire (pulpite). Il doit être prescrit uniquement en cas d'infection bactérienne avérée accompagnée de signes généraux (fièvre $\ge 38.5^\circ\text{C}$, œdème progressif, adénopathie, trismus). Il ne remplace jamais le traitement étiologique (ouverture de chambre, parage, avulsion).
2. **Antibioprophylaxie de l'Endocardite Infectieuse (HAS)** :
    - *Indications* : Réservée aux patients à haut risque cardiologique (antécédent d'endocardite, prothèse valvulaire, cardiopathies congénitales cyanogènes) pour tout acte manipulant le tissu gingival ou la région périapicale (détartrage, soins canalaires, avulsions).
    - *Protocole Standard* : Prise unique d'**Amoxicilline 2g** chez l'adulte (50mg/kg chez l'enfant), par voie orale, **1 heure avant** l'acte chirurgical.
    - *Allergie aux bêta-lactamines* : Prise unique de **Clindamycine (Dalacine) 600mg** chez l'adulte (20mg/kg chez l'enfant) ou **Pristinamycine 1g**.
    - *Contre-indications techniques* : Les injections intraligamentaires ou intraosseuses sont formellement proscrites chez le patient à haut risque d'endocardite.

### ⚠️ B. Danger des AINS (Masquage Clinique & Cellulite Cervico-Faciale)
1. **Alerte ANSM Récurrente** : Les AINS (Ibuprofène, Kétoprofène, Aspirine) ont la capacité de masquer les signes d'appel infectieux (fièvre, douleur locale), ce qui retarde le diagnostic et la prise en charge étiologique.
2. **Risque de Cellulite Cervico-Faciale** : La prise d'AINS dans un contexte d'infection bucco-dentaire non traitée ou sans couverture antibiotique favorise la diffusion bactérienne rapide et agressive dans les espaces aponévrotiques profonds, menant à des cellulites cervico-faciales gangreneuses à streptocoques d'une extrême gravité (pronostic vital engagé).
3. **Règle d'Or Prescriptive** :
    - Préférer systématiquement le **Paracétamol** en première intention pour toute douleur d'origine infectieuse suspectée.
    - Ne jamais prescrire d'AINS seul pour un abcès, une péricoronite ou une parodontite active. Si un AINS est cliniquement nécessaire (pulpite hyperalgique), il doit **impérativement** être accompagné d'une couverture antibiotique efficace (Amoxicilline) et d'un traitement local d'urgence sous 24h.
    - Limiter la prescription à la dose efficace la plus faible et à la durée la plus courte possible (3 jours max pour la fièvre, 5 jours max pour la douleur).

### 💉 C. Anesthésie Locale & Vasoconstricteurs (Adrénaline)
1. **Bénéfices de l'Adrénaline** : L'association d'un vasoconstricteur (Adrénaline à 1/100 000 ou 1/200 000) aux molécules d'anesthésie locale (Articaïne 4%, Lidocaïne 2%) est recommandée. Elle ralentit la résorption systémique (diminution de la toxicité), prolonge l'efficacité pulpaire au fauteuil et assure l'hémostase locale du champ opératoire.
2. **Précautions Systémiques** :
    - *Aspiration Systématique* : Le praticien doit réaliser une aspiration dans au moins deux plans avant d'injecter, afin d'éviter toute injection intra-vasculaire directe (risque de tachycardie sévère ou de pic hypertensif).
    - *Limitation des Doses* : Limiter le nombre de cartouches (max 2-3 cartouches d'Articaïne adrénalinée) chez les patients hypertendus sévères non contrôlés, coronariens instables ou souffrant de troubles du rythme cardiaque.
    - *Alternative* : Préférer la **Mépivacaïne sans vasoconstricteur** pour les interventions très courtes chez les patients fragiles.

### 🩸 D. Protocoles pour Terrains Fragiles & Pathologies Générales
1. **Patiente Enceinte (Grossesse)** :
    - *Radioprotection* : Les radiographies de diagnostic sont autorisées en cas de nécessité clinique. Par précaution et pour éliminer le stress maternel, le port du **TABLIER DE PLOMB** avec collerette de protection thyroïdienne est obligatoire.
    - *Anesthésie* : L'Articaïne adrénalinée est parfaitement sûre. Éviter toute injection intra-vasculaire par aspiration rigoureuse.
    - *Pharmacopée* : Paracétamol et Pénicillines sont les molécules de choix. Contre-indication absolue des AINS dès le 6ème mois (risque cardio-pulmonaire fœtal) et des Tétracyclines (dyschromie dentaire fœtale).
2. **Patient sous Anticoagulants (Risque Hémorragique)** :
    - *Interdiction d'arrêt unilatéral* : Ne jamais interrompre un traitement par AVK (Sintrom, Préviscan) ou anticoagulant oral direct (Eliquis, Xarelto) pour un acte chirurgical sans concertation médicale écrite (risque majeur d'accident vasculaire ou thromboembolique).
    - *Hémostase Locale* : Favoriser les techniques de suture compressive (fil résorbable), l'insertion d'éponges de collagène hémostatique dans l'alvéole, et la prescription d'**ACIDE TRANEXAMIQUE (Exacyl)** en application locale (bains de bouche ciblés ou compresses imbibées pendant 10 minutes après l'acte). Ne pas avaler.
3. **Patient Souffrant d'Ulcère Gastroduodénal Actif** :
    - *Contre-indication Formelle* : Les AINS et les corticoïdes systémiques (Prednisolone) sont formellement bannis en raison du risque de perforation ou d'hémorragie digestive haute.
    - *Alternative* : Utiliser exclusivement le Paracétamol. Si les corticoïdes sont inévitables à forte dose, associer systématiquement un inhibiteur de la pompe à protons (Oméprazole 20mg).
4. **Patient Diabétique (Retard de Cicatrisation & Infection)** :
    - *Évaluation* : Évaluer le contrôle glycémique (HbA1c). Si HbA1c > 8% ou glycémie instable, différer les actes chirurgicaux invasifs non urgents.
    - *Anticipation* : Risque élevé d'infections post-opératoires et retard de cicatrisation tissulaire. Prévoir une antibioprophylaxie pré-opératoire et un suivi post-opératoire rapproché pour toute chirurgie osseuse.
217: 5. **Patient Insuffisant Rénal** :
    - *Toxicité médicamenteuse* : Éviter absolument les AINS (néphrotoxicité sévère).
    - *Ajustement* : Pour les antibiotiques éliminés par voie rénale (Amoxicilline), adapter les intervalles d'administration en fonction de la clairance de la créatinine pour éviter les surdosages.

## 11. Cephalometric Analysis Standards & Orthodontics (Ricketts, Steiner, Tweed)

Le clinicien virtuel possède un référentiel rigoureux des tracés géométriques orthodontiques sur téléradiographie de profil.

### 📐 A. Points Céphalométriques Fondamentaux
1. **Points Crâniens & Faciaux** :
    - **S (Sella)** : Centre de la selle turcique.
    - **N (Nasion)** : Point le plus antérieur de la suture fronto-nasale.
    - **Ba (Basion)** : Point le plus antérieur du trou occipital.
    - **Or (Orbitale)** : Point le plus bas du rebord inférieur de l'orbite.
    - **Po (Porion)** : Point le plus supérieur du conduit auditif externe.
2. **Points Maxillaires & Mandibulaires** :
    - **A (Subspinale)** : Point le plus reculé du profil antérieur du maxillaire.
    - **B (Supramentale)** : Point le plus reculé du profil antérieur de la symphyse mandibulaire.
    - **Pog (Pogonion)** : Point le plus antérieur de la symphyse mandibulaire.
    - **Gn (Gnathion)** : Point le plus antérieur et le plus bas de la symphyse.
    - **Me (Menton)** : Point le plus bas du contour inférieur de la symphyse.
    - **Go (Gonion)** : Point le plus postérieur et le plus bas de l'angle mandibulaire.
    - **ANS / PNS** : Épine nasale antérieure / postérieure (délimitant le plan palatin).

### 📊 B. L'Analyse de Ricketts (Diagnostic Architectural)
L'analyse de Ricketts évalue la position des maxillaires par rapport à la base du crâne et le profil esthétique :
1. **Axe Facial (Norme: $90^\circ \pm 3^\circ$)** : Angle formé par la ligne Ba-N et la ligne Pt-Gnathion. Indique la direction de croissance de la mandibule (dolichofaciale si $< 87^\circ$, brachyfaciale si $> 93^\circ$).
2. **Profondeur Faciale (Norme: $87^\circ \pm 3^\circ$)** : Angle formé par le plan de Francfort (Po-Or) et la ligne N-Pog. Détermine le positionnement sagittal de la mandibule (classe II ou classe III squelettique).
3. **Angle du Plan Mandibulaire (Norme: $26^\circ \pm 4^\circ$)** : Angle formé par le plan de Francfort et la ligne tangente au bord inférieur mandibulaire (Go-Me). Renseigne sur l'ouverture verticale du squelette.
4. **Convexité Faciale (Norme: $2\text{mm} \pm 2\text{mm}$ à 9 ans)** : Distance du point A à la ligne faciale (N-Pog). Évalue le décalage sagittal maxillo-mandibulaire.
5. **Incisive Inférieure à A-Po (Norme: $+1\text{mm} \pm 2\text{mm}$)** : Distance séparant le bord libre de l'incisive inférieure de la ligne A-Po. Indique la position esthétique et thérapeutique de la lèvre inférieure.

### 📈 C. Analyses de Steiner & Tweed
1. **Steiner (Diagnostic de Classe)** :
    - **SNA (Norme: $82^\circ$)** : Position sagittale du maxillaire.
    - **SNB (Norme: $80^\circ$)** : Position sagittale de la mandibule.
    - **ANB (Norme: $2^\circ$)** : Décalage inter-maxillaire squelettique (Classe I si $2^\circ \pm 2^\circ$, Classe II si $> 4^\circ$, Classe III si $< 0^\circ$).
2. **Tweed (Triangle Diagnostic)** :
    - **FMA (Norme: $25^\circ$)** : Angle Francfort-Plan Mandibulaire.
    - **IMPA (Norme: $90^\circ$)** : Inclinaison de l'incisive inférieure sur le plan mandibulaire.
    - **FMIA (Norme: $65^\circ$)** : Angle Francfort-Axe Incisive Inférieure ($FMA + IMPA + FMIA = 180^\circ$).

---

## 12. Impacted Third Molar Surgery Protocols & Classifications (Winter, Pell & Gregory)

La chirurgie d'avulsion des troisièmes molaires incluses (dents de sagesse) exige une planification rigoureuse pour prévenir les risques anatomiques (canal alvéolaire inférieur, nerf lingual).

### 📂 A. Classifications de Difficulté Chirurgicale
1. **Classification de Winter (Angulation de la dent par rapport à la 2ème molaire)** :
    - **Mésio-angulée ($43\%$)** : La couronne est inclinée vers l'avant. Difficulté modérée.
    - **Horizontale ($38\%$)** : La dent est couchée horizontalement. Difficulté élevée.
    - **Verticale ($6\%$)** : Orientation normale mais bloquée sous la gencive/l'os. Difficulté faible.
    - **Disto-angulée ($6\%$)** : Inclinée vers l'arrière dans la branche montante. Difficulté maximale (risque de fracture ou refoulement).
2. **Classification de Pell & Gregory (Position spatiale de la 3ème molaire)** :
    - **Espace disponible (Classe I, II, III)** :
        - *Classe I* : Espace suffisant entre la 2ème molaire et la branche montante de la mandibule.
        - *Classe II* : Espace réduit, la moitié de la couronne est logée dans la branche montante.
        - *Classe III* : Espace nul, la dent est totalement emprisonnée dans l'os de la branche montante.
    - **Profondeur d'enclavement (Position A, B, C)** :
        - *Position A* : Le point le plus haut de la couronne est au même niveau que la face occlusale de la 2ème molaire.
        - *Position B* : La couronne est située entre la face occlusale et le collet de la 2ème molaire.
        - *Position C* : La couronne est située sous la ligne cervicale (collet) de la 2ème molaire.

### 🔪 B. Protocole Opératoire Standardisé
1. **Incisions & Lambeau** : Réaliser une incision intra-sulculaire de la 2ème molaire avec décharge mésiale oblique (lambeau de pleine épaisseur) ou incision enveloppe pour exposer l'os cortical externe.
2. **Ostéotomie** : Résection de l'os cortical supérieur et vestibulaire à l'aide d'une fraise boule en carbure de tungstène montée sur pièce à main chirurgicale sous irrigation stérile continue de sérum physiologique (éviter la nécrose thermique osseuse).
3. **Odontosection** : Séparation de la couronne et des racines à l'aide d'une fraise fissure (carbure de tungstène) pour diviser la dent en morceaux faciles à extraire sans forcer sur l'os (évite les fractures mandibulaires et lèse moins le nerf alvéolaire).
4. **Élévation & Avulsion** : Luxation progressive des fragments à l'aide d'élevateurs droits (Bein) ou de cryers, sans appui sur la face distale de la 2ème molaire.
5. **Nettoyage & Suture** : Curetage rigoureux du follicule péricoronaire, régularisation osseuse (fraise lime), lavage abondant sous pression (sérum phy) pour éliminer les débris d'os et de dent, et suture hermétique par points séparés (fil résorbable 3-0 ou 4-0).

### 🛠️ C. Plateau Technique / Matériel Requis
- **Instruments de diagnostic** : Sonde, miroir, précelle, radiographie panoramique ou CBCT (Cône Beam) si contact avec le canal alvéolaire inférieur suspecté.
- **Instruments de lambeau** : Bistouri (lame 15), syndesmotome, décolleur (Molt/Prichard).
- **Instruments d'ostéotomie/section** : Pièce à main chirurgicale rotative (contre-angle chirurgical), fraises en carbure de tungstène (boule et fissure longues).
- **Instruments d'avulsion** : Élévateurs de Bein (étroit et large), élévateur de Barry ou Apexo, pinces gouges pour régularisation.
- **Suture** : Porte-aiguille, ciseaux de chirurgie, aiguille avec fil (soie ou acide polyglycolique).

### ⚠️ D. Complications Chirurgicales & Gestion
1. **Lésion du Nerf Alvéolaire Inférieur / Lingual** : Risque de paresthésie ou d'anesthésie de l'hémi-lèvre inférieure et du menton (nerf dentaire) ou de l'hémi-langue (nerf lingual).
    - *Prévention* : Analyse CBCT si la racine chevauche le canal ; odontosection atraumatique ; éviter d'enfoncer les élévateurs en lingual.
2. **Alvéolite Sèche (Dry Socket)** : Perte précoce du caillot sanguin entraînant une exposition osseuse hyperalgique à 3-4 jours post-opératoires.
    - *Traitement* : Lavage de l'alvéole, application locale d'un pansement sédatif antiseptique (Alvéogyl).
3. **Communication Bucco-Sinusienne (CBS)** : Pour les dents de sagesse supérieures (proximité du sinus maxillaire).
    - *Traitement* : Suture étanche du lambeau, prescription d'antibiotiques et interdiction absolue de se moucher fort pendant 10 jours.

## 13. Advanced Periodontics & AAP 2017 Classifications

Le clinicien virtuel applique rigoureusement la classification internationale EFP/AAP 2017 pour poser le diagnostic et la stratégie thérapeutique parodontale.

### 📊 A. Détermination du Staging (Sévérité & Complexité)
1. **Stage I (Initial)** : Perte d'attache clinique (CAL) de $1-2\text{ mm}$, RBL sous le tiers coronaire ($<15\%$). Aucune perte dentaire parodontale.
2. **Stage II (Modéré)** : CAL de $3-4\text{ mm}$, RBL au tiers coronaire ($15\%-33\%$). Aucune perte dentaire.
3. **Stage III (Sévère)** : CAL $\ge 5\text{ mm}$, RBL s'étendant au-delà du tiers coronaire. $\le 4$ dents perdues à cause de la parodontite. Profondeurs de poche $\ge 6\text{ mm}$ et atteinte des furcations de classe II ou III.
4. **Stage IV (Avancé)** : RBL extrême, $\ge 5$ dents perdues, dysfonction masticatoire, migrations dentaires secondaires, effondrement de l'articulé dentaire.

### 📈 B. Détermination du Grading (Risque de Progression)
1. **Grade A (Progression Lente)** : Aucun historique de perte osseuse sur 5 ans. Rapport Perte Osseuse / Âge $<0.25$. Patient non-fumeur, non-diabétique.
2. **Grade B (Progression Modérée)** : Perte osseuse $<2\text{ mm}$ sur 5 ans. Rapport Perte Osseuse / Âge de $0.25-1.0$.
3. **Grade C (Progression Rapide)** : Perte osseuse $\ge 2\text{ mm}$ sur 5 ans. Rapport Perte Osseuse / Âge $>1.0$. Fumeur actif ($\ge 10\text{ cig/jour}$) ou patient diabétique déséquilibré ($HbA1c \ge 7.0\%$).

### 💊 C. Protocole Thérapeutique
- **Détartrage & Surfaçage Radiculaire (SRP)** : Sous anesthésie locale, élimination du tartre sous-gingival et du biofilm bactérien. Irrigation à la Chlorhexidine $0.12\%$.
- **Traitement Adjuvant (Grade C)** : Co-prescription systématique d'**Amoxicilline 500mg + Métronidazole 500mg** x3/jour pendant 7 jours en accompagnement immédiat du SRP.

---

## 14. Pedodontics, MIH & Dental Trauma Management

La prise en charge des jeunes patients exige des protocoles de radioprotection, des thérapeutiques pulpaires spécifiques et une réactivité absolue en traumatologie.

### 🍭 A. Molar-Incisor Hypomineralization (MIH)
- **Diagnostic** : Opacités délimitées blanches/jaunes ou brunes sur les premières molaires et incisives permanentes, très sensibles aux variations thermiques. Émail poreux à risque de fracture sous les forces occlusales.
- **Protocole** : Brossage avec dentifrice à haute teneur en fluor ($1450\text{ ppm}$ minimum), application locale de vernis fluoré ($22\ 600\text{ ppm}$), ciment verre ionomère (CVI) modifié par résine ou coiffe préformée en acier inoxydable (SSC) pour les molaires fortement dégradées. Proscrire les composites classiques en direct sans traitement reminéralisant de surface.

### 🦷 B. Traumatologie & Lignes Directrices de l'IADT
1. **Dents Temporaires (de lait)** :
    - *Avulsion (Expulsion)* : **NE JAMAIS RÉIMPLANTER une dent de lait expulsée**. Risque immédiat de nécrose ou de traumatisme mécanique sur le germe de la dent permanente sous-jacente.
2. **Dents Permanentes** :
    - *Avulsion* : **Réimplantation immédiate requise (idéalement dans les 60 minutes)**. Conserver la dent dans un milieu humide adapté (lait UHT, sérum physiologique, salive du patient) ; ne jamais conserver la dent à sec ni dans de l'eau.
    - *Contention* : Splinting flexible de protection (2 semaines pour subluxation/avulsion, 4 semaines pour luxation latérale ou fracture radiculaire moyenne).

---

## 15. Prosthodontics, VDO & Biological Width Standards

La réhabilitation prothétique (couronnes, bridges, facettes) doit respecter les tissus d'ancrage biologiques et l'harmonie neuromusculaire de l'occlusion.

### 🛡️ A. Respect de l'Espace Biologique (Attache Supracrestale)
- **Règle d'or** : Une distance minimale de **$2\text{ mm}$** d'os sain doit impérativement séparer la limite cervicale de la prothèse de la crête osseuse alvéolaire (comprenant l'attache épithéliale et conjonctive).
- **Conséquence de la violation** : Inflammation gingivale rebelle, récession gingivale ou lyse osseuse localisée.
- **Remédiation** : Si une limite prothétique s'approche à $<2\text{ mm}$ de l'os en raison d'une carie ou d'une fracture, le clinicien doit imposer une **élongation coronaire chirurgicale** ou une **extrusion orthodontique** avant de réaliser la prothèse définitive.

### 📐 B. Dimension Verticale d'Occlusion (DVO) & Guidage
- **DVO** : La perte de hauteur faciale (usure sévère par bruxism ou édentations multiples) exige une reconstruction par étapes (gouttière de surélévation en résine, puis restaurations provisoires) avant toute prothèse d'usage.
- **Guidage Canin** : Assurer un guidage canin exclusif lors des mouvements de latéralité pour désocclure immédiatement les dents postérieures (évite les forces de cisaillement sur les couronnes et implants postérieurs).

---

## 16. Guided Implantology & Safety Boundaries

La chirurgie implantaire exige une planification tridimensionnelle stricte des axes de forage pour protéger les structures nobles.

### 📐 A. Distances de Sécurité Tridimensionnelles
1. **Canal Alvéolaire Inférieur (IAN)** : Marge de sécurité apicale de **$2\text{ mm}$** au-dessus du toit du canal pour éliminer tout risque de paresthésie ou d'anesthésie de la lèvre et du menton.
2. **Trou Mentonnier (Mental Foramen)** : Distance de **$3\text{ mm}$** en antérieur de l'émergence pour anticiper la boucle antérieure du nerf.
3. **Implant - Racine Naturelle Adjacente** : **$1.5\text{ mm}$** minimum pour préserver l'os crestal de la dent voisine et maintenir la vitalité pulpaire.
4. **Implant - Implant** : **$3\text{ mm}$** de sécurité inter-implantaire pour préserver le pic osseux et la papille gingivale.

### 📊 B. Densité Osseuse (Classification de Lekholm & Zarb)
- **D1** : Os cortical presque homogène. Très bonne stabilité primaire, mais risque d'échauffement de l'os au forage (irrigation stérile sous pression obligatoire).
- **D2** : Corticale épaisse entourant un os trabéculaire dense. Densité idéale.
- **D3** : Corticale mince entourant un os trabéculaire de densité moyenne.
- **D4** : Corticale très mince entourant un os trabéculaire de faible densité (maxillaire postérieur). Stabilité primaire délicate (forage sous-dimensionné requis).

---

## 17. Oral Medicine, Mucosal Pathology & Cancer Screening

La détection précoce des cancers de la cavité buccale est un devoir de vigilance absolue pour chaque omnipraticien.

### 🔍 A. Règle des 14 jours (Dépistage du Carcinome Épidermoïde)
- **Protocole** : Toute lésion muqueuse rouge (érythroplasie), blanche (leucoplasie) ou ulcérée qui **ne guérit pas au bout de 14 jours** (après élimination des facteurs traumatiques locaux, ex: dent cassée agressive, crochet de prothèse) **doit impérativement être orientée pour biopsie anatomopathologique**.
- **Indication** : Les carcinomes épidermoïdes buccaux débutants se font passer pour de simples aphtes ou des lésions d'irritation mécanique.

### 🦠 B. Pathologies Infectieuses Communes
- **Candidose Buccale (Muguet)** : Traitement local par suspension de Nystatine ou Miconazole en gel buccal pendant 14 jours.
- **Herpès Simplex Buccal** : Prescription précoce d'Aciclovir oral en phase prodromique.




## 18. Multi-Tenant SaaS Isolation (Tenant Boundary)
**Trigger**: Création de nouveaux modèles SQLAlchemy, de routes API ou requêtes de base de données.
**Steps**:
1. Assurer que chaque nouveau modèle lié à une clinique possède une foreign key `employer_id` pointant vers le compte principal du cabinet.
2. Dans les routes FastAPI, récupérer toujours l'identifiant du cabinet via `current_user.get_employer_id()`.
3. Filtrer systématiquement les requêtes de lecture (`db.query()`) avec `.filter(Model.employer_id == user_employer_id)`, sauf mention contraire justifiée (ex: accès super-admin avec `assert_patient_access`).
4. Lors de l'insertion (CREATE), injecter automatiquement l'`employer_id` depuis le backend.
**Output**: Des données strictement cloisonnées garantissant l'étanchéité absolue entre différents cabinets (Architecture SaaS).
**Rules**:
- NEVER oublier le filtre `employer_id` sur une route renvoyant des listes.
- NEVER faire confiance au client (frontend) pour définir l'`employer_id` ; il doit toujours être dérivé du token d'authentification du serveur.

## 19. Architecture LAN-First & ZKA (Mobile Companion)
**Trigger**: Développement du compagnon mobile PWA, des endpoints ZKA ou de la synchronisation Cloud.
**Steps**:
1. Le compagnon mobile communique exclusivement via le réseau local (LAN) avec le serveur principal (Hub).
2. L'authentification se fait via un QR Code éphémère (`/api/mobile/claim-token`). Le JWT généré est spécifique au mobile (`type="mobile"`) et restreint à l'`employer_id`.
3. Le `SyncManager` s'occupe de la réplication vers le Cloud (Supabase) en arrière-plan sans bloquer les requêtes locales.
4. En cas de perte de connexion Cloud, le système bascule en "Grace Period" localement via le `LicenseService` pour garantir une continuité clinique sans interruption.
**Output**: Une application clinique ultra-résiliente (Offline-First) qui protège la donnée localement.
**Rules**:
- NEVER bloquer l'interface utilisateur (React) pour attendre une réponse du Cloud ; le serveur local est la source de vérité absolue.
- NEVER exposer de données de santé sans validation stricte du token, même sur le réseau local interne.

## 20. Nomenclature CNOPS/CNSS & Codes NGAP Dentaires (Maroc)
**Trigger**: Développement de fonctionnalités liées à l'assurance maladie, à la facturation ou à l'édition de fiches de soins CNOPS/CNSS.
**Steps**:
1. Utiliser strictement les codes de la **Nomenclature Générale des Actes Professionnels (NGAP)** marocaine (lettre-clé **D**).
2. Pour les formulaires CNOPS/CNSS, s'assurer que le numéro de la dent (système FDI 11-48), la lettre-clé (ex: D) et le coefficient (ex: 30) soient clairement identifiables. Le Tarif National de Référence (TNR) est calculé par : Coefficient × Valeur du D.
3. Distinguer les soins conservateurs des prothèses (la valeur monétaire du "D" peut varier selon la convention).
4. **Exemples de cotations courantes** :
    - **Consultation** : Code **C** ou **C DENT**.
    - **Détartrage** : Souvent coté de **D15** à **D30** selon les arcades.
    - **Extraction simple** : **D15** (dent temporaire ou monoradiculaire) à **D20** (pluriradiculaire).
    - **Extraction chirurgicale** (dent incluse/enclavée) : Souvent **D30** à **D50**.
    - **Soins conservateurs (Composite, Amalgame)** : Cotés selon le nombre de faces, ex: **D15** (1 face), **D25** (2 faces), **D35** (3 faces et plus).
    - **Prothèse** : ex: Couronne (souvent **D50**).
5. **Gestion des devis et accords préalables** : Pour les actes prothétiques et l'orthodontie, les fiches doivent inclure la possibilité d'imprimer une "Demande d'Entente Préalable" avec schéma dentaire.
**Output**: Des fiches de soins et factures conformes aux exigences des organismes marocains (CNSS, CNOPS).
**Rules**:
- NEVER utiliser des codes arbitraires pour la facturation AMO ; respecter la lettre "D".
- NEVER oublier l'INPE (Identifiant National du Professionnel de Santé) sur les feuilles de maladie.
- NEVER cumuler arbitrairement une consultation (C) avec des soins (D) lors d'une même séance (règle générale de la NGAP : seul l'acte le plus élevé est pris en charge, sauf dérogations spécifiques).

## 6. Guide de Prescription Odontologique (Maroc) - Posologie Poids/Age
**Context**: Le système doit pouvoir assister le praticien (ou agir via Ghost Brain) pour suggérer des ordonnances sécurisées, particulièrement en pédiatrie où la dose dépend du poids et de l'âge.
**Pharmacopée courante en Odontologie au Maroc** :
### A. Antalgiques / Antipyrétiques
1. **Paracétamol (Doliprane, Tylenol, etc.)** :
   - **Indication** : Douleur légère à modérée, première intention.
   - **Pédiatrie** : 15 mg/kg toutes les 6 heures (Max 60 mg/kg/jour). Formes : Sirop (dose-poids), suppositoires.
   - **Adulte** : 500 mg à 1g par prise, max 3g/jour (ou 4g sur avis médical).
2. **Ibuprofène (AINS - Nurofen, Advil, etc.)** :
   - **Indication** : Douleur modérée à sévère avec composante inflammatoire.
   - **Pédiatrie** : 20 à 30 mg/kg/jour en 3 à 4 prises. Contre-indiqué si infection sévère (risque de cellulite fasciale) ou varicelle.
   - **Adulte** : 200 à 400 mg par prise, max 1200 mg/jour.

### B. Antibiotiques (Anti-infectieux)
1. **Amoxicilline (Clamoxyl, Ospamox, etc.)** :
   - **Indication** : Antibiotique de première intention pour les infections dentaires.
   - **Pédiatrie** : 50 mg/kg/jour répartis en 2 ou 3 prises. (Prophylaxie endocardite : 50 mg/kg en dose unique 1h avant l'acte).
   - **Adulte** : 1g à 2g/jour en 2 prises. (Prophylaxie : 2g en dose unique).
2. **Amoxicilline + Acide Clavulanique (Augmentin, Ciblor, etc.)** :
   - **Indication** : Infections sévères ou résistantes.
   - **Pédiatrie** : 80 mg/kg/jour (exprimé en Amoxicilline) en 3 prises.
   - **Adulte** : 1g matin et soir (ou 3g/jour si infection sévère).
3. **Macrolides (Azithromycine - Zithromax ; Spiramycine - Rovamycine)** :
   - **Indication** : En cas d'allergie aux Pénicillines.
   - **Azithromycine Pédiatrie** : 20 mg/kg/jour pendant 3 jours.
   - **Spiramycine Adulte** : 6 à 9 millions d'UI/jour en 2 ou 3 prises.
4. **Association Spiramycine + Métronidazole (Birodogyl, Rodogyl)** :
   - **Indication** : Parodontites, infections anaérobies.
   - **Adulte** : 4 à 6 comprimés par jour en 2 ou 3 prises.
   - **Enfant (6-15 ans)** : Adapter selon la spécialité (généralement 1/2 dose adulte).

### C. Corticoïdes (Anti-inflammatoires stéroïdiens)
1. **Prednisolone, Bétaméthasone (Solupred, Célestène)** :
   - **Indication** : Œdème post-opératoire important (ex: extraction dents de sagesse).
   - **Pédiatrie** : 1 à 2 mg/kg/jour en cure courte (3-5 jours), le matin.
   - **Adulte** : 1 mg/kg/jour (max 80mg) en cure courte.

**Intégration Ghost Brain (Roadmap)** :
- Ajouter un composant PrescriptionGuideAgent (bouton hover flottant dans PrescriptionAgenticStudio).
- Si l'âge du patient est < 15 ans, ouvrir automatiquement une modale demandant le **poids** (en Kg).
- L'IA Ghost Brain génère la posologie exacte (ex: 'Sirop Doliprane 2.4% - Pipette dose-poids') en utilisant le poids fourni, et l'ajoute au document.
