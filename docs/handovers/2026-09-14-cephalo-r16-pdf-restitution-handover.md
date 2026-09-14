# HANDOVER — DIGITAL CROWN / CÉPHALOMÉTRIE — R16 PDF / RESTITUTION

**Date :** 2026-09-14  
**Repo :** `hraaaaf/Digital_crown`  
**Canonique :** `docs/CEPHALO_DIAGNOSTIC_SPEC.md`  
**Baseline produit :** R15bis mergé via PR #477  
**Candidate R15bis certifié :** `89c852bf95426623b942a90823db69bc85501b10`  
**Merge produit R15bis :** `127ed256c690f8cc9464bee68b8cd26c29f4129a`

## GOAL

Faire de la restitution PDF une représentation fidèle, traçable et cliniquement sûre du même état autoritaire déjà exposé par l’UI/API céphalométrique.

Le PDF ne doit jamais devenir une seconde source de vérité.

## SUCCÈS OBSERVABLE

R16 est réussi seulement si une certification prouve que, pour le même cas et la même analyse :

1. UI, API et PDF utilisent le même graphe de preuve et le même état validé ;
2. mesures indisponibles restent `NOT_COMPUTABLE` / non présentées comme valeurs valides ;
3. données manquantes restent visibles ;
4. contradictions restent visibles ;
5. contre-indications restent visibles ;
6. provenance scientifique et clinique utile reste restituée ;
7. états R11→R14 ne sont ni promus ni simplifiés de manière trompeuse ;
8. `EVALUABLE` n’est jamais rendu comme sélection/prescription ;
9. `BLOCKED != DROPPED` reste strictement respecté ;
10. validation praticien finale et décision d’option restent distinguées ;
11. aucun contenu clinique n’est généré ou complété pour “faire joli” dans le PDF ;
12. un cas avec données incomplètes produit un PDF explicitement incomplet et non une restitution faussement finalisée ;
13. les tests couvrent au minimum un cas complet et plusieurs cas négatifs/fail-closed ;
14. aucune régression R15bis UI/UX ;
15. aucun déploiement Vercel sans autorisation explicite.

## CONTRAT À PRÉSERVER

`landmark != construction != measurement != interpretation != diagnosis != indication != treatment plan`

Le chemin de preuve reste :

`SourceEvidence → LandmarkEvidence → ConstructionEvidence → MeasurementEvidence → finding → diagnostic → problem list → objectifs → options R13 → validation finale R14`

Le PDF est uniquement une **projection de lecture** de ce contrat.

## PÉRIMÈTRE R16

Autorisé :

- pipeline de restitution PDF ;
- mapping des objets autoritaires vers sections PDF ;
- ordre, hiérarchie et lisibilité documentaire ;
- métadonnées de provenance nécessaires à l’audit ;
- statut calculable/non calculable ;
- états R11/R12/R13/R14 ;
- données manquantes, contradictions, contre-indications et blockers ;
- identité praticien et validation uniquement lorsqu’elles existent réellement dans le graphe ;
- tests de cohérence UI/API/PDF ;
- certification documentaire/visuelle du PDF.

Hors scope / interdit :

- nouvelles formules céphalométriques ;
- nouvelles normes ;
- modification COM/CRANIOM ;
- nouvelle règle diagnostique ou thérapeutique ;
- auto-validation praticien ;
- auto-sélection d’une option R13 ;
- promotion d’un état `EVALUABLE` ;
- génération libre d’un plan de traitement ;
- masquage des données manquantes ou contradictions ;
- suppression d’un blocker pour obtenir un PDF “propre”.

## PLAN DE CERTIFICATION

### 1. Inventaire BEFORE

Avant modification :

- identifier le générateur PDF céphalométrique actuel ;
- identifier sa source de données exacte ;
- comparer le modèle PDF au read-path UI/API autoritaire ;
- lister chaque divergence de champ, état ou provenance ;
- capturer un PDF BEFORE ou son rendu page par page ;
- vérifier qu’aucune donnée clinique n’est injectée hors graphe.

### 2. Matrice de cohérence

Construire une matrice minimale :

| Objet | API | UI | PDF | État attendu |
| --- | --- | --- | --- | --- |
| mesure AVAILABLE | oui | oui | oui | valeur + unité + provenance |
| mesure NOT_COMPUTABLE | oui | oui | oui | explicitement indisponible |
| missing data | oui | oui | oui | visible |
| contradiction | oui | oui | oui | visible |
| contre-indication | oui | oui | oui | visible |
| R13 EVALUABLE | oui | oui | oui | jamais “sélectionné” |
| R13 BLOCKED | oui | oui | oui | blocker visible |
| R14 awaiting | oui | oui | oui | jamais final |
| R14 validated | oui | oui | oui | validation praticien traçable |

### 3. Implémentation

Privilégier une seule fonction/adaptateur de projection documentaire, alimentée par les objets autoritaires déjà validés, plutôt que de reconstruire la logique dans le PDF.

### 4. Goldens / négatifs

Cas minimum :

- complet et validé ;
- mesure non calculable ;
- missing data ;
- contradiction ;
- contre-indication active ;
- option R13 `EVALUABLE` sans sélection ;
- option R13 `BLOCKED` ;
- R14 `AWAITING_CLINICIAN_VALIDATION` ;
- validation finale incohérente/orpheline → refus ou fail-closed selon contrat existant.

### 5. AFTER

Comparer BEFORE/AFTER et prouver :

- contenu cohérent avec API/UI ;
- aucune donnée fabriquée ;
- aucun état promu ;
- aucun blocker perdu ;
- aucune régression UI R15bis ;
- rendu PDF lisible et audit-able.

## GATES MERGE R16

- tests ciblés PDF/restitution ;
- CI globale ;
- T2 Runtime Browser Certification si le read-path UI est touché ;
- PostgreSQL certification si persistence/read-path backend est touché ;
- certification visuelle/documentaire PDF ;
- reviews/threads vérifiés ;
- diff de scope vérifié ;
- aucun déploiement.

## NEXT EXACT

1. Lire `AGENTS.md`, `STATE.md`, `docs/CEPHALO_DIAGNOSTIC_SPEC.md`, puis ce handover.
2. Vérifier `master`, HEAD, PR et CI avant tout changement.
3. Localiser le générateur PDF céphalométrique actuel et son source-of-truth.
4. Produire le BEFORE et la matrice API/UI/PDF.
5. Corriger uniquement les divergences prouvées.
6. Certifier les cas positifs/négatifs puis closeout R16.

## SÉQUENCE RESTANTE

`R16 inventaire/BEFORE → matrice cohérence → implémentation → AFTER/certification → closeout R16 → R17 certification/closeout`

## DÉPLOIEMENT

Aucun déploiement Vercel sans autorisation explicite.
