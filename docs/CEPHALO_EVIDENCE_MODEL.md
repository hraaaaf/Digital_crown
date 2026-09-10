# CÉPHALO — EVIDENCE MODEL

**Statut : SPEC / implémentation non commencée**  
**Parent canonique :** `docs/CEPHALO_DIAGNOSTIC_SPEC.md`  
**Rôle :** architecture transversale des lots 3→14.

## GOAL

Interdire les sauts non traçables entre donnée patient, mesure, interprétation, diagnostic et traitement.

## CHAÎNE CANONIQUE

`SourceEvidence → LandmarkEvidence → Construction → Measurement → NormativeEvaluation → Finding → DiagnosticHypothesis → Problem → Objective → TreatmentOption → ClinicianValidation → FinalPlan`

Chaque objet dérivé conserve ses `evidence_refs`, sa méthode/version et son statut.

## STATUTS

- preuve : `OBSERVED | COMPUTED | INTERPRETED | CLINICIAN_VALIDATED` ;
- disponibilité : `AVAILABLE | MISSING | INVALID | NOT_APPLICABLE | NOT_COMPUTABLE`.

`MISSING` n'est jamais transformé en normalité, zéro, moyenne ou valeur patient par défaut.

## OBJETS MINIMAUX

### LandmarkEvidence

`landmark_id`, `x`, `y`, `source_image_ref`, `origin`, `model_sha256/pipeline_version` si automatique, coordonnées automatiques originales si corrigées, audit praticien, `evidence_refs`.

Origines : `SRPOSE38_AUTO | MANUAL | MANUAL_CORRECTED`.

### Construction

`construction_id`, `definition_id/version`, `landmark_refs`, géométrie, statut.

### Measurement

`measurement_id`, `analysis_id`, `method_id/version`, `value`, `unit`, `landmark_refs`, `construction_refs`, `calibration_ref` si linéaire, statut, `evidence_refs`.

La norme n'est jamais embarquée implicitement dans la mesure brute.

### NormativeEvaluation

`measurement_ref`, `norm_profile_id/version`, contexte d'applicabilité, plage/valeur de référence sourcée, règle de classification versionnée, statut, `source_refs`.

### Finding / DiagnosticHypothesis

Un finding conserve preuves favorables, défavorables, manquantes et contradictions. Une hypothèse diagnostique porte : `PROPOSED | ACCEPTED | EDITED | REJECTED | INSUFFICIENT_DATA`.

Un diagnostic retenu nécessite une validation praticien explicite.

### Problem / Objective

Chaque problème renvoie aux diagnostics/findings qui le justifient. Chaque objectif renvoie à ≥1 problème et décrit **ce qui doit être obtenu**, pas la mécanique thérapeutique.

### TreatmentOption

Une option contient préconditions, preuves requises, contre-indications, bénéfices, limites, risques, dépendance à la croissance, ancrage, impact profil/stabilité et statut : `EVALUABLE | BLOCKED_INSUFFICIENT_DATA | REJECTED | CLINICIAN_SELECTED`.

Aucun `best_option=true` automatique.

### ClinicianValidation / FinalPlan

Toute validation enregistre auteur, date, action `ACCEPT | EDIT | REJECT`, cible et audit avant/après.

**Invariant :** un `FinalPlan` est invalide sans `clinician_id` et `clinician_validated_at`.

## DETTE ACTUELLE

`backend/schemas/clinical.py` conserve encore des sorties historiques sous chaînes libres (`DiagnosticSLM`, `plan_traitement`, `resume_diagnostic`, `ai_narrative`). Elles restent compatibles pendant migration mais ne doivent pas redevenir la source clinique de vérité. Les résumés texte seront des vues dérivées du graphe typé.

## TESTS DE CONTRAT OBLIGATOIRES

1. mesure sans dépendance requise → `NOT_COMPUTABLE` ;
2. mesure linéaire sans calibration → `NOT_COMPUTABLE` ;
3. norme sans source + version → rejet ;
4. finding sans preuve → rejet ;
5. diagnostic accepté sans validation praticien → rejet ;
6. objectif sans problem_ref → rejet ;
7. option avec donnée indispensable absente → `BLOCKED_INSUFFICIENT_DATA` ;
8. plan final sans clinician gate → rejet ;
9. correction manuelle d'un landmark conserve coordonnée auto originale + audit ;
10. contradiction entre analyses reste visible.

## SUCCESS

Cette architecture sera considérée implémentée uniquement quand les schémas existent en code, les invariants sont testés et au moins un cas traverse la chaîne sans utiliser une narration libre comme source clinique.

## NEXT EXACT

Après fermeture documentaire du Lot 3 : implémenter les références de preuve + `Measurement`/`NormativeEvaluation` puis adapter l'actuel `CephaloAnalysisResult` sans casser la compatibilité.
