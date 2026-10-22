# Digital Crown LOT05 / 05.7-J10D — Panoramic FDI Tooth Localization Goal (2026-10-22)

**DECISION SUPERSEDES previous OralGuard-as-target recommendation.** Owner clarified the actual goal: detect/position **all visible teeth with correct FDI numbers** on panoramic images. Pathology detection, caries, periapical alerts, automatic diagnoses and automatic clinical act selection are **not required** by the model. OralGuard's four-class pathology checkpoint was built for the wrong task. **Research remains Draft/NO-GO on cabinet installation**, but engineering effort is now directed exclusively to the tooth-numbering component.

## 1. Target UX / requirements boundary

1. Clinician opens a patient panoramic X-ray in Digital Crown's local-first viewer. The detector proposes a **clickable tooth region and FDI number** (11-18, 21-28, 31-38, 41-48) for each visible permanent tooth; it must tolerate that some teeth are absent and number them **without shifting subsequent teeth**.
2. The clinician may drag/correct a region, change the FDI number, add a missed tooth, suppress a wrong proposal, or simply position a tooth manually if the model fails. The UI distinguishes **model suggestion** from **clinician-confirmed** anatomy.
3. Clicking a confirmed tooth opens a **manual act-picker by speciality** (e.g. conservative, endodontics, periodontology, surgery, prosthodontics, orthodontics). Only the clinician assigns an act. The model is **never** asked to infer caries, choose a procedure, prescribe or assign treatment.
4. An act not in the catalogue can be added explicitly by an authorized user, with unique local ID, specialty, label, optional description, provenance, and duplicate check; the local catalogue must persist through application restart and backup/restore, without affecting historical treatment records. Distinguish catalogue definitions from patient tooth records and chosen procedures; do not mutate global terminology automatically when a user types a free-text one-off patient note.
5. Do not hard-code the tooth count to 32: restorations, edentulism, nonstandard anatomy, implants, missing third molars, and overlapping/rotated teeth must be handled by explicit uncertainty and manual corrections. Primary/mixed dentition would require separate model support (FDI 51–85) and **is not silently supported** by the 32-class adult model.
6. Store the image and all annotation/correction data **on premise only**, honoring Digital Crown's RBAC and audit trail. No patient image to GitHub CI, external model demo, Hugging Face, or online research tools.

**In-scope now:** find and technically probe a real FDI numbering weight, pin source + checksum, test synthetic class mapping/negative paths and establish independent validation plan. **Out of scope this experimental PR:** patient DB migration, act dictionary implementation, new production UI/workflow, cabinet installation, retail distribution, Vercel and PR merge. They are downstream sub-lots subject to their own authorization and FUE.

## 2. Candidate evidence matrix

| Candidate | Actual task and availability | Observations and limits | Decision |
|---|---|---|---|
| [miquic/app-odonto-fdi-yolov8s](https://huggingface.co/miquic/app-odonto-fdi-yolov8s) | YOLOv8s, **32 tooth FDI classes**, explicitly trained on DENTEX `quadrant_enumeration`; publicly listed HF model. Class metadata 0→11, ... 31→48 per author card. | Author-reported mAP50 **0.930**, mAP50-95 **0.557** on **94 internal holdout radiographs**; **91.7% of numbering errors are neighboring-tooth swaps**, not a 91.7% overall error rate. This mAP is NOT percentage of correctly numbered teeth nor externally validated ability on every panorama. Model/dataset CC BY-NC-SA 4.0 (non-commercial). Weight filename and SHA unconfirmed until GitHub experimental run. | **PRIMARY RESEARCH CANDIDATE** for exact FDI goal; synthetic CPU checkpoint test in `lot05-j10d-fdi-tooth-probe.yml`. NO clinical/release readiness claim. |
| [abychkov/dental-fdi-detection](https://huggingface.co/abychkov/dental-fdi-detection) | ONNX FDI tooth proposal model, stated 32 labels; author claims 4k+ images, CPU timings. | Claims unverified by us; proprietary license expressly excludes clinical/commercial and redistribution; reports reference study, not independently established generalization. | Research comparator only with permission; not chosen for redistribution. |
| [zephinax/dental-cnn-segmentation](https://github.com/Zephinax/dental-cnn-segmentation) | Existing YOLO tooth detection/segmentation ONNX weights + `assign_fdi_numbers` algorithm in `src/utils/fdi.py`. | Segmentation/detection vs **learned 32-class FDI** differs: numbering uses separate positional postprocessing, at risk with missing/rotated/overlapping dentition; impressive reported detection mAP cannot certify FDI numbering. | BACKUP candidate for box localization if direct FDI not robust; all FDI proposals need review. |
| [OralGuard](https://huggingface.co/Enosh729/oralguard) | Four **pathology** labels only: caries/deep/periapical/impacted. | Does not enumerate healthy teeth. Built-in FDI based on geometry is a heuristic. Prior 76.4% lesion recall is irrelevant to this goal. | **REJECTED FOR CURRENT TASK**; previous work retained only as historic research, not the selected model. |

Relevant primary sources: [official DENTEX](https://github.com/ibrahimethemhamamci/DENTEX) offers quadrant+enumeration annotations (distinct from abnormal tooth diagnosis annotations); [miquic model card](https://huggingface.co/miquic/app-odonto-fdi-yolov8s); [abychkov license](https://huggingface.co/abychkov/dental-fdi-detection/blob/main/LICENSE); [zephinax inference](https://github.com/Zephinax/dental-cnn-segmentation/blob/main/src/pipeline/inference.py).

## 3. Interface contract (proposed; NOT implemented)

```json
{
  "image_id": "LOCAL_ID_ONLY",
  "model_id": "miquic/app-odonto-fdi-yolov8s",
  "model_sha256": "MUST_BE_PINNED_AFTER_TEST",
  "mode": "EXPERIMENTAL_FDI_SUGGESTIONS",
  "teeth": [
    {
      "annotation_id": "local-uuid",
      "bbox_xyxy": [100.0, 300.0, 170.0, 430.0],
      "proposed_fdi": "36",
      "confidence_uncalibrated": 0.93,
      "clinician_confirmed_fdi": null,
      "status": "SUGGESTED"
    }
  ]
}
```

The sample payload is **synthetic documentation**, not a model prediction. The `status` must stay `SUGGESTED` until clinician action; no global automatic clinical commitment. Duplicate proposed FDI labels, uncertain geometry, inverted panoramics and missing teeth must trigger explicit review, not a forced sorted reassignment.

The downstream act-picker contract is **separate** from the image model: `tooth_annotation_id + confirmed_fdi + specialty_id + act_definition_id`; act catalogue has its own controlled CRUD/role boundary. Persist act definitions in cabinet-local storage only. Reject mutation of past patient acts when a dictionary label changes.

## 4. Verification and exit criteria

**FUE-0 for this PR**: GitHub ephemeral CPU job obtains exact model HF commit+SHA, inspects 32 checkpoint class names, executes a synthetic panoramic-like gradient, rejects invalid/swapped FDI names, nonfinite/out-of-image boxes, duplicate proposals require manual review, empty predictions remain manual. No real patient image, no cloud-stored weights artifact.

**External accuracy NOT yet established**: clinically reviewed dataset spanning at least two/three devices/sites and tooth-loss patterns, strict patient/site disjoint from author training, correct count/FDI assignment *per tooth* at fixed IoU and specified confidence, error rates per radiograph, quadrant confusions, missing-tooth shifting, implants, crowding, atypical anatomy, latency Windows CPU and ease/time of manual correction. Thresholds to be frozen BEFORE validation and agreed with dentist; provisional product quality objectives could be per-tooth FDI correctness and high recall, but must be selected based on intended user harm and real data, not author mAP.

**Stop conditions**: checksum/class contract unknown, unsafe swap or forced labels, clinical diagnosis automatically generated, no manual override, patient image escapes local boundary. Weight use for commercial installation still needs applicable rights and regulatory review; owner's tolerance of risk is not a grant of third-party rights.

## 5. Roadmap / status

LOT05 → **05.7-J10D tooth-numbering model discovery** (PRIMARY CANDIDATE FOUND, technical CI OPEN) → external FDI validation → controlled local ONNX / reversible tooth correction UX → manual specialty-act-picker + persistent local catalogue (separate planned implementation gate) → clean Windows offline bundle + FUE → release decision. **V1.5 NO-GO**. PR #1004 is protected and remains separate; PR #1006 Draft, no merge.
