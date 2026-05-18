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

---

## ✅ 2. Agenda Clinique & Rappels Automatiques (TERMINÉ)
**Statut :** Déployé (v1.5)
**Spécialiste :** PixelMaster, Architector & Staff Software Engineer

- [x] **Modèle de Données** : Implémentation complète `Appointment` avec gestion des statuts.
- [x] **Modification Interactive** : Édition des créneaux en direct via modal intelligent.
- [x] **Rappels Automatiques (WhatsApp Reminders)** : Service cron automatisé de rappels de rendez-vous sous 24h avec logs d'audit et détection de créneaux.
- [x] **Smart Booking** : Intégration clinique déterministe pour suggérer les actes et durées du prochain rendez-vous selon le plan de traitement actif.

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

## ✅ 10. Smart QR Validation & Digital Trust (TERMINÉ)
**Statut :** Déployé (v5.2)
**Spécialiste :** Architector & Staff Staff Engineering

- [x] **Ordonnance E-Verify** : Validation de l'authenticité via portail sécurisé par QR Code.
- [x] **Signature Numérique** : Injection du QR Base64 dans les flux WeasyPrint (Ghost Elite).
- [x] **Scan to Contact** : Support des formats VCARD, WhatsApp et Instagram dans le QR dynamique.

---

## ✅ 11. Dynamic Theme Engine & Personnalisation Ghost Elite (TERMINÉ)
**Statut :** Déployé (v5.2)
**Spécialiste :** PixelMaster & Antigravity

- [x] **Ghost Elite Dashboard** : Refonte totale basée sur les variables CSS (`--primary`, `--secondary`).
- [x] **Thèmes Pré-définis** : 6 thèmes fonctionnels via `data-theme` (Elite, Emerald, Prestige, Rose, etc.).
- [x] **Dynamic Color Selectors** : Curseurs de couleurs (Primaire/Secondaire/Accent) intégrés dans les Settings avec persistence BDD.
- [x] **UX Zero-Friction** : Barre d'actions rapides (Quick Acts) et autocomplétion intelligente.

---

## ✅ 12. CRM & Fidélisation : Patient Scoring (TERMINÉ)
**Statut :** Déployé (v1.5)
**Spécialiste :** Architector & Financia

- [x] **Calculateur d'Intelligence Patient (Score 0-100)** : Évalue instantanément la complétude du dossier patient (antécédents, radiographies, données cliniques).
- [x] **Vigilance Financière Active (Pénalité Solvabilité)** : Soustraction automatique de `-15 points` en cas de dettes échues non réglées ($\ge 1000$ MAD) sur les actes cliniques finalisés.
- [x] **Gradation & Badges Élite** : Menu de grade interactif ("Bronze", "Silver", "Gold", "Platinum") avec persistance BDD et interaction zero-friction.

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

---

## ✅ 16. Moteur d'Habitudes & Apprentissage Clinique (TERMINÉ)
**Statut :** Déployé (v1.3)
**Spécialiste :** Staff Staff Engineering & Architector

- [x] **Système de Mémoire `DoctorActHabit`** : Tracking automatique de la fréquence d'usage des actes cliniques par praticien.
- [x] **Raccourcis Dynamiques (Quick Acts)** : La barre d'actions rapides s'adapte en temps réel aux habitudes réelles (Top 8 actes les plus utilisés).
- [x] **Apprentissage "Au Fil de l'Eau"** : Enregistrement transparent des habitudes lors de la génération de documents financiers (Devis/Notes).
- [x] **Persistance "One-Click"** : Possibilité d'enregistrer instantanément un nouvel acte personnalisé comme habitude depuis l'interface de saisie.

---

## ✅ 17. Bibliothèque Clinique v2 & Mode Soin Immersif (TERMINÉ)
**Statut :** Déployé (v2.0) — Digital Crown Edition
**Spécialiste :** Antigravity Staff Engineering

- [x] **Portage "Digital Crown"** : Interface premium avec glassmorphism, navigation par rail et thèmes dynamiques (Elite, Prestige, Emerald).
- [x] **Mode Soin Immersif** : Vue plein écran à haut contraste optimisée pour l'usage au fauteuil avec checklist critique et navigation clavier.
- [x] **Command Palette (⌘K)** : Recherche ultra-rapide par code acte ou spécialité avec navigation clavier totale.
- [x] **Architecture "App-Shell"** : Défilement interne indépendant pour une ergonomie fluide sur tablettes et écrans larges.

---

## 🎙️ 18. Assistant Vocal "Hands-Free" & Vision Advanced (En cours)
**Statut :** Planifié / Module Clinique Déployé
**Priorité :** Élevée

### ✅ Module 4 IA : Cohérence Clinique & Interactions (TERMINÉ)
- [x] **Moteur d'Interactions Médicamenteuses (DDI)** : Détection dynamique et résiliente des conflits médicamenteux de sévérité élevée ou moyenne (Macrolides/Statines, Macrolides/Amiodarone, Métronidazole/Alcool, AINS/AINS, AINS/Anticoagulants) dans le Studio de Prescription.
- [x] **Bannière de Pharmacovigilance Active** : Affichage d'alertes instantanées et d'avertissements de sécurité dans le Compagnon Diagnostique.
- [ ] **Cross-Check Intelligent** : Alerte automatique si une ordonnance d'antibiotiques est générée sans acte chirurgical ou endodontique lié dans la séance.
- [ ] **Détection d'Omissions** : Suggestion d'actes de prévention (Détartrage/Fluor) basée sur l'historique du patient.

---

## 🧠 20. Ghost Elite Intelligence V3 : Co-Pilote Agentique (En cours)
**Statut :** Planifié / En cours d'Analyse
**Priorité :** Élevée
**Spécialiste :** Antigravity Staff Engineering

- [ ] **Chat Clinique Interactif** : Remplacer les suggestions passives par une interface de dialogue contextuelle.
- [x] **App Awareness & Header Integration** : Capacité du Brain et de la Guide Tower à détecter le module actif (Compta, Céphalo, Dossier) pour adapter leurs conseils. Intégration finalisée dans le Header principal aux côtés des réglages.
- [ ] **Exécution Agentique** : Passage de la suggestion à l'action (ex: "Générer le devis" via un bouton piloté par l'IA).
- [ ] **Reasoning Visualization** : Affichage de la "chaîne de pensée" clinique derrière chaque diagnostic.

---

## ✅ 21. Compagnon Mobile PWA : Zero-Knowledge Access (TERMINÉ)
**Statut :** Déployé (v6.0-rc1)
**Spécialiste :** Staff Staff Engineering (ZKA Specialist)

- [x] **Onboarding Scanner** : Appairage sécurisé via QR Code (Capture Master Key).
- [x] **Moteur ZKA Pull** : Chiffrement AES-256 de bout en bout via Supabase Relais.
- [x] **Cockpit Mobile** : Vue Agenda, Performance Finance et Liste Rouge (Débiteurs) en temps réel.
- [x] **Mode Air-Gapped** : Zéro stockage de clé sur le cloud ; souveraineté totale des données cliniques.

---

## ✅ 22. Agenda Intelligent & Plan de Traitement (Odontogramme) (TERMINÉ)
**Statut :** Smart Booking Clinique Déployé (v5.3)
**Priorité :** Critique (Agentique)
**Spécialiste :** Antigravity Staff Engineering

L'objectif est d'interconnecter le cerveau de l'application, l'agenda et l'odontogramme pour créer un "Smart Booking" ultra-performant.
- [x] **Compagnon Diagnostique & Decision Tree (v2.0)** : Arbre décisionnel interactif multiniveau prenant en charge les urgences (douleurs, abcès), motifs esthétiques (dyschromie, alignement), problèmes prothétiques (dent manquante, casse), traumatismes (chocs, expulsion) et bilans de routine/tartre dans le TreatmentPlanStudio.
- [x] **Génération de Plan Scientifique** : Traduction automatique des réponses en un plan de traitement structuré en 5 phases cliniques avec panier de soins interactif.
- [x] **Agenda Contextuel** : Lors de la proposition du prochain RDV, l'Agenda lit dynamiquement le plan de traitement inachevé du patient pour suggérer le prochain acte prioritaire.
- [ ] **Questions Proactives** : L'agenda demande explicitement au praticien la nature de la suite (ex: *"S'agit-il de la 2ème séance de traitement canalaire, ou attaque-t-on le composite ?"*).
- [x] **Durée Auto-Calculée** : Le temps réservé dans l'agenda s'adapte automatiquement à l'acte suggéré (15-45 minutes).

---

## ✅ 23. Bilan Parodontal Interactif EFP/AAP 2017 (TERMINÉ)
**Statut :** Déployé (v1.0)
**Spécialiste :** Staff Software Engineering & PixelMaster

- [x] **Periodontal Charting Complet** : Interface interactive et fluide de saisie des profondeurs de poches, perte d'attache clinique (CAL) et saignements au sondage (BOP) pour les 32 dents.
- [x] **Standards AAP 2017** : Intégration des règles d'évaluation clinique et de gradation (Staging I à IV, Grading A à C).
- [x] **Co-prescription Adjuvante** : Recommandation automatique d'antibiothérapie d'accompagnement (Amoxicilline + Métronidazole) pour les parodontites agressives (Grade C).

---

## ✅ 24. Sécurité, Licences Off-line & Sauvegardes AES-256 (TERMINÉ)
**Statut :** Déployé (v1.0)
**Spécialiste :** Staff Software Engineering & Architector

- [x] **Elite Offline License System** : Gestionnaire de licences en ligne et hors-ligne via coffre-fort chiffré (`license_vault.bin`).
- [x] **Anti-Fraude Temporelle** : Détection automatique des retours en arrière de l'horloge système (clock rollback) et période de grâce de 72h sans Internet.
- [x] **Sauvegardes AES-256 Automatisées** : Script de sauvegarde chiffrée de la base de données SQLite locale avec exportation sécurisée vers Supabase Cloud.
- [x] **Logs d'Audit Systématiques** : Traçabilité totale des opérations de licence, de restauration et de sauvegarde dans l'AuditLog.

---

*Dernière mise à jour : 18 Mai 2026 — Phase 6 Deployment Ready (Elite Edition).*
