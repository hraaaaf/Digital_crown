# 👑 Digital Crown - AI Project Tracker

Ce fichier est le **point de référence vivant** de l'agent IA. Il sera mis à jour systématiquement à chaque modification significative de l'application pour garantir un contexte persistant entre les différentes sessions.

## 📌 État Actuel du Projet
- **Version** : 4.0 (Master Template Native & Identifiants Légaux)
- **Stack** : FastAPI (Python 3.12) / React 19 (TypeScript) / TailwindCSS 4
- **Dernière M.A.J** : 20 Avril 2026 (Native Engine v4.0 - Migration Vectorielle)

---

## 🏗️ Architecture Technique Référente

### Backend (Port 8000)
- **Point de départ :** `backend/main.py`
- **Moteur Géométrique :** `backend/services/cephalo_engine.py` (Calculs COM V4)
- **Moteur Vision (ML) :** `backend/services/vision_service.py` (CephLD-CCA / U-Net)
- **Moteur Diagnostic (LLM) :** `backend/services/ai_advisor.py` (Ollama/Llama 3.2 local)
- **Générateurs PDF :** `backend/services/generators/` (ReportLab)
- **Base de données :** PostgreSQL (config: `backend/database.py`)

### Frontend (Port 5173)
- **Interface Base :** `frontend/src/`
- **Routing :** React Router
- **Composants Transverses :** `frontend/src/components/`
- **Setup Wizard & Studio :** `frontend/src/features/admin/SetupWizard.tsx` (Architecture v4.0 optimisée avec `useMemo` et `useCallback`)
- **Composants Studio :** `frontend/src/features/admin/components/LiveDocumentStudio.tsx` (Moteur de rendu WYSIWYG isolé) et `CrownGuide.tsx`
- **Odontogramme FDI :** `frontend/src/components/odontogram/` (Interactif SVG)

---

## 🚀 Fonctionnalités Clés Implémentées

1. **Analyse Céphalométrique Automatisée :** De l'upload radio (Vision PyTorch) jusqu'au compte rendu clinique (ReportLab), incluant les calculs COM et le diagnostic assisté.
2. **Odontogramme Interactif :** Interface graphique de suivi patient avec les nomenclatures (11-48, etc) et une logique de devis.
3. **Sécurité et Anti-Doublons :** Logiques en place pour les saisies patients, avec module d'archivage des documents avec délai de rétention.
4. **Design** : Choix entre en-tête automatique (Logo + Texte) ou Papier en-tête pré-imprimé (A5).
    *   **Template Studio** : Choix du layout (`modern`, `classic`, `minimal`).
5. **Ambiance** : Sélection du thème global (`elite`, `emerald`, `prestige`) avec application instantanée via variables CSS.

---

## 🔄 Registre des Modifications (Changelog Actif)

| Date | Agent / Action | Fichiers Modifiés | Statut |
|------|----------------|-------------------|--------|
| 15/04/2026 | Refonte de l'archivage en base de données, implémentation option Modifier/Régénérer et Suppression logique (Corbeille). Fix nettoyage linter. | `main.py`, `PatientDocuments.tsx`, `PatientDetails.tsx`, `DocumentHub.tsx` | ✅ |
| 15/04/2026 | Initialisation de la documentation de suivi (`AI_TRACKER.md`). | `AI_TRACKER.md` | ✅ |
| 18/04/2026 | Stabilisation critique du SetupWizard (v1.1). Fix erreurs de scope (specialties) et structure JSX (LiveDocumentStudio). Synchronisation des thèmes. | `SetupWizard.tsx`, `ROADMAP.md`, `AGENTS.md` | ✅ |
| 18/04/2026 | Intégration du Template Studio dans le Wizard. Sélection de 3 modèles de layouts avec prévisualisation dynamique. | `SetupWizard.tsx`, `ROADMAP.md`, `AGENTS.md` | ✅ |
| 18/04/2026 | Déploiement du Branding Engine (v3.0). Personnalisation typographique (Premium Fonts) et chromatique (Elite Colors). | `SetupWizard.tsx`, `ROADMAP.md`, `AGENTS.md` | ✅ |
| 18/04/2026 | **Stabilisation Technique Finale** : Correction du typage `CabinetConfig` (couleurs secondaires/accent), unification du nommage (`primary_color`), fix des imports d'icônes Lucide et nettoyage linter. Synchronisation critique du mode Démo. Migration DB auto implémentée pour `secondary_color` et `accent_color`. Correction du conflit de schémas `CabinetConfigOut`. | `template.ts`, `SetupWizard.tsx`, `MainLayout.tsx`, `Sidebar.tsx`, `WelcomeScreen.tsx`, `database.py`, `schemas.py`, `main.py` | ✅ |
| 19/04/2026 | **Refactoring Architectural 10/10** : Extraction de `LiveDocumentStudio` et `CrownGuide` pour éliminer les re-rendus. Optimisation performance (hooks), support Arabe diacritique, confirmation IA extraction, et validation contacts Step 3. | `SetupWizard.tsx`, `LiveDocumentStudio.tsx`, `CrownGuide.tsx`, `AI_TRACKER.md` | ✅ |
| 20/04/2026 | **Sécurisation Live Preview (v4.1)** : Résolution de `RuntimeError: Response content shorter than Content-Length` via l'implémentation d'un nommage unique avec horodatage (seconde) dans tous les générateurs. Isolation des imports critiques pour la stabilité ASGI. | `accounting_gen.py`, `libre_gen.py`, `ordonnance_gen.py`, `certificat_gen.py`, `template_engine.py` | ✅ |
| 20/04/2026 | **Master Template Native (v4.0)** : Transition complète vers un moteur vectoriel sans images de fond. Centralisation de la mise en page dans `BaseTemplate`. Intégration des identifiants ICE, IF, INPE dans `CabinetConfig` et affichage conditionnel sur les factures/devis. Mise à jour de l'UI Settings. | `base_template.py`, `models.py`, `schemas.py`, `clinics.py`, `Settings.tsx`, `accounting_gen.py`, `ordonnance_gen.py`, `certificat_gen.py`, `libre_gen.py`, `cephalo_gen.py` | ✅ |

---

## 🎯 Prochaines Actions & Todo (À remplir lors des directives)

- [ ] **Validation Impresseur** : Confirmer l'alignement millimétré du papier en-tête physique vs PDF.
- [ ] **Morphing T2** : Finalisation du moteur de prédiction de croissance.
- [ ] **Audit Accessibilité** : Vérifier le contraste des thèmes `emerald` et `prestige`.

---

> **Note interne à l'IA :** Toujours valider les paths en absolu ou relatifs au dossier racine (`DigitalCrown/`) et actualiser la section `Registre des Modifications` quand des refactorisations ou nouvelles logiques sont injectées.
