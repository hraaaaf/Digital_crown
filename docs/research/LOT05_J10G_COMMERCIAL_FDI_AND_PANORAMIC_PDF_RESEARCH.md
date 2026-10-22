# Digital Crown — LOT05 / J10G — Commercial-first FDI and panoramic PDF (2026-10-22)

Owner explicitly requires a genuinely commercially usable open-source model with no special license negotiation and a complete annotated panoramic radiology PDF, following model correction.

## Verified research / provenance matrix

- Current 32-class research model miquic/app-odonto-fdi-yolov8s: DENTEX source is **CC BY-NC-SA**, therefore **NO commercial release**. Prior 40-film benchmark: 840/1036 correctly numbered and localized teeth, 3/40 complete panoramics exactly correct. Reference: https://github.com/ibrahimethemhamamci/DENTEX/blob/main/README.md
- Nexedia FDI panoramic detector, YOLO26n, 32 classes, published CC BY 4.0, provider mAP50 94.2%: https://universe.roboflow.com/nexedia/panoramic-dental-xray-fdi-oo2fv . **BLOCKED pending actual model-weight, source-image provenance, and YOLO26 AGPL rights audit**. Provider mAP is not full-film recall.
- Kölüş/Güleç: YOLO model weights listed CC BY 4.0 on Mendeley, 1061 panoramics/29012 annotated teeth: https://data.mendeley.com/datasets/83k2rtz4bc/1 . **BLOCKED** pending inspection of checkpoint FDI class ontology, datasets and upstream YOLO licensing.
- Roboflow panoramic FDI dataset, 32 FDI classes, ~1577 images listed CC BY 4.0: https://universe.roboflow.com/dentalxray-yjztn/panoramic-dental-xray-fdi . **DATA CANDIDATE** only; verify original radiograph ownership, train/val overlap, consent and whether it mirrors NC original sources.
- HITL Teeth Segmentation 598 films/15318 tooth polygons, published CC0 but labels 1–32 not FDI: https://humansintheloop.org/resources/datasets/teeth-segmentation-dataset/ . Verify source-image rights and mapping separately.
- Panoramic Radiography Dataset 3000 images, images/masks/COCO, listed CC BY 4.0: https://datasetcatalog.nlm.nih.gov/dataset?q=0003374872 . Audit FDI support and provenance before training.
- Original DENTEX official source CC BY-NC-SA, even if unauthorized mirrors claim CC BY; reject for commercial training.
- Intraoral SegmentAnyTooth MIT code has separately prohibited commercial WEIGHTS; also wrong imaging modality.

**Legal dependency caveat**: CC BY 4.0 permits commercial usage with attribution (https://creativecommons.org/licenses/by/4.0/), but only for rights the uploader actually controls. Ultralytics expressly says YOLO training/code/architecture/weights require AGPL-3.0 copyleft for closed-source products or separate Enterprise license (https://www.ultralytics.com/license); a model card badge may not waive those rights. Roboflow identifies **RF-DETR Nano-to-Large** (not XL/2XL) as **Apache-2.0** (https://roboflow.com/licensing). Preferred path: verified original data CC BY 4.0/CC0 + audited Apache-2.0 RF-DETR and suitable backbone weights + TRAIN OWN FDI model; independently validate FDI correctness and keep dentist correction mandatory. **No commercially cleared checkpoint has yet been technically established.**

## PDF benchmark and implementation

Diagnocat publishes [a genuine 12-page OPG report specimen](https://diagnocat.com/files/reports/en/radiology/pano.pdf) with patient/exam info, panoramic imaging/FDI chart, tooth-by-tooth clinical findings and doctor signoff. This is a workflow reference only; do not copy copyrighted artwork/templates. 2026 structured panoramic dental reporting study: https://www.frontiersin.org/journals/dental-medicine/articles/10.3389/fdmed.2026.1769864/full .

Digital Crown **already** has a PANORAMIC PDF: authenticated GET /api/ia/panoramic/{analysis_id}/pdf, assert_patient_access and RBAC panoramic, backend/services/generators/panoramic_elite_gen.py, Jinja backend/templates/panoramic_elite.html; frontend PanoramicStudio has preview + download. Do not replace or duplicate these.

**This J10G DRAFT adds**:
1. backend/services/panoramic_fdi_report_rows.py: ONLY manually documented findings in already-persisted analysis.detections_data.manual_anomalies, FDI permanent whitelist, dictionary anomaly labels; never infer status or act.
2. The EXISTING panoramic PDF generator/context and Jinja template are extended with a detailed per-tooth table, conditional on actual clinician manually stored findings. Existing authorized route, image and document controls unchanged.
3. A SEPARATE NOT-PATIENT PDF engine backend/services/generators/fdi_research_pdf.py that can render a complete annotated FDI report using only explicitly confirmed tooth boxes, manually entered observations and acts, clinician-typed summary and reviewer metadata. Use only fictional patient and artificial panoramic for CI artifacts; rejects duplicate/temporary/unconfirmed FDI, automatic act links and bad images, labels every page research-only. No API/DB patient route or model weights.
4. Tests and CI limited to synthetic samples, visual PDF and FAIL closed. Existing clinical PDF is still the authoritative one.

**Not yet delivered**: model commercial readiness, clinician FDI annotation persistence with audit/multiuser RBAC, autoloading suggestions from patient image, immutable signed PDF archival to patient chart, independent clinical certification, production Windows installer. J10G does not activate noncommercial model, rewrite patient records, merge PR or deploy.

**NEXT:** copyright provenance audit → select commercially compatible training data/architecture → train independently owned checkpoint and test Windows ONNX + FDI on held-out images → close real clinician confirmation/database/act catalog + PDF archival under separate clinical safety signoff. V1.5 stays NO-GO.
