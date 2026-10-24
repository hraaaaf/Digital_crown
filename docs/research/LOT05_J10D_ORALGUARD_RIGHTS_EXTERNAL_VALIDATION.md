# LOT05 / 05.7-J10D — OralGuard rights clearance & independent panoramic validation (DRAFT)

**Date / checked_at:** 2026-10-22  
**Status:** RESEARCH ONLY / OPEN / NO-GO FOR CLINICAL RELEASE  
**Target product:** Digital Crown V1.5, offline on-premise Windows dental-clinic software, closed-source distribution in Morocco.  
**Scope:** this existing LOT05/05.7-J10D panoramic candidate only. No change to runtime, weights, diagnosis, installer, PR #1004, merge, or deployment.  
**Reference PRs:** [#1004](https://github.com/hraaaaf/Digital_crown/pull/1004) `6910cceed8b7dd166bcbc0c4f78293f29dcc4808` (keep untouched); [#1006](https://github.com/hraaaaf/Digital_crown/pull/1006) research experiment, predecessor `a2a376fc9f1983c2f84d35863e149c655f65f171`.  
**Related risk register:** `techdoubt.md`, LOT05/05.7-J10D OralGuard blocks.

## 1. Verified evidence vs unresolved permissions

| Layer | Primary source and observed statement | Result / action |
|---|---|---|
| OralGuard weights | [Model card](https://huggingface.co/Enosh729/oralguard) says MIT; YOLOv8m detector; source [DrEnosh/Oral_guard](https://github.com/DrEnosh/Oral_guard) README claims MIT, references a LICENSE file; direct GitHub contents lookup of `LICENSE` on `main` returned 404 on 2026-10-22. | **UNKNOWN:** author authority to sublicense these particular weights, including derivatives. MIT label alone is not a chain-of-title. Seek signed clarification from author. |
| Ultralytics YOLOv8m | [Ultralytics official licensing](https://www.ultralytics.com/license) says AGPL-3.0 by default for its trained models and Enterprise for embedding YOLO/custom-trained models in closed-source commercial products; review actual current contract, not merely marketing FAQs. | **OPEN/BLOCKER:** confirm license rights for training, weights, exported ONNX, offline on-prem end-customer distribution and number of cabinets. A direct agreement/qualified legal opinion is required before packaging. |
| Official DENTEX | [DENTEX team repository](https://github.com/ibrahimethemhamamci/DENTEX) and [official HF dataset](https://huggingface.co/datasets/ibrahimhamamci/DENTEX) explicitly advertise **CC BY-NC-SA 4.0** for *data*, MIT for repository code. | **OPEN/BLOCKER:** clarify whether a commercial model based on the specific original training copies needs additional authorization, and obtain rights covering use and any necessary redistribution. Copyright consequences for trained weights are fact-/jurisdiction-specific; do **not** automatically assert every weight is legally a derivative of the dataset. |
| Third-party reformatted DENTEX | [tirandazdylan/dentex-panoramic](https://huggingface.co/datasets/tirandazdylan/dentex-panoramic) declares **CC BY 4.0**, states it re-encoded **DENTEX public training_data.zip** from [Zenodo 7812323](https://zenodo.org/records/7812323); its `diagnosis/test` split is a **new derived split**, not original challenge blinded test. | **CONFLICT:** uploader's CC BY label is not proof the original copyright owner authorized a license change. Obtain original record/license text and the DENTEX owner statement, including any historical dual licensing. Zenodo license field was not reliably retrieved in this review; do not resolve by assumption. |
| Other OralGuard training sources | [Author README](https://github.com/DrEnosh/Oral_guard/blob/main/README.md) additionally lists Kaggle teeth segmentation, cavity, adult caries and pediatric panoramic datasets, and model/segmenter/classifier components. | **UNKNOWN:** which exact datasets/splits/weights were used for `oralguard_det_best.pt` (as opposed to other pipeline stages). Ask for complete detector-only provenance and authorization of each actual contributor. |
| Moroccan legal classification | [Loi 84-12 (official ministry)](https://www.sante.gov.ma/Reglementation/REGLEMENTATIONAPPLICABLEAUPRODUITSDESANTE/84-12.pdf) and [ministry regulations index](https://www.sante.gov.ma/Reglementation/Pages/REGLEMENTATION-APPLICABLE-AU-PRODUITS-DE-SANTE.aspx), including Decree 2-14-607. | **CONDITIONAL:** intended-use/function-specific Moroccan regulatory classification and required authorizations remain to be determined by qualified counsel and competent authority; documentation here is NOT medical-device certification. |
| Personal data / patients | Digital Crown local-first contract; Moroccan data-protection obligations (Loi 09-08 / CNDP, as applicable). | Written site permission/ethics and privacy assessment needed before obtaining or processing clinical films. No patient data in public CI, Hugging Face, GitHub, logs or AI prompts. |

**Important distinction:** Legal reuse of research data, compliance with model code/framework licenses, permission to redistribute exported weights, and regulatory authorization to market clinical software are **four separate questions**. Do not treat a single MIT badge or a successful ONNX conversion as satisfying any other question.

### Written-clearance checklist (retain signed/documented answers)

- Identify legal owner of the **specific** pinned detector `Enosh729/oralguard`, HF revision `06b2a3c390a6caca640e6c6f74f73017e0c5a17b`, original `oralguard_det_best.pt` SHA-256 `c3303656e72ede3f3d3229e58b2da276448fa204046d3e7a11e13f4d77bc723a`.
- Obtain detector-only data lineage: originating institution/record/dataset version, exact image IDs/manifests and split criteria, train/validation/test overlaps and near-duplicates, use of pretrained weights and third-party pipelines.
- Obtain permission or a well-supported legal opinion covering **commercial training-derived model reuse, ONNX conversion, reproduction, on-prem installer redistribution in Morocco, per-cabinet installation, and updates**; identify any required attribution/source disclosure, sublicensing or payment.
- Resolve DENTEX Zenodo vs canonical HF/GitHub licensing ambiguity with an authorized original rightsholder; resolve each other contributor relevant to this weight.
- Evaluate Ultralytics terms for actual commercial use and chain-of-title through original model author, not by assuming an Ultralytics agreement retroactively cures unrelated dataset restrictions.
- Separately document Moroccan intended purpose, qualification/classification and any applicable data/ethical/marketing approvals.

### Enquiry templates — drafts only, not sent

**To OralGuard author** — Subject: Rights and training provenance of OralGuard detector for offline Moroccan dental software

> We are evaluating your pinned `oralguard_det_best.pt` checkpoint (revision `06b2a3c390a6caca640e6c6f74f73017e0c5a17b`) for potential offline, closed-source, commercial on-prem dental-clinic use in Morocco. We are not currently deploying it. Could you please identify who owns and may license these detector weights, the exact train/validation/test image and dataset sources (including DENTEX/Kaggle and any pretrained Ultralytics weights), evidence of train/test patient separation, and applicable code/model/data licenses? The model card advertises MIT but your GitHub README's LICENSE reference currently returns 404; can you provide the binding license and clarify whether redistribution as exported ONNX inside a commercial Windows installer is explicitly authorized, including transfer of any upstream rights? A written statement and provenance manifest would help us assess eligibility.

**To DENTEX maintainers/rightsholders** — Subject: Clarification of DENTEX training dataset permissions for commercial model

> We need an authoritative clarification regarding DENTEX 2023 data in the official Hugging Face/GitHub publication (CC BY-NC-SA 4.0), the Zenodo 7812323 training_data.zip record, and the third-party reformatted `tirandazdylan/dentex-panoramic` (CC BY 4.0). Which permissions govern the exact original films and their re-encodings, including any historical multiple licensing? Does your organization offer written authorization for commercial use of the data to train or exploit an offline dental pathology model for Moroccan private clinics, and what privacy/site or downstream-distribution constraints apply? Please identify the authorized licensing contact and evidence.

**To Ultralytics** — Subject: Enterprise license scope — YOLOv8m third-party checkpoint exported ONNX, offline clinics

> Please clarify required Enterprise licensing, scope and price for a proprietary dental Windows on-premise product used at independent Moroccan clinics. The candidate is a third-party YOLOv8m-trained checkpoint, later exported to ONNX with CPU execution; no Ultralytics cloud service is used. Does the agreement cover the particular derived weights, embedding/redistribution to multiple independent customers, offline inference, developer/CI research, future upgrades and model conversions? What evidence of upstream author authorization is still required and what terms/fees apply by clinic or installation?

## 2. External clinical evaluation protocol (DRAFT for clinician/statistician/ethics approval)

**Objective:** estimate external, patient-independent performance and safety of the **four-class detector**, not claim an autonomous dental diagnosis or clinically reliable FDI identification.

### 2.1 Intended use and cohort (freeze before recruitment)

- **Intended-use draft:** offline candidate assists a licensed dentist by **highlighting possible radiographic findings** on panoramic dental X-rays; dentist must confirm/deny. Findings are not diagnosis; non-detection is not absence; confidence is not probability of disease.
- Start with **adult permanent-dentition panoramic studies** of variable devices/quality; explicit exclusions (mixed dentition, pediatric, limited fields, major artefact, post-op, severe anatomical distortion) must be stated and counted before enrollment, not silently dropped. Widen scope only after separate evidence.
- Obtain lawful, de-identified films from **at least three genuinely independent clinical sites**, none sourced from public DENTEX/author's train or validation material. Separate a consecutive, prevalence-reflective cohort and a *clearly labeled* enriched rare-lesion cohort for precision assessment.
- Planning **targets**, not statistically powered sample sizes or clinical approval thresholds: aim for 400+ unique-patient panoramics across sites and, where feasible, 100+ **distinct positive patients per class**, plus sufficient confirmed-negative films. A qualified clinical statistician must calculate final requirements from desired confidence interval width, prevalence, cluster structure and intended purpose **before** data collection; expand target where class rarity or subgroup uncertainty demands.
- Independent annotation by **two blinded qualified dental radiology/clinical readers**, discrepancies resolved by a designated third adjudicator; record calibration set outside final cohort, inter-reader disagreement, radiographic-only uncertainty, and when additional bitewing/periapical images or clinical records are necessary to establish a defensible reference. Do not force uncertain cases into false definitive GT; classify indeterminate and report.
- No access to predictions during annotation; no access to reference labels by model developers before freeze. Blind source/patient IDs; check cryptographic hashes and perceptual hashes against known DENTEX/OralGuard **training manifests if obtained** and published datasets. Absence of manifests prevents a high-confidence independence claim, even if local hashes do not match.

### 2.2 Locked detector and prespecified evaluation

- Pin exact weights/ONNX SHA-256, software packages, preprocessing (DICOM/JPEG/PNG normalization, orientation, letterbox, 1024px), postprocessing/NMS IoU, class index-to-clinical-label map, confidence threshold and hardware before the external test. Choose/lock confidence on a **distinct calibration cohort**, not the final holdout. Threshold 0.25 is a prior exploratory setting **not a clinical default**.
- OralGuard indices: `0 caries, 1 deep_caries, 2 periapical_lesion, 3 impacted_tooth`; Digital Crown SOTA historical indices: `0 Caries, 1 Deep Caries, 2 Impacted, 3 Periapical Lesion`. A future integration must require explicit immutable schema validation and fail closed on missing, duplicated, permuted or unknown metadata. No direct replacement of `panoramic_model.onnx`.
- Independent clinical oracle: bounding-box matching one-to-one on the **same pathology class** at prespecified IoU >= 0.50; present sensitivity and positive predictive value **per class** with appropriate patient-clustered 95% confidence intervals. Report FP per image, FN per patient, confusion matrix, case/teeth/lesion-level metrics where valid, failure-to-read rate, patient-level completely missed lesions, and decision implications.
- Prespecify subgroup breakdown (site, acquisition vendor, image quality, age groups actually included, restoration/implant artefact, lesion severity, edentulous regions), minimum subgroup support and confidence intervals; report uncertainty/unknown rather than a pass for underpowered strata. Distinguish lesion localization from confirmed disease diagnosis, especially for early/deep caries on panoramic images.
- Analyze clinician-only vs clinician-assisted utility in a separate ethically approved, randomized/crossover **reader study** if the marketed intended use claims clinical benefit. Independent lesion localization alone does not establish that benefit. Use [STARD-AI 2025](https://www.nature.com/articles/s41591-025-03953-8) for reporting transparency and [IMDRF N41 (2017)](https://www.imdrf.org/documents/software-medical-device-samd-clinical-evaluation) for relevant analytical / clinical evidence concepts (not automatically Moroccan legal requirements).

### 2.3 Gates and STOP rules

| Gate | Necessary proof before advancing |
|---|---|
| R1 — Provenance and licence | All three rights layers (model author, DENTEX and other training data, Ultralytics) supported by reviewable written documents for the **actual intended commercial deployment**. If unresolved: commercial integration **NO-GO**. |
| R2 — Privacy and ethics | Site data-sharing/ethics/legal-basis approval, de-identification check incl. DICOM metadata and pixels, secure local dataset boundary, no patient film to cloud/CI, incident and retention policy. No transfer before clearance. |
| R3 — Independent holdout | Signed protocol, frozen cohort IDs and selection, patient/site independence and leakage audit, sufficient per-class cases, blinded expert reference. Lack of train manifests marked UNKNOWN (not silently PASS). |
| R4 — Clinical evidence | Prespecified metrics including patient-clustered 95% CI and adverse-error review. **Provisional decision rule** only: no clinically significant unreviewed harm scenario; clinician/regulatory owner must set **numerical minimum sensitivity, acceptable FP burden and statistical confidence bounds before opening the test set**. Do not invent or retro-fit a universal medical cutoff. |
| R5 — Software safety | Explicit class mapping, output shape and names contracts, sample by class, permuted-label negative tests, per-class end-to-end ONNX preprocessing+NMS parity on lawful nonpatient/synthetic and later clinical test images, FDI not guessed; fail-closed empty/manual path for missing/corrupt/unlicensed weights. |
| R6 — Offline Windows | Isolated clean Windows x64 install, multiple CPU profiles and memory limits, shutdown/restart, bad-image paths, rollback, hash-pinned bundle, 390/430/768/1280 UI review **if affected UI exists**, case/no-diagnosis UX, clinician acknowledgement; no exposure to real patients before approvals. |
| R7 — Human release | Clinical expert and legal/regulatory review of specific product, independent scientific assessment, exact-HEAD CI/FUE and immutable asset build evidence; explicit owner authorization for merge/install/release. Green research CI is insufficient. |

**GO/NO-GO today:** NO-GO. No independent external cohort, permissions, accepted numeric clinical thresholds, production class mapping or Windows validation.  
**Next exact:** obtain written answers to the three inquiry templates; authorize *only a data-free protocol review* until lawful sites are ready. If rights impossible, stop trying to integrate this weight and assess an independently licensed alternative within the same lot.  
**Evidence discipline:** preserve source URLs, versions, SHA, audit scripts, registered protocol, blinded case count, reviewer signatures, leakage checks and exact software state. No experimental metric advertised as patient-level sensitivity.

## 3. Sources and update triggers

1. [OralGuard model card](https://huggingface.co/Enosh729/oralguard) — checked 2026-10-22; refresh on new weight/version/license.
2. [OralGuard author repository](https://github.com/DrEnosh/Oral_guard), README/license lookup — checked 2026-10-22; refresh if LICENSE appears or provenance supplied.
3. [DENTEX original GitHub](https://github.com/ibrahimethemhamamci/DENTEX) and [original HF](https://huggingface.co/datasets/ibrahimhamamci/DENTEX) — checked 2026-10-22; refresh after rightsholder response.
4. [Third-party reformatted DENTEX](https://huggingface.co/datasets/tirandazdylan/dentex-panoramic) and [original Zenodo](https://zenodo.org/records/7812323) — checked 2026-10-22; resolve historic/license uncertainty directly with owner.
5. [Ultralytics licensing](https://www.ultralytics.com/license) — checked 2026-10-22; rely on **actual executed license** for a commercial GO.
6. [STARD-AI reporting guideline](https://www.nature.com/articles/s41591-025-03953-8), 2025 guideline with 2026 correction; [IMDRF N41](https://www.imdrf.org/documents/software-medical-device-samd-clinical-evaluation) — checked 2026-10-22, research/reporting benchmark only.
7. [Ministry Moroccan device law/regs](https://www.sante.gov.ma/Reglementation/Pages/REGLEMENTATION-APPLICABLE-AU-PRODUITS-DE-SANTE.aspx) — checked 2026-10-22, applicability is conditional.

**This document is a draft validation and rights-clearance plan, not a legal opinion, clinical validation, a software certification, or an authorization to process patient data.**
