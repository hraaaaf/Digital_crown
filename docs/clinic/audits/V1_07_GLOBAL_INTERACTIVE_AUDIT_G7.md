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
