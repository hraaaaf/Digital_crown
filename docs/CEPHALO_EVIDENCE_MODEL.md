# CÉPHALO — EVIDENCE MODEL

**Statut : EN COURS — persistence runtime #397 et calibration auditée #398 mergées ; correction-landmark audit en PR #399 ; lecture applicative encore legacy**  
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
- `backend/services/cephalo_runtime_evidence.py` — #397
- `backend/services/cephalo_calibration_evidence.py` — #398, renforcé par #399 pour conserver le jeu courant explicite
- `backend/routers/cephalo_calibration_provenance.py` — #398
- `backend/services/cephalo_landmark_correction_evidence.py` — #399
- `backend/routers/cephalo_landmark_refinement.py` — #399

## PERSISTENCE #397

Le snapshot est écrit sous `_evidence_graph_v1` dans `CephaloAnalysis.angles_data`, dans la même écriture que le résultat historique. Aucune migration DB n'est requise.

Le payload public de `process_new_radio` et `refine_analysis` reste inchangé. Le graphe porte `authority_status=PERSISTED_NOT_YET_READ_PATH` tant que les lectures historiques ne sont pas migrées.

PR #397 est mergée au commit `7aa83d566c87db6796cddea5a1facd891f8b5896`. Son HEAD final `a52fc93ec8cc37b72b8e9b66e48f5a26d38f91b0` a passé CI `34490188077` et T2 `34490188120`.

## GATES FAIL-CLOSED

- `SRPOSE38_AUTO` exige le mode `SOTA_ONNX_38` et l'ensemble exact des 38 identifiants certifiés.
- un fallback automatique legacy ne peut pas être enregistré comme preuve SRPose38.
- schema, `case_id`, patient et identité de l'image source sont vérifiés.
- les quatre constructions CRANIOM versionnées utilisent uniquement les landmarks courants.
- les quatre valeurs CRANIOM sont recroisées avec leur géométrie avant persistence.
- l'auto-calibration legacy seule ne débloque aucune mesure linéaire typée.
- seules `Situation_A`, `Situation_B`, `Decalage_A_B` et `Profondeur_Faciale` sont adaptées actuellement.
- sans construction et calibration prouvées : `value=None`, `NOT_COMPUTABLE`.

## CALIBRATION MANUELLE #398

PR #398 est mergée au commit `35f5eca034ab780e92aa877b1120fd4e6c3b3dce`. Son HEAD `e06af52d611ece465e5087b2c485784b6cf74d49` a passé CI `34498056894` et T2 `34498056887`.

La calibration est une transition de preuve distincte : p1/p2, distance réelle, ratio, méthode/version, opérateur authentifié et horodatage UTC. Elle crée une révision `MANUAL_CALIBRATION`, remplace uniquement la source de calibration, recalcule les quatre mesures linéaires et refuse toute couche clinique aval non vide.

Une analyse legacy sans `_evidence_graph_v1` reste calibrable, mais aucun historique scientifique rétroactif n'est fabriqué.

## CORRECTIONS LANDMARKS #399

Le PUT canonique d'édition est relié au praticien authentifié. Une vraie modification crée une révision `LANDMARK_EDIT`; une soumission géométriquement identique n'en crée aucune.

Le snapshot conserve à la fois :
- l'evidence SRPose38 automatique immuable pour audit ;
- les corrections `MANUAL_CORRECTED` avec `original_auto_x/y`, praticien et timestamp ;
- `current_landmark_refs`, liste explicite des evidence objets qui constituent le jeu courant.

Cette liste explicite ferme un piège important : conserver l'auto historique ne doit jamais réactiver silencieusement un landmark supprimé/omis. La calibration #398 est renforcée dans #399 pour préserver et vérifier `current_landmark_refs` entre transitions. Un point SRPose réintroduit après omission devient une correction auditée, même s'il reprend exactement ses coordonnées automatiques d'origine.

Le PUT générique ne peut pas changer `mm_per_pixel` sur un cas typé : le changement d'échelle passe obligatoirement par la route de calibration auditée.

## SUCCESS LOT 0

Le lot reste ouvert jusqu'à ce que persistence + lecture utilisent le graphe comme vérité scientifique, que toutes les modifications manuelles portent une provenance réelle et que les tests traversants soient verts.

## NEXT EXACT

Certifier et merger #399, puis basculer le read-path des quatre mesures CRANIOM vers `_evidence_graph_v1` avant toute activation normative.
