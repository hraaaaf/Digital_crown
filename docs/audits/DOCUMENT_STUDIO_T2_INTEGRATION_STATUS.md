# Document Studio — T2 Integration Status

Date: 2026-08-16
Canonical stack: T2 baseline #98 → T2-A #99 → T2-B #103 → T2-E #104 → T2-F #105.
Current canonical PR: #105 (`agent/t2-f-global-recertification`).
Last code-bearing candidate HEAD certified by CI: `4d5ce377079f0304323e0aa9c2abf16824f7ceb0`.
Certified PR merge ref: `a851cc56c16ccfb49eecb3f5af87b719800ed567`.
Exact automated evidence: CI #628 / run `31957613657` — SUCCESS.

Parallel closeout PR #102 is superseded by this stack. Its useful LivePreview accessibility delta was migrated to #105 before closure.

## Proof contract

- **CODE VÉRIFIÉ**: demonstrated by inspected source/diff.
- **TEST EXÉCUTÉ**: demonstrated by a real repository run.
- **RUNTIME / VISUEL**: requires authenticated/browser evidence.
- **CERTIFICATION AUTOMATISÉE**: exact code-bearing head passes repository CI/tests/build.
- **CERTIFICATION FINALE**: additionally requires the remaining runtime/browser/PDF/financial gates below.

## T2-A — Information architecture

**State: CODE + AUTOMATED TESTS VERIFIED — AUTHENTICATED RUNTIME OPEN**

Verified:
- one canonical P1→P7 vocabulary/parser;
- dormant `ai` removed from certifiable tab types and rejected by URL parsing;
- no AI execution plumbing in `useDocumentGenerator`;
- P7→P3 transfer remains explicit and filtered through `convertPlanActsToQuoteItems()`;
- navigation dirty-state policy tests pass in CI #628.

Open:
- authenticated browser URL/navigation verification.

## T2-B — Preview truth / freshness

**State: CODE + AUTOMATED CONTRACTS VERIFIED — BROWSER OPEN**

Verified:
- deterministic `documentPreviewFingerprint()` covers document-domain state;
- visible stale PDF is suppressed while regeneration is pending;
- preview freshness resets correctly on close/reopen contract;
- synthetic `Espèces` for `EN_ATTENTE` is removed;
- Honoraires emits `mode_reglement` only for `PAYE`;
- fingerprint/controller regression tests pass in CI #628.

Open:
- authenticated browser rapid edits / tab switches / preview close-reopen / stale-PDF verification.

## T2-C — Shell decomposition

**State: ENGINEERING BOUNDARIES VERIFIED + AUTOMATED REGRESSION PASS**

Verified boundaries:
- `useDocumentHubNavigation`: URL sync, dirty guards, discard flow, `beforeunload`, P3→P4 reset routing;
- `useDocumentHubPatient`: patient/session boundary;
- `DocumentHubPreview`: preview freshness boundary;
- `DocumentHubDialogs`: modal boundary;
- `DocumentHubContent`: P1→P7 page-studio rendering boundary;
- root `DocumentHub`: orchestration/shell composition.

`DocumentHubDecomposition.t2c.test.ts` passes in CI #628.

Open:
- authenticated navigation/browser regression.

## T2-D — Accessibility residual closeout

**State: CODE + AUTOMATED TESTS VERIFIED — BROWSER KEYBOARD MATRIX OPEN**

Verified:
- LivePreview labelled dialog semantics;
- initial close focus;
- Escape close;
- loading announcement;
- discard/duplicate modal semantics;
- legal annotation switch semantics;
- relevant accessibility regressions pass in CI #628.

Open:
- authenticated browser keyboard/focus/Escape matrix.

## T2-E — Product polish

**State: CODE + AUTOMATED SOURCE GATES VERIFIED — VISUAL MATRIX OPEN**

Verified:
- canonical patient/document labels;
- dark-mode contrast/source polish retained;
- explicit `Préparer impression` label;
- touch/focus source invariants;
- product-polish source tests pass in CI #628.

Open:
- browser visual review at 390/430/768/1280;
- real dark-mode and overflow verification.

## T2-F — Global recertification

**State: AUTOMATED EXACT-HEAD CODE CERTIFICATION PASS — FINAL RUNTIME GATES OPEN**

CI #628 / run `31957613657` completed SUCCESS on the code-bearing candidate:

- Frontend: **69/69 test files PASS**;
- Frontend: **296/296 tests PASS**;
- Frontend production build: **PASS**;
- Backend: **2635 passed / 7 skipped**;
- Backend warnings: **4 SQLAlchemy warnings**, non-failing and unrelated to T2 Document Studio;
- Prod safety check: **PASS** in CI development environment;
- Negative production guard: **PASS**.

This proves repository-level automated source/test/build compatibility for the code-bearing candidate. It does **not** prove authenticated browser behavior, real print output, persisted financial reconciliation, or clinical/regulatory human certification.

## Independent anomalies / non-T2 blockers

- CI dependency install force-pins `httpx==0.27.2` after dependencies requiring 0.28.x; CI still passes, but dependency hygiene remains a separate issue.
- npm install reports dependency vulnerabilities; no security certification is inferred from CI success.
- GitHub Actions warns that Node 20-based action runtimes are deprecated/forced onto Node 24.
- No Playwright/Cypress/Puppeteer harness exists in the repository.
- The connected Vercel account exposes no Digital Crown project, so no authenticated browser certification path is available through that connector.

## Remaining critical path

1. authenticated runtime/browser access for navigation, dirty guards, preview freshness and keyboard/focus;
2. responsive/dark-mode matrix at 390/430/768/1280 using before/mockup/after evidence where visual changes are evaluated;
3. real PDF/print evidence;
4. persisted P3/P4/P5 financial reconciliation evidence;
5. separate clinical/regulatory human certification where required;
6. only after these gates: final ready/merge decision.

PR #105 remains draft. No production-ready, merge-ready, or final T2 certification claim is made.

No percentage is assigned because the canonical roadmap still has no validated weighting model.
