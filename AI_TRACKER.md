# 👑 Digital Crown - AI Project Tracker

Ce fichier est le **point de référence vivant** de l'agent IA. Il sera mis à jour systématiquement à chaque modification significative de l'application pour garantir un contexte persistant entre les différentes sessions.

## 📌 État Actuel du Projet
- **Version** : 1.1 (En développement actif)
- **Stack** : FastAPI (Python 3.12) / React 19 (TypeScript) / TailwindCSS
- **Dernière M.A.J** : 15 Avril 2026

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
- **Modules Dépérisés :** `features/patients`, `features/ortho`, `features/admin`
- **Odontogramme FDI :** `frontend/src/components/odontogram/` (Interactif SVG)

---

## 🚀 Fonctionnalités Clés Implémentées

1. **Analyse Céphalométrique Automatisée :** De l'upload radio (Vision PyTorch) jusqu'au compte rendu clinique (ReportLab), incluant les calculs COM et le diagnostic assisté.
2. **Odontogramme Interactif :** Interface graphique de suivi patient avec les nomenclatures (11-48, etc) et une logique de devis.
3. **Sécurité et Anti-Doublons :** Logiques en place pour les saisies patients, avec module d'archivage des documents avec délai de rétention.
4. **Dashboard & UI :** Implémentation via React et classes utilitaires Tailwind (Glassmorphism / Design moderne).

---

## 🔄 Registre des Modifications (Changelog Actif)

| Date | Agent / Action | Fichiers Modifiés | Statut |
|------|----------------|-------------------|--------|
| 15/04/2026 | Initialisation de la documentation de suivi (`AI_TRACKER.md`). | `AI_TRACKER.md` | ✅ |

---

## 🎯 Prochaines Actions & Todo (À remplir lors des directives)

- [ ] *En attente de tâche liée à l'évolution du frontend ou backend.*
- [ ] *Affinage des API.*
- [ ] *Débogage UI/UX si nécessaire.*

---

> **Note interne à l'IA :** Toujours valider les paths en absolu ou relatifs au dossier racine (`DigitalCrown/`) et actualiser la section `Registre des Modifications` quand des refactorisations ou nouvelles logiques sont injectées.
