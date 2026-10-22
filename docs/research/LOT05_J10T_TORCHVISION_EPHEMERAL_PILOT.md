# LOT05/J10T — CPU-only academic pilot FDI-32, not clinical training

**2026-10-22. Scope: research smoke only, disposable compute, no clinical or commercial use.**

## Why Torchvision instead of Ultralytics

The J10R staging code retains YOLO-shaped TXT labels but **does not require the Ultralytics YOLO package** to run. Ultralytics states its software and trained derivatives fall under AGPL-3.0 unless an Enterprise arrangement is in place for proprietary products: https://www.ultralytics.com/license . Do not add Ultralytics as a silent licensing dependency for Digital Crown. A pilot via official PyTorch/Torchvision `fasterrcnn_mobilenet_v3_large_320_fpn` trains a new 36-way detection head (35 AKUDENTAL categories + 1 background) from a generic COCO-pretrained detector in a separate ephemeral research job. The PyTorch/Torchvision and pretrained checkpoint usage must be rechecked by legal before product use.

## Training protocol and inference of claims

- **Dataset**: AKUDENTAL SHA `92e2cc3ae5eebc9de509311a3edefb7106fca7dd`, sourced from academic GitHub under the README's **CC BY-NC-SA 4.0**, exclusively for isolated experimental research; this is **NOT an authorization to use it in commercial Digital Crown**.
- **No clinic data**, no uploaded human images, no persistence of this third-party corpus in our Git repo. Temporary GitHub Actions machine downloads the 333 publicly released research JPEGs and their FDI annotations. The J10R staging module checks all 333 labels and emits symlinks and TXT only.
- **Split**: fold_0 train (266) and val (33); **test 34 is sealed and never accessed for model training/evaluation**. Smoke budget: random, reproducible (seed 20261022) **24 train** and **8 validation images**. Other folds not used. Only one epoch, head fine-tuning on CPU (backbone frozen). No commercial claims.
- **No images, predictions, model checkpoints or plots published or uploaded**. The workflow logs ONLY aggregate loss, IoU50 class-exact P/R with confidence >=0.25, TP/FP/FN, plus metadata. This is **not mAP** and has no clinical significance on such a tiny subset. No weights are exported or added to CI artifacts.
- **Build**: Python 3.11 + CPU torch/torchvision, Pillow; official Torchvision Faster R-CNN MobileNetV3 320 FPN weights. No dependency on Ultralytics; license chain still requires review before commercial exploitation.
- J10T script `experiments/lot05_j10t_akudental_torchvision_pilot.py` + 5 synthetic tests; dedicated workflow `.github/workflows/lot05-j10t-akudental-cpu-training-pilot.yml`. The workflow is specifically a CPU experiment capped at 25 minutes, no deployment/merge, transient checkout, post-run cleanup.
- **Safety interpretation**: any numeric score is a **technical smoke signal** only. Missing-class variation in 24 images, 31 duplicate-position records seen in full corpus, possible patient/split correlation, incomplete verification of consent and data rights all invalidate medical/production claims. Clinician review of the 31 anomalies must occur before serious training or scoring.

## Next gates

1. Observe exact HEAD job results, verify successful training loop and nonempty validation metrics. If failure, diagnose CI without claiming a trained model.
2. Expand only within a *separately approved noncommercial research environment* after assessing data rights and duplicate annotations; no distribution of trained weights.
3. Acquire suitable documented rights to the dataset and framework, plus independent patient-level test data and clinical governance, **before any commercial or medical rollout**.

**Prohibitions:** no Vercel / production, no PR merge, no clinic patient radiographs, no transfer of model weights or third-party licensed images into Digital Crown product storage.
