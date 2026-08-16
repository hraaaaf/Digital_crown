# Document Studio — T2 Integration Status

Date: 2026-08-16
Canonical stack: T2 baseline #98 → T2-A #99 → T2-B #103 → T2-E #104 → T2-F #105.

Parallel closeout PR #102 is superseded by this stack. Its useful LivePreview accessibility delta (initial close focus + labelled dialog + Escape regression test) has been migrated to #105 before closure.

## Proof contract

- **CODE VÉRIFIÉ**: demonstrated by inspected source/diff.
- **TEST PRÉPARÉ**: test/harness exists but has not executed on the exact head.
- **TEST EXÉCUTÉ**: only a real repository run counts.
- **RUNTIME / VISUEL**: only authenticated/browser evidence counts.
- **CERTIFICATION**: separate final gate; never inferred from code presence.

## T2-A — Information architecture

**State: CODE VÉRIFIÉ — RUNTIME OPEN**

Verified on current #105 head:
- one canonical P1→P7 vocabulary;
- canonical ordered certifiable tab list and parser;
- `HubDocumentType` is now the canonical certifiable tab type;
- the URL parser rejects dormant `ai`;
- `useDocumentGenerator` exposes no `aiReport`, `loadingAi`, `handleGenerateAI` or `/ai-diagnostic` execution path;
- canonical P5/P7 preview labels;
- StudioTabs/Header/Footer presentation components decoupled from the DocumentHub type import;
- shell navigation emits only P1→P7 tab events;
- P7→P3 transfer remains explicit and filtered through `convertPlanActsToQuoteItems()`.

Open:
- authenticated runtime verification of URL/navigation behavior.

## T2-B — Preview truth / freshness

**State: CODE VÉRIFIÉ / LOCAL CONTRACT PASS — EXPLICIT CONTROLLER INTEGRATION OPEN**

Verified on current #105 head:
- deterministic `documentPreviewFingerprint()` covers active page, patient/date, prescription, certificate, financial state, installments, selected teeth, every Document Libre custom/page/alignment field, legal annotations, P5 payload and `isAccounted`;
- fingerprint source compiles with `tsc --strict` in the available Linux environment;
- local isolated fingerprint contract: **13/13 assertions PASS**;
- `useDocumentPreviewController()` regenerates only on an enabled fingerprint change and forgets freshness when preview closes;
- current runtime debounce still depends on `generator.handleGenerate`; that callback depends on the complete memoized generator params, so all current payload-relevant fields invalidate the preview generation callback;
- synthetic `Espèces` transport for `EN_ATTENTE` is removed;
- Honoraires emits `mode_reglement` only when `paymentStatus === 'PAYE'`.

Still open:
- replace the indirect callback-identity freshness mechanism with the explicit fingerprint/controller in `DocumentHub`;
- explicitly mark/hide a visible PDF as stale while a new fingerprint is waiting for regeneration;
- authenticated browser verification of rapid edits / tab switches / preview-close-reopen behavior.

## T2-C — Shell decomposition

**State: OPEN**

Target remains:
- router/navigation boundary;
- patient/session boundary;
- preview controller boundary;
- domain-local page studios;
- shell-only header/tabs/footer/dialog composition.

No extraction is claimed yet. This is now the main remaining engineering refactor.

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

**State: CODE VÉRIFIÉ, RUNTIME/VISUAL OPEN**

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

**State: HARNESS PREPARED, NOT EXECUTED**

`scripts/certify_document_studio_t2.sh` remains the fail-closed exact-head harness. No PASS is claimed merely because the harness exists.

Local targeted evidence added on 2026-08-16:
- preview fingerprint source: `tsc --strict` PASS;
- preview fingerprint contract: 13/13 isolated assertions PASS.

## Infrastructure evidence — exact cause verified

Latest fully inspected GitHub Actions class remains a runner-allocation failure before repository execution:
- jobs expose no repository steps;
- runner allocation did not begin;
- GitHub annotation identifies account Billing / spending-limit as the blocker.

This is not evidence of application-code failure and is not a PASS.

Local fallback remains partial: Linux execution is available for reconstructed targeted policies, but no authenticated full private-repository checkout/dependency tree is available in the current shell.

## Current critical path

1. T2-C: decompose the `DocumentHub` shell with regression-preserving boundaries;
2. T2-B: replace indirect preview invalidation with the explicit fingerprint/controller + stale-visible-PDF state;
3. run exact-head repository harness when a real checkout/runner is available;
4. run authenticated browser/PDF/financial matrices;
5. update final roadmap/status and only then consider ready/merge/global certification.

No percentage is assigned because the canonical roadmap still has no validated weighting model.
