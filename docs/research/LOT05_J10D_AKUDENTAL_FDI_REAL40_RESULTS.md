# Digital Crown — LOT05 / 05.7-J10D — AKUDENTAL 40 real panoramics / FDI report

**Run date:** 2026-10-22. **RUN: [39764642070](https://github.com/hraaaaf/Digital_crown/actions/runs/39764642070) completed SUCCESS.** Tested Digital Crown experiment commit **`4af6e5e67e94d35dd918d2f134a5ac16cb6ef855`** in PR [#1006](https://github.com/hraaaaf/Digital_crown/pull/1006), OPEN DRAFT, not merged. Relevant green workflows at same code SHA include FDI weight model synthetic proof, AKUDENTAL COCO adapter and CI Scope Gate. PR #1004 untouched.

## 1. Provenance and exact execution

- Original already-public author research images and COCO: [melihoz/AKUDENTAL](https://github.com/melihoz/AKUDENTAL), source checkout SHA **`92e2cc3ae5eebc9de509311a3edefb7106fca7dd`** (confirmed CI logs). **No private cabinet data.** 333 images declared in original COCO.
- Detector: [miquic/app-odonto-fdi-yolov8s](https://huggingface.co/miquic/app-odonto-fdi-yolov8s), pinned revision `82b4d9a02f9e6f32a746dc17afe681e20e8b99e2`, `best.pt` SHA256 `533833a4244f092f82bc94a6c2d6fac7e1656c9437994e98d09843c54aafd3f6`. Hugging Face snapshot symlink copied to verified regular ephemeral file before use; no executable weights retained.
- Executed **40 original images**, fixed deterministic prefix sorted numerically by source image ID **before inference**, not clinically representative random sample. Ground truth: **1,036 annotated teeth** excluding the three non-tooth object classes. **Two source images contained duplicate FDI ground-truth codes** (further reference review needed).
- Inference: CPU, imgsz=1024, conf=0.25, class-aware YOLO NMS IoU 0.5; evaluator greedy one-to-one box matching at IoU >=0.5 independent of label, then test exact FDI class. All boxes and per-image outputs kept ephemeral; only aggregate JSON artifact.
- Github Actions 2 jobs SUCCESS: synthetic checkpoint validation and **real public image CPU**. Real job consumed publisher dataset in runner and wrote aggregate-only [artifact 12419457821](https://github.com/hraaaaf/Digital_crown/actions/runs/39764642070) (archive named `lot05-fdi-real-public-akudental-4af6e5e67e94d35dd918d2f134a5ac16cb6ef855`). Only 2,363-byte aggregate JSON inside. The original [red run 39763251899](https://github.com/hraaaaf/Digital_crown/actions/runs/39763251899) downloaded real source and then failed `BenchmarkError`; code inspection indicated likely Hub-symlink rejection. Fixed by source SHA validation + regular file materialization, with new tests for valid symlink and corrupt source. **The new test succeeds**; old failure cause remains inferred rather than directly logged.

## 2. Reported observed metrics

| Metric | Actual aggregate result | Definition / caveat |
|---|---:|---|
| Real panoramics analyzed | **40** | Fixed prefix research sample, not randomized clinical cohort |
| Annotated teeth | **1,036** | Reference labels from author AKUDENTAL, not independently re-adjudicated by Digital Crown |
| Predicted proposals | **1,063** | After model confidence/NMS |
| Teeth correctly localized | **897** | IoU >=0.5 regardless of assigned FDI |
| Localization recall | **86.5830%** | 897 / 1,036 |
| Correct FDI and localization | **840** | Both IoU match and correct FDI |
| **FDI-correct recall** | **81.0811%** | 840 / 1,036; key metric for user goal |
| FDI accuracy conditional on localization | **93.6455%** | 840 / 897; **NOT** whole-radiograph or all-tooth accuracy |
| Correct-FDI proposal precision | **79.0216%** | 840 / 1,063 |
| Wrong FDI on localized tooth | **57** | 50 adjacent same-quadrant swaps + 7 other |
| Adjacent FDI swaps | **50** | Subset of the 57 mislabeled localized teeth |
| Other FDI swaps | **7** | Additional mislabeled localized teeth |
| GT teeth missed (unlocalized) | **139** | 1,036 - 897 |
| Unmatched candidate proposals | **166** | 1,063 - 897; ~4.15 per film, not all equivalent to clinically harmful detections |
| Duplicate FDI labels | **51** | Sum of duplicated code *groups per film* among predictions; not necessarily 51 additional teeth |
| Exactly correct panoramics | **3 / 40 (7.5%)** | Every reference tooth matched and FDI correct, no unmatched/duplicates |
| Films with any error | **37 / 40 (92.5%)** | No guarantee that all errors would alter a treatment decision |
| Bootstrap 95% interval on FDI-correct recall | **[74.7583%, 86.4791%]** | Film-clustered resampling, fixed small biased cohort; NOT formal multisite performance guarantee |
| GT duplicate-code films | **2 / 40** | Reference data need expert quality audit before claimed performance |
| Original COCO non-tooth annotations skipped | **1,135** | Across the complete source annotations, NOT only the selected 40 |

The author model card reports mAP50 ~0.930 **on a different internal cohort**, and that is not comparable to the current measured 81.1% whole-tooth FDI-correct recall by IoU plus exact FDI. No claim of universal panoramic performance.

## 3. FDI tooth click-UX consequence

**The model is technically useful for proposing bounding boxes/FDI, but not adequate for hands-off tooth numbering**: 139 GT teeth unlocalized, 166 unmatched proposals and 57 localized tooth-number errors across 40 scans. For the **owner-confirmed intent** (user dentist clicks tooth → chooses *manually* an act in a specialty catalogue), guardrails remain required: visibly **unconfirmed** suggestions, manual add/drag/remove and number reassignment, marker for duplicate FDI and absent teeth, no clinical act automatically chosen, and clinician review of a detected tooth's number before linking acts/patient chart records. The actual click-UX and act dictionary are future authorized work, not built in this PR.

**No clinical/marketing certification:** dataset source and model license marked noncommercial, no direct rights clearance for commercial embedded Digital Crown, no patient/site/pHash collision audit vs DENTEX model training, no blinded multi-expert reference, no device robustness study, not enough sample for regulatory claims, Windows ONNX decoder and click UI not validated. Performance depends on fixed thresholds and this specific sample. Current status **LOT05/05.7-J10D RESEARCH, V1.5 NO-GO**.

## 4. Next decision gate (not silently authorized)

1. Validate AKUDENTAL original annotations on two duplicate-reference images and a systematic random selection of false positives, swaps, missing teeth, with dentist adjudication.
2. Extend to an independent full cohort and patient/site/device-level duplicate audit with prespecified metrics, potentially all 333 public images after data governance approval, or multiple sources with permissions.
3. If goal remains clinician-correctable proposal UI rather than autonomous numbering, define an explicit acceptable clinician correction burden, FDI wrong-number warning/confirmation, and separately test Windows ONNX parity and interactive tooth selection.
4. Preserve all open licensing/clinical reservations in `techdoubt.md` and [Notion J10D decision page](https://app.notion.com/p/40177c6633628150a72fd8dac3170915). No merge/installer/cabinet change or Vercel. PR #1004 preserved.

**Artifact reproducibility:** GitHub job logs contain safe aggregate summary; full metrics extracted and read back from 2,363-byte JSON in artifact 12419457821. No images, patient IDs, image path, per-case predictions or raw weights were retained.
