# P6 Scientific Assets Refresh

Status: ACTIVE RESEARCH — no clinical product wiring changed.

## Goal
Replace/recover scientific runtime assets with candidates that are reproducible, portable, legally distributable in a commercial closed-source desktop package, and compatible with Digital Crown's existing fail-closed contracts.

## Current product contracts

### Cephalometry
- Current legacy runtime: CephLD-CCA architecture, 19 landmarks, PyTorch weight `ceph_weights.pth`.
- Current optional SOTA runtime: ONNX, 38 landmarks, expected at `model.onnx` / `cephalometric_sota/model.onnx`.
- No numerical equivalence claim may be made without benchmark evidence.

### Panoramic
Current runtime contract expects four pathology labels:
1. Caries
2. Deep Caries
3. Impacted
4. Periapical Lesion

Clinical mode is fail-closed if the required model is unavailable.

## Candidate matrix

| Candidate | Task | License | Weight/runtime footprint | Contract fit | Portability | Decision |
|---|---|---|---|---|---|---|
| MonoHaru/CephLD-CCA | Cephalo 19 landmarks | GPL-3.0 | Repository ~928 MB; PyTorch runtime | High architectural fit | Medium/low | REJECT for proprietary bundle; reference/reproducibility only unless separately cleared |
| szuboy/CL-Detection2023 | Cephalo 38 landmarks challenge baseline | Apache-2.0 | Repo ~8.7 MB; pretrained artifact external (Google/Baidu), exact weight still to pin | High semantic fit to existing 38-point SOTA adapter | Candidate | PRIMARY CEPHALO BENCHMARK |
| liodon-ai/dental-panoramic-detector | Pano 3 pathology classes | CC-BY-NC-4.0 | ONNX ~10.6 MB | Medium; merges Caries + Deep Caries | Excellent | REJECT for commercial distribution despite excellent footprint |
| Enosh729/oralguard detector | Pano 4 pathology classes | MIT | YOLOv8m PT ~52.1 MB; ONNX export feasibility to verify | Exact 4-class semantic fit | Medium/high if ONNX export succeeds | PRIMARY PANO BENCHMARK |
| abdubakr77/dental-xray-ai | Pano multi-stage | MIT | Multi-stage pipeline, size/runtime to measure | Strong semantic fit | Unknown / likely heavier | SECONDARY BENCHMARK |

## Verified observations

- `MonoHaru/CephLD-CCA` repository declares GPL-3.0. Its architecture matches the current Digital Crown legacy adapter, but it is not the preferred commercial packaging path.
- `szuboy/CL-Detection2023` official challenge repository declares Apache-2.0. It uses a 512×512 UNet heatmap model with 38 output channels. The README provides pretrained weights through Google Drive/Baidu Drive and reports approximate baseline performance `MRE = 3.323 mm`, `2 mm SDR = 65.421%`. Exact weight provenance/hash remains to be pinned before use.
- Liodon panoramic model card declares CC-BY-NC-4.0 and publishes `best.onnx` (~10.6 MB, SHA256 published by Hugging Face), but caries/deep-caries are merged. It is excluded from commercial packaging.
- OralGuard declares MIT and exposes `oralguard_det_best.pt`, a YOLOv8m detector for the exact four pathology classes used by Digital Crown. Published overall mAP@50 is 0.548; per-class values reported by the model card are Caries 0.544, Deep Caries 0.431, Periapical Lesion 0.263, Impacted Tooth 0.955. Weight size is ~52.1 MB. This is not clinically certifiable without our own benchmark.
- Because the product already fails closed when scientific assets are unavailable, this research can be completed without weakening safety behavior.

## Current ranking

### Cephalometry
1. `szuboy/CL-Detection2023` — Apache-2.0, 38 points, closest clean replacement path for current optional SOTA adapter.
2. Existing CephLD-CCA — keep only as reference/fallback research asset; do not select for proprietary bundle by default because of GPL-3.0.
3. Large multi-model challenge ensembles — deprioritized for portability.

### Panoramic
1. `Enosh729/oralguard` detector — MIT, exact 4-class contract, but heavier and weak on periapical lesions; must be exported/benchmarked.
2. `abdubakr77/dental-xray-ai` — MIT, useful secondary candidate if its multi-stage runtime can be collapsed efficiently.
3. Liodon YOLO11-N — technically attractive but commercially excluded by CC-BY-NC-4.0.

## Next exact

1. Resolve exact pretrained artifact and SHA256 for the CL-Detection2023 38-landmark baseline.
2. Pin the exact OralGuard detector weight revision/hash and export detector-only to ONNX, avoiding classifier/ResNet baggage unless benchmark proves it necessary.
3. Measure final ONNX size, opset, input/output tensor contract, CPU provider compatibility, and cold-load time on Linux as a preparatory proxy; Windows/macOS remain authoritative packaging gates.
4. Build adapter-only benchmark harnesses that do not change clinical product wiring.
5. Compare candidates on: licensing, number/semantics of outputs, model size, runtime dependencies, CPU inference, cold start, memory, and task-level benchmark metrics.
6. Only after a candidate wins, place pinned artifact + provenance + SHA256 in private `hraaaaf/DigitalCrown-assets`.
7. Resume P6 packaging on the pinned private bundle.

## Non-goals
- No product model replacement during this research branch.
- No clinical equivalence claim.
- No relaxation of fail-closed behavior.
- No public publication of proprietary/private runtime weights.
