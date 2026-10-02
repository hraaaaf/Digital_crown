# Cephalo vNext — LOT04 UNet Alternative Candidate Adversarial Review

Status: REVIEWED — candidate rejected; gate not satisfied
Candidate: CL-Detection2023 official UNet baseline
Inference HEAD: `2e5134cb215ab0083ca2af8b2553fef2ad3be950`
Evidence HEAD before this review: `e6f81f383dcd4fc5f6a7f83b44bf5c720f380ea0`

## Frozen evidence
- Candidate weights SHA256: `b391e7925522185f993a88048ca7ace2d209ae0864116bdd255660f7a993eb71`
- Source commit: `dc1ce2bd0a3f317de4160cde17e4a6f60371e67c`
- Manifest canonical SHA256: `edfa42fc8bcb98ad52a788a335616952700c92ab6bc3e9175412bd48aac0e66d`
- Manifest file SHA256: `3048e9ba5da87f0aef43cd706d218a35dd7cb4e46f226365e21f0ddfa592bc02`
- Results SHA256: `f88566d3e1056ee67dda7ddd6043da7e5dc69a272cc432d16b5ab55ca8e1cceb`
- Acceptance record SHA256: `0d0517653c1398f4435283f3034df16b588c6399b1db18cd698a4e6fc2c8210c`
- 850 development / 150 untouched acceptance cases.
- Device policy frozen before alternative scoring: n_device >=59 hard p95; n<59 descriptive-only; no post-hoc pooling.
- Current untouched device strata: all below 59; 0 hard-gated strata, 168 descriptive strata.

## Preprocessing compatibility event
The first score attempt aborted on grayscale input before producing any result/prediction artifact. Corpus modality inventory was then performed without candidate performance inspection. The structural compatibility rule was frozen: RGB unchanged; 2D grayscale replicated to three identical channels; no contrast/histogram/normalization/crop/threshold tuning. Candidate, split and policy remained unchanged between manifest v1 and v2.

## Perspective A — orthodontics / science / biometrics
Questions: arbitrary thresholds, misuse of human variability, aggregate masking, downstream propagation, device/modality bias, contamination, overclaiming.

Findings:
- Overall candidate decision = FAIL.
- 24/24 anatomy-compatible landmarks FAIL REFERENCE_EQUIVALENCE_V1.
- 9/9 sentinel measurements FAIL.
- No device-specific PASS/FAIL is claimed because every untouched device stratum has n<59; all are DESCRIPTIVE_ONLY as predeclared.
- Modality sensitivity does not explain the rejection: RGB (124 cases) pair-error median ~8.59 mm, p95 ~136.96 mm; grayscale (26 cases) median ~3.68 mm, p95 ~121.13 mm. Both modalities fail by a very large margin.
- CL-Detection 1..38 output order is source-bound through the existing Digital Crown landmark contract; unsupported semantic identities remain excluded from anatomy scoring.
- No post-result threshold adjustment, pooling or split modification occurred.
- Dataset contamination is not proven absent at patient level, but the frozen official source declares CL-Detection2023 training and no Aariz reference was found. This uncertainty cannot convert a FAIL into PASS.

Score after review: **9.2/10**.
No new BLOCKER/MAJOR affecting the rejection conclusion.

## Perspective B — ML / architecture / reproducibility / QA
Questions: mutable manifest, split leakage, wrong weights/version, hidden hardware dependency, fail-open, skips, artifact/HEAD mismatch, licence debt.

Findings:
- Checkpoint loads strict with 106 state_dict keys; model has 6,824,934 parameters; output shape verified [1,38,512,512].
- Source model.py and inference hashes are frozen in the manifest.
- Manifest v2 binds the exact candidate, policy, dataset, QC, calibration, landmark agreement and measurement agreement before the successful untouched run.
- Results and acceptance record bind to the same canonical manifest SHA and candidate SHA.
- Post-inference evidence commit changes only evidence files; no model/runtime/pipeline change after scoring.
- Targeted validation: 20/20 tests PASS; frozen manifest/acceptance semantic validation PASS.
- Recorded execution environment: Python 3.11.9, Torch 2.2.2+cpu, NumPy 1.26.4, scikit-image 0.22.0, CPU.
- Source README reports its tested reference environment as Torch 1.12 / CUDA 11.8. This environment drift is a documented reproducibility debt. It would block a positive promotion until cross-checked, but it is non-blocking for rejecting this candidate because the observed failure margins are orders above the preregistered envelopes.
- Repository code is Apache-2.0; the externally hosted checkpoint has no independently explicit weight-specific licence statement. This remains a production-redistribution gate, not a reason to reinterpret a FAIL.

Score after review: **9.0/10**.
No new BLOCKER/MAJOR affecting the rejection conclusion.

## Decision
CL-Detection2023 official UNet baseline is **REJECTED as the LOT04 selected detector candidate** under the frozen untouched protocol.

`CEPH_DETECTOR_SELECTED` remains **NOT SATISFIED**.

This review does not authorize runtime integration, merge, deployment, threshold changes, split changes or reuse of untouched results for tuning.

## Next exact
Identify another independently trained/publicly reproducible candidate with accessible frozen weights and sufficiently documented landmark semantics. Freeze candidate identity/license/preprocessing before any Aariz inference. If no such checkpoint exists, LOT04 remains open rather than training/tuning against the untouched acceptance set.
