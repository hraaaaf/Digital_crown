# P6 Scientific Assets Refresh

Status: **ACTIVE — CEPh TECHNICAL WINNER PROVEN; PRIVATE RETENTION + PANORAMIC REMAIN OPEN**.

This is a scientific-assets research sublot. It does **not** replace the canonical Portability P6 (`Industrialized Windows packaging`) and does not earn Portability EP by itself.

## Goal
Recover or replace scientific runtime assets with candidates that are reproducible, portable, legally distributable in a proprietary commercial desktop product, compatible with Digital Crown fail-closed clinical contracts, and supported by evidence rather than inherited model names.

## Success
1. Exact source/data/model provenance and hashes.
2. Held-out technical benchmark with a sealed test set.
3. Explicit product adapter contract; missing clinical geometry remains unavailable rather than synthesized.
4. Commercial-rights chain acceptable for the intended bundle.
5. Exact winning binary retained privately before public ephemeral cleanup.
6. Windows x64 + macOS ARM64 portability before product wiring.
7. No clinical-equivalence claim from public benchmark metrics alone.

## Product contracts

### Cephalometry
`CephaloEngine` consumes 22 canonical points:
`S, N, Po, Or, A, B, Go, Me, U1i, U1a, L1i, L1a, Prn, Pog_soft, Sn, Ls, Li, Co, Gn, ANS, Occ_Ant, Occ_Post`.

Aariz v1 directly covers 20/22. `Occ_Ant` and `Occ_Post` are absent, so automated Wits remains unavailable/manual/fail-closed until a separate clinical validation establishes an acceptable occlusal-plane definition.

The research adapter is title-keyed, never positional. This matters because published presentation order and repository/config order are not safely interchangeable. Tests verify exact 20-point mapping, order independence, ontology fail-closed behavior, and absence of synthesized Wits points.

### Panoramic
The current product contract expects exactly four pathology semantics:
1. `Caries`
2. `Deep Caries`
3. `Impacted`
4. `Periapical Lesion`

Clinical mode remains fail-closed when the required model is absent.

A class-order hazard is now explicitly tracked: `sota_panoramic_service.py` and `panoramic_service.py` do not list the last two semantics in the same order. This is not declared a production bug until the actual ONNX output-order provenance is established, but any replacement must carry an explicit canonical class-id mapping and tests. Positional inference alone is not acceptable.

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
1. **DC-Ceph-UNet29Q4 / Aariz v1** — technical winner and selected replacement candidate; cleanest current data/provenance route; product wiring not yet authorized.
2. **CL-Detection2023** — useful 38-point technical benchmark, but source-data/annotation rights do not establish a clean proprietary commercial weight chain.
3. **DeLR Aariz-26** — research reference only; drops soft-tissue points Digital Crown consumes and no explicit checkpoint redistribution license was pinned.
4. **CephLD-CCA** — research reference by default because GPL-3.0.

---

## Private asset retention — OPEN / external infrastructure block
Target private repo: `hraaaaf/DigitalCrown-assets`
Target branch: `training/p6-ceph-unet29`
Target paths:
- `models/cephalometry/dc_ceph_unet29_q4/aariz_v1/model.onnx`
- `models/cephalometry/dc_ceph_unet29_q4/aariz_v1/training_report.json`
- `provenance/dc_ceph_unet29_q4_aariz_v1/aariz_v1_ingestion_manifest.json`
- `provenance/dc_ceph_unet29_q4_aariz_v1/PROVENANCE.md`

Private Actions runs have repeatedly failed before executing usable steps/logs. The YAML-level defect in one intermediate workflow was corrected and independently parsed before retry, but the subsequent run still exposed no executable steps/logs. A direct Git object copy was also rejected by GitHub because a blob from the public repository is not a valid blob in the private repository.

Therefore the exact binary is **not yet claimed as retained privately**. The public ephemeral evidence branch must remain intact until private retention is actually proven. No cryptographic-erasure claim will be made after later branch reset because Git commits can remain addressable until Git garbage collection.

---

## Panoramic research state

### Ready-weight candidates
- **OralGuard**: exact four-class semantic fit and ONNX technical benchmark proven; not accepted for proprietary commercial bundling because current DENTEX rights are non-commercial and the Ultralytics training/license chain is not cleared.
- **Liodon**: compact technical candidate, explicitly non-commercial.
- **HierarchicalDet**: code-level research route, but DENTEX rights remain the data blocker and no ready final production checkpoint was located.

DENTEX current official distribution remains a technical benchmark source only unless explicit commercial rights are obtained.

### Alternative-data audit
Several panoramic datasets expose permissive-looking repository records, but associated publications/terms are not sufficiently consistent to certify the whole training chain as commercially clean. They remain **HOLD — rights clarification required**, not silently promoted to clean assets.

No inspected commercially clean source yet supplies a robust, separately annotated **Deep Caries** class matching the current Digital Crown contract. `Deep Caries` therefore remains the principal data-rights/semantic bottleneck for a clean four-class retrain.

### Panoramic replacement contract
Before any heavy panoramic benchmark:
1. pin exact data files, hashes, license snapshots and attribution;
2. split original patients/images before augmentation to prevent leakage;
3. preserve exact canonical four-class semantics;
4. make class-id mapping explicit by name, not duplicated positional arrays;
5. represent unavailable class capability as unavailable, never as a negative diagnosis;
6. seal the test split before model selection;
7. export ONNX opset 17 and aggregate into the existing `pathology/confidence/tooth/bbox` result contract;
8. certify Linux proxy, Windows x64 and macOS ARM64;
9. keep product fail-closed behavior unchanged until the candidate wins technical + rights + clinical gates.

No second heavy panoramic training run is authorized until that preparation is complete.

---

## Decisions locked
- No CL-Detection2023 or OralGuard production weight is copied into the proprietary bundle under current rights evidence.
- DC-Ceph-UNet29Q4 / Aariz v1 is the selected **technical cephalometric winner**.
- The inference layer must adapt to the model; clinical geometry must not be distorted to fit a paper/model ontology.
- `Occ_Ant` / `Occ_Post` are not synthesized; Wits stays fail-closed pending separate validation.
- No product wiring occurs before private retention + Windows/macOS portability + clinical validation plan.
- No clinical claim is inferred from the public Aariz benchmark result.
- Panoramic class-order provenance becomes an explicit gate.

## Next exact
1. Resolve private binary retention and verify the exact ONNX SHA256 in `DigitalCrown-assets`.
2. Only after that proof, reset the public ephemeral training branch to the canonical research base; do not claim cryptographic erasure.
3. Run Windows x64 + macOS ARM64 inference portability on the retained exact ceph winner.
4. Build the non-PHI/golden clinical validation protocol for the 20 direct cephalometric points; keep Wits separate.
5. Complete panoramic rights/data matrix, with `Deep Caries` remaining fail-closed until a clean source or explicit permission exists.
6. Only then evaluate product wiring in a separate controlled lot.

## Portability EP accounting
The canonical `PORTABILITY_LAUNCHER_ROADMAP.md` currently marks P0–P5 closed and Portability P6 (`Industrialized Windows packaging`) as NEXT. This scientific research sublot is not that packaging lot. **No Portability EP is added by this document.**
