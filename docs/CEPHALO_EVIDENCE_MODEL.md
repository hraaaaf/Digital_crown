# CÉPHALO — EVIDENCE MODEL

**Statut : EN COURS — schémas typés + registre de liens sur branche empilée ; pas encore source runtime de vérité**  
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
- tests de chaîne synthétique : `backend/tests/test_cephalo_evidence_graph.py`.

Le graphe **n'est pas encore branché comme source de vérité du workflow patient**. Les payloads céphalo historiques restent en compatibilité pendant la migration.

## STATUTS

- preuve : `OBSERVED | COMPUTED | INTERPRETED | CLINICIAN_VALIDATED` ;
- disponibilité : `AVAILABLE | MISSING | INVALID | NOT_APPLICABLE | NOT_COMPUTABLE`.

`MISSING` n'est jamais transformé en normalité, zéro, moyenne ou valeur patient par défaut.

## OBJETS MINIMAUX ET GATES

### LandmarkEvidence

Les coordonnées doivent être finies. `source_image_ref` et `evidence_refs` doivent résoudre vers une vraie `SourceEvidence`. Une correction manuelle conserve les coordonnées automatiques originales et son audit.

### Construction / Measurement

Les landmarks, constructions et calibration référencés doivent exister. Une mesure linéaire sans calibration ou une valeur non finie est rejetée.

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

## SUCCESS

Le Lot 0 ne sera fermé que lorsque :

- ces contrats sont verts en CI ;
- au moins un cas synthétique traverse toute la chaîne ;
- un adaptateur runtime transforme les mesures patient en `MeasurementEvidence` sans narration libre ;
- aucune narration libre ne sert de donnée clinique source ;
- le `FinalPlan` reste impossible sans validation praticien.

## NEXT EXACT

Après intégration des branches empilées : construire l'adaptateur runtime `CephaloAnalysisResult → MeasurementEvidence`, d'abord pour les mesures CRANIOM certifiées géométriquement. Aucun diagnostic ni traitement ne sera activé par cet adaptateur.
