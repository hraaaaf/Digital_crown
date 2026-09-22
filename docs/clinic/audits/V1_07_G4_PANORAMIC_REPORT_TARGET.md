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
