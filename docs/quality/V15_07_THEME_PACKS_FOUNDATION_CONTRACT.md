# V1.5-07A — Desktop Experience & MultiView | Foundation Contract

**Status: DRAFT / CONTRACT-ONLY IN THIS PR.** Pilots exist on other **OPEN, UNMERGED** PR branches; no runtime rollout or complete MultiView engine is delivered by this contract.
**Original baseline (historical):** `master@9158902e034c22b162873d5fd44ea7afd45f3e16` (2026-10-15). **Latest live master verified for this reconciliation (2026-10-17):** `d36a921e4b910a84cbce305bd501a3d046cfbb62`; the original baseline is 2 commits behind it. G0 BEFORE proofs retain their respective immutable baseline and must be rerun/reconciled against integration HEAD when merging.
**Canonical authority:** [ROADMAP UNIQUE V1.5](https://app.notion.com/p/3e677c66336281d88c82d2fbe43835fb) and [LOT07 decisions](https://app.notion.com/p/3e677c66336281639049f4cc7be1e5ae).
**Isolation:** LOT06 [PR #851](https://github.com/hraaaaf/Digital_crown/pull/851), LOT04/05, Queue, scientific engines, database and deployment remain out of scope. No runtime/UI activation in 07-A.

## 1. Approved product scope (not a proposal)

- **Digital Crown Signature** is one Cabinet Desktop experience with **Signature Core** (today's UI, unchanged baseline/default) and **Signature Iconic** (same layouts and workflows; optional icons, accents, decorations and motion).
- **Digital Crown Command** is the second, denser clinical workbench. Initial design candidates: Dashboard, Agenda, Patient Dossier, Imaging. Share all business rules, APIs, permissions and patient data; no second clinical app.
- **MultiView Studio (07.1)** is one shared desktop module/panel engine for both experiences, ultimately applicable to all **eligible and authorized Cabinet Desktop modules**. Not confined to Imaging.
- **One patient context per workspace**, across every patient-dependent panel. Switching from A to B must be explicit and protected; never show A and B as two dossiers in one workspace.
- **Desktop Cabinet only.** Do not extend new experiences or MultiView to Hub, Station, Pocket, Patient Companion, mobile or tablet. Preserve and test existing small-screen fallback and mobile behavior without inventing features.
- Experience selection (Core / Iconic / Command) and MultiView layout selection are two **separate settings scoped per authenticated user AND trusted workstation**; no sync across PCs or cabinet-wide selection.
- Keep the existing clinic `selected_theme` palette independent, fully backwards-compatible and still available to its current Pocket/mobile consumers.
- The prior three-pack/theme-only product description and original 10-SP estimate are **historical and superseded**; no automatic new estimate or certification.

## 1.1. Implementation inventory (17 October 2026 — branches only; not master)

This is **status reconciliation, not acceptance**. The initially correct "not implemented" status described **this contract PR**, but must not be read as denying the separate work already developed. The listed SHA/CI statements concern isolated branches only, and they are not transferable after a new HEAD or an integration merge.

| Scope | Candidate PRs / state | Evidence and qualification |
| --- | --- | --- |
| G0/G1 → P1 → P2 stack | [#895](https://github.com/hraaaaf/Digital_crown/pull/895) → [#896](https://github.com/hraaaaf/Digital_crown/pull/896) → [#897](https://github.com/hraaaaf/Digital_crown/pull/897) → [#913](https://github.com/hraaaaf/Digital_crown/pull/913) → [#915](https://github.com/hraaaaf/Digital_crown/pull/915); **all OPEN / UNMERGED** | #916 [run #39033605478](https://github.com/hraaaaf/Digital_crown/actions/runs/39033605478) SUCCESS on the frozen #896 source, genuine authenticated browser native 200%; P1 and P2 separate CI/visual proofs, but **not a full nine-layout MultiView engine**. |
| P1 clinical notice, 200% visibility | [#925](https://github.com/hraaaaf/Digital_crown/pull/925), DRAFT, based on #913, HEAD `103a6cf3` | Prior [T2 authenticated #39040893372](https://github.com/hraaaaf/Digital_crown/actions/runs/39040893372) SUCCESS **on previous HEAD `8e9cd88e` only**; new HEAD adds A/B late-response suppression and requires renewed [P1 contract #39044043380](https://github.com/hraaaaf/Digital_crown/actions/runs/39044043380) and [authenticated T2 #39044043285](https://github.com/hraaaaf/Digital_crown/actions/runs/39044043285) checks. Replaces automatic 7-second obstruction with patient-scoped inline advice. Fresh owner visual approval and independent reviews missing. |
| P2 local Agenda date correctness | [#923](https://github.com/hraaaaf/Digital_crown/pull/923), DRAFT, based on #915, HEAD `82d7f3c9` | [AFTER #39041538848](https://github.com/hraaaaf/Digital_crown/actions/runs/39041538848) SUCCESS (React visual, 72 captured scenes, mocked APIs). Additional [#926 audit #39041982878](https://github.com/hraaaaf/Digital_crown/actions/runs/39041982878) SUCCESS: immutable #923 source, real FastAPI authenticated GET 200 at 390/1280, date 2026-10-17. **Does not test a real appointment write**; not release certification. |
| Dashboard accessibility | [#910](https://github.com/hraaaaf/Digital_crown/pull/910) OPEN / UNMERGED | P0 scoped visual regression complete on its own HEAD; master integration not validated. |
| Visual Human Gate security | [#914](https://github.com/hraaaaf/Digital_crown/pull/914) OPEN / UNMERGED | Fail-closed synchronize behavior tested in branch, **not yet installed on trusted master**. Approval logic on master must be corrected before treating new UI approval events as reliable. |
| Documentation and safety | [#893](https://github.com/hraaaaf/Digital_crown/pull/893) (this PR), DRAFT / UNMERGED | Contract only, no implementation or release. |

**Hard stop**: no independent formal GitHub review on the three new P1/P2/audit PRs as checked on 2026-10-17; neither Human Gate nor `CONVERGED` may be inferred from automated screenshots. Existing responsive/mobile functionality is protected through regression checks, **not extended** by Desktop Experience/MultiView. Current scoped pilot displays only a G1 imaging two-panel subset; full generic registry, nine layouts, safe windows and physical two-monitor behavior are still open.

## 2. Architecture and components to reuse

| Canonical existing component | Safe reuse / boundary |
| --- | --- |
| `frontend/src/index.css` | Semantic tokens, existing legacy themes, high contrast and reduced-motion. No second theme engine. |
| `frontend/src/features/admin/Settings/tabs/BrandingTab.tsx`, `branding/presets.ts`, `hooks/useSettingsStore.ts` | Cabinet palette, existing animations and preview/save behavior. **Do not** encode personal experience choice in clinic `selected_theme`. |
| `frontend/src/features/admin/Settings/hooks/themePersistenceTruth.test.ts` | Regression guard: preview before backend ACK must not persist theme. |
| `frontend/src/components/Layout/MainLayout.tsx` | Reuse one shell, Framer motion and existing navigation. Never embed/cloned entire router, sidebar or global stores in each pane. |
| `frontend/src/features/patients/components/PatientMediaTimeline.tsx` | Already has authenticated media, T0/T1/T2 and fixed two-media comparison; extend viewer but never call this a general MultiView engine. |
| `frontend/src/services/workstationMode.ts` | Opaque server-side workstation identity candidate, to verify before preference storage. Existing `defaultExperience` (cabinet/station/control_center) is **not** Core/Iconic/Command. |
| `frontend/src/stores/useAuthStore.ts`, backend authorization | Authenticated user/context. Every panel access remains controlled by authoritative backend RBAC/tenant, not frontend route presence. |

**Still open:** module-by-module R (read), W (bounded action), X (full workspace sensitive action) matrix; preference storage/identity on shared/revoked/offline workstations; four actual target mockups; patient A→B interaction; revised SP estimate for all-eligible-modules MultiView; popup protocol and physical proof. Do not infer architectural approval from product-scope approval.

## 3. Execution gates (G-numbers are order, not replacement canonical sublot IDs)

### G0 — Signature Core baseline and acceptance (07-A)
1. Capture real BEFORE of Dashboard, Agenda, Patient Dossier and Imaging from **one recorded current master HEAD** on controlled fictitious fixtures, without AI redraw or fabricated clinical events.
2. Desktop viewports 1280, 1440, 1920, 2560 plus 200% zoom; verify 390/430/768 only for existing mobile/responsive non-regression.
3. Check visible clinical truth, legibility, keyboard, focus, contrast, no overflow, relevant RBAC, error states and runtime logs. Log defects with screenshots and exact route/state/HEAD.
4. Fix real P0/P1/major defects on isolated scope, compare AFTER at identical state/viewport and request explicit visual human approval. Existing V0.3 concepts are historical multi-SHA references (~7.5/10 internal), **not** current runtime proof.

**Exit:** approved reproducible Core reference manifest with no unaddressed blocker for scope; NOT a blanket certification without evidence.

### G1 — First safe MultiView (07.1.A + narrow 07.1.B; BEFORE Iconic)
1. Define authorized `ViewSlot`/module registry and panel lifecycle (server RBAC, tenant and user checks); no duplicated routers, independent invented business stores or arbitrary module embedding.
2. Lock one active `patientId`; protect unsaved draft, invalidate stale requests and clear patient A media/popup before switching to B. No token, PHI, draft or image in layout preference, history, logs or broadcast.
3. Implement the first **two-pane** column and row splits for a small approved subset of eligible Desktop modules, with bounded resize, swap, maximize/reset, keyboard/focus and narrow-screen safe fallback.
4. Layout scoped to user+trusted workstation, independently of visual experience and palette; fail safely to one pane on unknown preference or unreliable device identity.
5. Execute negative tests for A/B race, revoked role, forbidden module, session expiry and empty/slow media; genuine UI AFTER then owner approval.

**Exit:** working, secure and accepted vertical/horizontal two-pane pilot. Final product scope all eligible modules remains unchanged.

### G2 — Signature Iconic (07-B + targeted 07-D)
1. Reuse current tokens, Lucide and Framer Motion; enrich iconography/decorations/optional motion without moving or hiding clinical actions or inventing new business flows.
2. Maintain manual motion-off and `prefers-reduced-motion`, focus/contrast/200% zoom and performance. Never encode clinical safety purely in color or decoration.
3. Preview without persistence, explicit Apply/Cancel/Rollback, **user+workstation** preference with safe fallback Core; no update to cabinet `selected_theme` on experience selection.
4. Compare same exact fixtures, screens, actions and permissions to Core; request visual human signoff.

**Exit:** demonstrably distinct but functionally identical Iconic, reversible and accepted.

### G3 — Digital Crown Command and advanced MultiView (07-C / 07-D / remaining 07.1)
1. Dense Dashboard, Agenda, Patient Dossier and Imaging, same underlying components, APIs, rules and auth.
2. Complete 3-column and 1+2 layouts, size/position persistence, zoom/pan and T0/T1/T2 comparisons with timepoint, date and evidence provenance labels.
3. Mark **actual results vs projection** unambiguously: “Projection / simulation — résultat non garanti”. No mockup/AI/3D generation silently included.
4. Patient display popout in **read-only** mode with clinician-side preview then Present action; blank on changed patient, logout, role revocation, lost session/network. Pop-up blocked or unsupported multi-display API must fail to a safe manual fallback. A second PC is not a second local monitor.
5. Persist visual experience and layout independently per user and workstation, preserving saved state and fail-closed draft/permissions.

**Exit:** Command and complex MultiView accepted with independently demonstrated same clinical behavior.

### G4 — Acceptance and FUE (07-E + 07.1.E)
- BEFORE / TARGET / AFTER on **exact HEAD**, same data/route/viewport; 1280/1440/1920/2560, 200% zoom, keyboard, contrast, high contrast, reduced-motion, relevant FR/AR, performance.
- RPG-C/J/F for contracts/journeys/privacy; RPG-X where cross-window actors/transport is involved. Test cross-tenant, cross-patient, stale async work, role changes, offline, bad device state, popup refusal and rollback.
- Two separate adversarial review perspectives plus exact-HEAD confirmation. No `CONVERGED`, **9.5/10** or `CLOSED` without required independent proof and actual tests; internal self-review has its documented ceiling.
- Real dual-screen Windows or other physical test remains **LOT10 / PHYSICAL OPEN** until performed on actual devices. Synthetic CI cannot certify that.
- No automatic merge, Vercel deploy, cabinet installation or release activation.

## 4. Stop conditions and next action

Stop if a layout could mix A/B patient contexts, leak PHI or tokens via preference/URL/log/window, lose drafts, bypass server RBAC, silently change real patient data, overwrite existing clinic/mobile themes, or mislabel a projection as actual outcome. UI attractiveness or green docs CI is not proof of runtime UI.

**This PR remains contract-only.** G0/G1/P1/P2 branches below supply partial isolated evidence, not a complete, released or merged product. Next: secure independent reviewers, close the exact-HEAD Human Gates and significant defects, reconcile the changing master baseline and integrate with explicit authorization. No full 07.1 acceptance follows from the two-pane imaging pilot. All mergers and deployment decisions remain separate.
