# V1-05 / F5 — Deterministic Engine Contract

**Method:** F5-MDR-001  
**Status:** engineering primitive only; clinical activation blocked.

## Pure engine boundary
`backend/services/cephalo_superimposition.py` may:
- accept two immutable uint8 source images;
- accept one clinician-selected/confirmed ACB ROI per image;
- detect SIFT features only inside those ROIs;
- filter KNN matches with the literature-derived ratio < 0.7;
- estimate a moving-to-reference 4-DOF similarity transform;
- expose raw match/inlier metadata;
- render a derived warped image.

It may not:
- infer diagnosis or treatment response;
- convert match counts into clinical success/failure;
- invent mm calibration;
- persist a new source image;
- create an unrestricted affine/projective/elastic warp;
- claim clinical validation.

## Coordinate contract
- all ROI coordinates are source-image pixels;
- transform direction is `moving_to_reference`;
- output canvas size is the reference image size;
- original images are never mutated.

## Quality contract
The engine exposes estimation metadata but deliberately has no clinical acceptance score. Apart from the Zhao 2025 KNN ratio (<0.7), clinical quality thresholds remain blocked until the prospective validation protocol establishes them.

## Next integration gate
After unit tests are green:
1. implement source resolver from OrthoTimepointEvidence -> CephaloAnalysis;
2. enforce same patient/case/timepoint and adult applicability;
3. carry calibration provenance without assuming scale;
4. add API contract only after service-level fail-closed tests;
5. UI later, with BEFORE/mockup/AFTER sequence.


## Concurrency determinism
OpenCV RANSAC uses process-global RNG state. F5 serializes the seed+estimate section with a process lock so concurrent requests cannot perturb deterministic replay. This lock protects only transform estimation; image decoding and SIFT extraction remain outside it.

A returned estimate must also contain at least two RANSAC inlier correspondences. This is a mathematical computability gate, not a clinical quality threshold.
