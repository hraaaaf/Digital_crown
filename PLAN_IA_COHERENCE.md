# 🛡️ Plan d'Action Chirurgical : Module IA - Cohérence Clinique

Ce module vise à transformer Digital Crown d'un outil de gestion en un véritable **assistant de vigilance clinique**.

## ✅ Phase 1 : Infrastructure de Cross-Check (TERMINÉE & TRIPLE-CHECKÉE)
**Objectif** : Établir les fondations logiques pour la détection d'incohérences.

- [x] **Création du service `clinical_coherence.py`** : Moteur de règles déterministes.
- [x] **Règle Sûre v1** : Détection des prescriptions d'antibiotiques/antalgiques forts sans acte invasif associé.
- [x] **Calcul de l'indice de cohérence** : Score retourné dans la réponse de prévisualisation du document.
- [x] **Triple-Check UX** : Validation de la remontée d'alertes dans le Studio Documentaire.

## ✅ Phase 2 : Intelligence Sémantique (TERMINÉE & TRIPLE-CHECKÉE)
**Objectif** : Passer de la règle statique à l'analyse de contexte.

- [x] **Analyse de Pertinence** : Intégration de Gemini 1.5 Flash pour analyser les antécédents médicaux.
- [x] **Détection de Contre-indications** : Vérification sémantique (AINS/Ulcère, Antibio/Cardio, etc.).
- [x] **Explications IA** : Justification textuelle concise avec préfixe 🤖 pour la transparence.
- [x] **Triple-Check Robustesse** : Gestion des timeouts et fallbacks si l'API Gemini est indisponible.

## 📍 Phase 3 : Studio de Vigilance (Frontend UX)
**Objectif** : Intégration fluide dans le workflow du praticien.

- [ ] **Composant `CoherenceAlert`** : Alertes dynamiques (Info, Warning, Critical) dans le Studio Documentaire.
- [ ] **Workflow de Validation** : Force l'utilisateur à acquitter une alerte "Critique" avant impression.
- [ ] **Live Sync** : Mise à jour des alertes en temps réel pendant la saisie (Debounced).

## 📍 Phase 4 : Assistant de Suggestion (Smart Prep)
**Objectif** : Automatiser la prévention et le suivi.

- [ ] **Smart Protocols** : Suggestion automatique d'ordonnances post-op dès qu'un acte chirurgical est ajouté.
- [ ] **Rappels Cliniques** : Alerte si un acte prévu au plan de traitement COM n'est pas encore facturé.

---

### 🛡️ Protocole de Validation "Triple-Check"
Après chaque phase, les tests suivants doivent être réalisés :
1. **Intégrité Backend** : Vérification des logs et des schémas de réponse.
2. **Synchronisation API** : Validation de la réception des données par le frontend (Zero-Loss).
3. **Cas de Test Réels** : Simulation de scénarios critiques (ex: prescription sans acte) pour valider l'affichage UI.

*Plan établi le 27 Avril 2026 par Antigravity Staff Engineering.*
