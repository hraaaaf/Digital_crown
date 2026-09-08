# DIGITAL CROWN — SCIENTIFIC CORE REBUILD

Status: PHASE 1 — NETTOYAGE EN COURS

Canonical file for the scientific-core cleanup, consolidation and rebuild.

## GOAL FINAL

Obtenir un noyau scientifique Digital Crown :

- minimal : aucun moteur mort, doublon ou wrapper sans utilité ;
- explicite : une seule responsabilité claire par moteur ;
- sûr : aucune décision clinique automatique non validée par le praticien ;
- déterministe et testable quand cela est possible ;
- traçable : chaque sortie clinique importante doit avoir une source, une règle et un niveau de confiance compréhensibles ;
- maintenable : les anciennes générations et couches transitoires sont retirées après remplacement prouvé ;
- certifié par tests avant intégration dans `master`.

Le but n'est pas de conserver le plus de moteurs possible. Le but est de conserver le moins de moteurs nécessaires, mais de très bonne qualité.

## RÈGLE DE SUPPRESSION

Aucun fichier scientifique n'est supprimé sur intuition seule.

Chaque candidat est classé :

1. `KEEP` — responsabilité utile, active et correcte ;
2. `CONSOLIDATE` — utile mais redondant avec une meilleure couche ;
3. `REPLACE` — actif mais scientifiquement insuffisant ou dangereux ;
4. `DELETE` — mort, non consommé, doublon intégral ou obsolète sans responsabilité nécessaire.

Pour `DELETE`, la preuve minimale est :

- références runtime vérifiées ;
- routes/services/scripts/tests vérifiés ;
- comportement équivalent ou responsabilité explicitement abandonnée ;
- tests/CI après suppression.

Une couche `REPLACE` n'est supprimée qu'après remplacement et validation du comportement requis.

## PHASE 1 — NETTOYAGE SCIENTIFIQUE

### 1.1 Inventaire de dépendances

Goal: établir la carte réelle des moteurs scientifiques actifs.

Succès:
- chaque moteur scientifique a ses consommateurs runtime connus ;
- les tests seuls sont distingués des appels produit ;
- les wrappers/imports inutilisés sont identifiés.

Preuve:
- code search + inspection runtime + CI/checks repo.

État: EN COURS.

### 1.2 Supprimer le code réellement mort

Première cible qualifiée : `backend/services/treatment_plan_engine.py`.

Constat vérifié au 2026-09-08 :
- les imports trouvés dans `backend/routers/ia.py` et `backend/services/elite_manager.py` ne correspondent à aucun appel du moteur ;
- `EliteManager.get_treatment_plan()` est déjà fail-closed et refuse la génération automatique d'un plan clinique ;
- les usages effectifs restants du vieux moteur sont ses propres tests ;
- ce moteur propose historiquement des actes et coûts à partir de labels automatiques, responsabilité qui ne doit plus exister sous cette forme.

Action:
- supprimer `treatment_plan_engine.py` ;
- retirer ses imports morts ;
- retirer uniquement ses tests dédiés sans supprimer les tests des autres moteurs présents dans les mêmes fichiers ;
- ajouter un contrat anti-régression si nécessaire ;
- certifier par CI.

État: QUALIFIÉ POUR SUPPRESSION, APPLICATION EN COURS.

### 1.3 Nettoyer les outils temporaires du chantier

Les workflows temporaires suivants ne doivent pas survivre au lot une fois leur rôle terminé :

- `.github/workflows/scientific-core-purge-apply.yml`
- `.github/workflows/scientific-core-purge-audit.yml`

État: À RETIRER après récupération des preuves utiles et migration vers les validations normales du repo.

### 1.4 Couche clinical coherence

Cible: `backend/services/clinical_coherence.py`.

Constat vérifié :
- couche réellement consommée par le runtime ;
- elle ne peut donc pas être supprimée comme code mort ;
- certaines heuristiques doivent être auditées scientifiquement avant conservation.

Classement actuel: `REPLACE / CONSOLIDATE`, PAS `DELETE` immédiat.

Next:
- inventorier chaque règle ;
- identifier celles déjà couvertes par prescription/safety ;
- retirer les règles faibles seulement après remplacement prouvé.

### 1.5 Prescription / safety legacy

Constat initial : certaines règles legacy sont trop larges ou simplistes pour servir de référence scientifique définitive.

Classement actuel: `REPLACE`, sous réserve d'audit exhaustif.

Next:
- séparer interaction/allergie/contre-indication/posologie ;
- identifier le moteur canonique pour chaque responsabilité ;
- conserver fail-closed et validation praticien ;
- supprimer les doublons seulement après couverture testée.

### 1.6 Imagerie panoramique

Goal: éliminer la multiplication historique des moteurs/wrappers panoramiques et vision.

À auditer :
- `panoramic_*` ;
- `vision_*` ;
- `sota_*` ;
- generators/report engines associés.

Succès:
- un pipeline produit clairement identifié ;
- aucun wrapper dormant ;
- aucune détection automatique transformée en diagnostic ou traitement ;
- tests du pipeline restant.

État: À AUDITER.

### 1.7 Céphalométrie

Goal: conserver un seul pipeline canonique et retirer les générations obsolètes sans réduire les mesures utiles.

À vérifier :
- service d'upload/process ;
- moteur landmarks ;
- calibration ;
- calculs de mesures ;
- refine manuel ;
- validator ;
- export/PDF.

État: À AUDITER après panoramique/safety.

## PHASE 2 — CONSOLIDATION

Après le nettoyage :

- définir les moteurs canoniques par domaine ;
- fusionner les responsabilités dupliquées ;
- normaliser les contrats d'entrée/sortie ;
- isoler règles cliniques, règles documentaires et règles financières ;
- supprimer les notions de score global qui mélangent des dimensions incompatibles ;
- documenter les dépendances et les limites.

État: NON COMMENCÉ.

## PHASE 3 — REBUILD SCIENTIFIQUE

Construire ou réécrire uniquement ce qui manque après consolidation :

- safety clinique déterministe ;
- prescription avec garde-fous explicites ;
- cohérence dossier/document ;
- céphalométrie ;
- panoramique limitée aux responsabilités réellement validées ;
- synthèse clinique sans plan de traitement automatique ;
- provenance et niveau de confiance des sorties.

État: NON COMMENCÉ.

## PHASE 4 — CERTIFICATION

Pour chaque moteur canonique :

- tests unitaires des règles ;
- golden cases ;
- tests négatifs/fail-closed ;
- tests de non-régression ;
- tests runtime sur les routes réellement exposées ;
- revue scientifique humaine des résultats cliniquement sensibles.

Aucune sortie n'est déclarée certifiée sans preuve.

État: NON COMMENCÉ.

## PHASE 5 — INTÉGRATION / CLOSEOUT

- cohérence du canonique ;
- PR vers `master` ;
- CI verte ;
- merge ;
- post-merge ;
- suppression des branches/workflows temporaires restants ;
- statut final documenté.

Aucun déploiement Vercel dans ce chantier sans autorisation explicite.

## ÉTAT VÉRIFIÉ AU DÉMARRAGE

Repo: `hraaaaf/Digital_crown`

Branche: `refactor/scientific-core-purge`

HEAD vérifié avant création du canonique: `cd084e39bbcecb9e47d8f80ea0acba0c588b1f8a`

Premières conclusions :

- `TreatmentPlanEngine` : `DELETE` qualifié ;
- `clinical_coherence.py` : actif, audit/remplacement requis ;
- prescription/safety legacy : actif mais à auditer/remplacer ;
- panoramique/vision : consolidation à auditer ;
- céphalométrie : audit après nettoyage prioritaire.

## NEXT EXACT

Appliquer la suppression atomique de `TreatmentPlanEngine`, nettoyer ses imports/tests dédiés et les runners scientifiques temporaires devenus inutiles, puis vérifier le diff et la CI avant de passer au prochain moteur.
