# LOT05 / 05.7-J10D — FDI numbering, external validation path (2026-10-22)

**Current result:** the [pinned FDI model](https://huggingface.co/miquic/app-odonto-fdi-yolov8s) `best.pt` (`82b4d9a02f9e6f32a746dc17afe681e20e8b99e2`, SHA-256 `533833a4244f092f82bc94a6c2d6fac7e1656c9437994e98d09843c54aafd3f6`) **loaded and inferred on synthetic image**, with 32 explicit FDI classes. Its published mAP is not an external correctly-numbered-teeth rate. An **offline evaluation harness** and synthetic adversarial tests are in PR #1006. There is **no valid external clinical performance estimate yet**. V1.5 release still NO-GO.

## Public/non-DENTEX FDI-labelled cohort discovery

| Dataset | Facts established from originating publication | Data access / value for this mission |
|---|---|---|
| **OdontoAI O²PR** | [IvisionLab original repository](https://github.com/IvisionLab/OdontoAI-Open-Panoramic-Radiographs) states 4,000 panoramics from its dental imaging lineage, 2,000 released with tooth instance masks and numbers; separate 2,000 reserved for private benchmark. [Paper](https://arxiv.org/abs/2203.15856) discusses two thousand public labels. [Dataset research](https://pmc.ncbi.nlm.nih.gov/articles/PMC10964594/) reports FDI tooth instance masks. | **First candidate for local research evaluation**: institution/collection differs from European-source DENTEX, but patient/image independence from the candidate model is NOT audited; access permissions and data licence to be inspected before download. Convert COCO polygon annotations to boxes locally, preserve verified category↔FDI mapping, use official released **labelled** subset only. |
| **InReDD-PAN924 v1.0** | [PhysioNet](https://physionet.org/content/inredd-dataset-pan924/1.0.0/) says 924 USP/Ribeirão Preto panoramics, 20,033 teeth with bounding boxes and FDI-position labels, COCO-compatible JSON and specialist annotations. | **Independent-source strong benchmark candidate**, but gated: **credentialed PhysioNet user, signed DUA and individual project approval** explicitly required. No attempt to bypass. Contact/data custodian approval needed before use. Metadata may contain demographic variables; no public CI or patient data in GitHub. |
| **AKUDENTAL** | [Paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC12874774/) describes 333 panoramics, per-tooth FDI+other annotations and external cross-dataset evaluation; [author GitHub README](https://github.com/melihoz/AKUDENTAL) still says images and full annotation files will be uploaded after publication, even though publication is Jan 2026. | **Availability unconfirmed**, do not assert 333 image bytes are currently accessible. Research-only noncommercial per author, no image transfer until actual dataset and rights checked. |
| **Roboflow panoramic-dental-xray-FDI** | [Dataset card](https://universe.roboflow.com/dentalxray-yjztn/panoramic-dental-xray-fdi) lists 1,577 panoramics with 32 FDI labels, CC BY 4.0. | **Hold**: absent original collection provenance and no disjointness manifest. Could be repackaged training material; CC badge is insufficient evidence of independent holdout. |
| **DENTEX itself** | [DENTEX creators](https://github.com/ibrahimethemhamamci/DENTEX) publish quadrant-enumeration training labels and diagnosis labels. | **Forbidden as an external/independent validation assertion**, as primary FDI model explicitly trained on DENTEX. Fine as historical development context only. |

## What is delivered, and what is not

**Delivered in experimental PR:** `experiments/lot05_j10d_fdi_local_benchmark.py` with an offline-only mode for authorized local radiographs and synthetic/precomputed prediction mode; `experiments/test_lot05_j10d_fdi_local_benchmark.py`; ephemeral CI `.github/workflows/lot05-j10d-fdi-evaluator-contract.yml`. Model file must reside on the local controlled computer and match the pinned SHA-256; only local inference, no upload. Output JSON contains **aggregate metrics only**, not case IDs, paths, pixels or image predictions. Test fixtures synthetic; public GitHub CI **must never download or upload patient films**.

**What is NOT delivered:** access to OdontoAI/InReDD/AKUDENTAL datasets, patient- and institution-disjointness proof, case annotations reviewed for this project, real-panoramic model evaluation, trained/pinned ONNX output, clinician UX or act catalogue. No accuracy percentage from the evaluator will be described as independently validated until the cohort provenance is independently audited.

### Local-only input manifest (illustrative synthetic values)

```json
{
  "schema": "digital-crown-fdi-eval-v1",
  "cases": [
    {
      "case_id": "opaque-case-001",
      "image": "authorized/local-image-001.png",
      "height": 160,
      "width": 220,
      "dentition": "permanent",
      "gt": [
        { "fdi": "36", "bbox": [10, 10, 60, 60] },
        { "fdi": "37", "bbox": [70, 10, 120, 60] }
      ]
    }
  ]
}
```

These are synthetic coordinates, not clinical annotations. The image must be a local authorized image and its path relative to the controlled root. Use `"mixed"`, `"primary"` or `"unknown"` to flag out-of-scope dentition: the current 32-class permanent model **cannot** number deciduous teeth FDI 51–85.

### Real inference, only once legitimate local films, annotations and consent are available

```powershell
$env:HF_HUB_OFFLINE = "1"
$env:ULTRALYTICS_AUTOINSTALL = "False"
$env:WANDB_DISABLED = "true"
$env:PYTHONPATH = "experiments"
python experiments/lot05_j10d_fdi_local_benchmark.py --manifest C:\secure-OPG\manifest.json --checkpoint C:\trusted-weights\best.pt --images-root C:\secure-OPG --authorized-local-evaluation --report C:\secure-OPG\aggregate-report.json
```

Install pinned dependencies in an isolated environment, run without network, verify model hash and source provenance before executing third-party `.pt` (PyTorch pickle loading itself has code-execution risk). Never commit patient paths/manifest/images, weight binaries or reports with identifiers. **No recording of diagnosis or dental acts** in the benchmark.

### Alternative: deterministic fixtures or offline predictions without image loading

```json
{
  "schema": "digital-crown-fdi-predictions-v1",
  "predictions": {
    "opaque-case-001": [
      {"fdi": "36", "bbox": [10, 10, 60, 60], "confidence": 0.90},
      {"fdi": "36", "bbox": [70, 10, 120, 60], "confidence": 0.80}
    ]
  }
}
```

The example intentionally misnumbers tooth 37 as 36. The evaluator counts this as **correctly localized but incorrectly numbered, with a neighboring FDI error and duplicate FDI**, not as a correct hit. Run:

```bash
PYTHONPATH=experiments python experiments/lot05_j10d_fdi_local_benchmark.py --manifest /local/manifest.json --predictions /local/predictions.json --report /local/aggregates.json
```

### Metrics and decision criteria

- One-to-one IoU ≥0.50 association irrespective of FDI code, then **separate** localization recall, FDI-correct recall, FDI accuracy among localized teeth, precision of correctly numbered proposals, unlocalized GT, FP suggestions, neighboring-tooth swaps, duplicate FDI labels and exact-panorama fraction.
- Bootstrap 95% interval sampled **by image**, not by tooth; informative only for a sufficiently large, truly representative and independent cohort. Subgroups with fewer than five films are suppressed to avoid misleading small-sample percentages.
- Preregister study cohort inclusion/exclusion, reference annotation by licensed readers and adjudication, source and duplicate audit, acquisition devices/sites, reference accuracy, difficult cases (missing teeth, root remnants, mixed dentition, implants, overlapping arches, motion artefacts), confidence/NMS and FDI-correctness thresholds before examining output. Do not calibrate threshold on held-out test data.
- **GO for clinician-correctable suggestions** requires satisfactory real cross-site FDI behavior and safe manual correction; do not promise « quelle que soit la radiopanoramique ». Incorrect numbering must never silently create an act or change a patient's records. No clinical/Windows release based only on an author mAP or these unit tests.
- **Current status:** technical model checkpoint and synthetic evaluation contract PASS where CI recorded; independent FDI real-image cohort **OPEN**; legal reuse/commercial distribution **OPEN**, Windows ONNX/CPU **OPEN**, clinician validation and FUE **OPEN**. All reservations in `techdoubt.md`.

**Next within LOT05/05.7-J10D**: obtain an authorized and genuinely disjoint annotated OdontoAI/InReDD dataset locally; audit group-level duplicates and labels; run benchmark wholly offline; review examples with clinician, freeze acceptance limits; then plan FDI safe ONNX export and future separate UI act-picker sublot. PR #1006 remains DRAFT; PR #1004 untouched.
