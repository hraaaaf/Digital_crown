# P6 Scientific Assets Refresh

Status: **ACTIVE — CEPH TECHNICAL WINNER PROVEN; PRIVATE RETENTION + PANORAMIC FDI GROUND TRUTH REMAIN OPEN**.

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

Restoring the current product capability does **not** require a four-pathology diagnostic model. The replacement target is a commercially clean tooth-localization/enumeration model.

#### Legacy scientific debt behind `detect_teeth_only`
`backend/services/panoramic_service.py::detect_teeth_only()` delegates to `backend/services/sota_panoramic_service.py::analyze()` and then discards pathology semantics, retaining a geometrically inferred FDI number and box.

The delegated engine expects `[Caries, Deep Caries, Impacted, Periapical Lesion]`. A second engine loads the same expected file but reverses semantic IDs 2/3 (`Lésion Périapicale`, `Dent Incluse`). FDI is assigned by a fixed panoramic-geometry heuristic rather than by a directly trained enumeration target.

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

The exact binary is therefore **not yet claimed as retained privately**. The public ephemeral evidence branch remains intact until private retention is actually proven. A later branch reset would not constitute cryptographic erasure because Git objects may remain addressable until garbage collection.

Private provenance HEAD `adf9d99b615274d1ab822bce2e410a36ce4d724c` records the winner while explicitly marking binary retention pending.

---

## Panoramic research state

### Phase A — exact target
Restore **tooth instance localization + FDI enumeration** matching the existing `fdi/confidence/bbox` API. Clinical semiology stays manual. A pathology model is neither required nor authorized for Phase A.

### Direct-FDI data audit — 2026-08-25
No inspected direct-FDI panoramic dataset currently closes all four required gates at once: raw-image provenance, explicit commercial rights, expert/traceable FDI labels, and reproducible files/splits.

#### 1. Panoramic Dental Xray Dataset V3 — useful auxiliary, NOT direct FDI
- DOI: `10.17632/73n3kz2k4k.3`
- Mendeley record: **CC BY 4.0**.
- Dataset description lists 107 high-resolution images for instance segmentation, 60 images annotated by tooth type, and 54 additional high-resolution panoramics.
- Direct inspection through a public V3 preparation mirror at commit `406e29bf43a4b73a301e493cd64dc9fa68aed65b` shows its `annotations.json` covers only `1.jpg`, `2.jpg`, `4.jpg`; `region_attributes` are empty and contain **no FDI labels**.
- That mirror's FDI demo assigns numbers from polygon centroid/arch ordering, i.e. synthesized positional numbering rather than source truth.

Decision: **ELIGIBLE AUXILIARY / IMAGE-SOURCE LEAD**, not a ready FDI benchmark corpus. Exact source ZIP/files/hashes still need a first-party ingestion manifest before any use.

#### 2. Humans in the Loop Teeth Segmentation — strongest permissive-labelled lead, rights chain not yet closed
- DOI: `10.34740/KAGGLE/DSV/5884500`
- publisher: Humans in the Loop / Kaggle
- 598 panoramic images; 15,318 tooth polygons; 32 positional classes
- publisher explicitly states **CC0 1.0 / public domain**
- class numbering starts at the upper-left side of the displayed panoramic image and proceeds clockwise; this is not FDI text but is an absolute per-position class system that can be mapped only after orientation semantics are verified.
- source images are stated to come from López et al. `Panoramic radiography database`, DOI `10.5281/zenodo.4457648`.
- canonical Zenodo record for `4457648` exposes the image archive and MD5 but no licence value; third-party mirrors disagree on the licence.

Decision: **HOLD FOR COMMERCIAL TRAINING** until Humans in the Loop or the upstream rights holder explicitly confirms that the CC0 dedication lawfully covers the redistributed source images, not just new annotations.

#### 3. AKUDENTAL — direct FDI, non-commercial
Source: `melihoz/AKUDENTAL`.
- 333 high-resolution OPGs
- per-tooth polygons/bounding boxes and FDI-oriented numbering
- source README states intended release under **CC BY-NC-SA 4.0**

Decision: **RESEARCH-ONLY / REJECT FOR PROPRIETARY TRAINING**.

#### 4. Zhou et al. dual-labeled dataset — expert FDI, licence unknown
Paper: DOI `10.1186/s12903-024-04984-2`.
- FDI `11–48` plus `91` supernumerary
- expert annotation workflow with postgraduate/dentist annotation and senior-doctor review
- public Kaggle page currently exposes 500 images and reports **License: Unknown**
- article itself is **CC BY-NC-ND 4.0**, which must not be mistaken for a commercial dataset grant

Decision: **HOLD** pending explicit dataset permission from rights holders.

#### 5. TL-pano — expert FDI structure, explicitly non-commercial
- DOI `10.5281/zenodo.15038971`
- tooth polygons with quadrant + tooth-type fields sufficient to derive FDI structurally
- expert annotation / consent provenance described
- Zenodo description explicitly says **non-commercial research purposes only**

Decision: **RESEARCH-ONLY / REJECT FOR PROPRIETARY TRAINING**.

#### 6. STS-2D / STS-2024 — rights metadata conflict
- STS-2D contains 4,000 OPGs / 900 binary masks and is useful for tooth-region segmentation.
- Hugging Face mirrors state CC BY 4.0, but the canonical Zenodo `10.5281/zenodo.10597292` currently exposes a blank licence field in the retrieved record; challenge distributions have separate access agreements.
- STS-2024 instance-level FDI data are tied to challenge/scientific-use restrictions in the inspected distribution.

Decision: **HOLD** until one authoritative rights grant is pinned for the exact files intended for commercial training.

#### 7. Roboflow Panoramic-Dental-Xray-FDI — explicit page licence, missing provenance
- 1,577 images, object detection, 32 FDI classes
- Roboflow page declares **CC BY 4.0**
- source-image origin and annotation provenance are not documented on the dataset page

Decision: **HOLD**. A platform licence declaration cannot substitute for an auditable upstream image/annotation rights chain.

### Phase-A data decision
There is currently **no benchmark-authorized direct-FDI training corpus** for proprietary Digital Crown use.

The clean path is therefore:
1. use only source images whose own commercial rights are explicitly pinned;
2. create clinician-controlled FDI ground truth under `docs/P6_PANORAMIC_FDI_ANNOTATION_PROTOCOL.md`;
3. use permissive existing tooth masks/type labels only as annotation aids when their rights chain is also closed;
4. never promote geometry-based positional guesses to ground truth;
5. train only after rights + annotation + split + provenance gates are all green.

This is slower than borrowing an anonymous Roboflow dataset and calling it science, but it is the shortest path that survives commercial and clinical scrutiny.

### Phase B — automatic pathology remains separate
Legacy semantics:
- `Caries`
- `Deep Caries`
- `Impacted`
- `Periapical Lesion`

They are not required to restore the active upload/report contract. Any future automatic pathology detector is a separate clinical expansion lot with its own dataset, rights, calibration and practitioner validation.

#### Pathology rights/data matrix
1. **Periapical lesions — Mendeley `kx52tk2ddj`, V3**: dataset page declares CC BY 4.0; associated Data in Brief article is CC BY-NC 4.0. **HOLD** until file-level rights are reconciled.
2. **Caries + impacted — Mendeley `c4hhrkxytw`, V4**: dataset pages declare CC BY 4.0; associated article is CC BY-NC 4.0; source OPGs were photographed with an Android phone. **HOLD**.
3. **DENTEX**: exact four diagnoses exist, but inspected first-party distributions disagree between CC BY-SA and CC BY-NC-SA. **HOLD / benchmark-only under conservative interpretation**.

### Deep Caries bottleneck
No inspected source with a closed proprietary-commercial rights chain supplies a separately annotated `Deep Caries` class matching the legacy semantic contract. Ordinary caries must never be relabelled as deep caries.

---

## Panoramic Phase-A benchmark contract
A heavy benchmark is authorized only after:
1. exact source files + hashes + commercial-rights snapshot are pinned;
2. direct FDI ground truth passes `P6_PANORAMIC_FDI_ANNOTATION_PROTOCOL.md`;
3. patient/source/near-duplicate grouping is complete before split;
4. train/validation/test are sealed before model selection;
5. architecture/initial weights have a proprietary-compatible provenance chain;
6. outputs are direct tooth instances with confidence + bbox/mask + validated FDI semantics;
7. ONNX opset 17 export is defined;
8. adapter preserves the current `detections_data.detections[]` API and manual-semiology truth;
9. gates include tooth detection/localization and per-FDI numbering accuracy, not pathology mAP;
10. winner must later pass Linux proxy, Windows x64, macOS ARM64 and non-PHI clinician golden-set review before product wiring.

Heavy benchmark policy: **one complete preparation → one final commit → one run**.

---

## Decisions locked
- DC-Ceph-UNet29Q4 / Aariz v1 is the selected **technical cephalometric winner**.
- `Occ_Ant` / `Occ_Post` are not synthesized; Wits stays fail-closed pending separate validation.
- No cephalometric product wiring occurs before private retention + Windows/macOS portability + clinical validation plan.
- No clinical claim is inferred from the public Aariz benchmark result.
- Panoramic Phase A restores **tooth localization/enumeration only**.
- The current pathology-detector-to-FDI heuristic is legacy debt and is not the target architecture.
- No inspected direct-FDI panoramic dataset is yet benchmark-authorized for proprietary commercial training.
- V3 `73n3kz2k4k.3` is demoted from direct-FDI lead to auxiliary/right-cleared image candidate because its inspected annotations contain no FDI truth.
- Humans in the Loop CC0 is the strongest permissive-labelled lead but remains HOLD until upstream image rights are confirmed.
- AKUDENTAL and TL-pano are non-commercial research references only.
- Zhou dual-labeled dataset and Roboflow FDI remain HOLD until explicit rights/provenance are closed.
- Automatic pathology detection remains a separate future clinical lot.
- `Deep Caries` remains unavailable for automatic pathology inference until clean separately annotated data or explicit permission is proven.

## Next exact
1. Pin exact downloadable V3 files/hashes and identify which V3 images are independently rights-cleared and non-duplicated for a possible expert-FDI annotation pool.
2. Seek/record an authoritative source-image rights confirmation for Humans in the Loop `5884500` / upstream López `4457648`; do not train commercially before this gate closes.
3. Apply `P6_PANORAMIC_FDI_ANNOTATION_PROTOCOL.md` to the first rights-cleared image pool; no heavy run yet.
4. In parallel, resolve cephalometric private binary retention; do not reset the public winner branch before exact private SHA proof.
5. After private retention, run Windows x64 + macOS ARM64 inference portability on the exact ceph winner.
6. Build the non-PHI/golden clinical validation protocol for the 20 direct cephalometric points; keep Wits separate.
7. Keep automatic pathology research on HOLD until rights and clinical scope are separately closed.

## Portability EP accounting
The canonical `PORTABILITY_LAUNCHER_ROADMAP.md` marks P0–P5 closed and Portability P6 (`Industrialized Windows packaging`) separately. This scientific research sublot is not that packaging lot. **No Portability EP is added by this document.**
