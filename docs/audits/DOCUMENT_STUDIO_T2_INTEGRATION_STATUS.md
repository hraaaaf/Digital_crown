# Document Studio — T2 Integration Status

Date: 2026-08-16
Canonical stack: T2 baseline #98 → T2-A #99 → T2-B #103 → T2-E #104 → T2-F #105.
Current canonical PR: #105 (`agent/t2-f-global-recertification`).
Current exact HEAD: `4546d761b7ef4643472f23e5bb3715a807dfb3e3`.

## Proof contract

- **CODE VÉRIFIÉ**: demonstrated by inspected source/diff.
- **TEST EXÉCUTÉ**: demonstrated by a real repository run.
- **RUNTIME / VISUEL**: only authenticated/browser evidence counts.
- **CERTIFICATION**: separate final gate; never inferred from code presence alone.

## Automated exact-head proof

CI #630 / run `31958552660` completed **SUCCESS** on exact documentation-closeout HEAD `4546d761b7ef4643472f23e5bb3715a807dfb3e3`.

Verified jobs:
- Frontend test suite: SUCCESS;
- Frontend production build: SUCCESS;
- Backend tests & hardening: SUCCESS;
- Production negative guard: SUCCESS.

The immediately preceding code-bearing candidate was validated by CI #628 / run `31957613657` on source HEAD `4d5ce377079f0304323e0aa9c2abf16824f7ceb0` / PR merge ref `a851cc56c16ccfb49eecb3f5af87b719800ed567` with:
- frontend **69/69 files PASS**;
- frontend **296/296 tests PASS**;
- frontend production build PASS;
- backend **2635 passed / 7 skipped**;
- production safety check PASS;
- negative production guard PASS.

The #630 descendant contains only the canonical status closeout change after that code-bearing candidate and all repository CI jobs also pass on #630.

## T2-A — Information architecture

**State: AUTOMATED SOURCE/TEST VERIFIED — AUTHENTICATED RUNTIME OPEN**

Verified:
- canonical P1→P7 vocabulary/parser;
- dormant `ai` rejected by certifiable navigation/types;
- no AI execution plumbing in `useDocumentGenerator`;
- explicit P7→P3 filtered conversion.

Open:
- authenticated URL/navigation browser verification.

## T2-B — Preview truth / freshness

**State: AUTOMATED CONTRACT VERIFIED — BROWSER OPEN**

Verified:
- deterministic preview fingerprint;
- fingerprint-driven preview controller;
- stale PDF hidden during regeneration;
- no synthetic `Espèces` for pending state;
- installment payload serializable;
- relevant Vitest contracts pass in #628/#630.

Open:
- rapid edits / tab switches / close-reopen / stale-PDF browser verification.

## T2-C — Shell decomposition

**State: AUTOMATED SOURCE/TEST VERIFIED**

Verified boundaries:
- `useDocumentHubNavigation`;
- `useDocumentHubPatient`;
- `DocumentHubPreview`;
- `DocumentHubDialogs`;
- `DocumentHubContent`;
- root `DocumentHub` reduced to orchestration/shell composition.

Relevant decomposition regression tests pass in #628/#630.

## T2-D — Accessibility residual closeout

**State: AUTOMATED SOURCE/TEST VERIFIED — BROWSER OPEN**

Verified in code/tests:
- modal semantics;
- initial close focus;
- Escape handling;
- announced loading state;
- labelled discard/duplicate dialogs;
- legal annotation switch semantics.

Open:
- authenticated keyboard/focus/Escape browser matrix.

## T2-E — Product polish

**State: AUTOMATED SOURCE/TEST VERIFIED — VISUAL OPEN**

Verified:
- canonical labels and action hierarchy;
- dark-mode source hardening;
- prepared-print accessible label;
- relevant product-polish source gates pass.

Open:
- 390/430/768/1280 browser captures;
- real dark mode and overflow verification.

## T2-F — Global recertification

**State: AUTOMATED REPOSITORY CLOSEOUT PASS — RUNTIME/HUMAN GATES OPEN**

Closed with evidence:
- code-bearing CI #628 SUCCESS;
- documentation-closeout exact-head CI #630 SUCCESS;
- canonical status synchronized to exact evidence.

Still open and not inferable from CI:
- authenticated browser matrices;
- real PDF/print output;
- persisted P3/P4/P5 financial reconciliation;
- separate clinical/regulatory human certification where required.

## Runtime/tooling boundary

No Playwright/Cypress/Puppeteer harness exists in the repository. The currently connected Vercel account exposes no Digital Crown project, so no authenticated remote browser path is available through current connected tools.

## Independent anomalies

- CI force-pins `httpx==0.27.2` although newer Firebase/Ultralytics packages require 0.28.x. This did not break #628/#630 and remains separate dependency-hygiene work.
- npm install reports dependency vulnerabilities; no security certification is claimed.
- GitHub Actions reports Node 20 action-runtime deprecation warnings.

## Current critical path

1. obtain an authenticated Digital Crown runtime/browser path;
2. execute navigation/dirty guards, preview freshness and keyboard/focus matrices;
3. execute 390/430/768/1280 + dark mode/overflow visual certification;
4. execute real PDF/print and persisted financial reconciliation checks;
5. only after those gates, consider ready/merge/final T2 certification.

PR #105 remains draft. No production-ready, merge-ready, or final T2 certification claim.

No percentage is assigned because the canonical roadmap has no validated weighting model.