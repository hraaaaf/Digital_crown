# LOT05/05.7-J10D — AKUDENTAL FDI local evaluation runbook (2026-10-22)

**Scope**: the panoramic model proposes tooth bounding boxes and FDI identifiers; dentists correct and confirm. No pathology inference, acts catalogue implementation, patient DB updates, Windows release or Vercel. This guide covers offline research only.

## Verified AKUDENTAL facts

Original author repo: https://github.com/melihoz/AKUDENTAL/tree/main/AKUDENTAL . At 2026-10-22 its public tree actually contains images/, annotations/, folds/, yolo_labels/, akudental_instances.json and dataset.yaml. The author's README still describes a forthcoming data release and non-commercial research use. Before downloading, check the upstream data licence and authorized use; readable files alone are not a right to commercial redistribution.

Original AKUDENTAL/dataset.yaml was inspected directly through GitHub: it has **35 classes**. Indices 0-31 represent 32 permanent FDI teeth 11…48, while 32 = Bridge, 33 = Filling - Crown and 34 = Implant. The FDI adapter maps COCO category IDs through category names to avoid false numbering and skips these three non-tooth object classes explicitly. The actual large COCO JSON could not be expanded by the connected text reader, so real-data schema compatibility is **NOT YET VERIFIED**.

Second independent-source candidate: UFBA-425 author repo https://github.com/devichand579/Instance_seg_teeth and Figshare https://doi.org/10.6084/m9.figshare.29827475.v1 . Its published origin differs from DENTEX, but training-data patient/pixel overlap and licence are not independently proven. OdontoAI now requires an academic signed application from an associate/full professor (https://github.com/IvisionLab/MEDIA-datasets); InReDD PAN924 needs PhysioNet credentials plus DUA and contributor review (https://physionet.org/content/inredd-dataset-pan924/1.0.0/). No access bypass.

## Implemented/tested (experimental PR #1006)

- `experiments/lot05_j10d_fdi_akudental_coco_adapter.py`: COCO image/category/annotation to private local evaluation manifest, strict 32 tooth categories plus 3 excluded objects; rejects unknown labels, missing images, malformed boxes and path traversal.
- `experiments/test_lot05_j10d_fdi_akudental_coco_adapter.py`: 14 synthetic tests, including swap 37→36 and source category-index permutation, all PASS in https://github.com/hraaaaf/Digital_crown/actions/runs/39760842972 .
- `.github/workflows/lot05-j10d-akudental-adapter-contract.yml`: FUE-0 synthetic-only CI, no source patient data and no model binaries.
- `experiments/lot05_j10d_fdi_local_benchmark.py`: existing LOCAL 1:1 IoU evaluator for localization + exact FDI recall, adjacent swaps, missing teeth, duplicates, false positives, per-film correctness, film bootstrap and anonymous site/device groups.

## Exact Windows offline research instructions — not executed by this session

Preconditions: authorized non-clinical Windows research workstation, source/rights approval, adequate space, git and Python 3.11 with local CPU torch + ultralytics + OpenCV. DO NOT upload patient images or private manifests to public CI, GitHub or HF.

Download source into a secured directory, optionally via a sparse clone; verify the author source revision before analysis.

```powershell
git clone --depth 1 --filter=blob:none --sparse https://github.com/melihoz/AKUDENTAL.git C:\research\AKUDENTAL-src
cd C:\research\AKUDENTAL-src
git sparse-checkout set AKUDENTAL
```

Use the pinned FDI YOLO model from https://huggingface.co/miquic/app-odonto-fdi-yolov8s at revision `82b4d9a02f9e6f32a746dc17afe681e20e8b99e2`; file `best.pt` size 22,600,746 bytes, SHA256 `533833a4244f092f82bc94a6c2d6fac7e1656c9437994e98d09843c54aafd3f6`. Confirm exact hash **before** loading the PyTorch checkpoint (pickle risk).

```powershell
(Get-FileHash C:\research\trusted-weights\best.pt -Algorithm SHA256).Hash.ToLower()
$env:PYTHONPATH = "experiments"
$env:HF_HUB_OFFLINE = "1"
$env:ULTRALYTICS_AUTOINSTALL = "False"
$env:WANDB_DISABLED = "true"
```

Convert real COCO to private manifest. **Single-line commands** avoid PowerShell continuation ambiguities. Do not put these outputs into the source repo.

```powershell
python experiments/lot05_j10d_fdi_akudental_coco_adapter.py --coco C:\research\AKUDENTAL-src\AKUDENTAL\akudental_instances.json --images-root C:\research\AKUDENTAL-src\AKUDENTAL\images --manifest C:\research-private\fdi-eval\manifest.json --audit-report C:\research-private\fdi-eval\aggregate-audit.json --authorized-local-conversion
python experiments/lot05_j10d_fdi_local_benchmark.py --manifest C:\research-private\fdi-eval\manifest.json --checkpoint C:\research\trusted-weights\best.pt --images-root C:\research\AKUDENTAL-src\AKUDENTAL\images --authorized-local-evaluation --report C:\research-private\fdi-eval\aggregate-report.json
```

**Fail closed** if actual COCO categories or file paths differ; inspect original annotation convention rather than silently mapping. Adult-only model cannot safely name primary teeth FDI 51–85; the converted cases have dentition `unknown` pending reader confirmation.

## Evidence and GO rule

A clinical reader must audit teeth labels/regions, missing teeth and implants, verify study licensing, assess image hash/pHash vs author training manifest, and validate across patient/site/device strata with thresholds locked before interpretation. External test can produce 95% CI by image but doesn't prove independent patients without provenance. No automatic act selection is supported and proposed FDI remains unconfirmed until the dentist corrects/approves.

**Actual outcome here**: GitHub/source tree + category list independently verified; synthetic adapter contract 14/14 PASS. No external image bytes are present on the accessible local container, network/DNS cannot fetch those images, and no private patient data may run in cloud CI. Thus **zero real-image FDI predictions, no measured external accuracy and no clinical release approval**. Preserve this reservation in `techdoubt.md`. PR #1006 DRAFT; PR #1004 untouched; V1.5 NO-GO.
