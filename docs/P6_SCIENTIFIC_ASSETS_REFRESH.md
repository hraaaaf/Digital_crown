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
| MonoHaru/CephLD-CCA | Cephalo 19 landmarks | GPL-3.0 | Repository is very large; PyTorch runtime | High architectural fit | Medium/low | REFERENCE ONLY for proprietary packaging; do not bundle without legal review |
| szuboy/CL-Detection2023 | Cephalo 38 landmarks challenge baseline | Apache-2.0 | Repo itself small; usable pretrained artifact still to pin | High semantic fit to existing 38-point SOTA adapter | Candidate | BENCHMARK / weight provenance required |
| liodon-ai/dental-panoramic-detector | Pano 3 pathology classes | CC-BY-NC-4.0 | ONNX ~10.6 MB | Medium; merges Caries + Deep Caries | Excellent | REJECT for commercial distribution despite excellent footprint |
| Enosh729/oralguard detector | Pano 4 pathology classes | MIT | YOLOv8m PT ~52.1 MB; ONNX export feasibility to verify | Exact 4-class semantic fit | Medium/high if ONNX export succeeds | PRIORITY BENCHMARK |
| abdubakr77/dental-xray-ai | Pano multi-stage | MIT | Multi-stage pipeline, size/runtime to measure | Strong semantic fit | Unknown / likely heavier | SECONDARY BENCHMARK |

## Verified observations

- `MonoHaru/CephLD-CCA` repository declares GPL-3.0.
- `szuboy/CL-Detection2023` official challenge repository declares Apache-2.0.
- Liodon panoramic model card declares CC-BY-NC-4.0 and publishes `best.onnx` (~10.6 MB), but caries/deep-caries are merged.
- OralGuard declares MIT and exposes a YOLOv8m detector for the exact four pathology classes used by Digital Crown. Published overall mAP@50 is 0.548; periapical lesion performance is materially weaker than impacted-tooth performance, so this is not clinically certifiable without our own benchmark.

## Next exact

1. Resolve exact pretrained artifact(s) and hashes for CL-Detection2023-compatible 38-landmark inference.
2. Resolve OralGuard detector weight hash and export to ONNX without Ultralytics/PyTorch runtime dependency at inference if technically clean.
3. Measure final ONNX size, opset, input/output tensor contract, CPU provider compatibility, and cold-load time on Linux as a preparatory proxy; Windows/macOS remain authoritative packaging gates.
4. Compare candidates against Digital Crown adapters without changing clinical output contracts.
5. Only after a candidate wins on license + contract + portability + benchmark, place the pinned artifact in private `hraaaaf/DigitalCrown-assets` with SHA256 and provenance metadata.
6. Resume P6 packaging on the pinned private bundle.

## Non-goals
- No product model replacement during this research branch.
- No clinical equivalence claim.
- No relaxation of fail-closed behavior.
- No public publication of proprietary/private runtime weights.
