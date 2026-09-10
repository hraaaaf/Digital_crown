# CÉPHALO — CALIBRATION PROVENANCE

**Statut : EN COURS — implémentation empilée après PR #397**  
**Parent :** `docs/CEPHALO_DIAGNOSTIC_SPEC.md`

## GOAL

Une mesure linéaire en millimètres ne devient disponible que si sa calibration manuelle est reproductible et auditée.

## CONTRAT

La calibration canonique conserve atomiquement :
- `p1`, `p2` ;
- `distance_mm` ;
- `mm_per_pixel` recalculé ;
- méthode `MANUAL_TWO_POINT`, version `1` ;
- `calibrated_by` ;
- `calibrated_at`.

Si un `_evidence_graph_v1` existe, la calibration crée une nouvelle révision `MANUAL_CALIBRATION`, une `SourceEvidence(kind="calibration")` auditée et recalcule uniquement les quatre `MeasurementEvidence` CRANIOM déjà versionnées.

Le snapshot précédent est conservé dans `history`. Les landmarks et constructions ne sont pas réinventés lors d'une action de calibration.

## FAIL-CLOSED

- géométrie calibration invalide ou ratio incohérent : refus ;
- landmarks runtime différents des landmarks soutenant les constructions : refus ;
- patient/cas/image incohérents : refus ;
- présence de findings/diagnostics/options/plans aval : refus plutôt que conservation silencieuse de conclusions potentiellement périmées ;
- analyse legacy sans graphe : calibration historique mise à jour, mais aucun graphe scientifique fabriqué rétroactivement.

## COMPATIBILITÉ

Le POST public reste `/analyses/{analysis_id}/calibrate`. Le payload de réponse reste `status`, `mm_per_pixel`, `is_calibrated`.

Les sections géométriques du payload historique sont recalculées avec le nouveau ratio, tandis que les champs cliniques/narratifs saisis restent conservés.

## SUCCESS

- route unique réellement enregistrée ;
- provenance praticien/date persistée ;
- même transaction pour ratio, provenance, géométrie et evidence snapshot ;
- quatre mesures CRANIOM `AVAILABLE` seulement avec calibration prouvée ;
- tests fail-closed + CI exact-head verts.
