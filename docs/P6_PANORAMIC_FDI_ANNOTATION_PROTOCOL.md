# P6 Panoramic FDI Annotation Protocol

Status: **READY FOR CLINICIAN ANNOTATION — SOURCE PACK CERTIFIED — NO PRODUCT WIRING**.

## Goal
Create a commercially usable, clinician-controlled FDI ground-truth set for panoramic tooth localization/enumeration that can replace the legacy pathology-detector-to-FDI heuristic without expanding Digital Crown into automatic pathology diagnosis.

## Success
1. Every source image has a pinned source URL/DOI, file hash and commercial-use-compatible rights record.
2. Every accepted tooth instance has a clinician-approved FDI label and polygon/bounding box.
3. Image orientation is explicit before numbering; no left/right inference is silently guessed.
4. Patient/source identity is deduplicated before splitting.
5. Train/validation/test are sealed before model selection; no augmented derivative crosses a split.
6. Test labels are independently reviewed and adjudicated.
7. A complete provenance ledger can reproduce each annotation from source image to final export.

## Current rights gate
No currently inspected direct-FDI panoramic dataset has a fully closed proprietary-commercial rights chain:

- `Panoramic Dental Xray Dataset V3`, DOI `10.17632/73n3kz2k4k.3`: the first-party Mendeley V3 record is CC BY 4.0. Exact semantic provenance run `32910743873` proved 111 downloadable files / 84,254,649 bytes, 107 metadata images, 25 images with source geometry and 772 source regions. `annotations.json` SHA256 is `b6de2c396cb76758227562798141a00fb5d769f9d8f9eb3919470f4ff23578bd`. The `Teeth` attribute exists on 540 regions, but all 540 values are the empty string; there are 0 tooth tokens, 0 explicit FDI codes and 0 FDI-labelled regions. It is therefore a rights-cleared image/geometry source for clinician annotation, **not** direct FDI ground truth.
- Humans in the Loop `Teeth Segmentation on dental X-ray images`, DOI `10.34740/KAGGLE/DSV/5884500`: publisher states CC0, 598 images, 15,318 tooth polygons and 32 positional classes; however the images are derived from López et al. `10.5281/zenodo.4457648`, whose canonical Zenodo record does not expose a licence. Commercial use therefore remains HOLD until the upstream image-rights chain is confirmed.
- `AKUDENTAL`: direct tooth polygons/boxes and FDI-oriented numbering, but the source repository states future release under CC BY-NC-SA 4.0. Research-only for Digital Crown.
- `A dual-labeled dataset` (Zhou et al., BMC Oral Health 2024): explicit FDI 11–48/91 and expert annotation, but the public Kaggle dataset currently reports licence `Unknown`; the article itself is CC BY-NC-ND 4.0. HOLD pending explicit dataset permission.
- `TL-pano`, DOI `10.5281/zenodo.15038971`: direct tooth/quadrant/type labels from dental experts, but the Zenodo description explicitly limits the dataset to non-commercial research. Research-only.
- STS-2D/STS-2024: useful segmentation/FDI research references, but canonical rights metadata are not sufficiently consistent for proprietary commercial training; do not use until a single authoritative commercial grant is pinned.
- Roboflow `Panoramic-Dental-Xray-FDI`: page states CC BY 4.0 and exposes 32 FDI classes, but source-image provenance is not documented. HOLD until provenance and upstream rights are proven.

## Certified first-party clinician pack
The first clinician-annotation pack is now reproducible from the first-party Mendeley V3 source.

Proof:
- builder: `scripts/p6_mendeley_fdi_annotation_pack.py`;
- workflow: `.github/workflows/p6-mendeley-fdi-annotation-pack.yml`;
- exact HEAD: `6f7614f23b793dd6804d6c7d770f62928a3a09f0`;
- run: `32912109975` — **SUCCESS**;
- artifact: `9586914372`, `p6-mendeley-v3-fdi-clinician-pack`;
- artifact digest: `sha256:a72599acf4b96b3d8519f174614feca3cec011dddce0dcc594f01ac4c656ea09`;
- source images: `107`;
- images with source geometry proposals: `25`;
- source geometry proposals: `772`;
- clinician FDI assigned: `0`;
- orientation confirmed: `0`;
- ledger SHA256: `42950b89eb2856b8b4c9302837ea95a170aec5b11257d15a06ed3ae619122cad`;
- source manifest SHA256: `f59fb925d9e33123300fcd984edb6091e6353205e6b9ef5b0a549a4b5ce8cebd`.

The pack deliberately preserves source VIA regions only as `SOURCE_PROPOSAL_ONLY`. `geometry_to_fdi_inference_allowed=false`, `source_fdi_labels_present=false`, every orientation is unset, and every `clinician_instances` list is empty. This is the required fail-closed starting point for clinical annotation.

## Source-image policy
Only images whose own rights are commercially compatible may enter the production annotation pool.

For each source file record:
- source name / DOI / version;
- original filename or stable source ID;
- SHA256;
- acquisition metadata when available;
- rights/licence text and retrieval date;
- whether redistribution of the raw image is allowed;
- whether derivative annotations/model training are allowed;
- duplicate-group ID.

If any field affecting commercial use is unresolved, `eligible_for_training=false`.

## Annotation schema
One image record contains:

- `image_id`
- `source_id`
- `orientation`: radiographic patient-right/patient-left confirmed
- `dentition`: permanent / mixed / deciduous / uncertain
- `instances[]`

Each tooth instance contains:
- `fdi`: permanent `11–18`, `21–28`, `31–38`, `41–48`; deciduous numbering is a separate future ontology and must never be coerced into permanent labels;
- `polygon` and derived `bbox`;
- `visibility`: visible / partial / uncertain;
- `eruption_state`: erupted / unerupted-or-impacted / uncertain, used only as geometry metadata, not as a diagnostic finding;
- `annotator_status`: accepted / needs_adjudication / excluded;
- optional comment.

No caries, periapical or other pathology label is required for P6 Phase A.

## Annotation workflow
1. **Ingest** only rights-cleared source images and compute hashes.
2. **Orient** the image explicitly. FDI assignment is forbidden until orientation is confirmed.
3. **Geometry proposal** may be manual or generated by a separately rights-cleared annotation-assist model. A proposal is never ground truth by itself.
4. **Clinician A** validates/edits each tooth boundary and assigns FDI.
5. **Clinician B** independently reviews all sealed-test images and a predefined quality-control subset of train/validation images.
6. **Adjudication** resolves every FDI disagreement, missing/extra tooth disagreement and clinically meaningful geometry disagreement.
7. **Freeze** the accepted annotation revision before dataset split finalization.

Qualified dental clinicians control FDI truth. Model-assisted annotation may reduce clicking; it cannot decide the final tooth number.

## Split / leakage contract
- Group by patient/source identity before splitting.
- Near-duplicate image detection runs before split.
- All versions, crops and augmentations of one source image remain in the same split.
- Test is sealed before model/hyperparameter selection.
- Test annotations are not exposed to the training workflow.
- Mixed/deciduous dentition is excluded from the first permanent-FDI model unless a separately validated ontology is implemented.

## Quality gates before training
The dataset is benchmark-authorized only when:
1. rights gate passes for every training/validation/test image;
2. all accepted labels conform to the FDI ontology;
3. no duplicate group crosses a split;
4. every test image has independent clinical review and adjudication;
5. orientation is known for 100% of included images;
6. annotation export passes schema/integrity checks;
7. a provenance manifest pins hashes and split membership.

No fixed accuracy claim is predeclared here; acceptance thresholds belong to the benchmark plan after a clean ground-truth corpus exists.

## Model-output contract
The Phase-A model may output only:
- `fdi`
- `confidence`
- `bbox` (optionally mask retained internally)
- `present`

Any uncertain/unsupported numbering must fail closed rather than be replaced by a smile-curve positional guess.

## Clinical validation after technical training
Before product wiring:
- evaluate tooth detection recall/precision;
- per-FDI macro precision/recall/F1;
- exact tooth-number accuracy;
- confusion matrix by FDI;
- missing-tooth false-assignment rate;
- difficult-case strata: edentulous gaps, impacted/unerupted teeth, restorations, overlapping structures;
- Windows x64 and macOS ARM64 ONNX parity;
- clinician review on a non-PHI golden set.

## Heavy-run rule
No heavy panoramic benchmark is authorized until the rights, annotation, split and provenance gates above are all green.

Then: **one complete preparation → one final commit → one run**.

## Next exact
A qualified dental clinician must now review the certified pack: confirm orientation first, then validate/edit source geometry and assign FDI. Only after clinician truth, deduplication, split sealing and independent test review may panoramic training begin.
