# Digital Crown CEPH PDF Premium V2 — Benchmark and safe design implementation
**2026-10-23 — owner requested to examine competitors' orthodontic reports and improve ours. DRAFT, no merge/deployment.**

## Actual audited starting point
The [FUE-P2 #1046](https://github.com/hraaaaf/Digital_crown/pull/1046) genuine synthetic-only study `#4 / rev 2` generated an **eight-page WeasyPrint report** titled `Bilan orthodontique`, contract `CEPHALO_PDF_PROJECTION_V1`. The output includes a five-column per-measurement table (measurement/result/full method/source/calibration) spanning five pages; Steiner and Tweed/Merrifield protocol analyses; R11→R14 BLOCKED statuses; nine global blockers. It repeats long machine IDs and expands raw evidence in the same grid as clinician-readable values; images are not presented. The user reviewed the PDF, asked for improved design. **Original PDF remains the historical evidence and is not altered**.

Extraction of that *specific PDF* yielded **63 printed named measurement rows** (44 available, 19 not computable) while R11 text says **66 typed measures active**. These are different reported quantities; do not silently declare equivalence. Some table rows are split across A4 pages. The prototype user-facing 5-page visual PDF uses 63 named printed rows; it is a mock of the actual data **not identical to the production template**.

## Competitive references, features not clinical authority

- [CephX — Download analysis UI (2026)](https://help.cephx.com/en/articles/15690869-download-analysis-new-ui): radiograph + measurements on a common preview screen, choose specific report modules, optional logo/practitioner name and multiple export formats. Design implication: separate a 1-page overview from selected analyses and dense evidence appendix.
- [Diagnocat — Orthodontic Report](https://diagnocat.com/za/products/orthodontic-report): strong image+measurement visual association, print-friendly layout and approachable report. Product is CBCT/3D; its specific modalities and clinical claims **are not transferred** to DC 2D.
- [WebCeph](https://webceph.com/en/pricing/): reference/norm tables and graphical deviations; chart inspiration is useful, but **never reproduce severity colours or diagnosis based on non-source-locked modern norms**.
- [AudaxCeph](https://www.audaxceph.com/): visual anatomy/tracing and related layer controls. The trace can only appear in our PDF if it is **bound to the same study/revision and has explicit source provenance**; never insert screenshot of an arbitrary patient.
- [Dolphin official Imaging brochure](https://www.dolphinimaging.com/Areas/Product/Documents/Imaging/ImagingBrochure.pdf): cephalometric norms with bibliography, multiple analyses, overlays, print/measure; this is feature context, not evidence of our clinical equivalence.

## Delivered V2 direction

**Local five-page design mock in conversation** with Digital Crown navy/teal identity: (1) 1-page hierarchy and synthetic-phantom screenshot clearly identified, plus raw metric cards; (2) Steiner/Tweed reference tables without diagnosis; (3) angular appendix; (4) linear appendix; (5) R11–R14 and blockers. **Only original synthetic data, no invented therapeutic interpretation or norm status.** This is NOT an approved production final.

**GitHub implementation DRAFT** changes the actual authoritative HTML/Jinja WeasyPrint template `backend/templates/bilan_ortho_authoritative.html` only, plus safety tests/workflow:
- Navy hero, document state, case study/revision provenance, branded footer, stronger typography and white space;
- measurement dashboard counts from actual `measurements` context (don't mix with backend typed-active count);
- three-column measurement table with method, source, calibration **still visible on every line**; no loss of source fields;
- clearer compact Steiner/Tweed protocol tables; retains interpretation status and strict original source-lock/norm caveats;
- R11→R14 stages and ALL original blockers unchanged and readable;
- safety state colours communicate document availability only, **not healthy/pathological or severity**;
- no actual cephalogram photo added to product render until the image's identity/revision and storage permission can be independently source-bound. The local mock uses an explicitly synthetic phantom ONLY; DO NOT generalize the mock screenshot into production.

## Tests and gates

`tests/test_cephalo_premium_pdf_v2_contract.py` checks template compilation/escaping, untrusted fields, all original source/method/calibration metadata, missing statuses, stage/blocker preservation and historical-only refs. [Exact-head workflow](../.github/workflows/ceph-pdf-premium-v2.yml) renders a tiny **synthetic-only** PDF via WeasyPrint as a smoke test.

No math, source registry, model, patient data, DB, storage, API, inference, FACAD vendor, deployments or master changed. `CEPH_DETECTOR_SELECTED=NO`, 6 Ricketts HOLD, **CLINICAL NO-GO**, roadmap **41/99**. Actual full production PDF should be re-tested on a nonhuman T2 fixture **after review**; no claim of real patient approval or printed vendor equivalent.

**Follow-up after this template PR**: independent visual audit of exact HTML renderer, automated paper/PDF regression, authenticated preview/download with study/revision response headers, accessibility of narrative/context, French hyphenation; only then consider staged safe merge. A report's nicer design must never imply clinical accuracy.
