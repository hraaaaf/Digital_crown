# F01.13 — Atlas 2009, publisher authority versus Facad `PM'` source alignment (2026-10-09)

**Classification:** BOOK FIRST EDITION BIBLIOGRAPHICALLY VERIFIED; 13.1/13.2 ORIGINAL EDITORIAL CONTENT NOT AUTHENTICATED; `Mand len` FACAD↔INDEXED ATLAS EXTENDED-AXIS CONSTRUCTION **CANDIDATE**, NOT CLINICAL PARITY. Research branch only. All D3/clinical gates remain CLOSED.

## 1. What is genuinely authenticated?

Bibliographic information is corroborated by independent institutional catalogue records and Google Books: **Jesús Fernández Sánchez and Omar Gabriel Da Silva Filho, *Atlas [de] cefalometría y análisis facial*, Ripano, Madrid, first edition 2009, ISBN 9788493675677, 296 catalogue pages**. Evidence:
- [WorldCat book record](https://search.worldcat.org/title/655853982) — original print publication metadata.
- [Universidad Europea Miguel de Cervantes library ISBD record](https://biblioteca.uemc.es/cgi-bin/koha/opac-ISBDdetail.pl?biblionumber=165483) — year, publisher, ISBN, 296 pp, print.
- [Universidad Nacional del Altiplano library record](https://biblioteca.unap.edu.pe/opac_css/index.php?lvl=notice_display&id=101246) — **primera edición**, 2009, 296 pages, Ricketts chapter in contents.
- [Google Books record](https://books.google.com/books/about/Atlas_de_cefalometr%C3%ADa_y_an%C3%A1lisis_facia.html?id=6_fWYgEACAAJ) — matching author/publisher/ISBN.
- [Bookseller's chapter-level contents](https://libreriamedica.com/odontologia-general/1350-896-atlas-de-cefalometria-y-analisis-facial) — chapter **13. Análisis de Ricketts**, section **13.4 La simplificación de los 12 factores**; this is a reseller's transcription of contents, **not** proof of the original chart's factor semantics.

These sources establish **the book's identity**, **not access to or authentication of the publisher-issued full pages or tables**. No valid editor-licensed/original publisher byte-verifiable scan of figures 13.28 / tables 13.1 and 13.2 has been found in this search.

## 2. New fact from a *secondary reproduction* — mandibular body length

An online [third-party facsimile of chapter 13, printed p.235, figure 13.28](https://es.slideshare.net/slideshow/analisis-dericketts/239250329) describes mandibular body length as following the axis **Xi–Pm prolonged until line A–Pog**. It also captions the construction as the distance from Xi to its relevant location on A–Pog. **This directly changes the interpretation of a previously suspected mismatch**: the manufacturer construction `PM' = Intersect(Xi,PM,A,Pog)` looks **geometrically consistent** with that *secondary representation of Atlas text*. This is not merely nominal label similarity; it is an extension-to-a-line construction consistent at the functional level.

A separate 2017 [UNAM dentistry thesis, printed page 118 (PDF page zero-index 118)](https://tesiunamdocumentos.dgb.unam.mx/ptd2017/agosto/0762938/0762938.pdf) recounts that same extended-axis description. **Important limitation:** this is a secondary academic citation likely depending on the same upstream source, not an independent verification of the 2009 printed figure; PDF text could be retrieved but a screenshot fetch failed, so **no claim of direct visual inspection of its diagram**.

In the actual official **Facad Ricketts 32F CPH** (captured/authenticated previously), the vendor defines:
- `PM'`: `Intersect(Xi, PM, A, Pog)`, i.e. line Xi–PM meets line A–Pog.
- `Mand len`: `Dist2p(Xi, PM')`; editor literal norm `78±2.5` (not automatically the same population/age or number as the indexed book norm).
- Digital Crown currently records `M_RICKETTS_CORPUS_LENGTH_XI_PM_MM_V1` using direct anatomical Pm. **Do not silently rewrite that canonical measurement or alias it**.

**Cautious result:** `ATLAS_FACSIMILE_EXTENDED_AXIS_GEOMETRY_CANDIDATE`, stronger than `vendor-specific unexplained`, but weaker than `PUBLISHER_AUTHENTICATED_ATLAS_EQUIVALENCE`. The synthetic geometry [run #37990316751](https://github.com/hraaaaf/Digital_crown/actions/runs/37990316751) proved that `Xi→PM'` and `Xi→PM` can be different distances; that warning remains fully valid even when the *Atlas's intended* length appears to follow the extended endpoint.

To **promote** this candidate, a licensed original print/scan must authenticate *p.235 figure 13.28 and its legend*, and the vendor and Atlas landmark interpretations (including PM/Pm, Xi, A and Pog) must be independently compared. Only after verified D3 isolation could one do same-tracing, numerical, signed/direction-aware parity tests. A secondary facsimile alone is inadequate for a clinical source-lock.

## 3. Contradictions still unsolved — do NOT infer 2009 publisher endorsement

- **Atlas 33 versus Facad 32.** Third-party chapter text shows 33 full items; the directly observed Facad editor has 32 measured items. Atlas candidate **#29 60° angular total facial height** is not observed as a separate 32F editor item. Table 13.1 and exact caption remain unauthenticated.
- **Atlas 12 versus Facad 13.** A bookseller's table of contents does support an original *section titled 12-factor simplification*; but the actual 12 measurements of table 13.2 were only transcribed from a third-party facsimile. Facad includes `InterIncisal`, absent from the indexed Atlas 12 list.
- **Ambiguous 60° angular item versus Facad PFH linear.** The secondary Atlas table labels a 60° item with a posterior-facial-height phrase, whereas the manufacturer has `PFH = Dist2p(CF,Go)` and a linear `63±3.5` literal norm, source-locked through CPH and PDF glossary. Different dimensions are **not aliases**; publisher may have a caption/transcription error, but neither such correction nor a vendor error can be certified without original evidence.
- **Age & population norms.** The indexed Atlas describes age trends (e.g. body length) while vendor editor displays snapshot norms. No direct application of a 2009 generic norm to other ages/populations is authorized. Page counts differ on some seller pages (292 versus 296); use matching **institutional catalogue/Google 296-page metadata**, not a commercial listing, for bibliographic grounding, and avoid treating pagination variants as proof of a new edition.

## 4. Auditable status and required next evidence

[Source-tier machine matrix](data/FACAD_F01_13_ATLAS2009_PRIMARY_EDITION_AUTHORITY_V1_2026-10-09.json) stores 8 links and explicit per-source `supports` versus `does_not_support` lists; it marks original editor tables **unavailable**. Separately, [geometry source dossier](CEPHALO_FACAD_F01_13_RICKETTS_GEOMETRY_DISCREPANCY_TRIAGE_2026-10-09.md) records the precise original *Facad* CPH construction and non-alias proof.

**Next acquisition targets (copyright-compliant, no claims of current access):** a legitimately obtained first-edition book, an authorized publisher excerpt, or controlled reading room access to pp. 214 / 233–236, especially **Cuadro 13.1, fig. 13.28, Cuadro 13.2**. Record edition/printing, page labels, full geometric dependencies, dimensions, signed conventions and age-corrected norms, not bulk chapter images. If publisher assistance is required, prepare a targeted question about table 13.1 #29 versus #28 and the 12-factor summary's 60° entry; **do not send requests without authorization**.

**GATES:** `F01_13_GLOBAL_CLOSED=false`, `PUBLISHER_ORIGINAL_EDITION_AUTHENTICATED=false`, `SHARED_APP_STORAGE_ISOLATION=UNVERIFIED`, `CLINICAL_EDIT_ALLOWED=false`, `FACAD_NUMERICAL_PARITY_CERTIFIED=false`, `ORTHO_ANALYSIS_PROTOCOLS_VERIFIED=OPEN`. No patient use, frontend/backend runtime edits, merge or deployment.
