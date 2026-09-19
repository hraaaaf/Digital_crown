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
