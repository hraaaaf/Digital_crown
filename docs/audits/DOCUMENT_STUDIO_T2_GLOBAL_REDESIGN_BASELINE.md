# Document Studio — T2 Refonte intelligente finale / baseline

Date: 2026-08-16
Baseline: `b67edc2848540dc231b84f0a3d0163259cde0047` (T1-F head)
Scope: final information architecture, interaction model, preview truth, dead paths, terminology and global recertification preparation after P1→P7 + T1 engineering.

## 1. Proof contract

- **CODE VÉRIFIÉ**: directly inspected on the exact baseline.
- **TEST EXÉCUTÉ**: only when a real run executes repository steps.
- **RUNTIME OBSERVÉ**: only when reproduced in the authenticated application.
- **CERTIFICATION**: only after exact-head automated + browser/runtime gates.

T1 remains not certified because its exact-head harness/runtime/browser gates have not executed.

## 2. Baseline architecture — CODE VÉRIFIÉ

`DocumentHub.tsx` remains the central orchestrator for P1→P7 and still carries:
- document routing/tab state;
- page-specific draft state;
- accounting Zustand state;
- patient fetch + smart suggestion fetch;
- preview orchestration;
- dirty navigation arbitration;
- archive/generation wiring;
- duplicate and discard dialogs;
- legacy `ai` route compatibility.

This is functional consolidation, but the component now owns too many independent concerns for a final premium architecture.

## 3. GARDER

- One visible Document Studio shell with a stable patient identity.
- Canonical P1→P7 navigation.
- T1 patient-boundary reset/cancellation contract.
- One dirty-state arbitration path for manual + URL navigation.
- Dedicated page engines/components for prescription, certificate, accounting, installments, libre and diagnostic companion.
- Explicit preview as read-only PDF output.
- P7→P3 conversion as an explicit user action.

## 4. CORRIGER / REFAIRE

### T2-P0-1 — Residual T1 accessibility gap in DocumentHub dialogs

**CODE VÉRIFIÉ**

The discard-draft and duplicate-warning overlays in `DocumentHub.tsx` are visually modal but are not declared with `role="dialog"`, `aria-modal="true"` and labelled/described relationships. The prescription legal-annotation switch has `role="switch"` / `aria-checked` but no explicit accessible name linked to the adjacent visible text.

**Impact:** T1-E cannot be called fully converged at runtime/accessibility level until these controls are hardened and browser-checked.

### T2-P0-2 — Preview freshness contract is implicit and incomplete

**CODE VÉRIFIÉ**

The automatic preview effect watches only a subset of document inputs (`drugs`, `items`, certificate type/days/start date, payment mode, libre title/content, date, active tab and generator callback). Other payload inputs are not explicitly present in that dependency set, including several libre options/custom fields and financial state.

**Risk:** a visible preview can become stale relative to the current editor state unless the callback identity happens to change. Final architecture must make preview freshness explicit and testable, not incidental to hook identity.

### T2-P1-1 — Dormant `ai` route remains in the canonical hub type

**CODE VÉRIFIÉ**

`HubDocumentType` and URL parsing still accept `ai`. T1-C disabled execution, but the route remains part of the public hub state and preview title map still contains `Assistant IA`.

**Target:** remove the dormant route from the certifiable navigation contract, or isolate it behind a separately governed feature boundary. Do not keep a dead clinical route in the canonical document type.

### T2-P1-2 — Dead AI plumbing remains wired through the shell

**CODE VÉRIFIÉ**

`DocumentHub` still passes `aiReport`, `onGenerateAI` and `loadingAi` into `StudioFooter` even though the footer now renders the clinical function as unavailable. `useDocumentGenerator` still owns `aiReport` / `loadingAi` state.

**Target:** delete dead shell plumbing from the certifiable path. Historical backend functionality may remain separately, but the main Studio should not carry unused clinical-AI state.

### T2-P1-3 — Naming model is inconsistent

**CODE VÉRIFIÉ**

The same P7 surface is represented as:
- internal tab key `plan`;
- UI label `Compagnon Diagnostique`;
- preview title `Stratégie Clinique`;
- component `TreatmentPlanStudio`.

P5 similarly uses internal `echeancier` while the canonical page label is `Suivi Paiement`.

**Target:** separate stable internal identifiers from one canonical product vocabulary and remove legacy product-language drift.

### T2-P1-4 — DocumentHub remains a high-coupling orchestration monolith

**CODE VÉRIFIÉ**

The hub owns page state, global-store interactions, API reads, navigation guards, preview timing, generation, dialogs and cross-page conversion.

**Target:** split into explicit boundaries:
1. `DocumentStudioRouter` — page identity/navigation only;
2. `DocumentSessionBoundary` — patient scoped reset/dirty lifecycle;
3. `DocumentPreviewController` — preview freshness/generation only;
4. page studios — domain-specific state/actions;
5. global shell — header/tabs/footer/dialogs only.

### T2-P1-5 — Synthetic payment-mode transport remains architectural debt

**CODE VÉRIFIÉ**

For non-PAYE Honoraires, `DocumentHub` passes `Espèces` into generator parameters solely to satisfy an older frontend validation contract, while the real financial contract says EN_ATTENTE has no payment method.

**Target:** remove synthetic transport values. Validation types must represent the real domain: payment mode optional unless `PAYE`.

### T2-P1-6 — P7→P3 conversion bypasses the canonical tab-transition function

**CODE VÉRIFIÉ**

The conversion callback writes quote items, then directly calls `setActiveTab('devis')` + URL sync instead of the common `handleTabChange`/transition contract.

This may be intentional after an explicit conversion, but the architecture should expose a named forced/committed transition primitive rather than bypassing the router contract ad hoc.

## 5. SIMPLIFIER / SUPPRIMER

- Remove `ai` from `HubDocumentType` and URL parsing once compatibility migration is decided.
- Remove `aiReport`, `loadingAi`, `handleGenerateAI` from the main Document Studio generation contract.
- Remove stale “IA” comments/naming for deterministic or disabled features.
- Remove synthetic `Espèces` transport for EN_ATTENTE.
- Replace page-name drift (`plan`, `TreatmentPlan`, `Stratégie Clinique`) with one canonical display vocabulary.
- Avoid generic `any` payload/state for installments and smart suggestions where a bounded type already exists or can be defined.

## 6. T2 corrective lots

### T2-A — Information architecture cleanup
- canonical product vocabulary;
- remove dormant `ai` route from certifiable Studio;
- delete dead AI props/state;
- formalize committed P7→P3 transition.

### T2-B — Preview truth/freshness
- explicit preview input fingerprint or complete dependency contract;
- invalidate preview immediately on relevant edits;
- no stale PDF presented as current;
- remove synthetic financial transport values.

### T2-C — Shell decomposition
- extract router/session/preview controllers from `DocumentHub`;
- keep page studios domain-local;
- preserve T1 isolation/dirty invariants with regression gates.

### T2-D — Accessibility residual closeout
- harden remaining `DocumentHub` dialogs/switch naming;
- keyboard focus/escape semantics;
- 390/430/768/1280 shell matrix.

### T2-E — Product polish
- loading/empty/error/success consistency;
- typography/spacing/terminology consistency;
- dark-mode consistency;
- compact patient identity retained in all states.

### T2-F — Global recertification
- targeted P1→P7 + T1/T2 regression;
- full frontend/backend suites + production build;
- authenticated patient A→B + dirty navigation matrix;
- financial P3/P4/P5 scenarios;
- real PDF/preview/print matrix;
- browser 390/430/768/1280 + keyboard/a11y;
- separate human clinical/pharmacological/financial/regulatory gates where required.

## 7. Current decision

T2 may proceed in engineering while T1 runtime execution is externally blocked, but T2 must remain stacked/draft and cannot be globally certified or merged as final closeout until T1 exact-head execution and the remaining P1→P7 gates are reconciled.

No percentage is assigned: the canonical roadmap still has no validated weighting model for the global chantier.
