# FAC-01 F01.13 / FAC-04 — Official Facad 3.14 manual: scientific type semantics, source acquisition and export feasibility

**Date:** 2026-10-09. **State:** THREE ORIGINAL PUBLIC MANUFACTURER PDFs DOWNLOADED + SHA256 + PAGE-TEXT VERIFIED on [GitHub Actions #37978611128](https://github.com/hraaaaf/Digital_crown/actions/runs/37978611128); clinical formula/parity remains UNVERIFIED. The research browser's visual PDF screenshot function failed; PDF text/page matching was independently executed in GitHub Actions, but visual rendering of the PDFs is NOT VERIFIED.

## Evidence hierarchy / version boundary

1. **Current official manufacturer manual**: Ilexis AB, *Facad 3.14 Reference Manual*, URL https://www.facad.com/dox/dox314/FacadRefMan.pdf — publicly indexed text from **chapter 14 (pages labelled 105 onward)** and help menu. This documentation is for v3.14, relevant to installed 3.14.1.1111. **Exact downloaded file:** 5,230,584 bytes, 150 pages, SHA-256 `bb678ab66aca94953505f9e243edaac6e5112297a3e615340b4db9e213a87ad7`; CI verified export paths on PDF pages 107/111 and types `Dist2p`/`Angle4p` on PDF page 92. Page numbers here are 1-based PDF pages, not printed chapter page numbering.
2. **Previous official manufacturer manual**: Ilexis AB, *Facad 3.9 Reference Manual*, URL https://www.facad.com/dox/dox39/FacadRefMan.pdf — browser retrieved full parsed PDF text, chapter 12, pp. 84–86, but screenshot retrieval failed. A *historical version* supporting definitions; **do not automatically assume every v3.9 definition persisted unchanged in v3.14**.
3. **Official v3.14 user guide**: https://www.facad.com/dox/dox314/FacadTracingUsersGuide_ENG.pdf — indexed section **Help > Manuals > Cephalometry** explicitly says standard analyses, cephalometry library and markers are documented there. **Exact downloaded file:** 1,448,758 bytes, 42 pages, SHA-256 `cbbf28c983cc959e59ad864e8e601f20e43b8283f496c5437759536838e6aa78`; CI verified `Help > Manuals > Cephalometry` on PDF page 5. This identifies potentially decisive manufacturer-owned source PDFs *within the installed software*, without assuming those individual analysis PDFs are public online.
4. **Official Facad v3.12 release notes**: https://www.facad.com/wp/wp-content/uploads/2020/12/FacadReleaseNotes_3.12.pdf — states Ricketts 32 F and Ricketts 13 F both attributed to Fernández Sánchez / Da Silva Filho (2009) Atlas; separate Gerry Samson adaptation. **Exact downloaded file:** 267,975 bytes, 6 pages, SHA-256 `8c4c676ce4182c08e32e4747f4f02df242d4c0ee1e6a2a80ad6c4059a2ea8359`, vendor attribution and Ricketts names on PDF page 2. Vendor *attribution* is not proof of equal factor composition to the Atlas.

## Chapter 14 of the current v3.14 manual — precise output contracts

These are **documented UI command descriptions**, NOT proof that a specific current installation exported anything, NOT proof of numeric consistency and NOT authorization for filesystem/patient writes.

| Vendor command | Vendor-documented content | Documented file types | Safety classification |
|---|---|---|---|
| `Cephalometry > Export > Analysis Values` | Current patient information and cephalometric analysis **numeric measurement values**; tabs between columns | text `*.txt` or XML `*.xml` | **DOCUMENTED / NOT_EXECUTED / WRITE_EXPECTED / PATIENT_DATA_PRESENT** |
| `Cephalometry > Export > Analysis Properties` | Current patient information and **analysis definition without measured values**; normative metadata affected by locale | tab-separated text `*.txt` | **DOCUMENTED / NOT_EXECUTED / WRITE_EXPECTED / PATIENT_DATA_PRESENT** |
| `Cephalometry > Export > Object Values` | Current patient information, graphic objects, **marker positions**, planned movements of hard tissue / teeth / markers | text `*.txt` or XML `*.xml` | **DOCUMENTED / NOT_EXECUTED / WRITE_EXPECTED / PATIENT_DATA_PRESENT** |
| `Cephalometry > Export > Object Properties` | Current patient information, placed graphic object properties, profile-marker binding data | tab-separated text `*.txt` | **DOCUMENTED / NOT_EXECUTED / WRITE_EXPECTED / PATIENT_DATA_PRESENT** |

**Locale effect:** the *Regional > Use comma as decimal symbol* setting changes export text formatting and norms. Do not compare numeric files with a naive parser that assumes '.' decimal or comma delimitation; use locale-aware structured schema and source metadata. 

**Version distinction:** the v3.14 PDF indexed text explicitly lists these **four distinct export menu paths**, whereas the F04.1 passive Windows UIA run #37970277495 only observed `Cephalometry > Export` at root level without expanding submenus. **Documented command availability != runtime menu observed != actual export performed.** No F04.2 clinical or filesystem gate is closed here.

## Additional non-file output surface (manufacturer documented)

The Facad 3.14 Reference Manual chapter 14.1 (official indexed PDF text) describes **Edit > Copy** on the active analysis window to copy *visible cephalometric values as text* to the Windows clipboard. It separately documents **Cephalometry > Copy as Image > Analysis/Objects**. These avoid a conventional file-save action but **write into the system clipboard**, which is a shared/external side effect and may carry patient-identifying data; they are **NOT privacy-safe or D3-cleared by default**. This is a candidate route for a future *strictly isolated disposable demo* comparison, only after proving clipboard handling/isolation and obtaining required human consent. No clipboard copy has been run in F01.13/F04.2.

## Scientific type semantics available from the official manuals

The v3.9 Reference Manual, chapter 12.1.2, p.85, defines:

- `Dist2p`: a distance **between two points/markers**, hence a linear length.
- `Dist3p`: distance from a point/marker to a line defined by two markers.
- `DistLine`: perpendicular distance from a marker to a named line.
- `Angle4p`: angle between two lines each defined by two markers.
- `Angle2ln`: angle between two named lines.
- `ProjLine`: projection of the distance between two markers onto a named line.
- `Proj90Line`: distance between two markers projected onto a **perpendicular** to a named line.
- Facad norm `x±y` is an interval represented as mean ± one standard deviation **within that software definition**, not evidence of cross-population clinical applicability.

**Specific validated *type* incompatibility, not formula parity:** The Ricketts (13 F) actual UIA factor `PFH`, `Type=Dist2p`, args `CF, Go`, norm `63±3.5`, uses a two-marker distance. The third-party chapter 13 facsimile of the Atlas 2009, summary table 13.2, lists `Altura facial posterior` with `60°±3°` (angular dimension). The discrepancy is **genuinely dimensional**, although the Atlas reproduction has ambiguous *posterior/total* wording and is not independently publisher-authenticated. Thus **no scientific equivalence, no automatic renaming, no norm activation**. **Same-version confirmation improved:** the Facad **3.14** original official Reference Manual PDF at page 92 contains both `Distance (Dist2p)` and `Angle between lines (4pt)` type names. The v3.9 manual provided extended explanatory semantics. Exact 3.14 full definitions and landmark construction examples still merit per-page review in the installed Cephalometry Library; no numerical/clinical equivalence is inferred.

## Manufacturer-supplied sources to acquire next (no clinical mutation)

The current v3.14 user guide points to `Help > Manuals > Cephalometry`:

1. Vendor's **Ricketts (32 F) standard analysis PDF** — original equation / required landmark identity / `PM'` definition / treatment of Atlas factor 29.
2. Vendor's **Ricketts (13 F) standard analysis PDF** — reconciliation of Facad `PFH=CF-Go` distance to Atlas angular item, and source basis for extra `InterIncisal`.
3. Vendor's **Cephalometry Library (measurements and lines) PDF** — type definitions, signs, orientation, constructed points, line references.
4. Vendor's **Overview of Landmarks** — exact `Pm`, `PM'`, `Pt`, `PtV`, `Xi`, `CF`, `DC` identity diagrams, documented alternatives and provenance.
5. Publisher-authenticated **Atlas 2009** chapter 13, `Cuadro 13.1` entry 29 / `Cuadro 13.2` angular entry 3. Confirm by licensed physical edition or publisher-permitted excerpt; third-party chapter scan is *candidate evidence* only.

The manufacturer indicates paper documentation can be requested at **support@facad.com**: https://www.facad.com/wp/function-overview/ . Contacting a third party in the user's name is a **separate external action**; this document neither sends a message nor assumes permission.

## Unchanged clinical gate

`SHARED_APP_STORAGE_ISOLATION=UNVERIFIED` ; `CLINICAL_EDIT_ALLOWED=false` ; `FACAD_NUMERICAL_PARITY_CERTIFIED=false` ; `ORTHO_ANALYSIS_PROTOCOLS_VERIFIED=OPEN`.

**Proof manifest:** [`FACAD_314_OFFICIAL_PDF_SOURCE_MANIFEST_2026-10-09.json`](data/FACAD_314_OFFICIAL_PDF_SOURCE_MANIFEST_2026-10-09.json) stores URLs, exact SHA256, byte lengths and 1-based PDF page matches, without republishing copyrighted PDFs. **No export executed, no patient values collected, no PHI added to repository, no merge or deployment, no alteration of Digital Crown V1.5.** The evidence found supports the **documented capabilities** gate of FAC-04 but not the practical/clinical validity gates of F04.1/F04.2 or F01.13.
