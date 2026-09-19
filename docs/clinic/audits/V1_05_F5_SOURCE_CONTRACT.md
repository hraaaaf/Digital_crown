# V1-05 / F5 — Canonical Source Contract

**Status:** implemented as a service-level source resolver; no API/UI activation yet.

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
- original image path is present;
- calibrated analyses have a finite positive `mm_per_pixel`;
- F5-MDR-001 adult applicability is satisfied at both timepoints.

## Calibration rule
An uncalibrated source does **not** fabricate scale. Source resolution may still permit an engineering visual overlay, but `quantitative_mm_allowed=false`. Millimetric displacement is not exposed.

## Ambiguity rule
If a timepoint has multiple CephaloAnalysis evidences, F5 fails with `CEPHALO_EVIDENCE_AMBIGUOUS`; it never guesses the intended radiograph.

## Population rule
F5-MDR-001 is adult-only for the initial validation scope. Any timepoint acquired before age 18 fails with `POPULATION_NOT_VALIDATED` until a separate growing-patient validation record exists.

## Persistence
No F5 result table is introduced. This remains a recalculable derived operation pending evidence that persistence is needed.
