# CÉPHALO — EVIDENCE MODEL

**Statut : EN COURS — schémas typés + intégrité inter-objets + premier adaptateur de mesures sur branches empilées ; pas encore source runtime de vérité**  
**Parent canonique :** `docs/CEPHALO_DIAGNOSTIC_SPEC.md`  
**Rôle :** architecture transversale des lots 3→14.

## GOAL

Interdire les sauts non traçables entre donnée patient, mesure, interprétation, diagnostic et traitement.

## CHAÎNE CANONIQUE

`SourceEvidence → LandmarkEvidence → Construction → Measurement → NormativeEvaluation → Finding → DiagnosticHypothesis → Problem → Objective → TreatmentOption → ClinicianValidation → FinalPlan`

Chaque objet dérivé conserve ses `evidence_refs`, sa méthode/version et son statut.

## IMPLÉMENTATION ACTUELLE

- contrat typé : `backend/schemas/cephalo_evidence.py` ;
- tests unitaires d'objet : `backend/tests/test_cephalo_evidence_contracts.py` ;
- validation inter-objets : `backend/services/cephalo_evidence_graph.py` ;
- tests de chaîne synthétique : `backend/tests/test_cephalo_evidence_graph.py` ;
- premier adaptateur runtime : `backend/services/cephalo_measurement_adapter.py` ;
- tests adaptateur : `backend/tests/test_cephalo_measurement_adapter.py`.

Le graphe **n'est pas encore la source de vérité persistée du workflow patient**. L'adaptateur actuel ne couvre volontairement que les quatre mesures linéaires CRANIOM déjà reliées à des constructions géométriques versionnées : `Situation_A`, `Situation_B`, `Decalage_A_B`, `Profondeur_Faciale`.

## STATUTS

- preuve : `OBSERVED | COMPUTED | INTERPRETED | CLINICIAN_VALIDATED` ;
- disponibilité : `AVAILABLE | MISSING | INVALID | NOT_APPLICABLE | NOT_COMPUTABLE`.

`MISSING` n'est jamais transformé en normalité, zéro, moyenne ou valeur patient par défaut.

## OBJETS MINIMAUX ET GATES

### LandmarkEvidence

Les coordonnées doivent être finies. `source_image_ref` et `evidence_refs` doivent résoudre vers une vraie `SourceEvidence`. Une correction manuelle conserve les coordonnées automatiques originales et son audit.

### Construction / Measurement

Les landmarks, constructions et calibrations référencés doivent exister. Une valeur patient non finie est rejetée/neutralisée. Une mesure linéaire `AVAILABLE` exige une référence de calibration ; sans calibration traçable elle reste explicitement `NOT_COMPUTABLE` avec `value=None`.

### NormativeEvaluation

Le profil normatif doit exister dans le registre versionné, sa version doit correspondre, et ses sources doivent être celles enregistrées pour cette référence. Une classification sans règle versionnée reste interdite.

### Finding / DiagnosticHypothesis

Les preuves et findings cités doivent réellement exister. Un diagnostic `ACCEPTED/EDITED` nécessite praticien + date.

### Problem / Objective

Un état `ACCEPTED/EDITED` nécessite praticien + date. Les références diagnostic/problème doivent résoudre.

### TreatmentOption

Une option avec gate manquant ne peut être évaluable/sélectionnée. Une option `CLINICIAN_SELECTED` nécessite praticien + date.

### ClinicianValidation / FinalPlan

Un plan final exige :

- option réellement `CLINICIAN_SELECTED` par le même praticien ;
- diagnostics/problèmes/objectifs réellement validés ;
- référence de validation qui cible **ce plan précis** ;
- action de validation `ACCEPT` ou `EDIT`, jamais `REJECT` ;
- cohérence de l'identité praticien ;
- toutes les phases reliées à de vrais objectifs.

## ADAPTATEUR CRANIOM

`adapt_craniom_linear_measurements(...)` ne copie ni norme, ni interprétation, ni diagnostic depuis `CephaloAnalysisResult`.

Pour qu'une valeur brute soit émise comme `AVAILABLE`, il exige :
1. un payload `COM_Skeletal` ;
2. une construction matérialisée pour la mesure ;
3. un `pixel_ratio` positif et fini ;
4. une `calibration_ref` explicite.

Si la valeur runtime existe mais que la calibration n'est pas traçable, la valeur est supprimée du graphe et la mesure devient `NOT_COMPUTABLE`. Une valeur legacy non finie devient `INVALID` et n'est jamais propagée.

## SUCCESS

Le Lot 0 ne sera fermé que lorsque :

- contrats + intégrité graphe + adaptateur sont verts en CI ;
- au moins un cas synthétique traverse toute la chaîne ;
- les mesures patient CRANIOM certifiées passent par `MeasurementEvidence` sans narration libre ;
- aucune narration libre ne sert de donnée clinique source ;
- le `FinalPlan` reste impossible sans validation praticien.

## NEXT EXACT

Valider l'adaptateur en CI, puis l'intégrer au workflow patient derrière une frontière explicite de compatibilité. Étendre ensuite uniquement aux mesures dont la construction et la source scientifique sont certifiées. Aucun diagnostic ni traitement n'est activé par cet adaptateur.
