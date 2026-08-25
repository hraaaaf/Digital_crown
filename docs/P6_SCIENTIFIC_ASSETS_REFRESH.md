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
| szuboy/CL-Detection2023 | Cephalo 38 landmarks challenge baseline | Apache-2.0 | Official `best_model.pt` is linked from README via Google Drive ID `1Qvnym4oGSG903ti0z2HE6Dm1udNO692G`; SHA256 pending benchmark download | High semantic fit to existing 38-point SOTA adapter | Candidate | PRIMARY CEPHALO BENCHMARK |
| liodon-ai/dental-panoramic-detector | Pano 3 pathology classes | CC-BY-NC-4.0 | ONNX ~10.6 MB | Medium; merges Caries + Deep Caries | Excellent | REJECT for commercial distribution despite excellent footprint |
| Enosh729/oralguard weights + DrEnosh/Oral_guard source | Pano 4 pathology classes | MIT | YOLOv8m `oralguard_det_best.pt` ~52.1 MB; detector-only ONNX export pending benchmark | Exact 4-class semantic fit | Medium/high if ONNX export succeeds | PRIMARY PANO BENCHMARK |
| abdubakr77/dental-xray-ai | Pano multi-stage | MIT | Multi-stage pipeline, size/runtime to measure | Strong semantic fit | Unknown / likely heavier | SECONDARY BENCHMARK |

## Verified observations

- `MonoHaru/CephLD-CCA` repository declares GPL-3.0. Its architecture matches the current Digital Crown legacy adapter, but it is not the preferred commercial packaging path.
- `szuboy/CL-Detection2023` official challenge repository declares Apache-2.0. It uses a 512×512 UNet heatmap model with 38 output channels. The official inference code loads a plain PyTorch state dict into that 38-channel UNet. The README links the pretrained `best_model.pt` through Google Drive ID `1Qvnym4oGSG903ti0z2HE6Dm1udNO692G` and reports approximate baseline performance `MRE = 3.323 mm`, `2 mm SDR = 65.421%`. Source commit pinned for the benchmark: `dc1ce2bd0a3f317de4160cde17e4a6f60371e67c`. Exact artifact SHA256 remains to be measured from the binary.
- Liodon panoramic model card declares CC-BY-NC-4.0 and publishes `best.onnx` (~10.6 MB, SHA256 published by Hugging Face), but caries/deep-caries are merged. It is excluded from commercial packaging.
- OralGuard's Hugging Face model card declares MIT and exposes `oralguard_det_best.pt`, a YOLOv8m detector for the exact four pathology classes used by Digital Crown. The source repository has moved to `DrEnosh/Oral_guard`; source commit pinned for the benchmark: `f619ae5078da80b1fc84fb34324d2100c2382e82`. Published overall mAP@50 is 0.548; per-class values are Caries 0.544, Deep Caries 0.431, Periapical Lesion 0.263, Impacted Tooth 0.955. Weight size is ~52.1 MB. This is not clinically certifiable without our own benchmark.
- Because the product already fails closed when scientific assets are unavailable, this research can be completed without weakening safety behavior.

## Benchmark preparation

The research branch contains an isolated portability harness:
- workflow: `.github/workflows/p6-scientific-assets-benchmark.yml`
- harness: `scripts/p6_scientific_assets_benchmark.py`
- no clinical/backend/frontend wiring is modified by the harness;
- candidate source revisions are pinned before execution;
- downloaded binaries are SHA256-hashed;
- OralGuard is exported detector-only to static 1024×1024 ONNX, opset 17;
- CL-Detection2023 is additionally exported to static 512×512 ONNX to prove the existing 38-heatmap adapter shape;
- ONNX Runtime is forced to `CPUExecutionProvider`;
- evidence includes size, SHA256, opset, tensor contracts, cold-load time, repeated CPU inference latency, package freeze, machine identity, and max RSS;
- Linux is only a preparatory portability proxy. Windows x64 and macOS ARM64 remain authoritative packaging gates;
- this harness does not establish clinical equivalence or diagnostic performance.

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

1. Run the single prepared portability benchmark commit once.
2. Read the artifact and pin exact SHA256, source revisions, ONNX sizes/opsets/tensor contracts, CPU latency and memory.
3. If the run fails, diagnose the exact failing gate and change strategy rather than weakening a contract.
4. Only after portability succeeds, add non-PHI task-level benchmark data before any clinical-equivalence claim.
5. Only after a candidate wins, place pinned artifact + provenance + SHA256 in private `hraaaaf/DigitalCrown-assets`.
6. Resume P6 packaging on the pinned private bundle.

## Non-goals
- No product model replacement during this research branch.
- No clinical equivalence claim.
- No relaxation of fail-closed behavior.
- No public publication of proprietary/private runtime weights.
