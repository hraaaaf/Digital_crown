# CÉPHALO — EVIDENCE MODEL

**Statut : EN COURS — schémas typés + intégrité inter-objets + premier adaptateur runtime sur branches empilées ; pas encore source runtime de vérité**  
**Parent canonique :** `docs/CEPHALO_DIAGNOSTIC_SPEC.md`  
**Rôle :** architecture transversale des lots 3→14.

## GOAL

Interdire les sauts non traçables entre donnée patient, mesure, interprétation, diagnostic et traitement.

## CHAÎNE CANONIQUE

`SourceEvidence → LandmarkEvidence → Construction → Measurement → NormativeEvaluation → Finding → DiagnosticHypothesis → Problem → Objective → TreatmentOption → ClinicianValidation → FinalPlan`

Chaque objet dérivé conserve ses références de preuve, sa méthode/version et son statut.

## IMPLÉMENTATION ACTUELLE

- contrat typé : `backend/schemas/cephalo_evidence.py` ;
- tests unitaires d'objet : `backend/tests/test_cephalo_evidence_contracts.py` ;
- validation inter-objets : `backend/services/cephalo_evidence_graph.py` ;
- tests de chaîne synthétique : `backend/tests/test_cephalo_evidence_graph.py` ;
- adaptateur runtime CRANIOM : `backend/services/cephalo_measurement_adapter.py` ;
- tests adaptateur : `backend/tests/test_cephalo_measurement_adapter.py`.

Le graphe **n'est pas encore la source de vérité persistée du workflow patient**. L'adaptateur couvre volontairement seulement les quatre mesures linéaires CRANIOM dont la géométrie backend est déjà versionnée : `Situation_A`, `Situation_B`, `Decalage_A_B`, `Profondeur_Faciale`.

## STATUTS

- preuve : `OBSERVED | COMPUTED | INTERPRETED | CLINICIAN_VALIDATED` ;
- disponibilité : `AVAILABLE | MISSING | INVALID | NOT_APPLICABLE | NOT_COMPUTABLE`.

`MISSING` ou `NOT_COMPUTABLE` n'est jamais transformé en normalité, zéro, moyenne ou valeur patient par défaut.

## OBJETS MINIMAUX ET GATES

### LandmarkEvidence

Les coordonnées doivent être finies. `source_image_ref` et `evidence_refs` doivent résoudre vers une vraie `SourceEvidence`. Une correction manuelle conserve les coordonnées automatiques originales et son audit.

### ConstructionEvidence

Une construction `AVAILABLE` exige de vrais `landmark_refs`, aucune dépendance déclarée manquante et une géométrie explicite. Une construction impossible peut être matérialisée en `NOT_COMPUTABLE` avec `missing_landmark_ids`, sans inventer de faux identifiants de landmarks.

### MeasurementEvidence

Les landmarks, constructions et calibrations cités doivent exister. Une valeur patient non finie est rejetée. Une mesure linéaire `AVAILABLE` exige une `calibration_ref`; si la calibration manque, elle reste `NOT_COMPUTABLE` avec `value=None`.

### NormativeEvaluation

Le profil normatif doit exister dans le registre versionné. Version, méthode, mesure cible, unité et payload de référence doivent correspondre exactement au registre. Les sources citées doivent être celles du profil enregistré. Une référence inactive ne peut classifier aucun patient.

### Finding / DiagnosticHypothesis

Les preuves et findings cités doivent réellement exister. Un diagnostic `ACCEPTED/EDITED` nécessite praticien + date.

### Problem / Objective

Un état `ACCEPTED/EDITED` nécessite praticien + date. Les références diagnostic/problème doivent résoudre.

### TreatmentOption

Une option avec gate manquant ne peut être évaluable/sélectionnée. Une option `CLINICIAN_SELECTED` nécessite praticien + date.

### ClinicianValidation / FinalPlan

Le type et l'identifiant de toute validation doivent viser le même espace d'objets. Un plan final exige :
- option réellement `CLINICIAN_SELECTED` par le même praticien ;
- diagnostics/problèmes/objectifs réellement validés ;
- validation qui cible **ce plan précis** ;
- action `ACCEPT` ou `EDIT`, jamais `REJECT` ;
- même identité praticien et même horodatage d'audit entre validation et plan ;
- toutes les phases reliées à de vrais objectifs.

## ADAPTATEUR CRANIOM

`adapt_craniom_linear_measurements(...)` ne copie ni norme, ni interprétation, ni diagnostic depuis `CephaloAnalysisResult`.

Une valeur est `AVAILABLE` seulement si :
1. le payload est `COM_Skeletal` en millimètres ;
2. le `pixel_ratio` est positif et fini ;
3. une `calibration_ref` explicite est fournie ;
4. une vraie `ConstructionEvidence` existe, avec l'identifiant de définition attendu, la version certifiée `1` et le statut `AVAILABLE`.

Sinon, la mesure devient `NOT_COMPUTABLE` sans valeur patient. Une valeur legacy non finie devient `INVALID` et n'est jamais propagée.

Mesures actuellement autorisées par cet adaptateur :
- `Situation_A` → `CRANIOM_A_TO_N_VERTICAL_V1` ;
- `Situation_B` → `CRANIOM_B_TO_N_VERTICAL_V1` ;
- `Decalage_A_B` → `CRANIOM_AB_PRIME_V1` ;
- `Profondeur_Faciale` → `CRANIOM_S_TO_N_VERTICAL_DEPTH_V1`.

## SUCCESS

Le Lot 0 ne sera fermé que lorsque :
- contrats + intégrité graphe + adaptateur sont verts en CI ;
- au moins un cas synthétique traverse toute la chaîne ;
- les mesures patient CRANIOM certifiées passent par `MeasurementEvidence` sans narration libre ;
- aucune narration libre ne sert de donnée clinique source ;
- le `FinalPlan` reste impossible sans validation praticien.

## NEXT EXACT

Valider les branches empilées en CI, puis matérialiser les `ConstructionEvidence` depuis les landmarks patient et intégrer l'adaptateur derrière une frontière de compatibilité explicite. Étendre ensuite uniquement aux mesures dont construction et source scientifique sont certifiées. Aucun diagnostic ni traitement n'est activé par cet adaptateur.
