# CÉPHALO — EVIDENCE MODEL

**Statut : EN COURS — persistence runtime mergée via #397 ; provenance calibration en certification #398 ; lecture applicative encore legacy**  
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
- `backend/services/cephalo_runtime_evidence.py` — mergé via #397
- `backend/services/cephalo_calibration_evidence.py` — PR #398
- `backend/routers/cephalo_calibration_provenance.py` — PR #398

## PERSISTENCE #397

Le snapshot est écrit sous `_evidence_graph_v1` dans `CephaloAnalysis.angles_data`, dans la même écriture que le résultat historique. Aucune migration DB n'est requise.

Le payload public de `process_new_radio` et `refine_analysis` reste inchangé. Le graphe porte `authority_status=PERSISTED_NOT_YET_READ_PATH` tant que les lectures historiques ne sont pas migrées.

PR #397 est mergée au commit `7aa83d566c87db6796cddea5a1facd891f8b5896`. Son HEAD final `a52fc93ec8cc37b72b8e9b66e48f5a26d38f91b0` a passé CI `34490188077` et T2 `34490188120`.

## GATES FAIL-CLOSED

- `SRPOSE38_AUTO` exige le mode `SOTA_ONNX_38` et l'ensemble exact des 38 identifiants certifiés.
- un fallback automatique legacy ne peut pas être enregistré comme preuve SRPose38.
- un raffinement conserve les points SRPose38 initiaux et archive le snapshot précédent.
- schema, `case_id` et identité de l'image source sont vérifiés.
- les quatre constructions CRANIOM versionnées utilisent uniquement les landmarks de la révision courante.
- les quatre valeurs CRANIOM sont recroisées avec leur géométrie avant persistence.
- l'auto-calibration legacy seule ne débloque aucune mesure linéaire typée.
- seules `Situation_A`, `Situation_B`, `Decalage_A_B` et `Profondeur_Faciale` sont adaptées actuellement.
- sans construction et calibration prouvées : `value=None`, `NOT_COMPUTABLE`.

## CALIBRATION MANUELLE #398

La calibration devient une transition de preuve distincte. Elle conserve p1/p2, distance réelle, ratio, méthode/version, opérateur et horodatage UTC.

Si un graphe typé existe :
- nouvelle révision `MANUAL_CALIBRATION` ;
- les landmarks/constructions courants sont réutilisés, jamais réinventés ;
- une nouvelle `SourceEvidence(kind="calibration")` porte opérateur + timestamp ;
- les quatre `MeasurementEvidence` CRANIOM sont recalculées avec cette source ;
- l'ancien snapshot est archivé dans `history` ;
- toute divergence entre landmarks runtime et evidence soutenant les constructions est refusée ;
- toute couche clinique aval non vide est refusée plutôt que conservée silencieusement après changement d'échelle.

Une analyse legacy sans `_evidence_graph_v1` reste calibrable, mais aucun historique scientifique rétroactif n'est fabriqué.

## SUCCESS LOT 0

Le lot reste ouvert jusqu'à ce que persistence + lecture utilisent le graphe comme vérité scientifique, que calibration et corrections manuelles portent une provenance réelle, et que les tests traversants soient verts.

## NEXT EXACT

Certifier #398, puis ajouter l'audit praticien des corrections manuelles. Basculer ensuite le read-path des quatre mesures CRANIOM vers `_evidence_graph_v1`.
