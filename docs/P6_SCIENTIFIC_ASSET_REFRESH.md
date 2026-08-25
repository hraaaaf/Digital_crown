# P6 Scientific Asset Refresh

Status: RESEARCH CHECKPOINT — no production model replacement, no P6 EP credit.

Base: `90b1262cb13b22172d6d0d2f36aa6eb96d360cdf`
Research branch: `portability/p6-scientific-assets-refresh`

## Goal
Recover scientific-model provenance where possible, reduce packaging/runtime weight, preserve fail-closed clinical behavior, and avoid shipping assets whose license, semantics, or portability are not sufficiently established.

## Success criteria
A production-selected scientific asset must have all of the following before P6 resumes:
- exact upstream source;
- license and redistribution status recorded;
- immutable SHA256;
- exact runtime format and input/output contract;
- measured file size and dependency footprint;
- Windows x64 and macOS arm64 CPU runtime proof;
- benchmark against the active Digital Crown clinical contract;
- no selection based only on self-reported upstream metrics or smaller size.

## Internal runtime truth

### Panoramic
The active `detect_teeth_only()` path still calls the YOLO-style panoramic pathology model, then discards pathology semantics and keeps only tooth/FDI, confidence, and bbox. The current scientific contract is therefore tooth-location assistance with practitioner annotation, not autonomous pathology diagnosis.

The expected external asset remains `backend/ai_models/panoramic_model.onnx`, parsed at 1280x1280 through ONNX Runtime. Its exact upstream repository, weight URL, training dataset, and redistribution license were not recorded in the repository history. Historical Git trees inspected during this refresh do not contain the model binary.

### Cephalometry
`vision_service.py` prefers the 38-landmark ONNX SOTA path when available and otherwise falls back to the legacy 19-landmark PyTorch CephLD-CCA path. If neither engine is available, the clinical workflow fails closed to manual placement rather than inventing landmarks.

`backend/scientific_assets.json` already marks `cephalo_sota` as deferred and both `cephalo_legacy` and `panoramic` as external.

## Candidate matrix

| Candidate | License / redistribution | Runtime / footprint | Semantic fit | Evidence / risk | Decision |
|---|---|---|---|---|---|
| Current CephLD-CCA legacy (`MonoHaru/CephLD-CCA`) | GPL-3.0 code; weight external | PyTorch, 19 landmarks, 512x512; architecture estimated ~8.82M params / ~33.6 MiB FP32 | Matches current legacy fallback | Source contains a hard-coded `cuda:0` transfer inside the Cartesian attention block; adds PyTorch/TorchVision footprint; weight provenance/redistribution still requires separate proof | **REJECT as default shipped P6 runtime**; keep only as research/legacy fallback until replaced and qualified |
| Official `szuboy/CL-Detection2023` baseline | Apache-2.0 code; pretrained weight linked externally; weight redistribution terms still need explicit verification | Simple PyTorch UNet, 38 landmarks, 512x512; estimated ~6.82M params / ~26.0 MiB FP32; standard ops suitable for ONNX export | Strong match to the intended 38-landmark SOTA pathway | Official baseline reports approximately MRE 3.323 mm and 2 mm SDR 65.421%; authors explicitly describe it as a baseline, not high-performance final model | **PRIMARY CEPH BENCHMARK CANDIDATE**, not production-selected yet |
| CL-Detection multi-model challenge ensemble | Research models | Multi-model ensemble | High landmark scope | Too heavy and operationally complex for P6 portability | **REJECT for P6** |
| Current `panoramic_model.onnx` | Upstream/license unresolved | ONNX Runtime, 1280x1280, YOLO-style | Poor semantic alignment: pathology detector is currently used as bbox/FDI proxy | Binary was external from early repository history; provenance has not been recovered | **KEEP only if provenance/license are recovered and benchmark remains acceptable; otherwise block shipping** |
| `abychkov/dental-fdi-detection` | Proprietary / non-commercial restrictions | ONNX, direct 32-FDI detector | Excellent semantic fit | License restrictions conflict with commercial/clinical shipping | **REJECT shipping** |
| `Mobe1/argos-dentsight-stage1-fdi-v1` | Apache-2.0 tag, but model-card release/licensing caveats remain | D-FINE Medium, ~19.6M params, 1024x512 | Direct 32-FDI | Author reports the v1 classification head barely learned and v2 retraining is needed | **REJECT v1**; monitor only |
| `liodon-ai/dental-panoramic-detector` | CC BY-NC 4.0 | YOLO11n ONNX, ~10.1 MB, 640 input | Pathology detector, not FDI/tooth-only | Lightweight but non-commercial and wrong active semantics | **REJECT shipping** |
| DENTEX-based custom FDI training | Dataset/license state requires clarification before commercial use | Depends on selected architecture | Potentially correct semantics | Current public metadata consulted during research is not sufficiently clean to certify commercial training/redistribution | **BLOCKED on dataset/license clarification** |

## Decisions
1. No new scientific weight is uploaded to `DigitalCrown-assets` at this checkpoint.
2. No production inference code is changed by this research branch.
3. Legacy CephLD-CCA is not accepted as the default shipped P6 path because portability and distribution risk are materially worse than the intended ONNX path.
4. The official CL-Detection2023 Apache-2.0 UNet is the primary cephalometry research candidate for an ONNX export/parity benchmark, not a certified clinical replacement.
5. No researched panoramic replacement currently satisfies all required gates at once: permissive/commercially usable terms, dedicated tooth/FDI semantics, compact CPU portability, retrievable weights, and sufficient validation evidence.
6. The current panoramic model must not be rehosted until its provenance and redistribution rights are recovered.
7. P6 remains paused. The heavy Windows packaging run must not restart until the scientific asset set is qualified.

## Packaging-size opportunity
`backend/requirements.txt` currently includes PyTorch, TorchVision, TorchAudio and Ultralytics in addition to ONNX Runtime. Removing the legacy PyTorch inference path may yield a much larger installer/runtime reduction than merely replacing a 20–40 MiB weight file. This is an opportunity, not yet a verified deletion plan: repository-wide dependency-use audit is required before removing any package.

## Next exact
1. Retrieve the official CL-Detection2023 pretrained weight from its upstream link.
2. Record upstream identity, file size, SHA256 and exact state-dict structure.
3. Export that exact model to ONNX on the research path only and prove PyTorch ↔ ONNX landmark parity on fixed fixtures.
4. Measure CPU runtime and packaged dependency footprint on Windows x64 and macOS arm64.
5. Continue panoramic search only for a permissively licensed, tooth/FDI-specific model with retrievable weights; otherwise keep the current pano asset blocked pending provenance.
6. Audit actual runtime use of `torch`, `torchvision`, `torchaudio`, and `ultralytics` before proposing dependency removal.
7. Only after those gates: select assets, place legally redistributable chosen assets in the private asset channel, record SHA256/provenance/license, update P6 manifest/workflow, then resume the single heavy Windows packaging certification.
