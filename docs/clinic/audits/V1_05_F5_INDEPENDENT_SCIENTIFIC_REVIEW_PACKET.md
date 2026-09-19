# V1-05 / F5 — Independent Scientific Review Packet

**Target:** PR #620 — `feat/v1-05-f5-scientific-superimposition`  
**Base:** `master@20bfe3349399bf49a2f5ece14c5f70526e9d4a1b`  
**Review status:** REQUIRED — this packet is preparation only and is not an independent review.

## Reviewer independence
Use a reviewer that did not author the F5 implementation. The reviewer is read-only and must not silently fix findings.

Required output:
- `decision`;
- `blocking_findings`;
- `major_findings`;
- `minor_findings`;
- `missing_tests`;
- `scientific_uncertainties`;
- `required_actions`.

No AI review may assign `approved-by-clinician`.

## Read first
1. `.claude/rules/scientific-engineering.md`
2. `.claude/agents/scientific-reviewer.md`
3. `docs/scientific-ai/SOURCE_POLICY.md`
4. `docs/scientific-ai/SOURCE_REGISTRY.yaml`
5. `docs/clinic/audits/V1_05_F5_SCIENTIFIC_SUPERIMPOSITION_LITERATURE_REVIEW.md`
6. `docs/clinic/audits/V1_05_F5_METHOD_DECISION_RECORD.md`
7. `docs/clinic/audits/V1_05_F5_VALIDATION_STRATEGY.md`
8. `docs/clinic/audits/V1_05_F5_ENGINE_CONTRACT.md`
9. `docs/clinic/audits/V1_05_F5_SOURCE_CONTRACT.md`

## Scientific claims to reconstruct independently
- Structural anterior-cranial-base superimposition is not equivalent to S-N-line alignment.
- ABO uses the structural method and stable structures for board superimpositions.
- The 2022 systematic review does not support claiming any method as universally accurate.
- Feature matching is an evidence-supported engineering candidate, not clinical ground truth.
- Zhao 2025 supports an adult feature-matching/similarity-transform method family.
- Digital Crown intentionally uses SIFT + L2 because OpenCV documents L1/L2 for SIFT descriptors; Zhao's SIFT/Hamming wording is recorded as a contradiction rather than copied silently.
- Adult-only scope is an engineering-validation boundary, not a claim that structural methods are invalid in younger patients.

## Source registry IDs
- `abo-superimpositions-structural-method`
- `graf-cephalo-superimposition-review-2022`
- `jiang-feature-matching-superimposition-2020`
- `zhao-feature-matching-superimposition-2025`
- `opencv-bfmatcher-4-13`
- `bland-altman-1986`

## Code to challenge
- `backend/services/cephalo_superimposition.py`
- `backend/services/cephalo_superimposition_source.py`
- `backend/services/cephalo_superimposition_api.py`
- `backend/routers/patients.py`
- `backend/schemas/ortho_superimposition.py`
- `frontend/src/features/ortho/OrthoSuperimpositionViewer.tsx`
- `frontend/src/features/ortho/OrthoLongitudinalComparePanel.tsx`

## Tests to inspect
- `backend/tests/test_cephalo_superimposition.py`
- `backend/tests/test_cephalo_superimposition_source.py`
- `backend/tests/test_cephalo_superimposition_api.py`
- `frontend/src/features/ortho/OrthoSuperimpositionViewer.test.ts`

## Mandatory negative gates
Verify that F5 fails closed for:
- growing-patient scope;
- cross-patient/cross-case/cross-cabinet sources;
- same or reversed timepoints;
- missing/ambiguous CephaloAnalysis evidence;
- invalid calibrated ratio;
- stale ratio on uncalibrated legacy rows;
- noncanonical/external/path-traversal media;
- blank/low-feature ROI;
- invalid ROI;
- degenerate/non-finite/sheared/reflected transform;
- insufficient mathematical inliers;
- caller lacking `cephalo` permission;
- engineering preview disabled.

## Claims F5 must never make
No automatic:
- diagnosis;
- treatment recommendation;
- improvement/aggravation;
- success/failure;
- progress score;
- growth prediction;
- normative heatmap.

## Validation boundary
Passing unit tests, CI, visual screenshots or an AI scientific review does not establish clinical validity. Clinical activation remains blocked until a governed expert-reference validation study and named human clinical review are completed.

## Reviewer decision rule
Any untraceable scientific claim, hidden clinical threshold, population overreach, source/license ambiguity that affects implementation, or mismatch between contract/code/tests must block merge or activation until resolved.
