# V1-05 / F5 — Method Decision Record

**Decision ID:** F5-MDR-001  
**Date:** 2026-09-19  
**Status:** ACCEPTED FOR ENGINEERING VALIDATION — NOT CLINICALLY VALIDATED

**Registered evidence:** `abo-superimpositions-structural-method`, `graf-cephalo-superimposition-review-2022`, `jiang-feature-matching-superimposition-2020`, `zhao-feature-matching-superimposition-2025`, `opencv-bfmatcher-4-13`.

## Decision
Digital Crown F5 will use **Anterior Cranial Base Structural Feature Registration** as the initial scientific method family.

Implementation candidate:

`clinician-confirmed stable ACB ROI -> grayscale feature extraction -> SIFT -> KNN ratio filter (<0.7) -> robust 2D similarity-transform estimation -> immutable transform metadata -> viewer`

## Why this method
- It follows the structural-method principle used by the ABO rather than substituting a landmark line for stable anatomy.
- Published 2020 and 2025 work supports feature matching for cephalometric superimposition.
- A similarity transform has four degrees of freedom and preserves anatomy up to rotation, uniform scale and translation.
- It fits Digital Crown's deterministic, local-first architecture and needs no generative AI/LLM.
- A clinician-confirmed ROI avoids adding a new learned ROI detector before Digital Crown has its own validation dataset.

## Rejected alternatives

### S-N line / two-landmark registration
**Rejected as final F5 method.** It is reproducible geometrically but is not equivalent to Björk/ABO structural superimposition and may inherit remodeling/growth error from the landmarks themselves.

### Unrestricted affine or projective registration
**Rejected.** Shear, anisotropic scaling or projective warping can alter anatomical geometry and make the overlay misleading.

### New YOLO-based stable-region detector in F5 v1
**Deferred.** Zhao 2025 makes this scientifically interesting, but adding another learned runtime model creates a separate dataset, model-provenance and validation burden. Digital Crown can revisit it only after the deterministic path is validated.

## Initial applicability
F5-MDR-001 is initially restricted to:
- same patient;
- two canonical OrthoTimepoints;
- each timepoint linked to a canonical CephaloAnalysis;
- lateral cephalograms with original image available;
- interpretable anterior-cranial-base region;
- **adult patients (>=18 years) for the first validation scope**.

Growing patients are **NOT YET VALIDATED** and must fail closed until a dedicated growth-population validation record exists.

## Calibration
Calibration status must always be displayed in metadata.

- Visual registration may be computed in image coordinates.
- No quantitative displacement in millimetres may be exposed unless both source analyses have valid calibration provenance.
- Missing calibration must never be converted into an assumed scale.

## Registration transform
Allowed transform family:
- rotation;
- uniform scale;
- X translation;
- Y translation.

No shear, non-uniform scaling, perspective transformation, elastic deformation or local warping.

## Stable-region contract
The region must contain the anterior-cranial-base structures used for structural superimposition, not merely S and N.

For F5 v1, the ROI is operator-selected/confirmed and carried in the recalculable result metadata. The engineering preview does not create a persistent F5 result table. The engine must not silently change the ROI.

## Determinism and provenance
A result must retain or expose enough metadata to reproduce it:
- source analysis IDs;
- source image references;
- from/to timepoint IDs;
- ROI coordinates for each image;
- algorithm ID + version;
- SIFT/KNN configuration;
- ratio-test value;
- transformation matrix;
- match count;
- inlier count/mask summary;
- image dimensions;
- calibration status;
- runtime/library version needed to reproduce the computation;
- software commit where the calling layer can supply it.

A computation timestamp is audit metadata, not an input required to reproduce the transform; the current engineering preview therefore does not persist one.

The original image is immutable.

## Fail-closed conditions
No usable superimposition result when:
- patient/case/timepoint linkage is inconsistent;
- source image is missing/unreadable;
- CephaloAnalysis link is missing;
- ROI is invalid or lacks detectable features;
- matching/transform estimation fails;
- transform is non-finite or geometrically invalid;
- population is outside the validated applicability record;
- future quality thresholds are not satisfied.

Quality thresholds beyond the literature-derived 0.7 KNN ratio are **not invented here**. Zhao et al. report SIFT with KNN ratio filtering but describe Hamming distance; OpenCV's own descriptor contract recommends L1/L2 for SIFT and Hamming for binary descriptors. Digital Crown therefore uses SIFT + L2 and treats Zhao as support for the feature-matching/ratio/similarity-transform method family, not as a byte-for-byte implementation specification. They must be derived and versioned from the validation program before clinical activation.

## UI safety
The viewer may show source, overlay, opacity/alternation and method metadata.

It must not automatically display:
- improvement/aggravation;
- success/failure;
- progress score;
- diagnostic arrows;
- treatment recommendations;
- normative heatmaps.

## Scientific uncertainty
ABO structural methodology is an established professional standard, but the 2022 systematic review found insufficient high-quality evidence to claim that any superimposition method is universally accurate. Digital Crown therefore treats this method as a reproducible comparison tool requiring clinician review, not a diagnostic oracle.

## Gate opened by this record
Engineering may now implement the deterministic registration primitive and synthetic numerical tests.

Clinical activation remains blocked pending the Validation Strategy and independent scientific review.


## Acquisition comparability amendment — 2026-09-19
The evidence does not justify assuming cross-machine/cross-protocol equivalence. Jiang 2020 used paired cephalograms from the same X-ray machine; Zhao 2025 used the same X-ray machine with identical resolution and quality.

Digital Crown currently lacks acquisition-device/protocol provenance in `CephaloAnalysis`. F5 therefore marks acquisition protocol as `UNVERIFIED` and remains engineering-only. Clinical activation requires either traceable acquisition comparability or dedicated cross-protocol validation; no equivalence is inferred from image dimensions or calibration alone.
