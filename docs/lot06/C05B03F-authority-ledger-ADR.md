# LOT06 C05B-03F - Authority ledger architecture decision (proposed)

Status: PROPOSED / NOT PRODUCT READY - 2026-11-01 - PR #1172 Draft.

Decision: local encrypted SQLCipher is the on-prem target for the capture authority ledger, co-resident with ClinicalAsset. The P1 remote PostgreSQL patient services and old in-memory transfer laboratory are NOT device-trust authorities. No bulk merge of backend/main.py.

The migration candidate lives in isolated_fue_lot06c/migrations, NOT in alembic/versions; Alembic's production head and empty-database baselining are untouched. It is hard-gated to test + isolated + explicit feature flag on a native SQLCipher connection with foreign keys ON.

Five namespaced tables: devices, approvals, receipts, audit, outbox. Composite identity keys, immutable receipts and protected approval version. SQL triggers enforce scoped staff, station, patient and asset at approval insertion. They are SQLite-specific and will need cross-dialect review if a product migration is proposed.

Authority still missing: authenticated clinical device enrollment/rotation/revocation, staff JWT/session + workstation and one-use human review challenge, real clinical API endpoint, independent credential issuer, runtime transaction authorization and Windows tests. No product endpoint is activated by this change.

Safety: downgrade rejects ANY nonempty ledger. Empty schema can downgrade. A populated rollback requires a pre-upgrade encrypted snapshot and operator approval, NOT destructive dropping of clinical receipts. SQL and filesystem are not globally atomic; WAL NORMAL is not a hardware power-loss certification.

Product release gates remain blocked: PRODUCT_READY=false, CLINICAL_GO=false, READY_TO_MERGE=false. No cabinet data, deploy, Tailnet or merge without explicit human approval.
