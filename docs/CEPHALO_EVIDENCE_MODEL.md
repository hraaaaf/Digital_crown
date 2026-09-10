# CÉPHALO — EVIDENCE MODEL

**Statut : EN COURS — schémas typés + intégrité inter-objets + matérialisation constructions + adaptateur mesures sur branches empilées ; pas encore source runtime de vérité**  
**Parent canonique :** `docs/CEPHALO_DIAGNOSTIC_SPEC.md`  
**Rôle :** architecture transversale des lots 3→14.

## GOAL

Interdire les sauts non traçables entre donnée patient, mesure, interprétation, diagnostic et traitement.

## CHAÎNE CANONIQUE

`SourceEvidence → LandmarkEvidence → Construction → Measurement → NormativeEvaluation → Finding → DiagnosticHypothesis → Problem → Objective → TreatmentOption → ClinicianValidation → FinalPlan`

Chaque objet dérivé conserve ses références de preuve, sa méthode/version et son statut.

## IMPLÉMENTATION ACTUELLE

- contrat typé : `backend/schemas/cephalo_evidence.py` ;
- validation inter-objets : `backend/services/cephalo_evidence_graph.py` ;
- matérialisation CRANIOM : `backend/services/cephalo_construction_evidence_adapter.py` ;
- adaptateur mesures CRANIOM : `backend/services/cephalo_measurement_adapter.py` ;
- tests dédiés : `backend/tests/test_cephalo_evidence_contracts.py`, `test_cephalo_evidence_graph.py`, `test_cephalo_construction_evidence_adapter.py`, `test_cephalo_measurement_adapter.py`.

Le graphe **n'est pas encore la source de vérité persistée du workflow patient**. La chaîne actuelle couvre volontairement seulement les quatre mesures linéaires CRANIOM dont la géométrie backend est déjà versionnée : `Situation_A`, `Situation_B`, `Decalage_A_B`, `Profondeur_Faciale`.

## STATUTS

- preuve : `OBSERVED | COMPUTED | INTERPRETED | CLINICIAN_VALIDATED` ;
- disponibilité : `AVAILABLE | MISSING | INVALID | NOT_APPLICABLE | NOT_COMPUTABLE`.

`MISSING` ou `NOT_COMPUTABLE` n'est jamais transformé en normalité, zéro, moyenne ou valeur patient par défaut.

## GATES STRUCTURELS

### LandmarkEvidence

Coordonnées finies, source image réelle, correction manuelle auditée avec coordonnées automatiques originales conservées.

### ConstructionEvidence

Une construction `AVAILABLE` exige de vrais `landmark_refs`, aucune dépendance déclarée manquante et une géométrie explicite. Une construction impossible devient `NOT_COMPUTABLE` avec `missing_landmark_ids`, sans faux landmark. Des landmarks provenant de radiographies différentes rendent la construction `INVALID`.

### MeasurementEvidence

Une valeur patient non finie est rejetée. Une mesure linéaire `AVAILABLE` exige une `calibration_ref`; sans calibration elle reste `NOT_COMPUTABLE` avec `value=None`.

### NormativeEvaluation

Profil versionné obligatoire. Version, méthode, mesure cible, unité et payload de référence doivent correspondre exactement au registre. Une référence inactive ne peut classifier aucun patient.

### Diagnostic → plan

Les références doivent réellement exister. Diagnostic, problème et objectif `ACCEPTED/EDITED` exigent praticien + date. Une option `CLINICIAN_SELECTED` exige praticien + date. Le plan final exige la même identité praticien, une validation `ACCEPT/EDIT` ciblant exactement le plan et le même horodatage d'audit.

## MATÉRIALISATION CRANIOM

`materialize_craniom_linear_constructions(...)` transforme des `LandmarkEvidence` canoniques en quatre `ConstructionEvidence` versionnées :
- `CRANIOM_A_TO_N_VERTICAL_V1` : A, N, Po, Or ;
- `CRANIOM_B_TO_N_VERTICAL_V1` : B, N, Po, Or ;
- `CRANIOM_AB_PRIME_V1` : A, B, Po, Or ;
- `CRANIOM_S_TO_N_VERTICAL_DEPTH_V1` : S, N, Po, Or.

Un landmark absent ou indisponible ne produit jamais une construction disponible. Une incohérence d'image source invalide uniquement les constructions dépendantes.

## ADAPTATEUR MESURES CRANIOM

`adapt_craniom_linear_measurements(...)` ne copie ni norme, ni interprétation, ni diagnostic depuis `CephaloAnalysisResult`.

Une valeur est `AVAILABLE` seulement si :
1. payload `COM_Skeletal` en millimètres ;
2. `pixel_ratio` positif et fini ;
3. `calibration_ref` explicite ;
4. vraie `ConstructionEvidence`, définition attendue, version `1`, statut `AVAILABLE`.

Sinon la mesure devient `NOT_COMPUTABLE` sans valeur patient. Une valeur legacy non finie devient `INVALID`.

## SUCCESS

Le Lot 0 ne sera fermé que lorsque :
- contrats + intégrité graphe + matérialisation + adaptateur sont verts en CI ;
- un cas synthétique traverse toute la chaîne ;
- les mesures patient CRANIOM certifiées passent par `MeasurementEvidence` sans narration libre ;
- aucune narration libre ne sert de donnée clinique source ;
- le `FinalPlan` reste impossible sans validation praticien.

## NEXT EXACT

Valider la pile en CI puis connecter la matérialisation et l'adaptateur au workflow patient derrière une frontière de compatibilité explicite. Étendre uniquement aux mesures dont construction et source scientifique sont certifiées. Aucun diagnostic ni traitement n'est activé par cette couche.
