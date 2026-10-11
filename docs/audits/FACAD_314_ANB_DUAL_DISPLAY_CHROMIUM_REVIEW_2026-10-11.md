# FACAD F01.13 — ANB real React display modes: Chromium source-only browser adjudication

**2026-10-11. Research-only. UI component test PASS; authenticated app E2E / FACAD vendor numeric parity NOT TESTED.** No patient case, no backend requests, no clinical runtime changes, no merge or deployment.

## 1 — Exact proof and report provenance

Successful experimental [Chromium browser run #38104902487](https://github.com/hraaaaf/Digital_crown/actions/runs/38104902487) **COMPLETED/SUCCESS** on exact commit **0e100a0bb6d80df7166341d16a6b168ad2f19fe9**. Runner used Node 22, npm lockfile dependencies, real Vite dev server and Playwright Chromium. Python 3.11 ran the previously source-pinned **9-test ANB math/routing oracle** before the browser and supplied its real four synthetic calculations to the browser. The browser mounted the **real, unmodified CephaloAnalysisWorkbenchPanel** and **real Zustand useOrthoStore**, generated and deleted a disposable HTML/TSX test entry in the checkout, with no actual account login or backend service.

Artifact **11689705284** was downloaded and inspected as a ZIP: SHA256 **97cb8e521b96c7565ed1fcf570fd4345a37e8362610015bdcfdfcc51c9c5f0fe**. It has **six files**, strictly no patient or vendor PDF: four PNGs (same viewports BEFORE/AFTER), `report.json` (SHA256 **f0df35c02c60d72889e0c4fa4f1f9e7a79928cdfa1208b6bfb08273b941f1331**) and `vite.log`. Browser report checks: `head` matches the exact run SHA, 2 viewports, 4 synthetic fixtures, 12 trace records, absence of patient data, absence of enabled external API calls, `facad_vendor_numeric_oracle_executed=false`. A Google Fonts stylesheet request was **blocked**, not allowed; no external requests succeeded through the test network route.

Images source SHA256:
- mobile-BEFORE-all.png = **bea8f8037195ab36a2b696d1bcb43bfd2e429ce47b2ec908dc50d696cfe618b5**
- mobile-AFTER-steiner.png = **93aea7da1904d8e5d4ad90d59b2c84d500f1e8f9f94ccb7e43babd6403ba8ebc**
- desktop-BEFORE-all.png = **464447b1ae873b7c46527eeb67930aa635be8f98f2031a4356eb52a136d6b202**
- desktop-AFTER-steiner.png = **d31a16352a60e56250e01191a397871fda188026cdb9fd5c946e5b3371f8f31f**

**Visual check:** The *first* run [#38104735298](https://github.com/hraaaaf/Digital_crown/actions/runs/38104735298) passed the component DOM assertions, but its mobile Steiner screenshot did **not** show the ANB table row in the viewport. The latest harness was tightened to require actual ANB row visibility in **each** screenshot and uses an adequate page height for standalone fixture composition. Final PNGs opened by an independent image viewer showed **ANB 0.0°** present in both viewport captures (390×844 and 1280×900). The BEFORE/AFTER comparison changes the selected **display mode**, not product code; screenshots are not visual regression approval of the full application.

## 2 — Actual rendered ANB values, not just text searches

| Source-pinned synthetic fixture | All / legacy ANB (mobile and desktop) | Steiner M_ANB_DEG_V1 (mobile and desktop) | Candidate C02 unoriented N angle; NOT measured by FACAD |
|---|---:|---:|---:|
| F1_STRADDLE | 0.0° | 0.0° | 90.0° |
| F1_MIRROR | 0.0° | 0.0° | 0.0° |
| F2_VERTICAL | −90.0° | −90.0° | 90.0° |
| F3_SAME_SIDE | −18.4° | −18.4° | 18.4° |

**8/8 value comparisons PASS:** Two real display modes across four fixtures and two viewports. Both originate from the Digital Crown source-locked Steiner candidate source, deliberately the same algorithm as legacy; this proves consistency of **displayed synthetic Digital Crown values**, **not** correctness of ANB vs manufacturer FACAD. Source FACAD C02 PDF p.5 describes N as vertex for ANB toward A/B, but we still have **no manufacturer Angle3p numeric oracle or orientation rule**.

Additional per-viewport checks:
- With `scientific_read_path.authority=LEGACY_ONLY` and `active_chain=UNVERIFIED`, Steiner **M_ANB_DEG_V1 shows NC** (not computable). The legacy **All analyses ANB still shows 0.0°**, because the historical raw metric is supplied separately.
- With deliberately **inconsistent fabricated evidence**, All shows **0.0°** while Steiner shows **1.0°**. The harness detects the difference; the rendered component **does not itself perform a cross-mode consistency warning**. However, actual production typed Steiner evidence adapter rejects legacy/typed disagreement: **the fabricated payload has not been shown to pass production backend checks**, so this is **not a demonstrated clinical product defect**.
- No page-level horizontal overflow was observed at the two test viewports, and the final screenshot assertion requires the ANB row bounding box inside the visible viewport. Other panels, logged-in routing, responsive app shell, real network/PDF, patients and editing are outside this test.

## 3 — Scope, adversarial reviews and limits

**Review A — scientific provenance / misleading green verdict (internal, not independent external).** Score **8/10** on isolated dual-mode display traceability; **0/10** on FACAD numeric parity. Critically, all 4 expected synthetic ANB numbers are *Digital Crown* candidate outputs. The signed vendor `Angle3p` conventions, orientation, 180/360 range, clinical norms, and actual same-image comparisons are unknown. Identical All/Steiner numbers do not authenticate either against FACAD.

**Review B — clinical safety, fail-closed boundary and user experience (internal, not independent clinician).** Score **7/10** on isolated browser evidence; **0/10** on authenticated patient-safe E2E or FAC03 D3. The verified Steiner projection correctly drops to NC if source authority is unverified. Yet legacy All continues showing an unverified raw numeric value, and an inconsistent fabricated payload can yield two modes with different values and no intrinsic consistency warning. This represents **a MAJOR potential presentation/provenance risk** requiring design review before clinical readiness; it is not proof a genuine backend-authorized case can reach that state. The initial mobile capture was fixed and rerun; final AFTER was visually checked. Fonts external fetch was blocked, and no patient/API data was used.

**Convergence**: NO. Two expert human independent clinical/release reviews on same product HEAD were not performed; these are two **internal perspectives only**.

## 4 — Strict gates and next

| Gate | Verdict |
|---|---|
| Source-pinned ANB Python geometry/routing | **9 tests PASS, 6 Git blob pins**; only Digital Crown |
| Real React component display all vs Steiner | **PASS** on 4 fixtures, 2 viewports; 4 source-checked screenshots |
| Canonical Steiner unverified source | **FAIL CLOSED to NC**; legacy raw value may still display |
| Actual full authenticated Digital Crown app UI | **NOT TESTED** |
| Numeric FACAD Angle3p same-case comparison | **NOT TESTED** |
| FAC03 D3 isolated-write guarantee | **OPEN_RED** |
| F01.13 scientific crosswalk / FAC05 parity | **OPEN / NOT_TESTED** |
| CLINICAL_EDIT_ALLOWED / CONVERGED | **false / false** |
| Canonical roadmap | **39/99 = 39.4%**, no clinical jalon closed |

**Next safe engineering research task:** test **the authenticated product route on a clearly isolated nonpatient test backend** and ensure legacy All ANB is labeled as raw/unverified when the scientific read path is absent; trace a canonical-vs-legacy mismatch through backend enforcement rather than inserting contradictory frontend-only JSON. Do not modify clinical interpretation or enable patient editing without D3 isolation and independent human approval. For FACAD numeric parity, require first a verified, safe disposable environment with no shared writes, then a real operator output on the *same fixture*, version-pinned.

No merge, no Vercel, no FACAD installed application invoked by the browser harness, no patient processed. The actual browser result is on SHA **0e100a0...**; a documentation-only follow-up commit must have its own CI checks.
