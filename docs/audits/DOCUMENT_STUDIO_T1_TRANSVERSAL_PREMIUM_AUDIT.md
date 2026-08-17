# Document Studio — T1 Audit transversal premium

Date: 2026-08-16
Baseline code: `0a720dace83613cfc9fb0e0ae1c754e19c447c28` (P7-G head)
Corrective stack: PR #88 → #89 → #91 → #92 → #93 → #94
Scope: shared Document Studio boundaries after P1–P7 engineering work.

## 1. Proof contract

This audit separates:
- **CODE VÉRIFIÉ**: statically inspected source/diff on the referenced branch/head.
- **TEST PRÉPARÉ**: automated test or harness exists but no execution result is inferred.
- **TEST EXÉCUTÉ**: only when an actual test run is observed.
- **INTERACTION RUNTIME**: only when reproduced in the authenticated product.
- **CERTIFICATION**: only after the required runtime/CI/manual gates pass.

A GitHub Actions job that fails before any step is neither a code failure nor a PASS.

## 2. Baseline shared architecture and defects

The T1 baseline demonstrated:
- `/patients/:id` could reuse the same `PatientDetails` tree while the patient id changed;
- P3/P4 patient-sensitive financial drafts lived in global `useAccountingStore` state without a patient-boundary reset;
- `DocumentHub` patient fetches could apply stale responses;
- URL-driven `documentTab` transitions bypassed the interactive dirty guard;
- dirty-state coverage was fragmented across P1–P7;
- shared “Ghost” logic derived clinical/radiological/therapeutic recommendations from free-text antecedents and financial act labels;
- a direct `documentTab=ai` path could expose a deterministic therapeutic-strategy generator under an “IA” label;
- shell truth/a11y/responsive invariants were not centrally gated.

These statements describe the **baseline**, not the post-correction state.

## 3. Baseline severity matrix

### P0

#### T1-P0-1 — Cross-patient financial/editor state persistence

A patient A draft could survive into patient B through shared global state and archived edit state.

**Required target:** patient identity is a hard isolation boundary.

#### T1-P0-2 — Stale patient-details response

A late patient A response could overwrite the current B context.

**Required target:** stale responses are ignored and old context is cleared at identity change.

#### T1-P0-3 — Free-text / financial-label clinical inference

Unstructured antecedents and financial descriptions could create prescriptive medication/imaging/treatment statements.

**Required target:** no clinical recommendation from those non-authoritative inputs in the certifiable shared path.

#### T1-P0-4 — Programmatic navigation bypass

`documentTab` synchronization could call `setActiveTab` outside the dirty-aware transition contract.

**Required target:** manual and URL-driven transitions share one guard.

### P1

- dirty-state parity across P1–P7;
- truthful capability/status messaging;
- responsive preview and compact shell;
- explicit keyboard/focus/accessible-state semantics;
- stale preview/suggestion/edit hydration invalidation at patient boundaries.

## 4. Target transversal contract

1. **Patient boundary:** patient id change invalidates patient-scoped shared document/edit state and stale async responses.
2. **Navigation boundary:** manual and URL-driven tab transitions use one dirty-aware decision path.
3. **Clinical boundary:** free-text antecedents and financial descriptions never prescribe/infer treatment, imaging or medication in the shared certifiable path.
4. **Truthful UI:** capability/status claims are evidenced or absent; uncertified clinical features are explicitly unavailable.
5. **Responsive/a11y:** core shell controls expose labels/state/focus semantics and remain usable on narrow screens.
6. **Proof:** T1 remains uncertified until executable harness + authenticated runtime/browser gates pass on the exact final head.

## 5. Corrective execution status

### T1-A — Patient isolation — CODE VÉRIFIÉ

PR #88.

Implemented:
- route-level `PatientDetails` wrapper remounts the patient workspace with `key={id}`;
- patient-boundary reset clears `useAccountingStore` and archived `editingDoc` state before the new patient tree renders;
- patient-boundary regression test verifies financial/store/edit reset;
- subsequent T1-C hardening makes `DocumentHub` patient and smart-suggestion fetches cancellation-safe and clears stale context before replacement.

**Engineering finding:** the baseline cross-patient shared-state path is closed statically.

**Not yet runtime-certified:** rapid authenticated A→B switch with delayed A network response.

### T1-B — Unified navigation guard — CODE VÉRIFIÉ

PR #89.

Implemented:
- one `DocumentTabNavigationPolicy` covers P1/P2/P3/P4/P5/P6/P7;
- P1/P6/P7 existing dirty-state primitives are retained;
- P2 gets explicit certificate dirty-state publication;
- P5 gets explicit unsaved-plan dirty-state publication without treating server hydration as user editing;
- P3/P4 shared accounting drafts are evaluated through the same central transition decision;
- `DocumentHub` is the authoritative transition orchestrator for both UI clicks and URL `documentTab` changes;
- URL cancellation restores the current tab rather than silently discarding the draft;
- unguarded reload/back controls were removed from the Studio header;
- patient boundary reset also clears document dirty-state modules.

**Engineering finding:** the baseline manual/programmatic dirty-guard split is closed statically.

**Not yet runtime-certified:** authenticated manual + URL-driven abandon/cancel matrix across all pages.

### T1-C — Clinical inference boundary — CODE VÉRIFIÉ

PR #91.

Implemented:
- removed the shared `Insight` side channel from `DocumentHub`;
- removed Ghost Complications, Ghost Mutuelle and missing-post-op protocol suggestions from the active shared hub;
- removed shared financial/free-text inference statements for anticoagulation, diabetes, bisphosphonates, pregnancy, antibiotics and radiography;
- dedicated deterministic prescription safety remains in the prescription-specific path rather than being duplicated in the shared financial/document hub;
- patient/smart-suggestion requests are cancellation-safe;
- the direct `documentTab=ai` footer executor no longer calls `/patients/{id}/ai-diagnostic`; it exposes an explicit unavailable state instead;
- source gates forbid reintroduction of the removed inference strings and AI launch control.

**Engineering finding:** no baseline free-text/financial-label prescriptive side channel remains in the inspected certifiable shared path.

**Important scope:** the historical backend deterministic `ai-diagnostic` engine is not certified by T1 and was not deleted; T1 only removes its executable Document Studio entry point.

### T1-D — UI truth — CODE VÉRIFIÉ

PR #92.

Inspected active shell surfaces:
- `StudioHeader.tsx`;
- `StudioTabs.tsx`;
- `StudioFooter.tsx`;
- `LivePreview.tsx`.

Result after T1-C:
- no additional active static “Moteur Local Actif”, “Lancer Analyse IA”, “Régénérer Analyse” or “IA certifiée” claim was demonstrated;
- anti-regression source gate added;
- uncertified clinical path must remain visibly unavailable pending separate scientific validation.

### T1-E — Responsive / accessibility shell — CODE VÉRIFIÉ

PR #93.

Implemented:
- explicit document-date `label`/`id` association;
- `aria-pressed` for odontogram, active document tabs and preview state;
- primary shell controls raised to touch-friendly minimum heights and given visible keyboard focus rings;
- print confirmation declared as an accessible modal dialog;
- PDF preview declared as a dialog when overlaid and region when inline;
- PDF preview closes on Escape;
- iframe keeps an explicit title;
- narrow-screen footer spacing/text sizing hardened;
- source-level accessibility invariants added.

**Not yet visually/runtime-certified:** real browser checks at 390/430/1280 and full keyboard/focus smoke test.

### T1-F — Final transversal recertification — TEST PRÉPARÉ, NOT EXECUTED

PR #94.

Added `scripts/certify_document_studio_t1.sh`:
1. targeted T1 transversal regression;
2. full frontend test suite;
3. frontend production build.

The harness requires Node 20 and a clean worktree and prints the exact candidate HEAD.

**No PASS is claimed merely because the harness exists.**

## 6. CI observation

On the observed T1-C exact head, GitHub Actions run #503 (`31941504118`) concluded failure before executing repository steps: jobs reported `runner_id=0` and empty `steps`.

Therefore:
- this is **not evidence of a code-test failure**;
- this is **not a PASS**;
- no repeated polling is useful until runner execution is restored.

The T1-F harness is the canonical executable gate to run once infrastructure permits.

## 7. Runtime gates still open

Required before final T1 certification:
- authenticated A→B patient switch with populated P3/P4 draft: zero old item/payment/installment/edit state survives;
- authenticated A→B with intentionally delayed A response: B remains authoritative;
- dirty P1/P2/P3/P4/P5/P6/P7: manual and URL-driven transitions show equivalent cancel/discard behavior;
- no Document Studio route can execute the uncertified `ai-diagnostic` clinical-strategy path;
- real 390 px / 430 px / 1280 px responsive matrix;
- keyboard/focus smoke check, including dialogs and PDF preview Escape close;
- real preview/print interaction check;
- targeted T1 harness + full frontend suite + production build on the exact final head.

Clinical, pharmacological, financial and regulatory certifications remain separate wherever applicable.

## 8. Current status

**Engineering A→E: statically converged on the stacked T1 branches.**

**T1-F automation: prepared, not executed.**

**Runtime / CI / visual certification: OPEN.**

Consequently, T1 must not be labelled “certified”, “production ready” or fully closed. The next technically valid transition is execution of the exact-head T1 harness when runners are available, followed by authenticated/browser runtime checks and only then final certification/merge closeout.
