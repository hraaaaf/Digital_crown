# Document Studio — T2 Integration Status

Date: 2026-08-16
Canonical stack: T2 baseline #98 → T2-A #99 → T2-B #103 → T2-E #104 → T2-F #105.
Current canonical PR: #105 (`agent/t2-f-global-recertification`).
Last code-bearing candidate HEAD inspected: `76675e9ed86f5dcaffd01c83963450b2478a24f7`.

Parallel closeout PR #102 is superseded by this stack. Its useful LivePreview accessibility delta (initial close focus + labelled dialog + Escape regression test) has been migrated to #105 before closure.

## Proof contract

- **CODE VÉRIFIÉ**: demonstrated by inspected source/diff.
- **TEST PRÉPARÉ**: test/harness exists but has not executed on the exact code-bearing head.
- **TEST EXÉCUTÉ**: only a real repository run counts.
- **RUNTIME / VISUEL**: only authenticated/browser evidence counts.
- **CERTIFICATION**: separate final gate; never inferred from code presence.

## T2-A — Information architecture

**State: CODE VÉRIFIÉ — RUNTIME OPEN**

Verified:
- one canonical P1→P7 vocabulary;
- canonical ordered certifiable tab list and parser;
- `HubDocumentType` is the canonical certifiable tab type;
- the URL parser rejects dormant `ai`;
- `useDocumentGenerator` exposes no `aiReport`, `loadingAi`, `handleGenerateAI` or `/ai-diagnostic` execution path;
- canonical P5/P7 preview labels;
- StudioTabs/Header/Footer presentation components are decoupled from the DocumentHub type import;
- navigation emits only P1→P7 tab events;
- P7→P3 transfer remains explicit and filtered through `convertPlanActsToQuoteItems()`.

Open:
- authenticated runtime verification of URL/navigation behavior.

## T2-B — Preview truth / freshness

**State: CODE VÉRIFIÉ / PRIOR LOCAL CONTRACT PASS — BROWSER + EXACT-HEAD EXECUTION OPEN**

Verified:
- deterministic `documentPreviewFingerprint()` covers active page, patient/date, prescription, certificate, financial state, installments, selected teeth, every Document Libre custom/page/alignment field, legal annotations, P5 payload and `isAccounted`;
- `DocumentHub` passes the explicit fingerprint to `DocumentHubPreview`;
- `DocumentHubPreview` delegates regeneration to `useDocumentPreviewController()`;
- the controller regenerates only on an enabled fingerprint change and forgets freshness when preview closes;
- a visible PDF is explicitly marked stale when the fingerprint changes or refresh starts;
- stale PDF content is hidden (`pdfUrl={null}`) and loading state remains visible until a new PDF URL arrives;
- synthetic `Espèces` transport for `EN_ATTENTE` is removed;
- Honoraires emits `mode_reglement` only when `paymentStatus === 'PAYE'`.

Prior local evidence, not exact-head certification:
- fingerprint source previously compiled with `tsc --strict`;
- isolated fingerprint contract previously passed **13/13 assertions**.

Still open:
- exact-head repository execution of frontend/type/test harness;
- authenticated browser verification of rapid edits / tab switches / preview-close-reopen behavior.

## T2-C — Shell decomposition

**State: ENGINEERING BOUNDARIES EXTRACTED / TEST PRÉPARÉ — EXACT-HEAD EXECUTION OPEN**

Verified extraction:
- router/navigation boundary: `useDocumentHubNavigation` owns canonical URL parsing/sync, dirty transition guards, discard confirmation state, P3→P4 financial reset routing and `beforeunload` protection;
- patient/session boundary: `useDocumentHubPatient` owns patient fetch/reset/error handling;
- preview boundary: `DocumentHubPreview` owns stale-PDF state and preview-controller integration;
- dialogs boundary: `DocumentHubDialogs` owns discard/duplicate modal presentation;
- domain/page boundary: `DocumentHubContent` owns the P1→P7 page-studio rendering and page-local interactions;
- root `DocumentHub` is reduced to orchestration/state assembly plus Header/Tabs/Content/Footer/Dialogs/Preview composition.

Behavior deliberately preserved during extraction:
- P3→P4 keeps acts while resetting financial context;
- dirty-state guards remain tab-specific;
- URL-origin cancellation restores the active canonical tab;
- P7→P3 conversion still passes through `convertPlanActsToQuoteItems()`;
- legal-annotation accessibility semantics remain in the ordonnance studio boundary.

Regression proof prepared:
- `DocumentHubDecomposition.t2c.test.ts` asserts root-shell imports and absence of direct navigation/patient plumbing;
- it asserts navigation, patient, content, preview and dialogs boundaries contain their expected responsibilities;
- `scripts/certify_document_studio_t2.sh` includes this T2-C source gate in the targeted frontend regression set.

Still open:
- exact-head TypeScript/Vitest/harness execution;
- authenticated navigation/dirty-guard/browser regression.

No certification claim is made from source decomposition alone.

## T2-D — Accessibility residual closeout

**State: CODE VÉRIFIÉ / TEST PRÉPARÉ — BROWSER OPEN**

Closed in current code:
- non-inline `LivePreview` exposes `role="dialog"` + `aria-modal`;
- dialog is labelled by its visible document title;
- focus moves initially to `Fermer`;
- Escape closes the preview;
- loading state is announced via `role="status"` / `aria-live`;
- discard-draft dialog exposes `role="dialog"`, `aria-modal` and a labelled visible title;
- duplicate dialog exposes `role="dialog"`, `aria-modal` and a labelled visible title;
- legal-annotation control exposes `role="switch"`, `aria-checked` and an explicit labelled relationship;
- Vitest regression remains versioned for LivePreview dialog semantics, initial focus and Escape.

Still open:
- authenticated browser keyboard/focus/escape matrix.

No full Vitest PASS is claimed until a repository execution path runs it.

## T2-E — Product polish

**State: CODE VÉRIFIÉ — RUNTIME/VISUAL OPEN**

Implemented:
- compact patient identity remains visible as `Patient actif`;
- current document label comes from canonical T2-A vocabulary;
- header/tabs/footer dark-mode contrast hardened;
- active tabs visually clarified without changing labels;
- financial total separated from action controls;
- action hierarchy remains preview → archive → print/preparation;
- touch/focus invariants preserved;
- source gates added.

Open:
- browser visual review at 390/430/768/1280;
- real dark-mode and overflow verification.

## T2-F — Global recertification

**State: HARNESS UPDATED / EXECUTION BLOCKED BY INFRASTRUCTURE**

`scripts/certify_document_studio_t2.sh` remains the fail-closed exact-head harness and includes the T2-C decomposition source gate. No PASS is claimed merely because the harness exists.

## Infrastructure evidence — exact-head CI #595

CI run **#595** targeted code-bearing HEAD `76675e9ed86f5dcaffd01c83963450b2478a24f7` and completed with three failed jobs:
- `Frontend (tests & build)`;
- `Tests & durcissement`;
- `Garde production (négatif)`.

This failure is **infrastructure-only evidence**:
- all three jobs expose zero repository steps;
- GitHub job logs are unavailable because runners never started;
- GitHub annotations state that recent account payments failed or the spending limit must be increased;
- therefore #595 is neither evidence of an application-code failure nor a PASS.

Local fallback remains partial: the available shell does not have an authenticated full private-repository checkout/dependency tree.

## Current critical path

1. restore an executable GitHub Actions runner or obtain an authenticated full checkout;
2. execute exact-head frontend TypeScript/Vitest/certification harness;
3. run authenticated browser matrices for navigation/dirty guards, preview freshness, keyboard/focus and 390/430/768/1280 visual/dark-mode behavior;
4. fix any evidence-backed regressions;
5. update final roadmap/status and only then consider ready/merge/global certification.

No percentage is assigned because the canonical roadmap still has no validated weighting model.