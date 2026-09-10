# CÉPHALO — EVIDENCE MODEL

**Statut : EN COURS — schémas typés + tests de contrat présents dans PR #390 ; pas encore source runtime de vérité**  
**Parent canonique :** `docs/CEPHALO_DIAGNOSTIC_SPEC.md`  
**Rôle :** architecture transversale des lots 3→14.

## GOAL

Interdire les sauts non traçables entre donnée patient, mesure, interprétation, diagnostic et traitement.

## CHAÎNE CANONIQUE

`SourceEvidence → LandmarkEvidence → Construction → Measurement → NormativeEvaluation → Finding → DiagnosticHypothesis → Problem → Objective → TreatmentOption → ClinicianValidation → FinalPlan`

Chaque objet dérivé conserve ses `evidence_refs`, sa méthode/version et son statut.

## IMPLÉMENTATION ACTUELLE

Le contrat typé est matérialisé dans `backend/schemas/cephalo_evidence.py`.

Les tests de contrat sont dans `backend/tests/test_cephalo_evidence_contracts.py`.

Ce graphe **n'est pas encore branché comme source de vérité du workflow patient**. Les payloads céphalo historiques restent en compatibilité pendant la migration.

## STATUTS

- preuve : `OBSERVED | COMPUTED | INTERPRETED | CLINICIAN_VALIDATED` ;
- disponibilité : `AVAILABLE | MISSING | INVALID | NOT_APPLICABLE | NOT_COMPUTABLE`.

`MISSING` n'est jamais transformé en normalité, zéro, moyenne ou valeur patient par défaut.

## OBJETS MINIMAUX

### LandmarkEvidence

`landmark_id`, coordonnées finies `x/y`, `source_image_ref`, `origin`, `model_sha256/pipeline_version` si automatique, coordonnées automatiques originales si corrigées, audit praticien, `evidence_refs`.

Origines : `SRPOSE38_AUTO | MANUAL | MANUAL_CORRECTED`.

### Construction

`construction_id`, `definition_id/version`, `landmark_refs`, géométrie, statut.

### Measurement

`measurement_id`, `analysis_id`, `method_id/version`, valeur patient finie, `unit`, `landmark_refs`, `construction_refs`, `calibration_ref` si linéaire, statut, `evidence_refs`.

La norme n'est jamais embarquée implicitement dans la mesure brute.

### NormativeEvaluation

`measurement_ref`, `norm_profile_id/version`, contexte d'applicabilité, plage/valeur de référence explicite et sourcée, règle de classification versionnée, statut, `source_refs`.

Une évaluation disponible avec référence vide est rejetée. Une classification sans `classification_rule_id` est rejetée.

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

**Invariant :** un `FinalPlan` est invalide sans `clinician_id`, `clinician_validated_at` et référence de validation.

## DETTE ACTUELLE

`backend/schemas/clinical.py` conserve encore des sorties historiques sous chaînes libres (`DiagnosticSLM`, `plan_traitement`, `resume_diagnostic`, `ai_narrative`). Elles restent compatibles pendant migration mais ne doivent pas redevenir la source clinique de vérité. Les résumés texte seront des vues dérivées du graphe typé.

## TESTS DE CONTRAT

Les tests actuels couvrent notamment :

1. mesure sans dépendance géométrique → rejet ;
2. mesure linéaire sans calibration → rejet ;
3. mesure marquée indisponible avec valeur patient → rejet ;
4. coordonnées landmark/mesure non finies → rejet ;
5. correction manuelle landmark sans coordonnées auto originales/audit → rejet ;
6. évaluation normative sans référence explicite → rejet ;
7. classification normative sans règle versionnée → rejet ;
8. diagnostic accepté sans validation praticien → rejet ;
9. option avec gate manquant mais marquée évaluable → rejet ;
10. plan final sans gate praticien → rejet.

Restent à tester lors du branchement runtime : existence réelle des références entre objets, propagation des contradictions, et parcours complet sans narration libre comme source clinique.

## SUCCESS

Le Lot 0 ne sera fermé que lorsque :

- les tests de contrat sont verts ;
- au moins un cas synthétique traverse `SourceEvidence → ... → FinalPlan` ;
- toutes les références sont résolues/validées ;
- aucune narration libre ne sert de donnée clinique source ;
- le `FinalPlan` reste impossible sans validation praticien.

## NEXT EXACT

Après validation CI du socle PR #390 : construire l'adaptateur de compatibilité `CephaloAnalysisResult → MeasurementEvidence` puis un premier cas synthétique CRANIOM traversant le graphe jusqu'au `Finding`, sans activer de diagnostic ni traitement.
