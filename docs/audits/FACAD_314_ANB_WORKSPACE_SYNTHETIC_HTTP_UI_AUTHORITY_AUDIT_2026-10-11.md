# FACAD F01.13 — ANB in real Digital Crown Workspace with synthetic HTTP backend (2026-10-11)

**Verdict: SYNTHETIC WORKSPACE DISPLAY PASS; mobile visual overlap OPEN/MAJOR; FACAD NUMERIC PARITY NOT TESTED. Research-only.**

## Evidence

- [GitHub Actions run #38105728514](https://github.com/hraaaaf/Digital_crown/actions/runs/38105728514): COMPLETED/SUCCESS on exact test-source HEAD c732e3eb0e1d4baa883977fcaace84c686edd8be.
- Downloaded artifact 11690141015 contains exactly 4 PNGs, report.json and vite.log; ZIP SHA256 04ee8ab0dc710f32b09c10841af0bba277790842365ace35288fb157b52d6c89; report.json SHA256 5c99ddd4200bffd2649b6bc7ea691ba7aee84843bb67662fa30fae42e0a7af5a. All four images independently opened and reviewed.
- Browser mounted the actual CephaloWorkspace, Step1Cephalo, CephaloTracingLayer selection controls, CephaloAnalysisWorkbenchPanel and Zustand. A temporary untracked test entry was removed on the runner.
- A local-only synthetic HTTP server returned fictional test metadata from 2 observed GET calls to /api/patients/918, with any other method/path rejected. No real patient, clinical database, authenticated login or FastAPI production backend. External Google Fonts request was blocked. No external API call or write.

## UI figures displayed by the real workspace

| Independent synthetic fixture | All / ANB | Steiner / M_ANB_DEG_V1 | FACAD measured |
|---|---:|---:|---|
| F1_STRADDLE | 0.0° | 0.0° | No |
| F1_MIRROR | 0.0° | 0.0° | No |
| F2_VERTICAL | -90.0° | -90.0° | No |
| F3_SAME_SIDE | -18.4° | -18.4° | No |

**8/8 synthetic value comparisons PASS** (four cases in 390x844 and 1280x900). Values derive from source-pinned Digital Crown typed Steiner code, not real FACAD Angle3p output.

- Provenance negative case: when canonical authority is UNVERIFIED, Steiner shows NC and All continues displaying legacy ANB 0.0°. This is a real rendered component behavior using controlled synthetic data, not evidence that a backend-authorized patient response can reach it.
- Contradictory payload injection: All 0.0°, Steiner 1.0°, no intrinsic inter-mode warning in the rendered component. The actual backend typed adapter has stricter consistency rules, so this does not establish an actual production defect.
- Desktop BEFORE and AFTER show ANB unobstructed. Mobile BEFORE shows ANB 0.0° visibly. **Mobile AFTER Steiner screenshot shows floating « Passer aux moulages » overlaying the ANB value row**, so the test cannot claim visual no-overlap compliance despite the green DOM/numeric assertions. The harness checked viewport bounding boxes, not hit-tested occlusion. A product-equivalent mobile capture and overlap regression test are required. Classify as MAJOR UX concern pending reproduction on an authenticated app viewport.

## Adversarial internal perspectives (NOT independent human reviewers)

- **Science 8/10 for traceability; 0/10 for vendor parity:** two internally equal algorithms are not scientific validation. FACAD Angle3p signed convention and actual output are unknown. F01.13 remains OPEN.
- **Safety/UX 7/10 test-environment confinement, 4/10 mobile visual certainty:** no write or real patient; no auth/backing DB/FastAPI tested. The mobile overlay and raw legacy provenance mismatch are outstanding and cannot be hidden behind a green Actions badge.

## Gates / next

- F01.13=OPEN; FAC03_D3=OPEN_RED; FAC05=NOT_TESTED; CLINICAL_EDIT_ALLOWED=false; CONVERGED=false; roadmap 39/99 = 39.4%. PR #829 remains DRAFT. No merge, runtime clinical edit, deployment, FACAD executable, or actual patient use.
- Next: verify mobile value-cell occlusion by elementFromPoint and a real-UI BEFORE/AFTER test, then review whether All legacy should explicitly show an unverified/provenance state. Keep UI changes out of this research PR until a decision is made. For true FACAD parity, safely isolate D3 first and acquire actual same-fixture manufacturer output.
- Earlier test runs #38105398451 and #38105508737 FAILED due test fixture syntax/path errors; they were fixed. Only #38105728514 proves this PASS.
