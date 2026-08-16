# Document Studio — T2 Integration Status

Date: 2026-08-16
Stack: T2 baseline #98 → T2-A #99 → T2-B #103 → T2-E #104 → T2-F current branch.

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

Reason still open: those changes require a large-monolith edit while no build/test runner currently executes repository steps.

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

**State: OPEN**

Verified residuals:
- DocumentHub discard-draft dialog needs dialog labelling/semantics;
- duplicate dialog needs dialog labelling/semantics;
- legal-annotation switch needs an explicit accessible name/relationship;
- browser keyboard/focus/escape matrix remains required.

T1-E shell-level accessibility improvements remain preserved.

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

## Infrastructure evidence

Exact checked T2-F head before this documentation-only update: `60b1bafb17e3bb7894086e977f203eac3c9b4875`.
GitHub Actions run #549 / `31947379642` concluded failure before repository execution: all three jobs (`Garde production (négatif)`, `Frontend (tests & build)`, `Tests & durcissement`) reported `steps:null`.

This is the same external runner/allocation failure class observed on earlier T1/T2 heads. The run is neither evidence of a code failure nor a PASS.

Local fallback is also unavailable in the current execution environment: no authenticated GitHub CLI/network checkout path was available, and connected Replit/Vercel tools did not expose an executable clone/build environment for this private repository.

## Current critical path

1. restore any real exact-head execution path and run `scripts/certify_document_studio_t2.sh`;
2. with build proof available, finish T2-A monolith cleanup;
3. wire T2-B preview freshness and remove synthetic payment transport;
4. perform T2-C decomposition with regression gates;
5. close T2-D residual accessibility;
6. run authenticated/browser/PDF/financial matrices;
7. update final roadmap/status and only then consider merge/global certification.

No percentage is assigned because the canonical roadmap still has no validated weighting model.
