# Orthodontic Studio LOT07 — BEFORE visual evidence

Status: observed BEFORE baseline
Product HEAD rendered: `8f266ea092a4516679319c9f8d157452e52b5482`
Theme: default
Fixture lineage: deterministic Cephalo R19 fixture
Viewports: 390×844, 430×932, 768×1024, 1280×900

## Capture result
- Normal text: all 4 viewports captured; six analysis modes exercised.
- 200% root-text scaling: all 4 viewports captured in the `all` analysis state.
- Browser page errors: 0.
- Browser console errors: 0.
- Blocked unexpected external requests: 0.
- Harness invalid captures: 0.
- Document-level horizontal overflow metric: false at every captured viewport.

These checks do not imply the visual layout is already acceptable.
## Observed normal-text baseline
- 390/430: navigation and primary controls stack cleanly; tracing remains usable, but the viewport is dominated by the viewer and there is no visible layer-manager model.
- 768: the tracing viewer becomes the primary surface; the analysis table is outside the initial viewport.
- 1280: established three-column composition exists: workbench controls / tracing / measurement panel.
- Existing controls expose Loupe, Tissus mous, Face 3D and T1/T2 projection-style controls rather than a registry-driven anatomical layer manager.
- The fixture patient label contains mojibake from the historical R19 fixture string; this is capture-fixture text and is not used as a product-quality verdict.

Severe baseline score — normal responsive composition: **8.2/10**.
Main debt: strong existing viewer, but not yet an Orthodontic Studio layer/edit architecture.
## Observed 200% text baseline
- 390: controls reflow vertically and remain reachable, but the tracing is pushed far below the header.
- 430: the control row visibly clips a following control at the right edge despite no document-level horizontal scrollbar.
- 768: the page title truncates to `Céphalo...`; the fourth workflow step extends outside the visible composition; the in-viewer analysis selector is clipped at the right.
- 1280: left workbench title truncates to `Toute...` and right analysis title to `Analyse Toutes...`; lower controls extend below the viewport.
- Therefore `horizontalOverflow=false` is insufficient as an accessibility gate; component-level clipping/truncation must also be tested.

Severe baseline score — 200% text/reflow: **6.0/10**.
This is a documented BEFORE defect set to eliminate in LOT07, not a PASS.
## Exact screenshot hashes
- `before-normal-390x844.png` — `e6ab0ec3cb7ba1c82354cf5aeb7cf31d504f385237e4ebfc19950b2cc3f16b2a`
- `before-normal-430x932.png` — `4ce7572b9175e6f9461299a03f778b1c0b8e231a58912f351bcdeb9290aecddf`
- `before-normal-768x1024.png` — `f48a6b0b133ca2d18662d5f70ae5464da5eb65ce3b4646eaa7a4159b36aafde3`
- `before-normal-1280x900.png` — `6c4513c3d8801651c14004413b27b9a5376bfe26aeebce7f44d4512776acd844`
- `before-text200-390x844.png` — `c7616fb3747e8fbe4d9065b30240587389cc3740f59e23d52d2b2cebe478a51e`
- `before-text200-430x932.png` — `91ca50f2f700799bd8cd34cd79fcf7e90512f2e7bce8439954ea8673c35e92cc`
- `before-text200-768x1024.png` — `7aac6005985689dcd13748286db772e673eee0262f73e47eced9cff5b4b9246a`
- `before-text200-1280x900.png` — `f6a616895eaff609c0f3a4948ea0c175d771a0c44c3a39a6b1eb9874faa71505`

## AFTER comparison gate
LOT07 visual completion must recapture the same normal and 200% states, compare against these exact viewports, and explicitly test component clipping in addition to document overflow.
