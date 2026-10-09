# FAC-01 F01.13 — External scientific source retrieval and Ricketts version reconciliation (2026-10-09)

Status: **PRIMARY LITERATURE LOCATED / VENDOR COMPOSITION GAP SPECIFIED / CLINICAL PARITY NOT CERTIFIED**

## Goal and evidence standard

Resolve the actual missing scientific evidence for the Facad 3.14.1.1111 Ricketts family, using original publications, publisher/library records, and **direct Facad editor observations**, not merely nominal factor counts. Preserve all source editions separately. This work is **read-only research** on the Facad branch; no patient analysis, edits, saving, extraction of clinical exports, frontend or backend code, merge or deploy.

The machine-checkable factor reconciliation is
[`FACAD_314_F01_13_RICKETTS_ATLAS_FACAD_COMPOSITION_DIFF_2026-10-09.csv`](data/FACAD_314_F01_13_RICKETTS_ATLAS_FACAD_COMPOSITION_DIFF_2026-10-09.csv):
**33 Atlas complete rows + 12 Atlas summary rows + 1 observed Facad-specific extra row**. This is a *candidate ordinal/semantic alignment*, **not** a validation of formula equivalence.

## Evidence discovered from outside the repository

| ID | Authority, source and stable locator | Exactly established | Cannot establish |
|---|---|---|---|
| S1 | **Facad (Ilexis) official release notes v3.12**, page 2/6, dated internally 2016-10-31: https://www.facad.com/wp/wp-content/uploads/2020/12/FacadReleaseNotes_3.12.pdf | Vendor explicitly names **Ricketts (32 F)** and **Ricketts (13 F)**, and attributes both to Fernández Sánchez & Da Silva Filho (2009); lists Samson adaptation separately | Why Facad differs numerically from Atlas 33/12, exact Facad formulas or edition-level identity |
| S2 | **Facad official release notes v3.5**, p. 3: https://www.facad.com/Download/ReleaseNotes/FacadReleaseNotes_3.5.pdf | Vendor says old Ricketts analysis was renamed **Ricketts Summary** and Ricketts analysis was extended with constructed Xi | Ricketts Summary exact membership or equality to historical 1960/1981 analyses |
| S3 | Fernández Sánchez J, Da Silva Filho OG. **Atlas cefalometría y análisis facial**. Ripano, Madrid 2009, ISBN 9788493675677; catalog https://search.worldcat.org/title/655853982 ; indexed chapter 13 facsimile https://es.slideshare.net/slideshow/analisis-dericketts/239250329 | Book bibliographic identity verified by library catalog; indexed chapter 13 **Cuadro 13.1** enumerates 33 factors and **Cuadro 13.2** presents a 12-factor summary | Facsimile upload is not publisher-authenticated; conflicting angular factor naming and Facad differences require print-edition inspection before scientific promotion |
| S4 | Ricketts RM. **A foundation for cephalometric communication**. *Am J Orthod.* 1960;46(5):330–357. DOI https://doi.org/10.1016/0002-9416(60)90047-6 | Primary publisher abstract specifies **five** communicated measurements in that original 1960 framework | Cannot turn 1960 five-factor framework into Facad 13/32 profile by author-name match |
| S5 | Ricketts RM. **Perspectives in the clinical application of cephalometrics: the first fifty years**. *Angle Orthod.* 1981;51(2):115–150, PMID 6942666, DOI https://doi.org/10.1043/0003-3219(1981)051%3C0115:PITCAO%3E2.0.CO;2 ; original article reproduction https://www.moroortodontia.com.br/leitura/ricketts1981.pdf **PDF p.10 (journal p.124)** | Visually checked the original **11-item** “Cue sheet for Ricketts' summary descriptive analysis” with units and age trends, including interincisal angle | Cannot assume 11-item 1981 summary = Facad Summary, Atlas 12 or vendor 13 |
| S6 | Bae E-J, Kwon H-J, Kwon O-W. **Changes in longitudinal craniofacial growth in subjects with normal occlusions using the Ricketts analysis**. *Korean J Orthod.* 2014;44(2):77–87, DOI https://doi.org/10.4041/kjod.2014.44.2.77 , PMID 24696824 | Peer-reviewed longitudinal data on **31 Korean subjects aged 9–19**; changes vary by age and sex | Does **not** justify direct application of its population-specific norms to Moroccan/French/other clinical patients or to Facad 3.14 implementation |

**Provenance restriction:** S1/S2 official PDF contents were indexed through public web search, but an independent PDF-page fetch was not available in that pass. Verify publisher PDF bytes/pages before asserting stronger document authenticity. S3 chapter content was read from an externally uploaded facsimile, **not a licensed publisher scan**; the 2009 bibliographic record itself is independently catalogued. S5 original-article page 124 was directly reviewed as a PDF screenshot. Do not embed/copy copyrighted whole chapters into this repository.

## Direct observed vendor measurements: evidence by blob SHA

- Facad 3.14.1.1111 **Ricketts (32 F)** UIA transcription: `docs/audits/data/FACAD_314_D1C_RICKETTS32F_EDITOR_MEASUREMENTS_UIA_2026-10-09.csv`, Git blob **`220b4a23d469e1c634ff9d8df7ad22706ae7cc7a`**. 38 UIA rows = 6 headings + **32 factor rows**. Evidence level for every row: `EDITOR_UIA_TRANSCRIPTION_ONLY`.
- Facad 3.14.1.1111 **Ricketts (13 F)** UIA transcription: `docs/audits/data/FACAD_314_D1C_RICKETTS13F_EDITOR_MEASUREMENTS_UIA_2026-10-09.csv`, Git blob **`802df33d3c15cbaba095123f4b2b700689edae44`**. 17 UIA rows = 4 headings + **13 factor rows**. No Save or patient Load.
- Atlas 33 composition already independently inventoried in `docs/audits/CEPHALO_LOT08_RICKETTS_ATLAS2009_COMPLETE33_COMPOSITION_LOCK.md` Git blob **`1dc3419ec9eb7881f18a932228dc2051f06a305f`**.
- Critical source-level conflicting use of **PFH / posterior facial height / total facial height** is not normalized away.

## Five concrete discrepancies identified by factor-by-factor comparison

1. **Atlas complete factor #29 has no observed separate Facad 32F counterpart.** The Atlas 33 list contains an *angular* total facial height entry, associated with approximately **60° ± 3°** in historical tables; none of the 32 measured Facad factors is a separate total-facial-height angle. This is a **capture-level absence**, not definitive proof about all private vendor formulas.
2. **Atlas summary slot #3 vs Facad 13F PFH is a genuine unit/type collision.** Indexed Atlas Cuadro 13.2 describes a factor with **60°** (though its Spanish label itself is ambiguous); Facad editor row #6 `PFH` is `Dist2p(CF, Go)` with literal normal interval **63±3.5**, i.e. a linear factor. **No interchangeability permitted.**
3. **Facad 13F includes a separate InterIncisal row**, `Angle4p(Iia,Ii,Isa,Is)`, row #15, norm literal `130±10`. The indexed Atlas 12-item summary has no corresponding interincisal slot. Do not merely label the vendor 13F “Atlas 12 + 1” because discrepancy #2 is also present.
4. **Facad 32F factor at row #38 uses `Xi–PM'`**, while Atlas complete #33 describes mandibular body length `Xi–Pm`. **Vendor definition recovered and fixed:** the official Facad 3.14.1.1111 `Ricketts (32 F).cph` has `PM' = Intersect(Xi,PM,A,Pog)` — intersection of the `Xi–PM` and `A–Pog` lines. This is a *derived point*, **not** the anatomical `Pm_Ricketts` identity. Evidence: `docs/audits/schemas/ortho_lot08_ricketts32_facad_final_seven_cluster_resolution_v1.json`, Git blob `411d5ba09dd596b2a2fbc3218ddf127c9fce3782`, official CPH SHA256 `d0b442b39ac7db3dc9c46d807cb3c20bd937c69783b096b484872017f9376518`, upstream artifact #11469783515. The unresolved question is *clinical equivalence to the Atlas construction*, not vendor `PM'` semantics. Direct alias forbidden.
5. **Facad 32F row #33 `Cranium ant len`, literal `61±2.5`,** is aligned only as a candidate to the Atlas anterior cranial compression/length entry. Geometry, landmarks, age norms and wording remain to be checked.

Additional vendor facts: 32F includes six section headings; 13F has four headings. These are excluded from factor counts, not silently treated as measurements.

## Scientific decisions — strict fail closed

- **PROVEN_VENDOR_ATTRIBUTION:** Facad calls its own profiles 32F/13F and attributes them to the named 2009 Atlas (S1).
- **PROVEN_BOOK_COMPOSITION_IN_INDEXED_COPY (not publisher authenticated):** Atlas 33 complete and 12 summary slots are documented, supporting meaningful comparison (S3).
- **PROVEN_DIRECT_EDITOR_CONTENT:** 32/13 actual Facad factor rows, their types and argument literals are documented by unsaved editor UIA; no patient result, no computation equivalence.
- **DISCOVERED_MISMATCH:** Atlas #29 vs 32F absence; Atlas 12 angular reference vs Facad 13F linear PFH; extra vendor interincisal.
- **UNVERIFIED FORMULA / SIGNS / AGE-NORMS:** All geometry/norms require source-qualified construct definitions and direct clinical reference before activation.
- **IDENTITY_CONFLICT:** original Ricketts 1960 five-item approach and 1981 eleven-item summary are **different historical versions**, not facad edition aliases (S4/S5).
- **HUMAN SCIENTIFIC REVIEW:** requires the licensed/publisher-authenticated Atlas 2009 original to settle factor 29/summary slot 3 editorial ambiguity, and scientific comparison of the **already recovered** vendor PM' intersection against the Atlas authorial Pm identity (no relabelling). Numerical same-trace comparison remains gated.
- **GATES unchanged:** `SHARED_APP_STORAGE_ISOLATION=UNVERIFIED`, `CLINICAL_EDIT_ALLOWED=false`, Facad→Digital Crown numerical parity `NOT_TESTED`, `ORTHO_ANALYSIS_PROTOCOLS_VERIFIED=OPEN`. No patient editing, no Save/Load/export.

## Next evidence acquisitions (in proof order)

1. Publisher-authenticated 2009 Atlas page for Cuadro 13.1 factor #29 and Cuadro 13.2 slot #3 (potential `posterior`/`total` translation/transcription confusion).
2. Vendor-authored Facad Ricketts 32F/13F manuals or licensed source evidence explaining the 33→32 omission and 12→13 extra; **vendor `PM'` definition is already source-locked as a derived line intersection**, while Atlas equivalence is NOT. Existing UIA alone is observational, but previous LOT08 original `.cph` inspection additionally proves the vendor construction.
3. Exact anatomical landmark and angular sign conventions from S5/Ricketts or author-qualified original sources; compare LOT06 canonical geometry row by row, never by English label alone.
4. Versioned age/sex/population normative evidence; S6 is evidence of **population-specificity**, not universal clinical norms.
5. Independent orthodontist confirmation, then controlled D3-approved numeric parity on aligned traced/calibrated cases; until then **F01.13 scientific gate OPEN**.

> Separation of concerns: source evidence exists and is expanding; **scientific equivalence cannot be invented from a name**. The deliverable here is proof of specific version and geometry mismatches, with auditable next proof requests.
