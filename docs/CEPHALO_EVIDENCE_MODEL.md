# CÉPHALO — EVIDENCE MODEL

**Statut : EN COURS — graphe + constructions + mesures mergés ; frontière patient/cas en certification ; pas encore source persistée de vérité**  
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
- frontière patient/cas : `backend/services/cephalo_evidence_case_integrity.py` ;
- matérialisation CRANIOM : `backend/services/cephalo_construction_evidence_adapter.py` ;
- adaptateur mesures CRANIOM : `backend/services/cephalo_measurement_adapter.py` ;
- tests dédiés : contrats, graphe, patient/cas, calibration, constructions et mesures.

Le graphe **n'est pas encore la source de vérité persistée du workflow patient**. La chaîne calculée couvre volontairement seulement les quatre mesures linéaires CRANIOM dont la géométrie backend est versionnée : `Situation_A`, `Situation_B`, `Decalage_A_B`, `Profondeur_Faciale`.

## STATUTS

- preuve : `OBSERVED | COMPUTED | INTERPRETED | CLINICIAN_VALIDATED` ;
- disponibilité : `AVAILABLE | MISSING | INVALID | NOT_APPLICABLE | NOT_COMPUTABLE`.

`MISSING` ou `NOT_COMPUTABLE` n'est jamais transformé en normalité, zéro, moyenne ou valeur patient par défaut.

## GATES STRUCTURELS

### SourceEvidence / patient / cas

Toute validation clinique du graphe exige un `patient_id` et un `case_id` explicites. Toutes les `SourceEvidence` du graphe doivent appartenir exactement à ce patient et porter ce même `case_id`. Le mélange inter-patient ou inter-cas est rejeté.

Une `calibration_ref` de mesure doit viser une vraie `SourceEvidence` dont `kind="calibration"`, pas simplement n'importe quelle source existante.

### LandmarkEvidence

Coordonnées finies, source image réelle, correction manuelle auditée avec coordonnées automatiques originales conservées.

### ConstructionEvidence

Une construction `AVAILABLE` exige de vrais `landmark_refs`, aucune dépendance déclarée manquante et une géométrie explicite. Une construction impossible devient `NOT_COMPUTABLE` avec `missing_landmark_ids`, sans faux landmark. Des landmarks provenant de radiographies différentes rendent la construction `INVALID`.

### MeasurementEvidence

Une valeur patient non finie est rejetée. Une mesure linéaire `AVAILABLE` exige une `calibration_ref`; sans calibration elle reste `NOT_COMPUTABLE` avec `value=None`.

### NormativeEvaluation

Profil versionné obligatoire. Version, méthode, mesure cible, unité et payload de référence doivent correspondre exactement au registre. Une référence inactive ne peut classifier aucun patient.

### Diagnostic / problème / objectif / option

Les références doivent réellement exister. En plus des champs praticien + date, un état `ACCEPTED/EDITED` pour diagnostic, problème ou objectif doit posséder un vrai `ClinicianValidationEvidence` visant exactement cet objet, avec le même praticien, le même horodatage et une action `ACCEPT/EDIT`.

Une option `CLINICIAN_SELECTED` suit le même contrat et ne peut être sélectionnée sur une simple affirmation embarquée dans l'objet.

### FinalPlan

Le plan final exige la même identité praticien, une validation `ACCEPT/EDIT` ciblant exactement le plan et le même horodatage d'audit. Toutes ses références doivent résoudre et son option doit réellement être sélectionnée.

## MATÉRIALISATION CRANIOM

`materialize_craniom_linear_constructions(...)` transforme des `LandmarkEvidence` canoniques en quatre `ConstructionEvidence` versionnées :
- `CRANIOM_A_TO_N_VERTICAL_V1` : A, N, Po, Or ;
- `CRANIOM_B_TO_N_VERTICAL_V1` : B, N, Po, Or ;
- `CRANIOM_AB_PRIME_V1` : A, B, Po, Or ;
- `CRANIOM_S_TO_N_VERTICAL_DEPTH_V1` : S, N, Po, Or.

Un landmark absent ou indisponible ne produit jamais une construction disponible. Une incohérence d'image source invalide uniquement les constructions dépendantes.

## ADAPTATEUR MESURES CRANIOM

`adapt_craniom_linear_measurements(...)` ne copie ni norme, ni interprétation, ni diagnostic depuis `CephaloAnalysisResult`.

Une valeur est `AVAILABLE` seulement si : payload `COM_Skeletal` en mm, `pixel_ratio` positif/fini, calibration explicite, et vraie `ConstructionEvidence` de définition/version attendue au statut `AVAILABLE`. Sinon la mesure reste `NOT_COMPUTABLE`; une valeur legacy non finie devient `INVALID`.

## SUCCESS LOT 0

Le Lot 0 ne sera fermé que lorsque :
- contrats + graphe + frontière patient/cas + matérialisation + adaptateur sont verts en CI ;
- un cas synthétique traverse la chaîne ;
- le workflow patient produit/persiste ces objets comme source de vérité, sans narration libre ;
- le `FinalPlan` reste impossible sans validation praticien.

## NEXT EXACT

Certifier #395, puis connecter `Source/Landmark → ConstructionEvidence → MeasurementEvidence` au workflow patient derrière une frontière de compatibilité explicite. Aucune norme, interprétation, diagnostic ou décision thérapeutique n'est activée par cette couche.
