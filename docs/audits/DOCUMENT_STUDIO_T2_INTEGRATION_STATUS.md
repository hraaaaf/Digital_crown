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

**State: PARTIAL — CODE VÉRIFIÉ**

Implemented:
- one canonical P1→P7 vocabulary;
- canonical ordered certifiable tab list and parser;
- parser rejects dormant `ai` as certifiable tab;
- canonical P5/P7 preview labels;
- StudioTabs/Header/Footer presentation components decoupled from the DocumentHub type import;
- shell navigation emits only P1→P7 tab events;
- regression source gates added.

Open:
- remove `ai` from the DocumentHub monolith type/URL parser/preview map;
- remove dead `aiReport` / `loadingAi` / `handleGenerateAI` generator plumbing;
- formalize committed P7→P3 transition inside the hub.

Reason still open: these changes touch the large DocumentHub/generator orchestration surface while no repository runner currently executes code.

## T2-B — Preview truth / freshness

**State: FOUNDATION IMPLEMENTED — TEST PRÉPARÉ**

Implemented:
- deterministic `documentPreviewFingerprint()` covering active page, patient/date, prescription, certificate, financial state, installments, selected teeth, every Document Libre custom/page/alignment field, legal annotations and P5 payload;
- `useDocumentPreviewController()` regenerates only on an enabled fingerprint change and forgets freshness when preview closes;
- regression tests cover previously omitted Libre/financial/selected-teeth/legal/P5 inputs.

Open:
- wire fingerprint/controller into DocumentHub;
- invalidate/mark stale visible PDF immediately on fingerprint change;
- remove synthetic `Espèces` transport for EN_ATTENTE.

## T2-C — Shell decomposition

**State: OPEN**

Target remains:
- router/navigation boundary;
- patient/session boundary;
- preview controller boundary;
- domain-local page studios;
- shell-only header/tabs/footer/dialog composition.

No extraction is claimed yet.

## T2-D — Accessibility residual closeout

**State: PARTIAL — CODE VÉRIFIÉ / TEST PRÉPARÉ**

Closed on #105:
- non-inline `LivePreview` exposes `role="dialog"` + `aria-modal`;
- dialog is labelled by its visible document title;
- focus moves initially to `Fermer`;
- Escape closes the preview;
- loading state is announced via `role="status"` / `aria-live`;
- Vitest regression is versioned for dialog semantics, initial focus and Escape.

Still open:
- DocumentHub discard-draft dialog labelling/semantics;
- duplicate dialog labelling/semantics;
- legal-annotation switch explicit accessible name/relationship;
- authenticated browser keyboard/focus/escape matrix.

No Vitest PASS is claimed for the new LivePreview regression until a repository execution path runs it.

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

`scripts/certify_document_studio_t2.sh` requires:
- Python 3.12;
- Node 20;
- clean exact-head worktree;
- positive production-safety gate;
- targeted T1/T2 regression;
- full backend suite;
- full frontend suite;
- frontend production build;
- prerequisite P3→P7/T1 harness presence;
- negative production-safety gate.

No PASS is claimed merely because the harness exists.

## Infrastructure evidence — exact cause verified

Latest fully inspected T2-F workflow evidence before the LivePreview migration:
- head: `4af8b9a4eb11e3a1a0fa2f2830133cd96ae5a032`;
- CI run #552 / `31947430902`;
- jobs: backend, frontend and negative production guard all completed `failure` with no repository step exposed;
- backend job `95165565692`: `runner_id=0`, empty runner name, `steps=[]`;
- GitHub check annotation: `The job was not started because recent account payments have failed or your spending limit needs to be increased. Please check the 'Billing & plans' section in your settings`.

Therefore the current Actions failure is an **account Billing / spending-limit runner allocation gate**, not evidence of application-code failure. No repository test executed in that run.

LivePreview accessibility code candidate immediately before this documentation-only update: `8ce37bf15f78ebfd100b9dad2c50227f76e47580`. Its new Vitest regression is versioned but not executed yet.

Local fallback remains unavailable in this execution environment: `git` exists but `gh` is not installed and no `GH_*` / `GITHUB_*` credential is exposed to the local shell; the private repository is therefore not available as an authenticated local checkout.

## Current critical path

1. fix GitHub Billing / Actions spending limit, then run the exact current #105 head once;
2. if the runner executes, diagnose any real logs before changing code;
3. finish T2-A monolith cleanup;
4. wire T2-B preview freshness and remove synthetic payment transport;
5. perform T2-C decomposition with regression gates;
6. close remaining T2-D DocumentHub accessibility;
7. run authenticated/browser/PDF/financial matrices;
8. update final roadmap/status and only then consider merge/global certification.

No percentage is assigned because the canonical roadmap still has no validated weighting model.
