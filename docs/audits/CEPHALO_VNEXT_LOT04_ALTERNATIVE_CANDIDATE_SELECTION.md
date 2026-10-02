# Cephalo vNext — LOT04 Alternative Candidate Selection

Status: SELECTED_FOR_BENCHMARK_ONLY — not detector-selected
Gate target: `CEPH_DETECTOR_SELECTED`

## Candidate
- Name: CL-Detection2023 official UNet baseline
- Source repository: `szuboy/CL-Detection2023`
- Frozen source commit: `dc1ce2bd0a3f317de4160cde17e4a6f60371e67c`
- Architecture: UNet heatmap regression
- Input: 512x512 RGB
- Output: 38 heatmap channels
- Decoder: per-channel argmax; ties averaged; coordinates rescaled to original image dimensions
- Published reference performance on the challenge baseline: approximate MRE 3.323 mm / SDR@2mm 65.421% on its own challenge test workflow.
- Source repository license: Apache-2.0.
- Pretrained checkpoint: linked by the official README through Google Drive; exact bytes/hash must be frozen locally before scoring.

## Why this candidate is next
1. Public pretrained weights are actually linked by the official source.
2. The implementation is simple enough to reproduce without hidden framework behavior.
3. It emits 38 ordered landmarks from the CL-Detection2023 task, compatible with the same LOT03 challenge-index mapping contract used for SRPose38, subject to exact pre-scoring identity verification.
4. It is materially architecture-independent from SRPose38, providing a useful second candidate rather than another export of the same model.
5. No Aariz result for this candidate has been observed by Digital Crown before selection.

## Rejected/deferred alternative
`Cestovatels/CephaloHRNet` (MIT, HRNet-W48, CEPHA29-native) is scientifically interesting and reports MRE 1.37 mm on CEPHA29, but the repository does not currently expose a downloadable trained checkpoint/release. Training a new model would introduce a separate training/tuning lot and is therefore deferred rather than silently substituted.

## Frozen device-stratified policy
Human-approved before this candidate is scored:
- `n_device >= 59`: hard device-specific p95 gate against the corresponding LOT02 human device p95;
- `n_device < 59`: descriptive only with `INSUFFICIENT_N_FOR_P95_GATE`;
- no post-hoc pooling;
- aggregate gates remain independently active;
- hard device failures cannot be hidden by aggregate PASS.

On the current untouched Aariz test split, device counts are all below 59, so device analysis is expected to be descriptive-only unless the frozen split evidence proves otherwise. The split must not be altered to create gate eligibility.

## License caution
Apache-2.0 is verified for repository source code. The pretrained checkpoint is externally hosted. Unless an explicit weight-license statement is source-backed, local benchmarking may proceed but production redistribution remains license-gated.

## Required pre-scoring freeze
Before inference:
1. download the official linked checkpoint;
2. record exact size + SHA256;
3. freeze source commit and exact inference code path;
4. validate 38-output shape and mapping identity;
5. create a new immutable benchmark manifest bound to the existing LOT02 corpus/QC/calibration/human-agreement artifacts and `REFERENCE_EQUIVALENCE_V1`;
6. run one untouched pass only.


## Aborted preprocessing compatibility attempt
A first technical score process was started from the initial candidate manifest but terminated with no results artifact when an Aariz grayscale image was encountered. No candidate performance metric or prediction artifact was produced or inspected.

A pre-performance corpus modality inventory then established:
- 820 RGB images;
- 178 8-bit grayscale images;
- 2 16-bit grayscale images;
- untouched test split: 124 RGB + 26 grayscale.

Before any scored rerun, the input compatibility rule is frozen as:
- RGB: unchanged;
- any 2D grayscale: replicate the same intensity plane into three identical RGB channels;
- no contrast adjustment, histogram manipulation, normalization tuning, cropping, or threshold change.

This is a structural input-compatibility fix, not performance-driven tuning. The failed process is recorded as `ABORTED_PREPROCESSING_COMPATIBILITY_RUN`, not as a completed untouched benchmark.
