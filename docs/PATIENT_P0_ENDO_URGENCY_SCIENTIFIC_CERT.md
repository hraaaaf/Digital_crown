# Page Patient P0-D — Endodontie + examen urgence — certification scientifique

Statut : **OPEN — implémentation clinique non certifiée**  
Date de vérification : 2026-08-17

## Sources primaires / institutionnelles vérifiées

1. American Dental Association — *Antibiotics for Dental Pain and Swelling Guideline (2019)*, page officielle ADA consultée le 2026-08-17.
   - La recommandation reste de ne pas utiliser d'antibiotiques pour la majorité des douleurs et tuméfactions pulpaires/péri-apicales chez l'adulte non sévèrement immunodéprimé.
   - Le traitement dentaire local est prioritaire (pulpotomie/pulpectomie, traitement endodontique, incision-drainage selon situation).
   - Une atteinte systémique telle que fièvre ou malaise change l'indication et peut justifier une antibiothérapie.
2. American Dental Association — *Antibiotic Prophylaxis Prior to Dental Procedures*, mise à jour officielle 2026-07-15.
   - La prophylaxie d'endocardite est limitée aux patients présentant les affections cardiaques associées au plus haut risque d'issue défavorable et aux gestes dentaires concernés.
   - Une simple étiquette générique « cardiopathie » ne suffit pas à déterminer automatiquement une prophylaxie.
3. American Association of Endodontists — *Updating Diagnostic Terminology in Endodontics*, initiative AAE/ESE active en 2026.
   - La terminologie diagnostique endodontique est en cours de révision ; le cadre historique de 2009 ne doit pas être traité comme une vérité algorithmique intemporelle.
4. American Association of Endodontists — page officielle *Clinical Guidelines & Position Statements*, consultée le 2026-08-17.
   - *AAE Guidance on the Use of Systemic Antibiotics in Endodontics* est actuellement signalé **Under Review**.
5. AAE — *Notification of Sunset Position Statements* (2025-12-01).
   - Les anciennes recommandations AAE de prophylaxie antibiotique 2017 ont été retirées/sunset.

## Audit AssistantEndo

Code : `frontend/src/features/patients/components/wizards/AssistantEndo.tsx`

### Règles actuelles non certifiables

| Règle actuelle | Risque | Décision P0 |
|---|---:|---|
| Vitalité négative + image radio-claire → « Nécrose pulpaire avec parodontite apicale asymptomatique » | Élevé | **RETIRER comme diagnostic automatique**. Les trois réponses QCM ne constituent pas un examen diagnostique complet. |
| Douleur spontanée ou réponse persistante → « Pulpite irréversible symptomatique » | Élevé | **RETIRER comme diagnostic automatique**. Présenter au plus des observations/hypothèses à confirmer. |
| Douleur courte provoquée → « Pulpite réversible » | Élevé | **RETIRER comme diagnostic automatique**. Ne pas confondre symptôme et diagnostic final. |
| Diagnostic automatique → traitement canalaire/extirpation/coiffage | Critique | **RETIRER comme prescription automatique**. Transformer en options de prise en charge soumises à validation explicite du praticien après examen complet. |
| Lésion radio-claire → suivi fixe à 6 mois | Élevé | **NE PAS imposer un délai universel** sans indication/source contextualisée. |

### Contrat cible

`observations saisies → hypothèses non validées → éléments manquants / examens complémentaires → options → validation explicite du praticien`

Le composant ne doit jamais enregistrer un diagnostic ou un plan comme vérité clinique du seul fait de trois réponses.

## Audit AssistantExamenComplet — urgence/routine

Code : `frontend/src/features/patients/components/wizards/AssistantExamenComplet.tsx`

### Règles à supprimer ou convertir en fail-closed

| Règle actuelle | Risque | Décision P0 |
|---|---:|---|
| « Cellulite cervico-faciale » → drainage immédiat + amoxicilline/métronidazole IV + orientation conditionnelle | Critique | **RETIRER le protocole médicamenteux automatique**. Conserver uniquement un red flag d'urgence et une recommandation d'évaluation/prise en charge urgente adaptée au contexte clinique. |
| Fièvre → « Amox 2 g/j × 5 j » | Critique | **RETIRER dose/durée automatiques**. Fièvre est un signal d'atteinte systémique mais la prescription nécessite diagnostic, terrain, allergies, médicaments, âge/poids et jugement clinique. |
| Abcès péri-apical aigu → antibiotique automatique | Critique | **RETIRER**. Le traitement local est prioritaire en l'absence d'atteinte systémique selon le guideline ADA. |
| « Cardiopathie / prothèse valvulaire » → « Amox 2 g, 1 h avant tout soin invasif » | Critique | **RETIRER**. L'éligibilité ne peut pas être inférée d'une catégorie générique ; les recommandations actuelles sont limitées à des sous-groupes précis et des gestes précis. |
| Douleur/tuméfaction → diagnostic final automatique | Élevé | **CONVERTIR en triage/hypothèse**, jamais diagnostic validé. |

## Gate avant modification UI

Aucune modification visuelle/flow des assistants n'est autorisée avant :
1. captures baseline des assistants Endo + Examen complet sur les viewports concernés ;
2. Goal visuel écrit ;
3. mockup/wireframe ;
4. implémentation fail-closed ;
5. captures après identiques ;
6. tests positifs/négatifs/données manquantes.

## Critère de fermeture de ce sous-lot

Ce document **ne ferme pas P0-D**. Endo/Urgence ne seront crédités qu'après implémentation, tests et preuve visuelle. Les 8 autres assistants restent à recertifier séparément.
