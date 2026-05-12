# 🚀 Roadmap & Projets à Venir - Digital Crown

Ce document centralise les fonctionnalités prévues et les architectures validées pour le développement futur de l'application Digital Crown.

---

## ✅ 1. Comptabilité Élite & Archivage (TERMINÉ)
**Statut :** Déployé (v1.2)
**Spécialiste :** Financia & Architector

- [x] **Archivage SYSTÉMATIQUE** : Toutes les notes d'honoraires et devis sont tracés en BDD dès la génération.
- [x] **Pare-feu Anti-Doublon** : Détection intelligente par contenu (actes/montants) pour éviter les erreurs de saisie.
- [x] **Dashboard Financier** : Vue centralisée avec filtres (Patient, Assurance, Date) et export PDF.
- [x] **Synchronisation d'Historique** : Import automatique de 50+ dossiers patients "Legacy" avec extraction des montants via PyPDF2.
- [x] **Navigation Fluide** : Liens directs entre la comptabilité et le hub de documents du patient.

## 🚧 2. Agenda Clinique (PARTIELLEMENT TERMINÉ)
**Statut :** Déployé (v1.2) — IA Booking non implémentée
**Spécialiste :** PixelMaster & Architector

- [x] **Modèle de Données** : Implémentation complète `Appointment` avec gestion des statuts.
- [x] **Modification Interactive** : Édition des créneaux en direct via modal intelligent.
- [ ] **Smart Booking** : Intégration de l'IA pour suggérer les durées de RDV selon l'historique.

---

## ✅ 3. Studio de Prescription "Zero-Clavier" (TERMINÉ)
**Statut :** Déployé (v2.0)
**Spécialiste :** DataPhysicist & PixelMaster

- [x] **Moteur Déterministe** : Arbre décisionnel (Acte > Poso > Sécurité).
- [x] **Sécurité Immuable** : Filtrage automatique allergies et pédiatrie 100% sûr.
- [x] **Bouton One-Click** : Génération instantanée basée sur le contexte clinique.
- [x] **Override Persistant** : Logique de surcharge adaptée aux habitudes du praticien.

---

## 👁️ 4. Évolutions IA Vision & Ortho
**Statut :** En cours
**Priorité :** Haute
**Spécialiste :** DataPhysicist

- [ ] **Morphing T2** : Prédiction de croissance à 5 ans basée sur les normes COM.
- [ ] **Détection 3D (Future)** : Passage à l'analyse volumétrique CBCT.

---

## 🚧 5. Évolutions UI - Liste des Patients
**Statut :** Partiellement Déployé (v1.3)
**Priorité :** Haute

- [x] **Tri Intelligent** : Support du tri par N° Dossier et Date de création.
- [ ] **Mode Vue Grille (Cards)** : Toggle "Table/Grid" pour usage sur tablettes.

---

## ✅ 6. Branding Engine v4.0 (Ghost Elite) & Contacts Granulaires (TERMINÉ)
**Statut :** Déployé (v4.0)
**Spécialiste :** PixelMaster & Architector

- [x] **Système de Contacts Granulaires** : Toggles individuels pour Tel, WhatsApp, Instagram avec persistence JSON.
- [x] **Moteur PDF v4.0 (ReportLab Dynamic)** : Synchronisation typographique totale (Amiri) entre le contenu et le pied de page.
- [x] **Branding Elite Ghost** : Rendu premium "Zero-Default" avec centrage géométrique parfait (10.5cm).
- [x] **Live Preview Stable** : Schémas Pydantic durcis pour une saisie WYSIWYG sans défaillance.
- [x] **Import IA (Card Extraction)** : Extraction automatique des infos praticien via Gemini 1.5 Flash.
- [x] **Structure Hybride** : Support natif "Cabinet Privé" vs "Clinique/Centre" (Multi-spécialistes).
- [x] **Arabic Studio** : Intégration clavier virtuel arabe et support "Autre spécialité" bilingue.
- [x] **Master Template PDF v4.0** : Abandon des fonds images au profit d'un rendu vectoriel natif "Ghost Elite".
- [x] **Identifiants Légaux Dynamiques** : Injection auto du ICE, IF, INPE sur les documents financiers uniquement.

---

## ✅ 7. Stabilisation Studio Documentaire v4.1 (TERMINÉ)
**Statut :** Déployé (v4.1)
**Spécialiste :** PixelMaster & Architector

- [x] **Aperçu Live 2026** : Panneau d'aperçu agrandi (850px) et non-bloquant pour une édition fluide en temps réel.
- [x] **Pipeline d'Archivage Robuste** : Correction des chemins relatifs et gestion intelligente des conflits (Force-creation vs Cancel).
- [x] **Clôture Comptable Standardisée** : Mention légale "Arrêtée la présente note..." repositionnée dynamiquement en bas de document pour éviter les superpositions.
- [x] **UI Odontogramme Optimisée** : Correction des conflits de clics et du z-index pour le Studio.

---

## ✅ 8. Stabilisation & Personnalisation Dynamique v4.2 (TERMINÉ)
**Statut :** Déployé (v4.2)
**Spécialiste :** PixelMaster & Architector

- [x] **Clôture Dynamique (Database-Driven)** : Migration des phrases de clôture vers `CabinetConfig` (Templates paramétrables `{total_words}`).
- [x] **Navigation Ghost Élite** : Résolution définitive du blocage `z-index` de l'odontogramme sur le dashboard.
- [x] **Footer de Haute Précision** : Épinglage du bloc total à `3.2cm` du bas de page (Rendu absolu) pour une harmonie parfaite.
- [x] **Branding Hiérarchisé** : Refonte de l'en-tête pour supporter 4 lignes de spécialités avec typographie différenciée (Elite Contrast).

---

## ✅ 9. Pack "Medical Premium" & Stabilisation Typographique v4.6 (TERMINÉ)
**Statut :** Déployé (v4.6)
**Spécialiste :** PixelMaster & Architector

- [x] **Premium Typography** : Intégration native des polices Google Fonts (Outfit & Inter) pour un rendu haut de gamme via WeasyPrint.
- [x] **Branding Forcing** : Application systématique de la couleur primaire sur l'intégralité du contenu textuel (élimination totale du noir).
- [x] **Smart Font Scaling** : Augmentation globale de +1pt sur tous les paragraphes et titres pour un confort de lecture "Elite".
- [x] **Simplification Comptable** : Affichage exclusif en lettres pour les mentions légales de clôture (Zéro redondance numérique).
- [x] **Layout Certificat v4.6** : Inversion patient/date avant le titre et alignement géométrique latéral optimisé.

---

## 🚧 10. Smart QR Validation & Digital Trust
**Statut :** En cours — Service backend créé, non intégré aux flux
**Priorité :** Confort Elite
**Spécialiste :** Architector & Financia

- [ ] **Ordonnance E-Verify** : Validation de l'authenticité via portail sécurisé par QR Code. *(Le `qr_service.py` existe mais n'est intégré dans aucun générateur PDF ni exposé côté frontend.)*
- [ ] **Signature Numérique** : Injection du QR Base64 dans les flux ReportLab/WeasyPrint. *(Non connecté.)*
- [ ] **Scan to Pay** : Intégration QR sur documents financiers pour paiement mobile direct (v4.5).

---

## 🚧 11. Dynamic Theme Engine & Personnalisation Ghost Elite
**Statut :** Partiellement Déployé (v5.0) — Thèmes CSS OK, sélecteur couleur manquant
**Spécialiste :** PixelMaster

- [x] **Ghost Elite Dashboard** : Refonte totale basée sur les variables CSS (`--primary`, `--secondary`).
- [x] **Thèmes Pré-définis** : 3 thèmes fonctionnels via `data-theme` (Elite, Emerald, Prestige) dans `index.css`.
- [ ] **Dynamic Color Selectors** : Curseurs de couleurs (Primaire/Secondaire) directement dans les Settings avec persistence BDD. *(Aucun ColorPicker implémenté dans `Settings.tsx`.)*
- [x] **UX Zero-Friction** : Barre d'actions rapides (Quick Acts) et autocomplétion intelligente.

---

## 💎 12. CRM & Fidélisation : Patient Scoring
**Statut :** Idée / Recherche
**Priorité :** Basse
**Spécialiste :** Architector & Financia

- [ ] **Logique de Scoring Discret** : Attribution d'un grade (Bronze, Silver, Gold, Platinum) basé sur un algorithme interne.
- [ ] **Indice d'Assiduité** : Calcul du ratio RDV honorés / RDV annulés ou "No-Show" (impacte le score négativement).

---

## 📊 13. Visual Insights & Business Analytics
**Statut :** En cours (v5.1)
**Priorité :** Moyenne

- [x] **Comptabilité Analytique** : Graphiques de revenus (Recharts) intégrés à la page Comptabilité.
- [ ] **Analyse de Rentabilité par Acte** : Visualisation des actes les plus performants.
- [ ] **Reporting Mensuel Automatisé** : Génération d'un bilan financier PDF avec graphiques WeasyPrint.

---

## ✅ 14. Stabilisation & Excellence Documentaire v1.2 (TERMINÉ)
**Statut :** Déployé (v1.2)
**Spécialiste :** Staff Staff Engineering & PixelMaster

- [x] **Restauration ReportLab** : Retour à la robustesse ReportLab pour les ordonnances et certificats (Stabilité v1.0).
- [x] **Correctif Accents "Elite"** : Élimination totale des caractères parasites dans tous les générateurs PDF.
- [x] **Ouverture Auto PDF** : Le document généré s'ouvre désormais automatiquement dans un nouvel onglet pour un feedback immédiat.
- [x] **Clinical Intelligence v1** : Intégration des routes `ai-diagnostic` et `ai-summary` dans le Studio Documentaire.
- [x] **Fix Boucle React** : Stabilisation du `DocumentHub` et du hook `useDocumentGenerator` (Zéro latence).

---

## 🚧 15. Gestion des Rôles : Mode Assistante du Cabinet
**Statut :** En cours (Phase 1 & 2 déployées)
**Priorité :** Élevée
**Spécialiste :** Architector & PixelMaster

Ce module vise à créer une expérience utilisateur (UX) sur mesure pour le personnel d'accueil et d'assistance, avec un contrôle granulaire des accès (RBAC - Role-Based Access Control).

- [x] **Sous-comptes Liés** : Création de profils "Assistante" rattachés au compte Maître du médecin via `employer_id` avec CRUD complet (`/api/team/`).
- [x] **Interface de Gestion d'Équipe** : Onglet "Mon Équipe" dans les Settings pour créer, suspendre et supprimer des sous-comptes.
- [x] **Suspension d'Accès** : Bouton de suspension instantanée (toggle `is_active`) avec blocage du login.
- [x] **RBAC Backend** : Dépendance `require_employer()` pour bloquer les opérations de gestion aux sous-comptes.
- [ ] **Tableau de Bord Dédié (Task-Driven)** : L'écran d'accueil de l'assistante mettra en évidence l'**Agenda** (arrivées, retards, confirmations) et la file d'attente du jour, plutôt que les statistiques financières.
- [ ] **Masquage Stratégique (Feature Hiding)** : Restriction d'accès aux données sensibles (Chiffre d'affaires global, diagnostics IA poussés, honoraires spécifiques) selon les permissions accordées par le médecin.
- [ ] **Workflow de Pré-Saisie** : Capacité pour l'assistante de créer le dossier patient, de remplir le questionnaire médical de base et de scanner les documents (carte d'identité, mutuelle) avant l'entrée en salle de soins.
- [ ] **Onboarding & Formation Assistée** : Intégration de "Tooltips" dynamiques et d'un mode "Tutoriel" pour aider les nouvelles assistantes à maîtriser rapidement le logiciel (facturation basique, prise de RDV).

---

## ✅ 16. Moteur d'Habitudes & Apprentissage Clinique (TERMINÉ)
**Statut :** Déployé (v1.3)
**Spécialiste :** Staff Staff Engineering & Architector

- [x] **Système de Mémoire `DoctorActHabit`** : Tracking automatique de la fréquence d'usage des actes cliniques par praticien.
- [x] **Raccourcis Dynamiques (Quick Acts)** : La barre d'actions rapides s'adapte en temps réel aux habitudes réelles (Top 8 actes les plus utilisés).
- [x] **Apprentissage "Au Fil de l'Eau"** : Enregistrement transparent des habitudes lors de la génération de documents financiers (Devis/Notes).
- [x] **Persistance "One-Click"** : Possibilité d'enregistrer instantanément un nouvel acte personnalisé comme habitude depuis l'interface de saisie.

---

## 🎙️ 17. Assistant Vocal "Hands-Free" & Vision Advanced (Prochaine Étape)
**Statut :** Planifié
**Priorité :** Élevée

### 🛡️ Module 4 IA : Cohérence Clinique (Priorité Haute)
- [ ] **Cross-Check Intelligent** : Alerte automatique si une ordonnance d'antibiotiques est générée sans acte chirurgical ou endodontique lié dans la séance.
- [ ] **Détection d'Omissions** : Suggestion d'actes de prévention (Détartrage/Fluor) basée sur l'historique du patient.

### 🦷 Odontogramme 3D & Vision Advanced
- [ ] **IA Overlay** : Superposition automatique des racines détectées sur la radio panoramique directement sur l'odontogramme SVG.

---

## ✅ 18. Hub Panoramique ELITE & Clinical Insights (TERMINÉ)
**Statut :** Déployé (v1.3)
**Spécialiste :** Staff Engineering & PixelMaster

- [x] **Panoramic Hub v2.0** : Interface de diagnostic panoramique interactive avec taxonomie par spécialité (Conservatrice, Endo, Paro, Chirurgie, Prothèse, ATM).
- [x] **Gestion des Zones** : Prise en charge native des bridges et des alvéolyses multi-dents avec calcul de plage FDI automatique (même entre quadrants).
- [x] **Elite Tips v1.2** : Système de micro-conseils cliniques en haut à gauche avec auto-disparition ultra-rapide (2s) pour zéro distraction.
- [x] **Moteur de Rapport Hybride** : Fusion déterministe IA + Expertise humaine dans un PDF structuré par secteur (FDI).

---

*Dernière mise à jour : 12 Mai 2026 — Elite Panoramic Release.*

