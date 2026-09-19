# V1-05 / F5 — Canonical Source Contract

**Status:** implemented as a service-level source resolver; engineering API/UI remain preview-gated.

## Chain
`OrthoCase -> OrthoTimepoint -> OrthoTimepointEvidence -> CephaloAnalysis -> image_original_path`

F5 never searches the media library heuristically and never duplicates the source image.

## Required invariants
- patient exists in the current employer/cabinet scope;
- patient is not soft-deleted;
- case belongs to that patient/cabinet;
- two distinct ordered timepoints belong to that same case;
- each selected timepoint has exactly one cephalometric evidence candidate;
- evidence resolves to a CephaloAnalysis owned by the same patient;
- original image path is present and resolves under the canonical local `api/static/uploads/radios/` root before browser use;
- calibrated analyses have a finite positive `mm_per_pixel`;
- F5-MDR-001 adult applicability is satisfied at both timepoints.

## Calibration rule
An uncalibrated source does **not** fabricate scale. Source resolution may still permit an engineering visual overlay, but `quantitative_mm_allowed=false`. Millimetric displacement is not exposed.

If a legacy row is marked `is_calibrated=false` but still contains a stale `mm_per_pixel`, F5 normalizes the public source metadata to `mm_per_pixel=null`. The stale ratio is never surfaced as usable scale.

A row marked `is_calibrated=true` without a finite positive `mm_per_pixel` fails closed with `INVALID_CALIBRATION`.

## Ambiguity rule
If a timepoint has multiple CephaloAnalysis evidences, F5 fails with `CEPHALO_EVIDENCE_AMBIGUOUS`; it never guesses the intended radiograph.

## Population rule
F5-MDR-001 is adult-only for the initial validation scope. Any timepoint acquired before age 18 fails with `POPULATION_NOT_VALIDATED` until a separate growing-patient validation record exists.

## Persistence
No F5 result table is introduced. This remains a recalculable derived operation pending evidence that persistence is needed.


## Permission and privacy boundary
Both F5 context and estimation endpoints require the canonical `cephalo` permission, not merely general patient access.

The engineering API validates both source paths before returning context to the browser. The viewer accepts only canonical local radiograph paths under `api/static/uploads/radios/`; arbitrary HTTP(S) image URLs are rejected to prevent unintended external egress.
