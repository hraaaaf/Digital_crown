# CEPH R23-M — SRPose38 error-tail diagnostic, aggregate-only

Status: **DRAFT / SOURCE-ONLY / CLINICAL NO-GO**, independent scientific root cause not established.

## Goal and scope

Make the published 23/24 `FAIL` landmark decisions interpretable alongside official SRPose38 performance metrics, **without retraining, changing model weights, adjusting clinical tolerances, remapping channels, retrieving patient images, or contaminating the frozen 150-case Aariz acceptance set**.

Source: the four immutable LOT04 evidence files committed in `cea3fa3cc23963fe4e41ec2666430fd186a79f04`, and the upstream R23-L SHA-locked scientific audit. The original raw-file SHA256 discrepancy is deliberately retained as an OPEN warning.

## Verified results derived from archived aggregate values

- 150 untouched Aariz radiographs, 24 anatomy-matched local identifiers out of 38 outputs; **3,374 qualified point observations** in these 24 categories.
- Weighted `mean Euclidean error = sum(n_i * mean_error_i) / sum(n_i)`: **1.7701473825424257 mm**, derived from the archived aggregate source. Unlike the paper's CL-Detection2023 38-point benchmark, this uses Aariz, its calibration, selected consensus references, and 24 rather than 38 named channels. **Do not claim an apples-to-apples ranking.**
- **14 / 24 points** have MRE below 2 mm, but only **3 / 24** have p95 error <= 2 mm. The original pre-registered clinical-equivalence gate is *not* a universal 2 mm threshold: 23 FAIL / 1 PASS remains unchanged.
- **Go**: n=120, median **1.256549265 mm**, mean **5.223730338 mm**, p95 **6.852890879 mm**, maximum **154.908927367 mm**. Different device groups show maxima ART Plus **154.908927367 mm** (n=40) and Hyperion X5 **120.159055947 mm** (n=21).
- Because two different device groups cannot refer to the same radiograph observation, these are **at least two distinct extreme errors**. Together they account for **43.88115477%** of all accumulated Go error in the archived accepted point pairs. A strictly hypothetical subtraction of those *two values* from the numerator yields **2.981183536 mm** across remaining n=118, purely to illustrate tail concentration. **DO NOT interpret this counterfactual as rescore, PASS, exclusion, or permission to optimize on untouched data.**

## What the result does not prove

- Which films are affected and what each expert reference x/y was: **individual paired human GT is not in the committed results**. No attempt to reconstruct patient-level data or infer its location.
- That any device caused the issue: machine groups have different n and may differ by sample characteristics.
- That 38 output channels follow the historical local S/N/A/etc. naming: [source provenance audit](./CEPHALO_SRPOSE38_PROVENANCE.md) maintains `SOURCE_LOCK_REQUIRED`.
- That conversion was wrong: [real-image challenge smoke CI](https://github.com/hraaaaf/Digital_crown/actions/runs/34281082886) scored one image, 38 channels, MRE 1.6995 mm, SDR2 73.6842%; [PyTorch → ONNX parity CI](https://github.com/hraaaaf/Digital_crown/actions/runs/34281082926) showed max 0.0001999201 px delta on that single fixture. The fixture proves parity only, not external clinical generalization.
- That the challenge-winning system was the identical model: the SUTD-VLG final competition entry used **seven-model ensemble**. Its public individual trained checkpoint differs from the ensemble.
- That archived original results are byte-bound to their acceptance detail: original `source_results_sha256` and frozen `results.json` raw SHA256 **disagree**; R23-L retained an explicit unresolved warning.

## Repeatable read-only instrument

`python -m unittest discover -s tests -p test_ceph_r23m_srpose38_error_tail.py -v`

`python scripts/audit_ceph_r23m_srpose38_error_tail.py`

The script calls the previous exact-frozen-blob check, recomputes qualified-pair weighted MRE, verifies every per-machine sample count and mean against the landmark aggregate, verifies per-machine/global maxima, and writes ONLY aggregate `report.json` + `README.md`. No case IDs or per-film predictions are written. The pipeline does not download checkpoint, corpus, or reference and cannot invoke ONNX/PyTorch inference. Unit tests test tampering and no clinical promotion.

## Decisive next test, **not executable until prerequisites obtained**

1. Recover legally accessible original byte-level `results.json` for the 2026-10-02 acceptance-detail `source_results_sha256` and re-check its computed digest; **do not replace frozen acceptance**.
2. Obtain an **authorized separate development dataset** pairing original CL-Detection2023 image + verified 38 numerical expert GT indices, source agreement/license and calibration; remote workstation currently offline.
3. For the SAME numerical channel under the SAME checkpoint, compare original PyTorch MMPose vs Digital Crown ONNX on that development set, with raw image geometry (padding, bbox, orientation), device spacing, heatmap post-processing, error distributions and outliers. Do NOT use 150 frozen untouched Aariz cases for debugging/selection.
4. Confirm any proposed anatomical mapping from primary definitions and independent specialist review, preregister modifications, then evaluate on a *new* independent untouched acceptance set.

No checkpoint selection, mapping fixes, retraining, merge, deploy, production or patient-facing change without new approval and independent evidence. `CEPH_DETECTOR_SELECTED=NO`; 6 Ricketts HOLD; roadmap **41/99** unchanged.
