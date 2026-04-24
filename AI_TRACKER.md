# 👑 Digital Crown - AI Project Tracker

Ce fichier est le **point de référence vivant** de l'agent IA. Il sera mis à jour systématiquement à chaque modification significative de l'application pour garantir un contexte persistant entre les différentes sessions.

## 📌 État Actuel du Projet
- **Version** : 5.0 (Ghost Elite & Secure QR Validation)
- **Stack** : FastAPI (Python 3.12) / React 19 (TypeScript) / TailwindCSS 4 / Recharts / WeasyPrint
- **Dernière M.A.J** : 22 Avril 2026 (Ghost Elite Rebranding & QR Integration)

---

## 🏗️ Architecture Technique Référente

### Backend (Port 8000)
- **Point de départ :** `backend/main.py`
- **Moteur Géométrique :** `backend/services/cephalo_engine.py` (Calculs COM V4)
- **Moteur Vision (ML) :** `backend/services/vision_service.py` (CephLD-CCA / U-Net)
- **Moteur Diagnostic (LLM) :** `backend/services/ai_advisor.py` (Ollama/Llama 3.2 local)
- **Générateurs PDF :** `backend/services/generators/` (Migration progressive vers WeasyPrint/Jinja2)
- **Service QR :** `backend/services/qr_service.py` (Validation sécurisée)
- **Base de données :** PostgreSQL (config: `backend/database.py`)

### Frontend (Port 5173)
- **Interface Base :** `frontend/src/`
- **Branding Engine :** `frontend/src/components/Layout/MainLayout.tsx` (CSS Variables Source of Truth)
- **Composants Analytiques :** `frontend/src/pages/AccountingPage.tsx` (Intégration Recharts)
- **Studio Comptable :** `frontend/src/features/admin/AccountingStudio.tsx` (UX Zero-Friction)

---

## 🚀 Fonctionnalités Clés Implémentées

1. **Analyse Céphalométrique Automatisée :** De l'upload radio (Vision PyTorch) jusqu'au compte rendu clinique (ReportLab/WeasyPrint), incluant les calculs COM et le diagnostic assisté.
2. **Odontogramme Interactif :** Interface graphique de suivi patient avec les nomenclatures (11-48, etc) et une logique de devis.
3. **Sécurité et Anti-Doublons :** Logiques en place pour les saisies patients, avec module d'archivage des documents avec délai de rétention.
4. **Design Ghost Elite** : Thème ultra-premium entièrement basé sur des variables CSS (`--primary`, `--secondary`), synchronisé entre le dashboard, la compta et les réglages.
5. **Visual Insights** : Graphiques de performance (Recharts) intégrés au Studio Comptable pour le suivi des revenus.
6. **Validation QR** : Signature numérique QR sur les documents (Ordonnances) pour certifier l'authenticité via `qr_service`.

---

## 🔄 Registre des Modifications (Changelog Actif)

| Date | Agent / Action | Fichiers Modifiés | Statut |
|------|----------------|-------------------|--------|
| 22/04/2026 | **Refonte Ghost Elite (Phase 1-4)** : Suppression des couleurs hardcodées, passage au branding dynamique CSS. Intégration Recharts dans `AccountingPage`. Optimisation UX `AccountingStudio` (Actes Rapides). Implémentation QR Validation & Migration `OrdonnanceGenerator` vers WeasyPrint. | `MainLayout.tsx`, `Dashboard.tsx`, `AccountingPage.tsx`, `Settings.tsx`, `AccountingStudio.tsx`, `qr_service.py`, `ordonnance_gen.py`, `base_elite.html` | ✅ |
| 23/04/2026 | **Phase 6 : Synchronisation & Rendu "Ghost Elite"** : Intégration des métriques esthétiques (Ricketts), Auto-Calibration IA, et Color-Coding des déviations. Certification PDF v4.6 stable. | `CephaloWorkspace.tsx`, `Step3Clinical.tsx`, `cephalo_gen.py`, `cephaloTypes.ts` | ✅ |

---

## 🎯 Prochaines Actions & Todo

- [x] **Smart QR Validation** : Implémenter la signature numérique QR sur les documents.
- [ ] **Validation Impresseur** : Confirmer l'alignement millimétré du papier en-tête physique vs PDF.
- [ ] **Morphing T2** : Finalisation du moteur de prédiction de croissance.
- [ ] **UX "Zero-Friction" Full** : Drag-and-Drop pour la réorganisation des actes dans le Studio.
- [ ] **Reporting PDF Global** : Migrer tous les générateurs (Certificat, Devis, Note) vers WeasyPrint + QR.

---

> **Note interne à l'IA :** Toujours valider les paths en absolu ou relatifs au dossier racine (`DigitalCrown/`) et actualiser la section `Registre des Modifications` quand des refactorisations ou nouvelles logiques sont injectées.
