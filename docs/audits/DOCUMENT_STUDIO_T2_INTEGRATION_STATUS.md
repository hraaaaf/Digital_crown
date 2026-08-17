# Document Studio — T2 Integration Status

Date: 2026-08-17
Canonical stack: T2 baseline #98 → T2-A #99 → T2-B #103 → T2-E #104 → T2-F #105.
Current canonical PR: #105 (`agent/t2-f-global-recertification`).
Runtime-certified source HEAD: `677d43a57f9cf564922370d3922c6a15b6ea138f`.

## Proof contract

- **CODE VÉRIFIÉ**: demonstrated by inspected source/diff.
- **TEST EXÉCUTÉ**: demonstrated by a real repository run.
- **RUNTIME / VISUEL**: only authenticated/browser evidence counts.
- **CERTIFICATION**: separate final gate; never inferred from code presence alone.

## Exact-head automated proof

The runtime-certified source HEAD `677d43a57f9cf564922370d3922c6a15b6ea138f` has two independent exact-head green runs:

- T2 Runtime Browser Certification #39 / run `31984350987`: **SUCCESS**;
- CI #720 / run `31984350982`: **SUCCESS**.

CI #720 verified:
- frontend test suite: SUCCESS;
- frontend production build: SUCCESS;
- backend tests & hardening: SUCCESS;
- production negative guard: SUCCESS.

Runtime #39 verified:
- authenticated browser matrix: 7/7 pages green;
- light responsive viewports: 390x844, 430x932, 768x1024, 1280x900;
- dark-mode verification: 1280x900;
- all seven page scorecards: overall 10/10 in the automated matrix;
- rapid-navigation stress: PASS;
- strict runtime PDF: generation HTTP 200, fetch HTTP 200, `application/pdf`, `%PDF` signature;
- browser print runtime path: PASS;
- PDF freshness after rapid edits: PASS;
- persisted P3/P4/P5 financial reconciliation: PASS.

## T2-A — Information architecture

**State: TECHNICAL RUNTIME PASS**

Verified:
- canonical P1→P7 vocabulary/parser;
- dormant `ai` rejected by certifiable navigation/types;
- no AI execution plumbing in `useDocumentGenerator`;
- explicit P7→P3 filtered conversion;
- authenticated browser navigation across the certifiable Document Studio surface passes in #39.

## T2-B — Preview truth / freshness

**State: TECHNICAL RUNTIME PASS**

Verified:
- deterministic preview fingerprint;
- fingerprint-driven preview controller;
- stale PDF hidden during regeneration;
- no synthetic `Espèces` for pending state;
- installment payload serializable;
- rapid-edit freshness runtime gate PASS in #39;
- latest payload observed as `T2 Freshness C` / `Version PDF C`;
- first and second PDFs both HTTP 200 / `application/pdf`;
- SHA-256 hashes differ, proving regenerated output rather than stale reuse.

## T2-C — Shell decomposition

**State: TECHNICAL PASS**

Verified boundaries:
- `useDocumentHubNavigation`;
- `useDocumentHubPatient`;
- `DocumentHubPreview`;
- `DocumentHubDialogs`;
- `DocumentHubContent`;
- root `DocumentHub` reduced to orchestration/shell composition.

Relevant decomposition regression tests pass in the exact-head CI.

## T2-D — Accessibility residual closeout

**State: TECHNICAL BROWSER PASS**

Verified in source/tests and authenticated browser matrix:
- modal semantics;
- initial close focus;
- Escape handling;
- announced loading state;
- labelled discard/duplicate dialogs;
- legal annotation switch semantics;
- responsive/runtime action-path coverage across the certified matrix.

## T2-E — Product polish

**State: TECHNICAL VISUAL PASS**

Verified:
- canonical labels and action hierarchy;
- dark-mode source hardening;
- prepared-print accessible label;
- 390/430/768/1280 light captures;
- 1280 dark captures;
- no certified responsive overflow findings;
- all seven automated visual scorecards: 10/10.

## T2-F — Global recertification

**State: TECHNICAL INTEGRATION CERTIFICATION PASS ON SOURCE HEAD**

Closed with exact evidence on `677d43a57f9cf564922370d3922c6a15b6ea138f`:
- CI #720 SUCCESS;
- runtime/browser #39 SUCCESS;
- 7/7 browser pages and rapid-navigation stress PASS;
- strict runtime PDF PASS;
- print runtime path PASS;
- rapid-edit PDF freshness PASS;
- P3/P4/P5 persisted reconciliation PASS.

Financial evidence from #39:
- P4 paid exact payment: **888 MAD**;
- P5 installment plan total: **1,200 MAD**;
- rows: **500 + 700 MAD**;
- collected: **500 MAD**.

## Print boundary

The automated browser gate certifies this runtime chain:

`PDF blob → hidden iframe → onload → contentWindow.focus() → contentWindow.print()`.

Exact #39 trace:
- iframe created: 1;
- blob source observed: 1;
- iframe appended: 1;
- onload assigned: 1;
- focus calls: 1;
- print calls: 1;
- fallback `window.open`: 0.

Because Chromium headless does not reliably emit the PDF plugin iframe load event, the harness supplies a controlled PDF load signal. Therefore CI certifies the application print callback path and real PDF generation/retrieval, **not observation of a native operating-system print dialog**.

## Runtime PDF evidence

Exact #39 strict PDF probe:
- generate status: 200;
- PDF fetch status: 200;
- content type: `application/pdf`;
- signature: `%PDF`;
- bytes: 2437.

## Independent anomalies

These are separate from the T2 technical integration gate and remain open:
- CI force-pins `httpx==0.27.2` although newer Firebase/Ultralytics packages require 0.28.x;
- npm install reports dependency vulnerabilities; no security certification is claimed;
- GitHub Actions reports Node 20 action-runtime deprecation warnings.

## Remaining external/human gates

The technical T2 integration gates are closed on the runtime-certified source HEAD. This status does **not** claim:
- native OS print-dialog observation;
- security certification;
- clinical/regulatory human certification;
- production-ready status.

PR #105 remains draft pending exact-head recertification of this documentation closeout and stacked-PR merge-topology review.

No percentage is assigned because the canonical roadmap has no validated weighting model.
