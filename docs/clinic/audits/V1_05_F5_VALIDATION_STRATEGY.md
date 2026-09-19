# V1-05 / F5 — Validation Strategy

**Date:** 2026-09-19  
**Status:** REQUIRED BEFORE CLINICAL ACTIVATION

**Agreement-method registry:** `bland-altman-1986`; scientific-method records are listed in F5-MDR-001.

## Goal
Demonstrate numerical correctness, reproducibility, explicit failure behavior and clinically acceptable agreement against an expert structural-superimposition reference before F5 is activated for clinical use.

## Layer 1 — deterministic numerical tests
Use synthetic/non-patient images only.

Required tests:
- exact identity transform;
- known translation;
- known rotation;
- known uniform scale;
- combined 4-DOF similarity transform;
- repeated-run determinism;
- blank/low-feature image -> explicit failure;
- invalid/out-of-bounds ROI -> explicit failure;
- unreadable image -> explicit failure;
- non-finite transform -> rejected;
- no accidental affine shear/perspective output.

Success is numeric recovery within a test-defined software tolerance. These tolerances validate implementation mathematics, not clinical accuracy.

## Layer 2 — source/data-contract tests
Verify:
- same patient and case;
- two distinct canonical timepoints;
- exactly referenced CephaloAnalysis evidence;
- original source image available;
- immutable source paths;
- calibration provenance retained;
- absent calibration blocks millimetric outputs;
- no duplicate media truth created.

## Layer 3 — expert clinical reference study
Before clinical activation, use appropriately governed/de-identified validation material and an independent orthodontic expert reference.

Reference procedure:
- expert structural ACB superimposition using the documented stable structures;
- repeated tracing/registration where required to estimate reference repeatability;
- compare F5 transform/output with the expert reference per case.

Analysis:
- individual-case differences, not only group means;
- Bland-Altman analysis for relevant positional differences;
- rotation/translation/scale residuals;
- failure rate;
- stratification by acquisition characteristics;
- explicit outlier review.

The clinical sample size and acceptance limits must be established prospectively by a validation protocol; this document does not invent them.

## Population gates
Initial engineering validation: adult applicability record only.

Separate validation records are required for:
- growing patients;
- materially different acquisition protocols/machines;
- images with significant projection/magnification mismatch;
- future automated ROI detection.

## Independent review
Before merge/activation:
1. code + tests;
2. independent scientific-reviewer reconstruction of source claims;
3. clinician review of method applicability and UI wording;
4. visual human gate at 390x844, 768x1024, 1280x900;
5. no claim of clinical validity until the clinical reference study is actually completed.

## Activation rule
Passing unit tests is **not** scientific validation. If the clinical reference gate is not completed, F5 may remain an experimental/engineering capability only.
