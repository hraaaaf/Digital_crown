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


## Engineering-preview activation boundary
F5 remains hidden and unavailable by default.

Both sides require explicit engineering opt-in:
- backend: `DIGITAL_CROWN_F5_ENGINEERING_PREVIEW=1`;
- frontend: `VITE_F5_ENGINEERING_PREVIEW=1`.

Without the frontend flag, the F5 entry point is not rendered. Without the backend flag, F5 endpoints return 404. These flags are engineering gates only and must not be interpreted as clinical approval.


## Acquisition-protocol provenance gap
The current `CephaloAnalysis` model does not persist X-ray device identity, acquisition protocol, resolution provenance, or an explicit cross-timepoint comparability record.

F5 therefore exposes `acquisition_protocol_status=UNVERIFIED` in every engineering-preview context. This is not a cosmetic warning: the feature-matching studies used controlled same-machine acquisition conditions. The current F5 preview must not be presented as clinically validated across unknown machines/protocols until provenance is added or a separate cross-protocol validation demonstrates acceptable agreement.
