# FACAD F01.13 — ANB: numeric-cell visual hit-test and historical value provenance

**2026-10-11 · Source-only research PR #829 · VISUAL-MOBILE-RED / LEGACY-PROVENANCE-VERIFIED-BY-SOURCE / FACAD-PARITY-NOT-TESTED.**

## 1. Reproduced visual problem and exact evidence

- [GitHub Actions EXPERIMENTAL #38106378176](https://github.com/hraaaaf/Digital_crown/actions/runs/38106378176), source HEAD `eeb4916b60cdceca3ba77dd11744d660a7a90887`: **COMPLETED / FAILURE BY DESIGN**, because the actual numeric cell was obscured; not because synthetic ANB calculations failed. The runner completed Python checks, Playwright rendering, and uploaded artifact despite the expected non-zero exit. No production frontend/backend source was touched.
- Artifact **11689282954**, ZIP SHA256 **346a7cdee931522a215b3035d91befa7d20f9aad90b276cf9a55749cc632c73b**. Seven members: `mobile-BEFORE-all.png`, `mobile-AFTER-steiner.png`, `desktop-BEFORE-all.png`, `desktop-AFTER-steiner.png`, `report.json`, `provenance.json`, `vite.log`. `report.json` SHA256 **94b5122016623f3ab40249ec8b2daa448056355f37844ba3b1af7e20efa2083a**; `provenance.json` SHA256 **3953baa6784f3cc13e6ad9a4ebcd6e6b3d23c2e6ec8520038c587e4f03361a04**. Exactly six image/JSON evidence members plus one short Vite log; no vendor PDF nor patient data.
- Rendered the **actual** `CephaloWorkspace` → `Step1Cephalo` → `CephaloTracingLayer` mode selector → `CephaloAnalysisWorkbenchPanel`, real Zustand, Vite, Chromium with localhost synthetic HTTP GET-only responder. This is **not** authenticated production application routing or real FastAPI/Postgres.
- `inspectNumericCellOcclusion` scrolls the **numeric table cell** into view and samples 5×5 points using `document.elementFromPoint`. Only a point hit **within the cell or its descendants** is marked clear; an overlay hit or off-viewport sample is BLOCKING. Screenshots use the same fixed 390×844 (mobile) and 1280×900 (desktop) viewports. No DOM existence-only green claim.

| Viewport | Mode / metric | Blocked samples | Hit attribution | Decision |
|---|---|---:|---|---|
| Mobile 390×844 | All / `ANB` | 0/25 | ANB `TD` | PASS |
| Mobile 390×844 | Steiner / `M_ANB_DEG_V1` | **15/25** | Overlapping `BUTTON` labeled **« Passer aux moulages »** | **BLOCKER for visual validation** |
| Desktop 1280×900 | All / `ANB` | 0/25 | ANB `TD` | PASS |
| Desktop 1280×900 | Steiner / `M_ANB_DEG_V1` | 0/25 | ANB `TD` | PASS |

- **Detector is not inert:** explicit synthetic overlay placed over the real cell was correctly detected **19/25 points on mobile** and **16/25 on desktop**, then removed. Both negative controls passed. This does not assert how many pixels of the actual glyph are hidden, only that the numeric cell surface is occluded, which is a valid regression guard.
- Numeric source-locked Digital Crown fixture values continue to match across modes **8/8** (0.0°, 0.0°, −90.0°, −18.4° on both viewports). The unverified-canonical fixture displays `Steiner = NC` while legacy All displays 0.0°. A deliberately contradictory injected fixture yields All=0.0° / Steiner=1.0°; this does **not** show a real production backend could issue such an inconsistent response.
- Test isolation: exactly **two GET** `/api/patients/918` to a loopback synthetic stub; **no writes, no real patient, no real FACAD execution, no permitted remote API**. No merge, deployment or clinical software edits. Current synthetic composition differs from fully authenticated product shell; actual mobile deployment still requires a separate AFTER confirmation.

## 2. Origin and authority of historical ANB — static source traced and pinned

New script `docs/audits/scripts/facad_anb_legacy_provenance_contract.py` on the same exact HEAD checks **13 original Git blob SHAs**, **21 structural source assertions**, and runs **8/8 Python self-tests** (including deliberate route modification rejection). All passed in GitHub job logs. This is **source provenance verification**, NOT live database/clinical authorization or FACAD numeric output.

1. `backend/services/cephalo_engine.py`: `SNA=angle(N→S,N→A)` and `SNB=angle(N→S,N→B)` use an **unsigned acos** (rounded to 0.1°); `metrics.analyse_osseuse.ANB.valeur` is built from **`SNA − SNB`**. The source itself is pinned by Git blob `240e938a6618557c9630fee8b5e9b49e18b6403c`.
2. `backend/services/cephalo_safe_engine.py` delegates to this legacy geometry and neutralizes historic norm metadata. `backend/services/cephalo_service.py` computes it; its result includes `metrics` plus the typed evidence graph persisted in `angles_data` by the repository.
3. `backend/services/cephalo_runtime_evidence.py` explicitly marks the legacy measurements `legacy_angles_data_role=COMPATIBILITY_OUTPUT` within the graph. This label is NOT an independent FACAD source truth or a normative interpretation.
4. `backend/services/cephalo_typed_read.py` overrides exactly **four linear legacy CRANIOM fields**: `Situation_A`, `Situation_B`, `Decalage_A_B`, `Profondeur_Faciale`. **ANB is NOT overridden** by that typed-read mapping. For a snapshot lacking typed graph, it returns a copy unchanged. For a valid typed graph it verifies case integrity; `backend/services/cephalo_runtime_chain.py` verifies the active chain and projects separate canonical and Steiner protocol measures. Invalid graphs fail the route instead of generating a fabricated canonical measurement.
5. The public `GET /api/ia/analyses/{analysis_id}` is wired through `backend/routers/__init__.py` (legacy GET removed and typed `cephalo_analysis_read` router included), with `backend/main.py` prefix `/api/ia`. Typed read route returns **409** if graph consistency fails.
6. `frontend/src/features/ortho/cephaloRepository.ts` fetches `/ia/analyses/{analysisId}`; `useOrthoStore` puts returned `angles_data` into `anglesData` after a persisted read. On initial upload it also consumes `data.results` directly. `CephaloAnalysisWorkbenchPanel.tsx` mode **All** selects `metrics.analyse_osseuse.ANB`; its fallback status label is **« Mesure brute »**. Mode **Steiner** selects `M_ANB_DEG_V1` from the verified `scientific_read_path.protocol_profiles.steiner` projection. **Distinct display authorities are therefore source-verified, not just hypothesized.**

**Boundaries:** The run did not execute real FastAPI handlers or database reads, and did not prove any genuinely authorized patient response displays the fabricated contradictory payload. A properly published typed graph can verify the active chain **without replacing the historic `ANB` legacy numeric field**. The equality between typed Steiner and legacy is an internal contract, not FACAD operator parity.

## 3. Adversarial internal reviews (not external/independent clinicians)

- **Review A — source/math; strict 8/10 provenance, 0/10 vendor parity:** 13 immutable blobs + 21 relationships and eight negative/positive tests verify the code structure, but the method still uses unsigned legacy angle subtraction and the real manufacturer `Angle3p(N,A,B)` numeric sign is unmeasured. **MAJOR scientific gate OPEN.**
- **Review B — UI/privacy; strict 9/10 detector evidence, 3/10 mobile legibility:** 15 of 25 actual numeric-cell hit points are covered on mobile Steiner; exact obstructing button identified, negative overlay tests demonstrate detector sensitivity, 0/25 elsewhere. This is a **reproduced UI regression in the isolated Workspace**, not an authenticated app regression certification. The test intentionally returns non-zero and uploads proof. No patient write. **MAJOR/visual release BLOCKER in scope.**
- **No real independent reviewers** and no two clean reviews on one release HEAD: **CONVERGED=false**.

## 4. Decision, gates, and next

- **EXPERIMENTAL scientific+UI test = FAILURE (correct fail-closed)**. Do not relabel this red as a runner flake or REQUIRED gate failure. The provenance subchecks succeeded independently.
- `F01.13=OPEN`, `FAC03_D3=OPEN_RED`, `FAC05=NOT_TESTED`, `CLINICAL_EDIT_ALLOWED=false`, `CONVERGED=false`; master roadmap **39/99 = 39.4%** unchanged.
- **Next safe scope:** authorize a **separate UI-only fix** for the overlay positioning on real mobile Workspace (likely sticky/floating step navigation), with BEFORE and AFTER at the same 390×844 and 1280×900, numerical tests and elementFromPoint checks. Separately decide if the legacy raw ANB should carry an explicit provenance cue on the All mode. No formula, clinical norm, patient persistence, merge or deployment changes in this research PR.
- Prove FACAD parity only with a safe D3-isolated actual manufacturer measurement on an identically calibrated synthetic case and competent human scientific review.
