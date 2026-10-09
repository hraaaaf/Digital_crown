# F01.13 — Science source acquisition from installed Facad 3.14.1.1111 Quick Demo (2026-10-09)

**Status:** OFFICIAL INSTALLED MANUALS LOCATED & SHA256-PINNED; FULL MEASUREMENT FORMULAS, FACAD↔ATLAS EQUIVALENCE AND CLINICAL PARITY **NOT CERTIFIED**.

## Exact provenance

- Facad version: **3.14.1.1111**, official `https://downloads.citodent.com/pub/Facad/Facad-Installer-3.14.1.1111.exe`; downloaded installer wrapper SHA-256 `a60d13ea2c32d49c192bcf07f40ba07d8c0410e6577fe28ce4b0181bb4018b86`.
- **Successful GitHub run:** [#37981554220](https://github.com/hraaaaf/Digital_crown/actions/runs/37981554220) at exact HEAD `e91a25e230258e3a2653df226df73937a5dd4a70`. All job steps successful, including selecting Quick demo installation, stopping installer-autostarted Facad.exe on an ephemeral hosted Windows VM, checking its absence, and enumerating **PDFs only under C:\Facad**.
- **Source metadata artifact:** [#11642105521](https://github.com/hraaaaf/Digital_crown/actions/runs/37981554220/artifacts/11642105521), artifact ZIP SHA256 `3bc0203f72e5c913056aba07ca3632586bbbf9b979c955ce2a1affb56027c27d`, only JSON/text metadata (no vendor PDFs, no .cph, no .fcd or PHI).
- **Original 145/75 evidence:** 145 installed PDFs counted; 75 document paths match research keywords; 75 file names and SHA-256 fingerprints in [pinned provenance manifest](data/FACAD_314_INSTALLED_SCIENCE_PDF_PROVENANCE_2026-10-09.json). The **75 is a file-name filter, not a count of scientifically validated documents**; there may be relevant documents in the other 70.
- The previous [ZIP-only run #37980071440](https://github.com/hraaaaf/Digital_crown/actions/runs/37980071440) correctly saw zero PDFs **inside the uninstalled FacadRelease ZIP**; it was not evidence that installed documentation did not exist.
- The prior [Quick Demo run #37980277530](https://github.com/hraaaaf/Digital_crown/actions/runs/37980277530) failed safely because the installer started Facad.exe before the inventory step. After addressing that exact process guard, the source discovery run succeeded. Never rewrite either original result.

## Twelve priority source documents FOUND (manufacturer copies in installed app)

These are original installed-source file fingerprints; **they do not assert editorial authorship, original publication content or correct runtime formula parity**.

| Official installed PDF filename | SHA-256 |
|---|---|
| `Ricketts (13 F).pdf` | `3f016b7976c87c0930548c6dbada1888357e34e16fc47efeeae2f1a822eedc5f` |
| `Ricketts (32 F).pdf` | `8ddf3979d59777a2b125146d4714fedd4466b38b17a1e77a18273ae8c1ae9987` |
| `Ricketts acc G. Samson.pdf` | `049ddde56b62ceaa81a6c8fdbb1c1542170175ccaeaf9a147ae5c8c222fc9b4f` |
| `Ricketts Summary.pdf` | `4b95b9b2514b98f3b876f784b17b4a54844df68d96c388a23afb8ba4f402af44` |
| `Ricketts.pdf` | `bb61a53ca666cef6f7bd888c20773525bc34791703fc7a77eb878a636497d73d` |
| `McNamara.pdf` | `87475767a5676d98fef236160e7b68643f1041ebfc6e5656f0c4cd93b27eacb5` |
| `Steiner.pdf` | `2a73001b6e5c0d872e89faabe1d686f24e67f950cea755cebd3f70b2cb47fdb5` |
| `Tweed.pdf` | `c8c60ff86bf7833ac2629baf692e99b0be964833d31adfdff2f3f7e124ab1a65` |
| `Downs.pdf` | `8a28f70d3b667a636c17765ddabb215e0707b7aa286747989c22e84c0986c2db` |
| `C01_Lateral Cephalometry Library - Lines and Contructed markers.pdf` | `a977f219b6c9b95543551fe7a6e48587ac597b065e0200ab844e20ed322ba119` |
| `C02_Lateral Cephalometry Library - Measurements.pdf` | `4dbd3fa8419b684529fcbc17f615f49f7486cdf037fcfff025b1b307c0c0a548` |
| `Overview of Landmarks.pdf` | `2493bc1218395fd1ff35bc57a0e9c5acdda77228d4cf8565719d374ca7caf7cd` |

The registry also includes Ricketts general, Ricketts Frontal, frontal and cast-model cephalometry library PDFs, overview, and other analysis profiles. The names above were **observed and SHA-pinned**; page-by-page formula reconciliation remains a separate gate.

## Scientific follow-on, specific and falsifiable

1. **Ricketts (32 F)** vendor-installed PDF vs Ricketts (32 F).cph actual 32 measured rows, and *Atlas de cefalometría y análisis facial* (2009), ch.13 cuadro 13.1 **33 rows**. Resolve allegedly missing Atlas factor 29 by proof, without assuming same edition/version.
2. **Ricketts (13 F)** vendor-installed PDF vs actual Facad 13 measured rows and Atlas cuadro 13.2 **12 rows**; specifically `PFH = Dist2p(CF,Go)` 63±3.5 **linear** versus indexed summary row at **60°±3°** **angular**, plus the additional vendor `InterIncisal` measure. Do not alias measurement dimensions by name.
3. **Mand len `Xi–PM'`**: previous source-locked Facad .cph already proved `PM' = intersection(Xi–PM, A–Pog)`. Vendor identity resolved, but this derived point is **not** automatically Atlas anatomical `Pm_Ricketts` and same-trace numerical equality is not yet proven.
4. **Cephalometry Library C01/C02 and Overview of Landmarks**: verify constructed lines (`Xi`, `PtV`, `CC`, `CF`, `PM'`) and marked anatomical points, unsigned/signed conventions and norms per population. Reconcile against existing CEPH08 source locks, not by English label alone.
5. **Steiner, Tweed, McNamara, Downs**: vendor manuals now located; compare the 36 prior candidate label mappings against vendor original definitions, especially blocked Steiner `Ls-SL`/`Li-SL` until marker `MS_Steiner` identity is proved.
6. **PDF licensing**: index/search only derived metadata and permissible brief excerpts/geometry, never check in full proprietary vendor PDFs or licensed Atlas pages, and never claim PDF pages were visually inspected when evidence is only PDF text extraction.
7. **Clinical safety**: `SHARED_APP_STORAGE_ISOLATION=UNVERIFIED`, `CLINICAL_EDIT_ALLOWED=false`, `ORTHO_ANALYSIS_PROTOCOLS_VERIFIED=OPEN`, `FACAD_NUMERICAL_PARITY_CERTIFIED=false`. No actual patient editing, analysis export, clipboard manipulation, activation, merge, or Vercel deployment.

**Scope score:** document discovery **PASS**; full source-lock **OPEN**; patient-specific clinical parity **NOT_TESTED**. This closes only the blocker *“cannot locate official installed 32F/13F vendor manuals”*, not F01.13 globally.
