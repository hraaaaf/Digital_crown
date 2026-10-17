# CEPH–FACAD P0.1 / WF_04 — preuve desktop, NOT clinical parity

**Status : P0 TECHNICAL EVIDENCE PASS / PRODUCT WF04 GAP OPEN / no vendor action / no patient data / no production change.** PR #934 targets `master` from `d36a921e4b910a84cbce305bd501a3d046cfbb62`. Source inventories: [Facad 3.14 census](https://github.com/hraaaaf/Digital_crown/blob/068d30a5437a4bf0fe8a46a96391fa3cd8a6428d/docs/audits/FACAD_314_FULL_APPLICATION_COVERAGE_CONTRACT.md), [Facad evidence PR #829](https://github.com/hraaaaf/Digital_crown/pull/829) (DRAFT), [D3 isolation PR #827](https://github.com/hraaaaf/Digital_crown/pull/827) (DRAFT).

## P0 matrix and quality gates

[Machine-readable inventory](data/CEPH_FACAD_PARITY_P0_DESKTOP_EVIDENCE_MATRIX_2026-10-17.json) is exactly **9 menu families**, **30 observed toolbar UIA IDs** (5 calibration/measure, 7 planning/transform, 6 tracing, 4 display, 8 patient/document), **7 desktop workflows**. Of 30 toolbar names, **9 have a source-verified candidate code reference** in Digital Crown, while **21 have no proven one-to-one code mapping** in this review. That never means absent. Even all 9 mapped source snippets do NOT demonstrate runtime-equivalent vendor behavior. No vendor action, case data, numerical oracle, or clinical release.

`python -m audit.ceph_facad_parity_p0_validate` checks enumerations, 9 live code symbol references, desktop scope, 7 workflow identities and all false safety/parity gates; it rejects **11 synthetic negative mutations**. It is deliberately a documentary validator, not a UI tester. Link exact GitHub run in the Notion POST only after observed status.

## WF_04 product discrepancy — BEFORE / TARGET / ACTUAL

| State | McNamara rows | Ricketts rows | Meaning |
|---|---:|---:|---|
| BEFORE code baseline `master@d36a921` | 3 (`Co_A`, `Co_Gn`, `ANS_Me`) | 2 (`Ligne_E_Ls`, `Ligne_E_Li`) | Actual `CephaloAnalysisWorkbenchPanel.tsx` source constants, not fully certified on fixture. |
| TARGET versioned profiles | 13 historical McNamara variables; 5 defined in LOT06 pack | Atlas2009 33 and Gregoret13 separately; vendor 32F/13F distinct | Render *all profile rows* with provenance/status, never invent a computed value. |
| AFTER browser observation | **3 (observed)** | **2 (observed)** | [real React R19 browser #39058647767](https://github.com/hraaaaf/Digital_crown/actions/runs/39058647767) on P0 exact HEAD `b9fc93c2` with 1280×900 synthetic viewport; code unchanged, gap confirmed. |

**Automated proof:** on [run #39058647767](https://github.com/hraaaaf/Digital_crown/actions/runs/39058647767), the Python validator PASSED **11/11 negative mutations**, Vitest **5/5 PASSED**, Chromium captured the real React workspace and reported `invalidCount=0` with 3 McNamara/2 Ricketts rows. The [artifact #12110666149](https://github.com/hraaaaf/Digital_crown/actions/runs/39058647767/artifacts/12110666149) contains screenshots for 1280×900 along with other historical R19 harness viewports, `report.json` and `wf04-finding.json`. Images are generated and linked, **not independently visually adjudicated here**. This test certifies discovery of incompleteness, NOT correctness of any measurement or production integration.

The existing `frontend/scripts/capture-cephalo-r19-analysis-reference-after.mjs` exercises the **actual CephaloWorkspace and analysis panel React source** via real Vite and Chromium. It uses **a synthetic SVG**, a fake patient route, and browser snapshots of modes `all`, `mcnamara`, `ricketts` at fixed viewports including desktop **1280×900**. The P0 job inspects two row counts and stores its finding plus screenshots under a dated GitHub Actions artifact. This is a **component/browser fixture, not authenticated product E2E**. The legacy R19 script also captures 390/768 **for its own regression**, not evidence that the next release includes mobile Céphalo.

### Highest-priority next product task

**WF_04 / CEPH08.4 + 08.5 + 08.10 :** **REUSE, REVIEW AND INTEGRATE** the existing [PR #911 R23-G2](https://github.com/hraaaaf/Digital_crown/pull/911) (OPEN/DRAFT on `d86d2963e3b31e6cacc2b77838f93d509460dfd1`): `CephaloR23G2ProtocolPanel.tsx` already implements source-versioned rows with McNamara 13 and Ricketts Atlas33 / Gregoret13, and `CephaloAnalysisWorkbenchPanel.tsx` delegates these modes there. [R23-G2 profile-contract CI #39028298136](https://github.com/hraaaaf/Digital_crown/actions/runs/39028298136) and [public visual audit #39028298114](https://github.com/hraaaaf/Digital_crown/actions/runs/39028298114) succeeded on #911 HEAD, **not evidence of integration into master or clinical certification**. Do not rewrite features already implemented in that stacked branch. The remaining work is verify/merge dependency order and end-to-end readiness, preserving distinctions `Co != Co_anatomic`, `Po != Po_anatomic`, `Atlas2009 != Gregoret13 != Facad32F/13F`. Include source-gated rows even if `SOURCE_MISSING`, `À placer`, `CALIBRATION_REQUIRED`, `NOT_COMPUTABLE`; keep `UNKNOWN != 0`; ensure Focus derives from every allowed profile dependency, not the historical 2–3 rows. Validate table ↔ SVG ↔ PDF using same canonical IDs, screenshots BEFORE/TARGET/AFTER and human review. **No automatic promotion of 23 conditional Atlas factors or six landmark HOLDs**.

### Required external gates

FAC-03 shared-storage isolation and vendor rights/licensing remain RED for potentially mutating Facad operations. F06.1 archival and F06.4 evidence handoff remain OPEN. Facad numerical parity needs same authorized image + landmark IDs + mm/px + signed geometry/units/rounding + real vendor output and independent clinician review. Any workflow beyond UIA discovery is **NOT_PROVEN**; neither a Scope-green run nor a synthetic browser fixture closes those gates.

**Next effort: Extra High**, inspect candidate #911 and stack against master and #878, prove authenticated nonpatient workflow after rebase and redo human desktop visual approval on new exact HEAD; clinical NO-GO, draft only; no merge/deploy.
