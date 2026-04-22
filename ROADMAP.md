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

## ✅ 2. Agenda Clinique (TERMINÉ)
**Statut :** Déployé (v1.2)
**Spécialiste :** PixelMaster & Architector

- [x] **Modèle de Données** : Implémentation complète `Appointment` avec gestion des statuts.
- [x] **Modification Interactive** : Édition des créneaux en direct via modal intelligent.
- [x] **Smart Booking** : Intégration de l'IA pour suggérer les durées de RDV selon l'historique.

---

## ✅ 3. Studio de Prescription "Zero-Clavier" (TERMINÉ)
**Statut :** Déployé (v2.0)
**Spécialiste :** DataPhysicist & PixelMaster

- [x] **Moteur Déterministe** : Arbre décisionnel (Acte > Poso > Sécurité).
- [x] **Sécurité Immuable** : Filtrage automatique allergies et pédiatrie 100% sûr.
- [x] **Bouton One-Click** : Génération instantanée basée sur le contexte clinique.
- [x] **Override Persistant** (En cours) : Logique de surcharge pour s'adapter aux habitudes du praticien.

---

## 👁️ 4. Évolutions IA Vision & Ortho
**Statut :** En cours
**Priorité :** Haute
**Spécialiste :** DataPhysicist

- [ ] **Morphing T2** : Prédiction de croissance à 5 ans basée sur les normes COM.
- [ ] **Détection 3D (Future)** : Passage à l'analyse volumétrique CBCT.

---

## 🗂️ 5. Évolutions UI - Liste des Patients
**Statut :** Planifié
**Priorité :** Moyenne

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

## 🔒 11. Smart QR Validation & Digital Trust (CONCEPT)
**Statut :** Brainstorming acté
**Priorité :** Basse / Confort Elite
**Spécialiste :** Architector & Financia

- [ ] **Ordonnance E-Verify** : Validation de l'authenticité via portail sécurisé.
- [ ] **Scan to Pay** : Intégration QR sur documents financiers pour paiement mobile direct.
- [ ] **Patient Digital Hub** : Scan pour téléchargement mobile instantané du bilan.

---

## 🎨 12. Multi-Style Engine & Personnalisation Avancée

- [ ] **Sélecteur de Style Contextuel** : Choix du rendu au moment de l'impression (Classic, Ghost Elite, Minimaliste).
- [ ] **Dynamic Theme Engine** : Curseurs de couleurs (Primaire/Secondaire) et sélecteur de polices Google Fonts directement dans les Settings.
- [ ] **Mode Impression sur Papier En-tête** : Toggle intelligent pour masquer dynamiquement le Header/Footer si le praticien utilise son propre papier physique.
- [ ] **Gestion Multi-Templates** : Possibilité de créer et sauvegarder plusieurs variantes (ex: Ordonnance Enfant vs Adulte) avec des styles distincts.

---

## 💎 10. CRM & Fidélisation : Patient Scoring
**Statut :** Idée / Recherche
**Priorité :** Basse
**Spécialiste :** Architector & Financia

- [ ] **Logique de Scoring Discret** : Attribution d'un grade (Bronze, Silver, Gold, Platinum) basé sur un algorithme interne.
- [ ] **Indice d'Assiduité** : Calcul du ratio RDV honorés / RDV annulés ou "No-Show" (impacte le score négativement).
- [ ] **Indice de Solvabilité** : Analyse du "Sérieu Paiement" (Délais de règlement, impayés résolus, acomptes immédiats).
- [ ] **Badge Visuel** : Affichage d'un badge discret sur la fiche patient pour alerter le praticien sur le profil du patient dès l'ouverture du dossier.
- [ ] **Avantages Automatisés** : Suggestion de remises ou priorités de rendez-vous pour les patients "Élite".

*Dernière mise à jour : 2026-04-21 par Antigravity Staff Engineering (v4.3 CRM Concept).*
