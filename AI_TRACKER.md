# 👑 Digital Crown - AI Project Tracker

Ce fichier est le **point de référence vivant** de l'agent IA. Il sera mis à jour systématiquement à chaque modification significative de l'application pour garantir un contexte persistant entre les différentes sessions.

## 📌 État Actuel du Projet
- **Version** : 1.8 (Elite Panoramic & Specialized Taxonomy)
- **Stack** : FastAPI (Python 3.12) / React 19 (TypeScript) / Beads + Dolt (Memory) / ReportLab
- **Dernière M.A.J** : 12 Mai 2026 (Elite Panoramic Hub, Specialized Taxonomy, Auto-Hide Tips)

---

## 🏗️ Architecture Technique Référente

### Backend (Port 8000)
- **Point de départ :** `backend/main.py`
- **Moteur Géométrique :** `backend/services/cephalo_engine.py` (Calculs COM V4)
- **Moteur Vision (ML) :** `backend/services/vision_service.py` (CephLD-CCA / U-Net)
- **Moteur Panoramique :** `backend/services/panoramic_service.py` (YOLOv11 ONNX)
- **Moteur Diagnostic (LLM) :** `backend/services/ai_advisor.py` (Ollama/Llama 3.2 local)
- **Moteur de Rapport :** `backend/services/panoramic_report_engine.py` (Hybride IA/Expert)
- **Moteur d'Habitudes :** `backend/services/accounting_service.py` (Apprentissage clinique)
- **Générateurs PDF :** `backend/services/generators/` (ReportLab / WeasyPrint)
- **Service QR :** `backend/services/qr_service.py` (Validation sécurisée)
- **Base de données :** PostgreSQL (config: `backend/database.py`)

### Frontend (Port 5173)
- **Interface Base :** `frontend/src/`
- **Studio Panoramique :** `frontend/src/features/panoramic/PanoramicStudio.tsx` (Elite Hub)
- **Branding Engine :** `frontend/src/components/Layout/MainLayout.tsx` (CSS Variables Source of Truth)
- **Composants Analytiques :** `frontend/src/pages/AccountingPage.tsx` (Intégration Recharts)
- **Studio Comptable :** `frontend/src/features/admin/AccountingStudio.tsx` (UX Zero-Friction)

---

## 🚀 Fonctionnalités Clés Implémentées

1. **Analyse Céphalométrique Automatisée :** De l'upload radio (Vision PyTorch) jusqu'au compte rendu clinique (ReportLab/WeasyPrint), incluant les calculs COM et le diagnostic assisté.
2. **Hub Panoramique ELITE v2.0 :** Diagnostic assisté par IA avec taxonomie spécialisée (6 pôles cliniques), gestion des zones (Bridges) et rapport PDF hybride structuré par secteur FDI.
3. **Elite Clinical Tips :** Système de conseils cognitifs discret (Auto-hide 2s) positionné systématiquement en haut à gauche.
4. **Odontogramme Interactif :** Interface graphique de suivi patient avec les nomenclatures (11-48, etc) et une logique de devis.
5. **Sécurité et Anti-Doublons :** Logiques en place pour les saisies patients, avec module d'archivage des documents avec délai de rétention.
6. **Design Ghost Elite** : Thème ultra-premium entièrement basé sur des variables CSS (`--primary`, `--secondary`), synchronisé entre le dashboard, la compta et les réglages.

---

## 🔄 Registre des Modifications (Changelog Actif)

| Date | Agent / Action | Fichiers Modifiés | Statut |
|------|----------------|-------------------|--------|
| 22/04/2026 | **Refonte Ghost Elite (Phase 1-4)** | `MainLayout.tsx`, etc. | ✅ |
| 23/04/2026 | **Phase 6 : Synchronisation & Rendu "Ghost Elite"** | `CephaloWorkspace.tsx`, etc. | ✅ |
| 29/04/2026 | **v1.3 : Habits & Learning Engine** : Implémentation du moteur d'apprentissage clinique `DoctorActHabit`. Dynamisation des Quick Acts. Ajout du tri par N° Dossier et Date de création. Automatisation de l'apprentissage lors de la génération de documents. | `models.py`, `accounting_service.py`, `accounting.py`, `documents.py`, `AccountingStudio.tsx`, `PatientList.tsx` | ✅ |
| 30/04/2026 | **Correction Sérialisation & Optimisation Panoramique SOTA** : Résolution du crash JSON (float32). Injection de CLAHE. Refonte du mapping FDI (Smile Curve). Correction de l'ordre des classes DENTEX. | `sota_panoramic_service.py`, `panoramic_expert_engine.py` | ✅ |
| 30/04/2026 | **Ghost Elite Panoramic Refinement** : Implémentation du mapping parabolique (Smile Curve) pour une numérotation FDI précise. Optimisation des seuils de confiance et du prétraitement d'image. | `sota_panoramic_service.py` | ✅ |
| 30/04/2026 | **Ghost Elite Refinement** : Précision sub-pixel (Centre de Masse local). Ajout des métriques de Steiner (SNA, SNB, ANB) et de l'Angle Nasolabial. Optimisation de la spline du profil (points Ls2, Li2). | `sota_vision_service.py`, `cephalo_engine.py`, `CephaloTracingLayer.tsx` | ✅ |
| 30/04/2026 | **Elite Calibration v1.5.3** : Rectification du mapping FDI (45->46, 34->35). Boost de contraste CLAHE (4.5) pour la détection apicale et des caries profondes. | `sota_panoramic_service.py` | ✅ |
| 12/05/2026 | **v1.8 : Elite Panoramic & Clinical Insights** : Déploiement du Hub Panoramique v2.0. Taxonomie par spécialité. Gestion des zones/bridges multi-dents. Intégration des Elite Tips auto-disparition (2s). Moteur de rapport PDF hybride structuré. | `PanoramicStudio.tsx`, `XRayCanvas.tsx`, `usePanoramicStore.ts`, `panoramic_report_engine.py`, `ClinicalTipBubble.tsx` | ✅ |

---

## 🎯 Prochaines Actions & Todo

- [x] **Smart QR Validation** : Implémenter la signature numérique QR sur les documents.
- [ ] **Validation Impresseur** : Confirmer l'alignement millimétré du papier en-tête physique vs PDF.
- [x] **Silent Steiner Fix** : Résolution du crash "undefined ligne_e_ls" via Deep-Merge LocalStorage.
- [x] **UX Breakthroughs v1.7** : Loupe/Filtres en Pano, Pulse-IA en Step 3, Calibration assistée, Elite Tips.

- [ ] **Apical Focused Filter** : Développer un filtre spécifique (Unsharp Mask/High-Pass) pour les incisives inférieures.
- [ ] **Morphing T2** : Finalisation du moteur de prédiction de croissance.
- [ ] **UX "Zero-Friction" Full** : Drag-and-Drop pour la réorganisation des actes dans le Studio.
- [ ] **Reporting PDF Global** : Migrer tous les générateurs (Certificat, Devis, Note) vers WeasyPrint + QR.

---

> **Note interne à l'IA :** Toujours valider les paths en absolu ou relatifs au dossier racine (`DigitalCrown/`) et actualiser la section `Registre des Modifications` quand des refactorisations ou nouvelles logiques sont injectées.
