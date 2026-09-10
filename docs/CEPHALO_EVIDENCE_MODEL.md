# CÉPHALO — EVIDENCE MODEL

**Statut : EN COURS — contrats, intégrité, patient/cas, constructions et mesures mergés ; persistence runtime en PR #397 ; lecture applicative encore legacy**  
**Parent canonique :** `docs/CEPHALO_DIAGNOSTIC_SPEC.md`

## GOAL

Rendre chaque mesure céphalométrique traçable jusqu'à sa source, ses landmarks, sa construction et sa calibration.

## CHAÎNE

`SourceEvidence → LandmarkEvidence → ConstructionEvidence → MeasurementEvidence`

Les couches cliniques aval restent hors du bridge runtime actuel.

## IMPLÉMENTATION

- `backend/schemas/cephalo_evidence.py`
- `backend/services/cephalo_evidence_graph.py`
- `backend/services/cephalo_evidence_case_integrity.py`
- `backend/services/cephalo_construction_evidence_adapter.py`
- `backend/services/cephalo_measurement_adapter.py`
- `backend/services/cephalo_runtime_evidence.py` — PR #397

## PERSISTENCE #397

Le snapshot est écrit sous `_evidence_graph_v1` dans `CephaloAnalysis.angles_data`, dans la même écriture que le résultat historique. Aucune migration DB n'est requise.

Le payload public de `process_new_radio` et `refine_analysis` reste inchangé. Le graphe porte `authority_status=PERSISTED_NOT_YET_READ_PATH` tant que les lectures historiques ne sont pas migrées.

## GATES FAIL-CLOSED

- `SRPOSE38_AUTO` exige le mode `SOTA_ONNX_38` et l'ensemble exact des 38 identifiants certifiés.
- un fallback automatique legacy ne peut pas être enregistré comme preuve SRPose38.
- un raffinement crée une nouvelle révision `MANUAL/OBSERVED` et conserve les points SRPose38 initiaux.
- les quatre constructions CRANIOM versionnées utilisent uniquement les landmarks de la révision courante.
- l'auto-calibration legacy seule ne débloque aucune mesure linéaire typed.
- une calibration utilisable exige `p1`, `p2`, une distance réelle et un ratio cohérent avec cette géométrie.
- seules `Situation_A`, `Situation_B`, `Decalage_A_B` et `Profondeur_Faciale` sont adaptées actuellement.
- sans construction et calibration prouvées : `value=None`, `NOT_COMPUTABLE`.

## SUCCESS LOT 0

Le lot reste ouvert jusqu'à ce que : persistence + lecture utilisent le graphe comme vérité scientifique, calibration et corrections manuelles portent une provenance réelle, et les tests traversants restent verts.

## NEXT EXACT

Certifier #397, puis câbler la provenance de calibration manuelle et l'identité praticien des corrections. Basculer ensuite le read-path des quatre mesures CRANIOM vers `_evidence_graph_v1`.
