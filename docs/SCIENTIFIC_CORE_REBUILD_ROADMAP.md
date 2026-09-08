# DIGITAL CROWN — SCIENTIFIC CORE REBUILD

Status: PHASE 1 — NETTOYAGE EN COURS

Fichier canonique du chantier de nettoyage, consolidation et reconstruction du noyau scientifique.

## GOAL FINAL

Obtenir un noyau scientifique Digital Crown :

- minimal : aucun moteur mort, doublon ou wrapper sans utilité ;
- explicite : une seule responsabilité claire par moteur ;
- sûr : aucune décision clinique automatique non validée par le praticien ;
- déterministe et testable quand cela est possible ;
- traçable : chaque sortie clinique importante doit avoir une source, une règle et un niveau de confiance compréhensibles ;
- maintenable : les couches transitoires sont retirées après remplacement prouvé ;
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

### 1.2 Lot 1 — supprimer le vieux TreatmentPlanEngine

Cible : `backend/services/treatment_plan_engine.py`.

Constat vérifié :
- imports présents dans `backend/routers/ia.py` et `backend/services/elite_manager.py`, sans appel runtime du moteur ;
- `EliteManager.get_treatment_plan()` est déjà fail-closed et refuse la génération automatique d'un plan clinique ;
- les usages effectifs restants du vieux moteur étaient ses propres tests ;
- le moteur proposait des actes et coûts à partir de labels automatiques, responsabilité qui ne doit plus exister sous cette forme.

Application :
- moteur supprimé ;
- imports morts supprimés ;
- tests dédiés supprimés sans retirer les tests des autres moteurs partageant les mêmes fichiers ;
- contrat anti-régression ajouté dans `backend/tests/test_scientific_core_purge_contract.py` ;
- workflows temporaires `.github/workflows/scientific-core-purge-apply.yml` et `.github/workflows/scientific-core-purge-audit.yml` supprimés.

Commit produit : `2eda05e73111cffce65309aef233438180f67e97`.

Diff net vérifié : 7 fichiers produit/tests/workflows, aucune modification parasite dans `ia.py` ou `elite_manager.py`.

État: APPLIQUÉ — CI STANDARD À CERTIFIER.

### 1.3 Couche clinical coherence

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

### 1.4 Prescription / safety legacy

Constat initial : certaines règles legacy sont trop larges ou simplistes pour servir de référence scientifique définitive.

Classement actuel: `REPLACE`, sous réserve d'audit exhaustif.

Next:
- séparer interaction/allergie/contre-indication/posologie ;
- identifier le moteur canonique pour chaque responsabilité ;
- conserver fail-closed et validation praticien ;
- supprimer les doublons seulement après couverture testée.

### 1.5 Imagerie panoramique

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

### 1.6 Céphalométrie

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
- isoler règles cliniques, documentaires et financières ;
- supprimer les scores globaux mélangeant des dimensions incompatibles ;
- documenter dépendances et limites.

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

## REPÈRES VÉRIFIÉS

Repo: `hraaaaf/Digital_crown`

Branche: `refactor/scientific-core-purge`

HEAD avant canonique: `cd084e39bbcecb9e47d8f80ea0acba0c588b1f8a`

Canonique créé: `6c2e082c15383091f6c7b5d921ae214d567dc275`

Contrat anti-régression ajouté: `15c7b8d9482ff645c2458c2367b48932eef34693`

Lot 1 appliqué: `2eda05e73111cffce65309aef233438180f67e97`

Premières conclusions :
- `TreatmentPlanEngine` : supprimé, CI à certifier ;
- `clinical_coherence.py` : actif, audit/remplacement requis ;
- prescription/safety legacy : actif mais à auditer/remplacer ;
- panoramique/vision : consolidation à auditer ;
- céphalométrie : audit après nettoyage prioritaire.

## NEXT EXACT

Lire la CI déclenchée par ce checkpoint, puis auditer exhaustivement `clinical_coherence.py` et ses recouvrements avec les moteurs prescription/safety avant toute nouvelle suppression.
