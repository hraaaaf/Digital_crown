# P6 Scientific Assets Refresh

Status: ACTIVE RESEARCH — portability benchmark passed; no clinical product wiring changed.

## Goal
Replace/recover scientific runtime assets with candidates that are reproducible, portable, legally distributable in a commercial closed-source desktop package, and compatible with Digital Crown's existing fail-closed contracts.

## Current product contracts

### Cephalometry — important distinction

Digital Crown currently has two different contracts that must not be confused:

1. **Inference adapter contract**
   - Legacy PyTorch adapter: 19 heatmaps.
   - Optional SOTA ONNX adapter: hard-coded to 38 heatmaps and 1024×1024 input in `backend/services/sota_vision_service.py`.
   - The number 38 is therefore an implementation/tensor contract of the current SOTA adapter, not the number of landmarks intrinsically required by the clinical engine.

2. **Clinical geometry contract**
   - `CephaloEngine.key_mapping` consumes 22 canonical points:
     `S, N, Po, Or, A, B, Go, Me, U1i, U1a, L1i, L1a, Prn, Pog_soft, Sn, Ls, Li, Co, Gn, ANS, Occ_Ant, Occ_Post`.
   - Metrics are calculated only when the required geometry is present; missing measurements remain unavailable rather than being fabricated.
   - Wits specifically requires `Occ_Ant`, `Occ_Post`, `A`, `B` plus calibration.

### Panoramic
Current runtime contract expects four pathology labels:
1. Caries
2. Deep Caries
3. Impacted
4. Periapical Lesion

Clinical mode remains fail-closed if the required model is unavailable.

## Candidate matrix

| Candidate | Task | Code/model/data rights | Technical evidence | Contract fit | Commercial bundle decision |
|---|---|---|---|---|---|
| MonoHaru/CephLD-CCA | Cephalo 19 | GPL-3.0 repo | Existing architectural reference | Partial | REJECT by default for proprietary bundle |
| szuboy/CL-Detection2023 | Cephalo 38 | Code Apache-2.0; challenge data restricted / annotations CC BY-NC 4.0 | Benchmark PASS; exact PT/ONNX hashes pinned | Tensor fit excellent | TECHNICAL BENCHMARK ONLY pending explicit rights clearance |
| Aariz dataset | Cephalo 29 | Dataset CC BY 4.0 | 1000 cephalograms, 7 devices, 29 landmarks | 20/22 Digital Crown canonical points directly covered | PRIMARY CLEAN RETRAIN DATA ROUTE |
| emad2001/DeLR-Cephalometric-ConvNeXtV2 | Cephalo 26 on Aariz | Pretrained checkpoint exists; model/checkpoint license provenance not yet sufficiently explicit | Published card reports MRE 1.073 mm | Potentially high | HOLD until code + checkpoint licensing is pinned |
| liodon-ai/dental-panoramic-detector | Pano 3 pathology classes | CC-BY-NC-4.0 | ONNX ~10.6 MB | Caries/deep-caries merged | REJECT commercial |
| OralGuard | Pano exact 4 classes | Repo/model card MIT, but trained with Ultralytics YOLOv8 and DENTEX | Benchmark PASS; detector-only ONNX exported | Exact 4-class semantic fit | TECHNICAL BENCHMARK ONLY; blocked by Ultralytics/DENTEX commercial gates absent written clearance |
| abdubakr77/dental-xray-ai | Pano multi-stage | MIT repo but depends on Ultralytics | Not yet benchmarked | Strong semantic fit | NOT a clean escape from Ultralytics license gate |
| HierarchicalDet | Pano DENTEX | MIT code, Detectron2/DiffusionDet; DENTEX rights non-commercial on current official distribution | No ready final checkpoint located | Scientific candidate | RETRAIN/REPRODUCTION ONLY; dataset clearance still required |

## Cephalometry compatibility audit — Aariz vs Digital Crown

Aariz provides 29 landmarks: 15 skeletal, 8 dental and 6 soft-tissue. Its dataset is published on Figshare under CC BY 4.0 and its Scientific Data paper explicitly states open publication under CC-BY.

### Directly covered Digital Crown canonical points — 20/22

- Skeletal: `S, N, Po, Or, A, B, Go, Me, Co, Gn, ANS`
- Dental: `U1i <- UIT`, `U1a <- UIA`, `L1i <- LIT`, `L1a <- LIA`
- Soft tissue: `Prn <- Pn`, `Pog_soft <- Pog'`, `Sn`, `Ls`, `Li`

### Not directly provided — 2/22

- `Occ_Ant`
- `Occ_Post`

These two points are used only by the current Wits geometry. Aariz does contain incisor, premolar and molar cusp landmarks, so an occlusal plane could be constructed geometrically, but this is **not accepted as clinically equivalent without separate validation**. Jacobson's original Wits method projects A and B onto an occlusal plane, and published literature shows that functional and bisected occlusal-plane definitions are not identical.

Therefore:
- Aariz is compatible with the existing clinical engine for 20/22 canonical points.
- A 29-point Aariz model is **not a drop-in** for the current hard-coded 38-heatmap ONNX adapter; an inference adapter change is required.
- No clinical-engine redesign is required for the 20 directly mapped points.
- Automated Wits must remain unavailable/manual/fail-closed until an occlusal-plane derivation is separately defined and clinically validated.
- This is not an automatic regression versus the current SOTA 38 mapping: the existing `SOTA_LANDMARKS_MAPPING` also does not emit `Occ_Ant` or `Occ_Post`.

## Portability benchmark — PASS

Workflow: `.github/workflows/p6-scientific-assets-benchmark.yml`
Harness: `scripts/p6_scientific_assets_benchmark.py`
Run: `32849860043`
Exact benchmark HEAD: `dff88e4ebd4f32184f4a75f6a8ba3abac319373d`
Artifact: `p6-scientific-assets-benchmark` / ID `9563867769`
Artifact ZIP digest: `sha256:82725c4ee2189a6f441bbe8e7e4ca640755096736717cffc2674a686ef831b0c`

Machine proxy:
- Ubuntu 24.04 GitHub-hosted runner
- AMD EPYC 7763
- 4 logical CPUs visible
- Python 3.11.16
- ONNX Runtime 1.18.0
- CPUExecutionProvider only

### CL-Detection2023

- Official source commit: `dc1ce2bd0a3f317de4160cde17e4a6f60371e67c`
- Official Google Drive weight ID: `1Qvnym4oGSG903ti0z2HE6Dm1udNO692G`
- PT size: `26.087 MiB`
- PT SHA256: `b391e7925522185f993a88048ca7ace2d209ae0864116bdd255660f7a993eb71`
- Export: ONNX opset 17, static `[1,3,512,512] -> [1,38,512,512]`
- ONNX size: `26.026 MiB`
- ONNX SHA256: `8a31cffe6638926fded9801c3d83a3b3e6a98749b62c16ff3891c29b68fc315e`
- ORT CPU cold load: `34.29 ms`
- ORT CPU inference median: `1794.02 ms` over 10 measured iterations

### OralGuard detector

- Source commit: `f619ae5078da80b1fc84fb34324d2100c2382e82`
- HF revision: `06b2a3c390a6caca640e6c6f74f73017e0c5a17b`
- Exact classes: `caries, deep_caries, periapical_lesion, impacted_tooth`
- PT size: `49.651 MiB`
- PT SHA256: `c3303656e72ede3f3d3229e58b2da276448fa204046d3e7a11e13f4d77bc723a`
- Export: ONNX opset 17, static `[1,3,1024,1024] -> [1,8,21504]`
- ONNX size: `99.047 MiB`
- ONNX SHA256: `32c982391f1638bda11323095808d843a1b4e14e1c19ff107494fcb7a744b182`
- ORT CPU cold load: `100.65 ms`
- ORT CPU inference median: `1277.63 ms` over 8 measured iterations

The run also proved `git diff --exit-code -- backend frontend` with no product modification. Max process RSS observed in the combined benchmark was `3197.55 MiB`; this is a harness/process proxy, not per-model isolated peak memory.

## Rights audit — corrected conclusions

### CL-Detection2023

The Apache-2.0 license on the baseline repository does not establish commercial rights to the trained weight. The official Zenodo training-data record states that no publication rights are given and that data may only be used for the challenge because of ethics constraints. The official annotation repository separately declares CC BY-NC 4.0. Therefore the downloaded `best_model.pt` must not be placed in the proprietary production bundle without explicit rights clearance covering the trained artifact.

References:
- https://zenodo.org/records/7787671
- https://github.com/cwwang1979/CL-detection2023
- https://github.com/szuboy/CL-Detection2023

### OralGuard / DENTEX / Ultralytics

The exact four-class technical contract is confirmed, but two independent commercial gates remain:

1. Current official DENTEX distribution declares `CC-BY-NC-SA-4.0` and explicitly describes non-commercial research use.
2. Ultralytics' current licensing page states that YOLO trained/fine-tuned models fall under AGPL-3.0 by default and that proprietary/commercial use requires an Enterprise/commercial license unless the whole project is released under the applicable open-source terms.

Therefore OralGuard's MIT repository/model-card label alone is insufficient to certify proprietary commercial redistribution.

References:
- https://huggingface.co/datasets/ibrahimhamamci/DENTEX
- https://www.ultralytics.com/license

### Aariz

The data route is materially cleaner:
- Figshare: `CC BY 4.0`
- Scientific Data paper: consent for open publication under CC-BY; dataset publicly available under CC-BY
- 1000 cephalograms from 7 devices, 29 landmarks

References:
- https://figshare.com/articles/dataset/Aariz_Cephalometric_Dataset/27986417
- https://www.nature.com/articles/s41597-025-05542-3

The article's own publication license is separate from the dataset license; the dataset license is the relevant asset-rights signal here.

## Current ranking

### Cephalometry

1. **Aariz CC-BY retrain route** — current best path toward a commercially clean proprietary asset. Train a permissively licensed architecture on the 29-point dataset, export ONNX, map 20 direct clinical points; keep Wits fail-closed until separately validated.
2. **DeLR Aariz-26 checkpoint** — technically attractive ready-weight lead, but HOLD until the architecture/code/checkpoint license chain is explicit and compatible.
3. **CL-Detection2023** — best current technical 38-point benchmark and adapter proof, but not commercially clean under the source-data restrictions without written clearance.
4. **CephLD-CCA** — research/reference only by default because GPL-3.0.

### Panoramic

No inspected ready-to-use weight is currently certified as commercially clean for the proprietary bundle.

1. **OralGuard** — technical benchmark leader: exact four classes, ONNX export proven, CPU proxy measured. Commercially blocked absent both dataset and Ultralytics clearance.
2. **HierarchicalDet reproduction/retrain** — avoids Ultralytics at code level, but no ready final checkpoint located and current official DENTEX rights remain non-commercial.
3. **Liodon** — technically compact but explicitly non-commercial.
4. **abdubakr77/dental-xray-ai** — same Ultralytics licensing gate, so not a clean fallback.

## Decision

- Do **not** copy CL-Detection2023 or OralGuard weights into `DigitalCrown-assets` as production assets at this stage.
- Preserve both as technical/research benchmark evidence only.
- Promote Aariz to the primary cephalometric **commercial-clean training-data route**.
- Do not modify `CephaloEngine` clinical definitions to force compatibility with a candidate model.
- Adapt the inference layer to the winning model, not the clinical geometry to an arbitrary published landmark count.

## Next exact

1. Pin the exact Aariz dataset version, file manifest and hashes.
2. Audit the Aariz/DeLR implementation license chain; if DeLR is not clean, choose a permissive architecture and train our own 29-point model.
3. Define the 29 -> Digital Crown 20-point adapter contract and tests without changing clinical calculations.
4. Build a non-PHI cephalometric golden benchmark for the 20 directly supported points and separately gate Wits.
5. Search/train a panoramic candidate using data and architecture with an explicit commercial-compatible rights chain; keep OralGuard as benchmark only.
6. After a candidate wins both technical and rights gates, place the pinned artifact + provenance + SHA256 in private `hraaaaf/DigitalCrown-assets` and resume P6 packaging.

## Non-goals
- No product model replacement during this research branch.
- No clinical equivalence claim from public benchmark scores alone.
- No automatic Wits derivation without separate clinical validation.
- No relaxation of fail-closed behavior.
- No public publication of proprietary/private runtime weights.
