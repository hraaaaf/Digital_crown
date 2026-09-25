# V1-07 G4 — Panoramic report target

Status: IMPLEMENTATION TARGET

## Goal
Produce a professional, deterministic panoramic radiography report from practitioner-validated observations without inventing normality, diagnosis, treatment, indication, comparison, or unrecorded anatomy.

## Evidence basis
- RSNA structured-report guidance: standard radiology sections separate technique, findings/observations, and impression/synthesis; findings should stay concise, factual, and non-redundant.
- Dental radiography guidance (clinical evaluation): every exposure outcome must be clinically evaluated and recorded with enough information for later audit; a full radiology report is not always required, but relevant findings must be documented.

## Target structure
1. TECHNIQUE
   - panoramic digital radiograph;
   - explicit boundary: only practitioner-validated observations are rendered.
2. OBSERVATIONS
   - grouped deterministically by documented domain: dento-alveolar, periodontal, prosthetic/implant, adjacent structures, and general findings;
   - tooth-specific phrasing in FDI notation;
   - no automatic declaration of normality for unannotated regions.
3. SYNTHÈSE
   - concise restatement of the documented observations only;
   - no treatment plan, billing act, differential diagnosis, or unsupported recommendation.
4. TRACEABILITY
   - QR described only as document/reference verification unless a real cryptographic signature is proved;
   - clinician identity shown as associated practitioner, not as a digitally signed report unless a signature event exists.

## Success
- deterministic output for identical inputs;
- no unsupported normality claim;
- no treatment/CCAM recommendation;
- no false cryptographic-signature or specialty claim;
- all manual findings preserved;
- empty input remains explicitly non-evaluable rather than normal;
- existing PDF pipeline still parses report sections.

## Proof
- backend semantic contract tests;
- PDF presentation tests;
- exact-head G4 panoramic browser action at 390x844 and 1280x900;
- no horizontal overflow and no runtime/page/HTTP5xx errors.


## Evidence expansion — reporting corpus / assets

External evidence review identified a directly relevant 2026 hospital study of 50 dental panoramic images comparing narrative reports with structured reports produced by a board-certified dentist. Its panoramic structured-report template explicitly covers dental anomalies, restorations, carious lesions, periodontal structures, apical changes, jawbone, temporomandibular joints and paranasal sinuses. The published example also records examination quality/assessability, teeth present by quadrant, restorations/crowns, caries by tooth/surface, periodontal bone loss, jawbone, TMJ and paranasal sinuses.

Additional public panoramic datasets support the finding ontology but are not treated as report-text corpora:
- Tufts Dental Database: 1,000 panoramic radiographs with expert abnormality/tooth labels and radiologist eye-tracking/think-aloud expertise.
- 2024 radiologist-labelled dataset: 936 panoramic radiographs / 23,619 annotations covering tooth numbering and dental conditions.
- 2026 multi-focus dataset: 8,655 images / 30,186 pixel-level lesion annotations.

### Engine design derived from evidence
The Digital Crown engine should be a deterministic decision-tree/text-module compiler, not an LLM narrator. Internal canonical fields should cover:
1. examination context / clinical question when explicitly entered;
2. image quality and assessability;
3. dentition / teeth present or missing in FDI notation;
4. restorations and prosthetic/implant status;
5. caries and tooth-level abnormalities;
6. endodontic / periapical findings;
7. periodontium / alveolar bone;
8. jawbone;
9. TMJ;
10. paranasal/maxillary sinuses;
11. free practitioner annotations;
12. concise synthesis generated only from documented findings.

No section may infer normality merely from an absent annotation. Normal findings require an explicit practitioner-confirmed normal state. Image-derived tooth detection may populate location/inventory support only within its validated capability; it must not create diagnoses.

### Gap against current engine
Current engine already covers many tooth-level findings, periodontium, prosthetics/implants and some sinus/TMJ findings, but it does not yet model explicit image-quality/assessability, clinical question, jawbone as its own domain, or explicit practitioner-confirmed normal states. These gaps must be closed before final Panoramic certification.


## Implemented deterministic core — 2026-09-22

Implemented on the G4 branch:
- canonical 8-domain ontology: dental anomalies, restorations/prostheses/implants, caries, apical/endodontic, periodontium, jawbone, TMJ, sinuses;
- optional clinical question and explicit image-quality/assessability state;
- per-domain state is exactly one of `not_assessed | normal | abnormal`;
- negative/normal wording is emitted only for an explicit practitioner-confirmed `normal` state;
- missing domains remain explicitly non-assessed;
- abnormal free text is preserved verbatim at the domain level;
- report context is persisted inside the panoramic analysis evidence payload;
- output sections now mirror the structured-report corpus domains instead of internal dental-specialty UI categories;
- terminology guardrails keep radiographic signs below unsupported histologic/clinical diagnoses:
  - periapical finding -> radiolucent periapical image, not cyst/granuloma;
  - peri-implant finding -> peri-implant bone loss, not automatic peri-implantitis;
  - condylar finding -> osseous remodeling, not automatic TMJ arthrosis;
  - generalized periodontal radiographic loss -> bone-loss wording, not automatic periodontitis diagnosis.

The UI decision-tree is intentionally not changed in this backend lot; exposing these structured fields visually requires its own BEFORE/AFTER responsive evidence pass.
