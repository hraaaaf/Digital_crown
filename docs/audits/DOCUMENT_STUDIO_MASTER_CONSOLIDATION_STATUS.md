# Document Studio — Master Consolidation Status

## Baseline
- master source: `6301f737f59e1f5c6c0e1e79402fbd5270637617`
- branch: `refactor/document-studio-master-consolidation`

## Ported
### Prescription R2 residuals
- removed implicit network fallback from active personalized suggestion path;
- retained doctor-scoped local DB ranking;
- `record_medication_usage()` now rolls back and propagates DB failures;
- dedicated regression tests added for network prohibition and fail-visible persistence.

## Superseded
- PR #336 header specialties: current master already implements a broader dynamic header layout.

## Still to reconcile
- PR #353 certificate signature caption: KEEP.
- PR #77 P3 Devis: REBUILD ON MASTER, especially `items ↔ teeth_data` integrity and accounting transition guards.
- PR #90 P4 Honoraires: compare financial invariants against current master.
- PR #95 P5 Paiement: compare authoritative payment lifecycle against current master.
- PR #96 P6 Libre: compare archive/dirty-state lifecycle against current master.
- PR #97 P7: only non-prescriptive/safety deltas, scientific gate separate.
- PR #101 T1: rebuild shared navigation/lifecycle policy directly on master.

## Proof policy
Nothing is certified until exact-head CI/tests and required runtime/PDF/browser gates are observed.
