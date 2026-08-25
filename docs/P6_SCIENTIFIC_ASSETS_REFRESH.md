# P6 Scientific Assets Refresh

Status: **ACTIVE — CEPH TECHNICAL WINNER PROVEN; PRIVATE RETENTION + PANORAMIC TOOTH-ENUMERATION REMAIN OPEN**.

This is a scientific-assets research sublot. It does **not** replace the canonical Portability P6 (`Industrialized Windows packaging`) and does not earn Portability EP by itself.

## Goal
Recover or replace scientific runtime assets with candidates that are reproducible, portable, legally distributable in a proprietary commercial desktop product, compatible with Digital Crown fail-closed clinical contracts, and supported by evidence rather than inherited model names.

## Success
1. Exact source/data/model provenance and hashes.
2. Held-out technical benchmark with a sealed test set.
3. Explicit product adapter contract; missing clinical geometry/capability remains unavailable rather than synthesized.
4. Commercial-rights chain acceptable for the intended bundle.
5. Exact winning binary retained privately before public ephemeral cleanup.
6. Windows x64 + macOS ARM64 portability before product wiring.
7. No clinical-equivalence claim from public benchmark metrics alone.

## Product contracts

### Cephalometry
`CephaloEngine` consumes 22 canonical points:
`S, N, Po, Or, A, B, Go, Me, U1i, U1a, L1i, L1a, Prn, Pog_soft, Sn, Ls, Li, Co, Gn, ANS, Occ_Ant, Occ_Post`.

Aariz v1 directly covers 20/22. `Occ_Ant` and `Occ_Post` are absent, so automated Wits remains unavailable/manual/fail-closed until a separate clinical validation establishes an acceptable occlusal-plane definition.

The research adapter is title-keyed, never positional. Tests verify exact 20-point mapping, order independence, ontology fail-closed behavior, and absence of synthesized Wits points.

### Panoramic — exact runtime contract at source HEAD `c505cf0e...`
The active upload route is `POST /upload-panoramic` in `backend/routers/ia.py`.

Its current clinical contract is **tooth localization / numbering only**, not automatic pathology diagnosis:
1. the route calls `panoramic_engine.detect_teeth_only(file_location)`;
2. persisted automatic detections contain tooth identity/location fields (`fdi`, `label`, `confidence`, `bbox`, `present`);
3. `panoramic_report_engine` states that the model only names teeth and that clinical semiology comes from practitioner-entered `manual_anomalies` and `global_findings`;
4. pathology reporting is therefore manual/deterministic in the active route.

This distinction is critical: restoring the current product capability does **not** require a four-pathology diagnostic model. The first replacement target is a commercially clean tooth-localization/enumeration model.

#### Legacy scientific debt behind `detect_teeth_only`
`backend/services/panoramic_service.py::detect_teeth_only()` delegates to `backend/services/sota_panoramic_service.py::analyze()` and then discards pathology semantics, retaining a geometrically inferred FDI number and box.

The delegated engine itself expects a four-class pathology ONNX:
`[Caries, Deep Caries, Impacted, Periapical Lesion]`.

A second engine loads the same expected file but uses the order:
`[Carie, Carie Profonde, Lésion Périapicale, Dent Incluse]`.

Therefore semantic IDs 2/3 disagree across the two consumers. The FDI number is also assigned by a fixed panoramic-geometry heuristic rather than by a directly trained tooth-enumeration target. This is legacy plumbing, not the desired replacement contract.

Both engines expect `backend/ai_models/panoramic_model.onnx`. The `backend/ai_models/` path is absent at the exact research source HEAD. In `cabinet` / `production`, absence of the model fails closed; simulation is development/test-only.

---

## Cephalometry — selected route

### Aariz v1 data pin
- Figshare article: `27986417`
- DOI: `10.6084/m9.figshare.27986417.v1`
- file ID: `51041642`
- file: `Aariz.zip`
- size: `2,098,209,792 bytes`
- license: `CC BY 4.0`
- MD5: `e0bd645bca6759abdae4f199d841bda6`
- independently verified SHA256: `d9fa872b36065dac9615cfcad0c7512c450fe2d86a1839cdec4cbe001def33ea`
- 1000 cephalograms / 7 devices
- official split: 700 train / 150 validation / 150 test
- calibration: 0.089–0.144 mm/px, median 0.1 mm/px

Primary source: https://figshare.com/articles/dataset/Aariz_Cephalometric_Dataset/27986417
Paper: https://www.nature.com/articles/s41597-025-05542-3

### DC-Ceph-UNet29Q4 contract
- Digital Crown-owned implementation trained from scratch; no third-party pretrained weight.
- input: `[B, 1, 512, 512]`
- output: `[B, 29, 128, 128]`
- stride: 4
- isotropic reversible letterbox
- ground truth: Aariz official v1 `ceil(mean(junior, senior))`
- decoder: quarter-pixel heatmap decode then inverse letterbox before native-mm scoring
- ONNX opset 17
- winner configuration: 1,899,117 parameters, seed `20260825`, batch 4, max 30 epochs

### Objective qualification
The initial weighted-MSE pipeline was rejected scientifically after producing ~130–140 mm MRE despite a decreasing loss. The replacement objective combines spatial Gaussian cross-entropy with `20×` normalized-coordinate SmoothL1.

Qualification run `32859703429` proved tiny-set overfit and >98% train-MRE reduction, sufficient to authorize one full run. It was not a clinical claim.

### Full sealed training — PASS
Public ephemeral branch: `p6/ephemeral-ceph-train-20260825`

- training run: `32876308676` — **SUCCESS**
- architecture/source HEAD: `c505cf0e3815049dbb6e7eb930c62f7bc4a2b293`
- preparation/fix HEAD: `eb1614f8c810e5987f3c9be177db9a838eda46e9`
- evidence commit: `1da113b8776aa2b57e42ac194f12b7a48b01558c`
- best epoch: `24`
- validation selected checkpoint only; test instantiated once after pre-test gate
- `clinical_claim=false`
- status: `PUBLIC_REFERENCE_PASS_NOT_CLINICAL`

#### Best validation — epoch 24
All 29 landmarks:
- MRE: **1.325857 mm**
- SDR2: **81.7931%**
- SDR4: **96.1839%**

Digital Crown direct 20:
- MRE: **1.204227 mm**
- SDR2: **85.1333%**
- SDR4: **97.3333%**

#### Held-out test
All 29 landmarks:
- MRE: **1.369337 mm**
- SDR2: **80.1839%**
- SDR4: **95.6782%**

Digital Crown direct 20:
- MRE: **1.232893 mm**
- SDR2: **83.1333%**
- SDR4: **97.2667%**

Published Aariz reference used by this gate:
- MRE `1.789 mm`
- SDR2 `78.44%`
- SDR4 `94.44%`

The candidate beats all three reference thresholds on the sealed all-29 test. This is a **technical benchmark result only**, not a clinical-equivalence or medical-device certification.

### Winning ONNX
- SHA256: `809f1d3d2347d2a34f57d4a3415bb319c29f8a25c325d41160e5f28d4e5dadad`
- size: `7,624,307 bytes`
- input: `[1,1,512,512]`
- output: `[1,29,128,128]`
- opset: 17
- Linux ORT CPU cold load: `22.86 ms`
- Linux ORT CPU inference median: **115.28 ms** over 8 measured iterations
- full training runtime: `10,216.21 s`
- max process RSS: `1,681.27 MiB`

The run also proved `git diff --exit-code -- backend frontend`: no product tree modification.

### Candidate ranking
1. **DC-Ceph-UNet29Q4 / Aariz v1** — technical winner and selected replacement candidate; product wiring not yet authorized.
2. **CL-Detection2023** — useful benchmark, but source-data/annotation rights do not establish a clean proprietary commercial weight chain.
3. **DeLR Aariz-26** — research reference only; drops soft-tissue points Digital Crown consumes and no explicit checkpoint redistribution license was pinned.
4. **CephLD-CCA** — research reference by default because GPL-3.0.

---

## Private asset retention — OPEN / infrastructure block
Target private repo: `hraaaaf/DigitalCrown-assets`
Target branch: `training/p6-ceph-unet29`
Target paths:
- `models/cephalometry/dc_ceph_unet29_q4/aariz_v1/model.onnx`
- `models/cephalometry/dc_ceph_unet29_q4/aariz_v1/training_report.json`
- `provenance/dc_ceph_unet29_q4_aariz_v1/aariz_v1_ingestion_manifest.json`
- `provenance/dc_ceph_unet29_q4_aariz_v1/PROVENANCE.md`

Two materially similar private Actions attempts failed before executing usable steps/logs. The latest verified failed run is `32895166801`; its job exposed `steps=null`. Per execution policy, no further blind private-run retry is authorized.

The exact binary is therefore **not yet claimed as retained privately**. The public ephemeral evidence branch must remain intact until private retention is actually proven. A later branch reset would not constitute cryptographic erasure because Git objects may remain addressable until garbage collection.

Private provenance HEAD `adf9d99b615274d1ab822bce2e410a36ce4d724c` records the winner while explicitly marking binary retention pending.

---

## Panoramic research state

### Phase A — restore the product's real automatic capability
Selected research direction: **direct tooth instance localization + enumeration**, producing the existing `fdi/confidence/bbox` contract without deriving FDI from a pathology detector.

Leading clean-data candidate:
**Panoramic Dental Xray Dataset V3**
- DOI: `10.17632/73n3kz2k4k.3`
- Mendeley dataset record: **CC BY 4.0**
- 107 images at 2964×1464 with tooth instance-segmentation annotations
- 60 images at 1024×512 annotated by tooth type (canine, central/lateral incisor, first/second/third molar, first/second premolar)
- 54 additional high-resolution panoramics at 2888×1309
- original 107-image paper reports a directly annotated tooth-identification/instance-segmentation task
- an independent 2024 review catalogues this dataset as CC BY 4.0 with pixel-level annotation, two annotators and VGG Image Annotator.

Decision: **PRIMARY PHASE-A DATA LEAD**, but not yet benchmark-authorized. Exact downloadable annotation files, hashes, subject/image identity, train/validation/test split, FDI semantics and leakage controls must be pinned first.

The associated journal article is published under separate Springer publication rights; those article rights must not be confused with the explicit CC BY 4.0 dataset record. Only the dataset files and their own pinned license are candidate training inputs.

### Phase B — automatic pathology capability is separate and remains unapproved
The legacy four semantics are:
- `Caries`
- `Deep Caries`
- `Impacted`
- `Periapical Lesion`

They are **not required to restore the active upload/report contract**, because current clinical semiology is manual. Automatic pathology detection would be a separate clinical expansion lot with its own dataset, rights, calibration, acceptance thresholds and practitioner validation.

#### Pathology rights/data matrix
1. **Periapical lesions — Mendeley `kx52tk2ddj`, V3**
   - DOI: `10.17632/kx52tk2ddj.3`
   - 3,926 original panoramic radiographs reported; augmented set reported at 17,004 images
   - Mendeley dataset record declares **CC BY 4.0**
   - associated Data in Brief article is **CC BY-NC 4.0**
   - decision: **HOLD** pending explicit resolution of which terms govern the downloadable training files plus exact file/hash/annotation audit.

2. **Caries + impacted — Dental OPG XRAY Dataset V4**
   - DOI: `10.17632/c4hhrkxytw.4`
   - 232 original OPG + 604 augmented images
   - Mendeley and NLM dataset records declare **CC BY 4.0**
   - associated Data in Brief article is **CC BY-NC 4.0**
   - classes include caries and impacted teeth, but no separate `Deep Caries`
   - limitation: source OPGs were photographed using an Android phone camera; native-radiograph domain fidelity cannot be assumed
   - decision: **HOLD** pending rights clarification and exact data audit.

3. **DENTEX — exact four-class semantic reference**
   - exact diagnoses include caries, deep caries, periapical lesions and impacted teeth
   - official GitHub README currently says DENTEX data are **CC BY-SA 4.0**
   - official Hugging Face dataset card currently declares **CC BY-NC-SA 4.0**
   - these two first-party distributions conflict materially on commercial permission
   - decision: **HOLD / benchmark-only under conservative interpretation** until the rights holder resolves the discrepancy in writing or a single authoritative licence is pinned.

### Deep Caries bottleneck
No inspected source with a closed proprietary-commercial rights chain yet supplies a separately annotated `Deep Caries` class matching the legacy semantic contract. Ordinary caries must never be relabelled as deep caries.

This is no longer a blocker for **Phase A tooth enumeration**, but it remains a hard blocker for any future four-pathology automatic model.

### Panoramic Phase-A benchmark contract
Before one heavy run:
1. pin exact V3 files, annotation files, hashes and the CC BY 4.0 licence snapshot;
2. establish whether annotations encode direct FDI, tooth type only, or instance masks requiring a deterministic FDI derivation layer;
3. prove unique source-image/patient grouping and split before any augmentation;
4. seal train/validation/test before model selection;
5. train from scratch or use only weights with a commercially compatible provenance chain;
6. output tooth instances with confidence and bounding boxes; map to FDI only from validated annotation semantics, never from a fixed smile-curve heuristic;
7. export ONNX opset 17;
8. adapt to the existing `detections_data.detections[]` API without changing manual-semiology truth;
9. technical gates must include tooth detection/localization and **FDI numbering accuracy**, not pathology mAP;
10. after a technical winner, certify Linux proxy, Windows x64 and macOS ARM64, then build the clinical golden-set protocol before product wiring.

No heavy panoramic run is authorized until items 1–4 are proven. Heavy benchmark policy remains: **one complete preparation → one final commit → one run**.

---

## Decisions locked
- DC-Ceph-UNet29Q4 / Aariz v1 is the selected **technical cephalometric winner**.
- `Occ_Ant` / `Occ_Post` are not synthesized; Wits stays fail-closed pending separate validation.
- No cephalometric product wiring occurs before private retention + Windows/macOS portability + clinical validation plan.
- No clinical claim is inferred from the public Aariz benchmark result.
- Panoramic Phase A restores **tooth localization/enumeration only**, matching the active route and deterministic/manual report contract.
- The current pathology-detector-to-FDI heuristic is legacy debt and is not the target architecture.
- Automatic panoramic pathology detection is a distinct future clinical lot; it must not silently expand P6 scope.
- DENTEX licensing is treated as unresolved because its official GitHub and Hugging Face distributions disagree.
- The two pathology-oriented Mendeley leads remain HOLD under the current conservative commercial-rights standard.
- `Deep Caries` remains unavailable for automatic pathology inference until clean separately annotated data or explicit permission is proven.

## Next exact
1. Pin the exact downloadable files/annotations/hashes and FDI semantics of `10.17632/73n3kz2k4k.3`; define patient/image deduplication and a sealed split.
2. Build a lightweight research-only ingestion/contract test for that dataset; no product tree change.
3. Prepare exactly one Phase-A tooth-enumeration benchmark only after the data contract passes.
4. In parallel, resolve cephalometric private binary retention; do not reset the public winner branch before exact private SHA proof.
5. After private retention, run Windows x64 + macOS ARM64 inference portability on the exact ceph winner.
6. Build the non-PHI/golden clinical validation protocol for the 20 direct cephalometric points; keep Wits separate.
7. Keep pathology research on HOLD until rights and clinical scope are separately closed.

## Portability EP accounting
The canonical `PORTABILITY_LAUNCHER_ROADMAP.md` marks P0–P5 closed and Portability P6 (`Industrialized Windows packaging`) separately. This scientific research sublot is not that packaging lot. **No Portability EP is added by this document.**
