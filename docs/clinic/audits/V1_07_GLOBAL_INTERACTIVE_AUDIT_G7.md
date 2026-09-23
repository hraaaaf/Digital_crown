# Digital Crown V1-07 — Global Interactive Audit — G7

Status: IN PROGRESS

## Goal
Certify Stock, partner marketplace/procurement, Library/Science Hub and remaining G0-exposed operational surfaces.

## Success
- stock CRUD/quantity/filter/error boundaries are behaviorally proved;
- marketplace browse/cart/checkout/refusal states are proved;
- supplier/product/admin reconciliation mutations are proved;
- Library/Science Hub navigation/search/filter/deep-link controls are proved;
- exact-head frontend tests + build pass.

## Verified surfaces

### Stock
`frontend/src/pages/StockPage.tsx`
- read items + alerts;
- add/edit item;
- quantity decrement/increment with floor 0;
- delete;
- category/search filters;
- cache invalidation after mutations.

### Partner marketplace
- `frontend/src/pages/PartnerMarketplacePage.tsx`
- `frontend/src/pages/PartnerSupplierPage.tsx`
- `frontend/src/pages/PartnerProductPage.tsx`
- hook: `frontend/src/features/partnerMarketplace/usePartnerMarketplace.ts`

### Partner administration
`frontend/src/pages/PartnerCatalogAdminPage.tsx`
- supplier create;
- product create;
- product filtering;
- partner-order reconciliation;
- reload/error/success truth.

### Library / Science Hub
- `frontend/src/features/clinical-ref/EliteLibrary.tsx`
- `frontend/src/features/clinical-ref/EliteScienceHub.tsx`

## Certification gate
Do not certify G7 until all exposed controls have behavioral mapping and exact-head frontend tests/build are green.


## Stock behavioral proof

`frontend/src/pages/StockPage.g7Interactive.test.tsx`
- load stock + alerts;
- search/category filters;
- add with numeric/null payload normalization;
- edit via PATCH;
- increment/decrement quantity;
- delete current control;
- query refresh after mutation ACK.

## Open Stock defects

1. Stock read failure currently falls through to `items = []`, so an unavailable backend can be rendered as “Aucun article” instead of an explicit unverified/error state.
2. Permanent stock deletion currently executes immediately from the trash button with no confirmation.
3. Stock add/edit/delete/quantity mutation failures have no explicit user-facing refusal/error state in this page.

These are product-truth/safety defects. G7 cannot be certified while they remain unresolved.


## Additional G7 behavioral proof

1. `frontend/src/features/partnerMarketplace/usePartnerMarketplace.g7Interactive.test.tsx`
   - empty-cart guard;
   - required-customer guard;
   - discontinued product cannot enter cart;
   - rejected order preserves cart;
   - catalog read failure remains explicit/unverified;
   - local filters are non-mutating.

2. `frontend/src/pages/PartnerMarketplacePage.g7Interactive.test.tsx`
   - search / refresh / availability / category controls;
   - visible +/− quantity controls;
   - checkout open/close;
   - customer edits delegated to canonical controller;
   - checkout closes only on successful draft save;
   - catalog error retry;
   - empty-cart controls disabled.

3. `frontend/src/pages/PartnerCatalogAdminPage.g7Interactive.test.tsx`
   - canonical admin reads;
   - supplier creation + refusal;
   - product creation with numeric/benefit normalization;
   - local catalog filters;
   - partner-order reconciliation + reload;
   - reconciliation refusal;
   - explicit reload.

4. `frontend/src/pages/PartnerDetailPages.g7Interactive.test.tsx`
   - supplier canonical load;
   - supplier category/specialty filtering;
   - supplier retry/reload;
   - product-detail navigation;
   - product API truth;
   - shared-cart quantity persistence;
   - discontinued-product ordering lock;
   - explicit unavailable/not-found state.

5. `frontend/src/features/clinical-ref/EliteLibrary.g7Interactive.test.tsx`
   - search/reset;
   - local favorite persistence;
   - sort and grid/list;
   - deep-link open/close;
   - recent history;
   - previous/next;
   - print;
   - immersive care mode;
   - command palette / keyboard.

6. `frontend/src/features/clinical-ref/EliteScienceHub.g7Interactive.test.tsx`
   - search title/author;
   - category filtering;
   - truthful no-results state;
   - exact safe external-study links;
   - router back navigation.

## G7 reconciliation

All inspected G7 families now map to behavioral proof:
- Stock;
- Marketplace controller and visible checkout controls;
- Supplier/Product detail pages;
- Partner catalog administration and order reconciliation;
- Clinical Library;
- Science Hub.

G7 remains **IN PROGRESS / NOT CERTIFIED** because the three documented Stock product defects remain open and exact-head frontend tests/build have not yet been proven green.


## Stock remediation candidate
The three Stock blockers were remediated in code:
1. read failure now renders explicit unverified/error state + Retry;
2. delete now requires an explicit in-app confirmation dialog;
3. add/edit/quantity/delete refusal is surfaced visibly without false success.

Behavioral proof:
- `frontend/src/pages/StockPage.g7Interactive.test.tsx` — read-error/Retry, delete confirm/cancel/refusal, quantity refusal, add refusal and edit refusal with state preserved.

UI target/reference:
- `docs/ux/V1_07_G6_G7_TRUTH_SAFETY_GOAL_UI.md`

Visual evidence workflow:
- `.github/workflows/v1-07-truth-safety-visual-evidence.yml`

Status: CODE REMEDIATED — CERTIFICATION PENDING matched BEFORE/AFTER evidence + exact-head tests/build.


## Browser escalation
G7 requires real Chromium action proof for Stock, Marketplace, partner administration and Library/Science Hub. Stock destructive/refusal truth must be exercised in-browser, not inferred from component tests. Marketplace cart/checkout and partner-admin mutations require visible result/refusal proof.


## Deep browser reconciliation — 2026-09-23

The G7 browser gate now proves the exposed operational contracts through their actual consequences:

### Stock
- explicit read failure, no false empty state, Retry -> verified data;
- search/category filters;
- quantity ACK and refusal/non-mutation;
- add ACK and refusal with modal preserved;
- edit ACK and refusal/non-mutation;
- delete cancel, refusal/non-mutation, and ACK removal;
- add/edit overlay now exposes dialog semantics and named close control;
- quantity +/- controls now have action-specific accessible names.

### Marketplace
- canonical strategy + active supplier fixture, so checkout reaches the actual POST boundary;
- search / availability / category effects and explicit catalog refresh;
- cart +/- and reload persistence;
- checkout close preserves cart;
- refused DRAFT POST preserves dialog/cart;
- successful DRAFT POST closes checkout and clears/disables cart.

### Partner administration
The previous G7 workflow had no SuperAdmin fixture, so `/approvisionnement/admin` was not browser-certifiable. The workflow now provisions an isolated T2 SuperAdmin and the browser gate covers:
- supplier create ACK/refetch and refusal/non-mutation;
- product create with numeric/benefit normalization and visible refetch;
- local catalog filtering;
- partner-order reconciliation refusal/non-mutation then ACK/refetch;
- explicit canonical reload.

### Supplier / Product details
- supplier read failure without stale cache -> Retry -> canonical data;
- supplier reload, category/specialty filters, exact product deep-link;
- product canonical links, +/- cart changes and reload persistence;
- discontinued product exposes no ordering controls;
- missing product renders explicit not-found truth and returns to catalog;
- product quantity controls now expose action-specific accessible names.

### Clinical Library / Science Hub
- search match, no-result and reset;
- favorite persistence + favorites filter after reload;
- grid/list rendered consumer proof and sort-order effect;
- protocol deep-link + recent history;
- next/previous round-trip;
- print action;
- immersive Soin mode open/close;
- command palette by button and Ctrl+K, search/open/no-result/Escape;
- recent history clear;
- Science Hub title search, author search, category purity, truthful no-result, safe external link, router back.
- stale hardcoded expectation of 4 ENDODONTIE cards was removed; certification now checks semantic category purity against the current source data.

Functional deep-check status: COMPLETE IN HARNESS. G7 remains NOT CERTIFIED until exact-head browser/CI are green and the required matched Stock truth-safety visual evidence is inspected.
