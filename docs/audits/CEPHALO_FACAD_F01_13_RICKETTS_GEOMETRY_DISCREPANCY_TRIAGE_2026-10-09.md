# FAC-01 F01.13 — Ricketts 32F/13F: primary vendor geometry versus Atlas 2009

**Date:** 2026-10-09. **Scope:** research-only source contract, not clinical evaluation. **Status:** three composition conflicts identified; vendor point `PM'` defined, but vendor/Atlas measurement equivalence still **OPEN**.

## Evidence, explicitly ranked

1. **Official proprietary Facad 3.14.1.1111 Ricketts analyses**: source-locked CPH for `Ricketts (32 F)` SHA-256 `d0b442b39ac7db3dc9c46d807cb3c20bd937c69783b096b484872017f9376518` (repo `docs/audits/schemas/ortho_lot08_ricketts32_facad_final_seven_cluster_resolution_v1.json`, blob `411d5ba09dd596b2a2fbc3218ddf127c9fce3782`; `docs/audits/schemas/ortho_lot08_ricketts32_facad_ptv_cranial_cluster_resolution_v1.json`, blob `c714d74956305bd6a3c55f954296544ca272239b`).
2. **Facad editor UIA on official app**: `docs/audits/data/FACAD_314_D1C_RICKETTS32F_EDITOR_MEASUREMENTS_UIA_2026-10-09.csv` blob `220b4a23d469e1c634ff9d8df7ad22706ae7cc7a` and `docs/audits/data/FACAD_314_D1C_RICKETTS13F_EDITOR_MEASUREMENTS_UIA_2026-10-09.csv` blob `802df33d3c15cbaba095123f4b2b700689edae44`. These are **observational, not actual saved/exported patient numerical outputs**.
3. **Official vendor-installed PDF manuals** [run #37981554220](https://github.com/hraaaaf/Digital_crown/actions/runs/37981554220), metadata [manifest](data/FACAD_314_INSTALLED_SCIENCE_PDF_PROVENANCE_2026-10-09.json): 32F PDF SHA256 `8ddf3979d59777a2b125146d4714fedd4466b38b17a1e77a18273ae8c1ae9987` (8 pages); 13F PDF SHA256 `3f016b7976c87c0930548c6dbada1888357e34e16fc47efeeae2f1a822eedc5f` (5 pages). **Location and hashes are proven; page-by-page formula equivalence requires separate study.**
4. **Atlas 2009** Fernández Sánchez and Da Silva Filho, ISBN 9788493675677, chapter 13 cuadros 13.1/13.2, indexed reproduction only: **publisher-authenticated original still missing**. A source ambiguity in translation between angular total facial height and linear posterior facial height cannot be eliminated solely by matching factor names. The 2009 book remains independent of Facad's vendor documentation.
5. **Independent research**: Ricketts 1981 original clinical perspective has a distinct 11-item cue sheet; it does not establish Facad's 13F as equal to Atlas 12 or another summary.

## High-confidence vendor facts, with clinical parity gate held

| Question | Source-observed fact | Defensible conclusion | Forbidden shortcut |
|---|---|---|---|
| **32F `Mand len` endpoint** | UIA row 38: `Dist2p(Xi,PM')`, vendor literal `78±2.5`. CPH: `PM' = Intersect(Xi,PM,A,Pog)` = intersection of lines Xi–PM and A–Pog | Vendor `PM'` point construction is **resolved**; distance endpoint differs from simply using anatomical `Pm_Ricketts` | `PM' = Pm_Ricketts`; direct alias / numeric parity |
| **13F `PFH` units** | UIA row 6: `Dist2p(CF,Go)`, literal `63±3.5` = **length**. Same Facad 32F row 34: `Dist2p(CF,Go)`. Indexed Atlas summary slot 3 reads approximately `60°±3°` = **angle**, despite ambiguous Spanish wording | Genuine *dimensional incompatibility* of these two indexed slots; do not bind software PFH to angular summary item. However Atlas source-label transcription still not publisher-authenticated | Convert an angle to a distance by renaming; activate population-unvalidated norms |
| **13F interincisal addition** | UIA row 15: `Angle4p(Iia,Ii,Isa,Is)`, vendor literal `130±10`. 13 measured Facad rows; indexed Atlas 2009 summary has 12 | Observed vendor composition differs from indexed Atlas 12-factor list. Note original Ricketts literature may include an interincisal angle in *other* summary forms | Claim “Facad 13F = Atlas 12+1” or imply authorial correction |
| **Atlas factor #29 total facial height** | Atlas complete reconstructed 33 factors, index #29 approximately `60°±3°`, canonical Ricketts angular `Ba–N / Pm–Xi`. Vendor 32F captured 32 rows with no separate matching total-facial-height angular item | The **separate editor factor row is not observed**; internal vendor ability or formula absence is not proven | Claim all Facad 32F factors match Atlas complete 33 or call vendor a clinical error |
| **Source-locked `CF` family** | Vendor 32F `CF = intersection(FH,PtV)`; `PtV` anchored to vendor Pt. Digital Crown source-lock requires specific `PR_Ricketts_PTV`/Gonion definition | Same *geometric family*, **landmark identity gate OPEN** even though both display `Go–CF` | Direct alias/clinical norm parity by equal label |

## Independent literature: dimensional checks only

- Cruz-Hervert et al., *Dent J.* 2026;14(4):194, [DOI 10.3390/dj14040194](https://doi.org/10.3390/dj14040194), [PubMed 42041647](https://pubmed.ncbi.nlm.nih.gov/42041647/): independent dataset of **604 adult cephalometric records** reports posterior facial height **Go–CF in millimeters** as a **linear** variable, with differences by birth cohort. Supports a dimension check; does NOT validate Facad's norm **63±3.5** or any Moroccan clinical norms.
- [Independent cephalometric study](https://pmc.ncbi.nlm.nih.gov/articles/PMC3520347/) defines corpus length as a **Xi–PM distance**. This cannot establish Facad's derived endpoint `PM'` equals the manual point `PM`.
- [Original Ilexis Facad Tracing 3.14 guide](https://www.facad.com/dox/dox314/FacadTracingUsersGuide_ENG.pdf) lists vendor `PM` as Protuberance Menti and warns against basing a clinical decision only on software analysis values.

The independent publications corroborate measurement *family/dimension*, not proprietary vendor formula execution. The indexed Atlas 2009 angular summary item and the linear vendor PFH stay **non-equivalent**; licensed original Atlas verification remains OPEN.

## Mathematical witness — constructed vendor endpoint is not a safe direct alias

A **purely synthetic** 2D configuration (not a patient tracing) shows why `PM'` cannot be blindly replaced with `PM` or authorial `Pm_Ricketts`. The original vendor CPH geometry defines `PM' = Intersect(Xi,PM,A,Pog)`.

Take `Xi=(0,0)`, `PM=(10,0)`, `A=(5,-5)`, and `Pog=(5,5)`. Their line intersection is `PM'=(5,0)`. Thus `distance(Xi,PM)=10` while `distance(Xi,PM')=5`. One valid coordinate configuration suffices to **disprove unconditional geometric interchangeability**. In a special arrangement where `PM` lies on `A–Pog`, the two points may coincide, but that is not a general identity.

Source assertion and degeneracy handling are exercised by `audit/facad_f01_13_pmprime_geometry_contract.py` under the experimental GitHub Actions guard `.github/workflows/facad-f01-13-pmprime-synthetic-geometry.yml`. This establishes only a mathematical non-alias counterexample; it **does not measure any patient or prove actual vendor runtime numeric parity**.

## Official manufacturer PDF wording — bounded direct source inspection

[Original official installation and PDF short-source evidence, GitHub Actions #37989589832](https://github.com/hraaaaf/Digital_crown/actions/runs/37989589832) is **SUCCESS** on exact source HEAD `9213e02406e807a3381ccb62b8cf2bfdf148104c`; [metadata-only artifact #11644323061](https://github.com/hraaaaf/Digital_crown/actions/runs/37989589832/artifacts/11644323061). The experiment examined three SHA-pinned vendor PDFs and limited vendor text snippets to 20 words per PDF, without distributing copyrighted originals.

Direct manufacturer page-text observations:
- `Ricketts (32 F).pdf`, PDF p.4: **PFH is described as a distance involving CF**, corroborating the source CPH `Dist2p(CF,Go)` definition; same PDF p.4 has `Mand len` and `Cranium ant len` labels. PDF p.3 contains the `PM'` name, but the limited extract alone does **not** prove its geometric construction (which comes from separately source-locked official CPH).
- `Ricketts (13 F).pdf`, PDF p.3: **PFH is described as a distance**, and **InterIncisal as an angle between lines**; corroborates editor `Dist2p` / `Angle4p` types without any same-trace numeric demonstration.
- `C01_Lateral Cephalometry Library - Lines and Contructed markers.pdf`, PDF p.1: **PtV is a Pterygoid Vertical defined with a perpendicular**; the exact reference line still requires per-analysis geometry / vendor CPH confirmation.
- **Adversarial lexical capture defect discovered:** the naive case-insensitive substring scan can match `Xi` **inside the unrelated word “Maxillary”** (C01, PDF p.1). Therefore C01 `Xi` hits in the earlier artifact are only *lexical candidates*, not certified Xi landmark definitions. The whole-token extraction validator `audit/facad_f01_13_vendor_measurement_snippet_probe.py` was corrected with explicit `Xi`/Maxillary negative tests, and a new original-source [run #37990457485](https://github.com/hraaaaf/Digital_crown/actions/runs/37990457485) is required to confirm corrected references. Do NOT silently upgrade the older page hit.

All PDF fragments are bounded and research-only; clinical gate and external publisher-Atlas gate **remain OPEN**.

## Corrected manufacturer C01 glossary + original CPH construction chain (source evidence, not numeric parity)

The earlier scientific PDF page-term matrix recorded **C01 'Xi' page 1** as a case-insensitive substring, later exposed as **'xi' inside 'Maxillary'**. Its raw observation remains archived with an explicit non-authoritative flag. A **whole-token** search against the original manufacturer document was executed on GitHub-hosted Windows, [run #37990457485](https://github.com/hraaaaf/Digital_crown/actions/runs/37990457485), exact HEAD `f30393f553044c97b932ac0cd90c25c5b280b634`, **SUCCESS**, [source metadata artifact #11644409092](https://github.com/hraaaaf/Digital_crown/actions/runs/37990457485/artifacts/11644409092). The original PDF SHA-256 matched the earlier source inventory. Corrected C01 source page 2 explicitly has **`Xi` and `CF` as separately named constructed intersection markers**. Original PDF p.1 `PtV` appears as Pterygoid Vertical (a perpendicular line); Ricketts 32F/13F each calls `PFH` a **distance** and 13F calls `InterIncisal` an **angle**. These are **short, manufacturer-authored PDF-text findings**, not complete equations or numerical runtime comparisons.

[Replayed immutable PDF short-context verifier](https://github.com/hraaaaf/Digital_crown/actions/runs/37993535235) **SUCCESS**, source run #37990457485 pinned. It authenticated **9 short contexts from 3 official PDFs**, and passed **10 self-tests (1 positive + 9 adversarial negatives)**, including rejection of a false `Xi` at p.1. Its canonical [short-source evidence matrix](data/FACAD_F01_13_V314_WHOLE_TOKEN_SOURCE_SNIPPETS_2026-10-09.json) deliberately avoids embedding full proprietary PDFs.

The previously source-locked original `Ricketts (32 F).cph` analysis gives the **full construction dependency chain**, which is different evidence from the short manual explanations:

| Vendor constructed object | Official Facad CPH operator / dependencies | Source and remaining gate |
|---|---|---|
| `FH` | `Line(P, Or)` | vendor Porion + Orbitale; landmark identities still need DC correspondence |
| `PtV` | `Normal(FH, Pt)` | pterygoid vertical perpendicular to vendor FH through **vendor Pt**; must NOT alias `PR_Ricketts_PTV` without evidence |
| `CF` | `Inter2ln(FH, PtV)` | line intersection; `CF` inherits the vendor Pt and FH identity restrictions |
| `Xi` | `Intersect(R23, R14, R13, R24)` | center of vendor ramal rectangle with FH/PtV line directions; `R1–R4` identities remain source-specific |
| `PM'` | `Intersect(Xi, PM, A, Pog)` | derived intersection of vendor Xi–PM and A–Pog, **not** direct manual `Pm_Ricketts` |

CPH evidence: `docs/audits/schemas/ortho_lot08_ricketts32_facad_ptv_cranial_cluster_resolution_v1.json` (blob `c714d74956305bd6a3c55f954296544ca272239b`) plus `docs/audits/schemas/ortho_lot08_ricketts32_facad_final_seven_cluster_resolution_v1.json` (blob `411d5ba09dd596b2a2fbc3218ddf127c9fce3782`). `PFH` in both Facad editor profiles remains `Dist2p(CF,Go)` with literal norm `63±3.5` (source editor rows), and 13F `InterIncisal` is `Angle4p(Iia,Ii,Isa,Is)`, norm `130±10`. These vendor facts are **not** endorsement of universally appropriate norms or a proof of Atlantis/Atlas 2009 authorial parity.

**Evidence-level conclusion:** `Xi` glossary identity **SOURCE CONFIRMED at p.2**, `CF` glossary identity **SOURCE CONFIRMED at p.2**, vendor CPH expression families **SOURCE-LOCKED**. Mapping to manual Digital Crown landmarks, signs, clinical norms, Atlas 2009 full/summary composition and Facad↔DC same-trace numerical equality remain **OPEN**. No patient analysis has been run or exported.

## Finite next scientific checks

The official installed PDF **Ricketts 32F pages 3,4,8** contains text matches for `PM'`, while 13F **pages 1,3,4** contain `Ricketts (13 F)` text. These are page-term matches only. Compare exact *formula diagrams and notation* under permitted viewing, then reconcile with C01 (12-page library of lines/constructions), C02 (34-page measurement library) and Overview of Landmarks (2 pages). Independent clinical/orthodontic review remains required before approving geometry; exact same-image numerical tests remain blocked by D3 isolation.

**Clinical gates unchanged:** `SHARED_APP_STORAGE_ISOLATION=UNVERIFIED`; `CLINICAL_EDIT_ALLOWED=false`; `ORTHO_ANALYSIS_PROTOCOLS_VERIFIED=OPEN`; `FACAD_NUMERICAL_PARITY_CERTIFIED=false`. No patient read, export, edit, clipboard, deployment, V1.5 changes or merge is authorized by this research note.

## Phase 8 — primary Ricketts vs official Facad geometry, synthetic-only (2026-10-09)

**New authorial primary source, independent of the unverified Ripano Atlas:** Robert M. Ricketts, "Perspectives in the clinical application of cephalometrics. The first fifty years", *Angle Orthodontist* **51(2):115–150 (1981)**, [PMID 6942666](https://pubmed.ncbi.nlm.nih.gov/6942666/), [journal article image PDF](https://www.moroortodontia.com.br/leitura/ricketts1981.pdf). In **Fig. 9A, printed p.132 / PDF zero-index p.17**, Ricketts names **PR** as the pterygoid-root reference from which the PTV perpendicular to the true Frankfort plane is erected, yielding intersection **CF**; he describes **PT separately** at the lower border of foramen rotundum. **Fig. 9B p.132** locates Xi centrally in the ramus and joins the anatomical suprapogonion **Pm** to Xi for the corpus axis. This is an authorial primary description of **Ricketts 1981**, **not** publisher authentication of the 2009 Ripano Atlas.

**Manufacturer original, operator semantics, not inferred:** [Facad Tracing 3.13 Reference Manual, editor printed pp.73–77 / PDF pp.78–82](https://www.facad.com/dox/dox313/FacadTracingRefMan.pdf) explicitly specifies `Normal(line,marker)` as a perpendicular through the marker, `Intersect(marker1,marker2,marker3,marker4)` as intersection of **two lines through marker pairs** (not a finite segment- or ray-restricted operation), `Inter2ln` as two-line intersection and `Dist2p` as a two-point distance. The manual's interactive Angle (4pt) section states **clockwise positive rotation**, but **this does not independently certify the saved analysis editor's angle-sign or supplementary-angle presentation under every orientation**. Manufacturer 3.14 source-locked CPH, not the 3.13 manual, is the specific evidence for its `PtV=Normal(FH,Pt)`, `CF=Inter2ln(FH,PtV)`, `PM'=Intersect(Xi,PM,A,Pog)`, `Mand len=Dist2p(Xi,PM')`, and `PFH=Dist2p(CF,Go)`.

**New, directly evidenced source-definition discrepancy:** authorial Ricketts 1981 **PTV-through-PR** versus Facad CPH **PtV-through-vendor-Pt**. These point descriptions are not interchangeable by name; their anatomical identity remains unverified. **PRIMARY_RICKETTS_1981_PR_PTV_VS_VENDOR_PT_PTV=DIFFERENT_SOURCE_CONSTRUCTION**. The synthetic theorem below shows their resulting CF/PFH **may differ**, but cannot establish real-world patient-size bias or prove the two independently placed markers differ in every study. This clarification strengthens the existing D3 blocked `M_RICKETTS_POSTERIOR_FACIAL_HEIGHT_GO_CF_MM_V1` source gate; it does **not** claim the clinically authoritative 2009 edition necessarily adopted exactly the 1981 rules.

**Synthetic non-patient 2D examples to test in GitHub:**
- `Xi=(0,0), PM=(10,0)`, A–Pog vertical at **x=5** => PM'=(5,0); vendor Xi–PM'=5 vs direct Xi–PM=10 synthetic units. Swap line endpoints: geometry invariant.
- A–Pog vertical at **x=-5** => PM'=(-5,0), on **opposite ray**; at **x=15** => PM'=(15,0), **outside Xi–PM segment**. Manufacturer Intersect is an infinite-line intersection; no unsourced ray/segment clipping.
- Parallel, collinear, zero-length and near-parallel line inputs must be rejected by the **test implementation** as ambiguous/ill-conditioned. This is a deliberately fail-closed mathematical harness contract; the vendor's *actual UI/error behavior* for such inputs is **not observed**.
- Synthetic horizontal FH P=(0,0), Or=(10,0) with vendor Pt=(4,7) => vendor CF=(4,0). Distinct authorial-PR candidate point (8,7) => authorial-PR-based CF=(8,0). For Go=(4,-20), vendor Go–CF=20, PR-candidate Go–CF=√416≈20.396 **synthetic coordinate units, not clinical millimeters**. Same mathematical operator, different input landmark.
- A generic unsigned 2D vector angle with Na–Ba along +x and Xi–Pm rotated +60° yields 60°; reverse the Xi–Pm vector and its directed vector angle is 120°, while the undirected line acute angle stays 60°. **This is a mathematics witness, not execution/proof of Facad Angle4p output**, nor a clinical norm.

**Scientific verdict:** `RICKETTS_1981_PTV_ANCHOR_VS_FACAD_PTV_ANCHOR=SOURCE_DISCREPANCY_CONFIRMED`; `FACAD_PM_PRIME_IS_UNBOUNDED_LINE_INTERSECTION=OFFICIAL_MANUAL_OPERATOR_TYPE`; `SYNTHETIC_GEOMETRY_ONLY=true`. None of these imply same-trace numeric parity, signed-angle parity, clinical norms, publisher Atlas caption validity or any correctness/incorrectness of Facad. `FACAD_NUMERICAL_PARITY_CERTIFIED=false`, `CLINICAL_EDIT_ALLOWED=false`, `SHARED_APP_STORAGE_ISOLATION=UNVERIFIED`, `ORTHO_ANALYSIS_PROTOCOLS_VERIFIED=OPEN`, `F01_13_GLOBAL_CLOSED=false`. No patient reads, Facad launches, source copyrighted file rehosting, merge or deployment.
