# CÉPHALO — LANDMARK CORRECTION AUDIT

**Statut : PR #399 — certification finale requise**  
**Parent :** `docs/CEPHALO_DIAGNOSTIC_SPEC.md`

## GOAL

Une correction manuelle d'un landmark doit conserver sa provenance automatique éventuelle, l'identité du praticien et l'horodatage, sans prétendre qu'un point inchangé a été corrigé.

## CONTRAT

- point inchangé : réutiliser l'evidence courante, aucune révision `LANDMARK_EDIT` ;
- point SRPose38 modifié : `MANUAL_CORRECTED`, conserver `original_auto_x/y`, `validated_by`, `validated_at`, statut `CLINICIAN_VALIDATED` ;
- correction ultérieure : conserver les mêmes coordonnées automatiques d'origine ;
- point omis : absent de `current_landmark_refs`, dépendances concernées `NOT_COMPUTABLE` ;
- réintroduction d'un point SRPose omis : correction auditée, même si les coordonnées redeviennent identiques à l'auto originel ;
- point manuel sans origine automatique : `MANUAL`, audit explicite, sans fabriquer `original_auto_x/y` ;
- calibration ultérieure : doit préserver/vérifier `current_landmark_refs` et ne jamais ressusciter un point historique ;
- modification mm/pixel d'un cas typé : uniquement via la transition de calibration auditée ;
- couche clinique aval existante : vraie correction refusée tant qu'une invalidation explicite n'est pas implémentée.

## FRONTIÈRE PATIENT/CAS

Le PUT canonique `/analyses/{analysis_id}` prend le praticien depuis `current_user.id`. Le client ne fournit pas `clinician_id`. Patient, cas et image source restent cohérents avec le snapshot persistant.

## SUCCESS

- unchanged ≠ corrected ;
- auto originel immuable à travers plusieurs corrections ;
- jeu courant explicite et non ambigu ;
- aucune résurrection après omission, y compris à travers une calibration ;
- praticien + timestamp obligatoires pour toute correction réelle ;
- constructions/mesures utilisent uniquement l'evidence courante ;
- route unique + tests multi-révisions + CI/T2 exact-head verts.

## NON-GOALS

Aucune norme, classification diagnostique ou décision thérapeutique dans ce lot.
