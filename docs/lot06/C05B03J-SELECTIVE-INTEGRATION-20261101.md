# LOT06 C05B-03J — selective source-contract integration (2026-11-01)

## Decision and hard stops

**Cabinet target:** existing on-prem encrypted SQLCipher database and AES-GCM ClinicalAsset media. The PostgreSQL receipt-authority candidate from LOT06-C05A is **test-only**, not a second production authority. This is the bounded integration path approved for study by the owner; it does **not** authorize altering a deployed cabinet schema. Any actual Alembic authority migration requires separate isolated upgrade, backward-compatibility, downgrade/restore and human release gate.

**Scope here:** child of DRAFT #1172 / `4abfad34cfd03a764a74dd89507d2a32a63a581f`. Import only three dormant services from witnessed DRAFT #1165 / `8f99cbd4fc5045c530d73270ae4dbecdb4ac8c24`: read-only patient/RDV preflight, TEST-only in-memory transfer ledger, and LAB-only staff/device/media binding. Do not mount new FastAPI routes or install a bridge. Existing protected ClinicalAsset storage and SQLCipher authority files on the child branch are preserved unchanged. No data or migration.

## Correction of the historical reconciliation interpretation

The #1172 reconciliation audit compares historical `90fd4a9543057d0af1f56d5d72845d8fa5738f5b` with `8f99cbd4fc5045c530d73270ae4dbecdb4ac8c24`. It saw **808 target-only / 450 source-only commits**, a merge-tree conflict and **64 critical-file differences**. These are **differences**, not 64 individually enumerated merge conflicts. The later HEAD #1172 `4abfad34` already contains **five of seven** source-contract files the historical audit listed as missing, verified by matching Git blob SHAs. It did *not* have the LAB media gate, its TEST-dependent prerequisites, or the bridge of #909. The historical audit must not be treated as a fresh diff against the latest child branch.

## Testable guarantees for this narrow step

- Explicit patient or appointment only; no inference from filenames or nearest appointment.
- A matching patient still requires human staff confirmation.
- Tenant mismatch and missing appointment rejected.
- The transfer and media gate refuse production/development, even if an opt-in flag was set.
- Existing read-only ClinicalAsset AES-GCM verification tests run against the combined HEAD.
- No new API router import in `backend/main.py`; no product upload, receipt, or clinical ACK.
- Same-head test evidence is required; all claims remain provisional until CI succeeds.

## Still missing for product integration

The LAB media gate is intentionally not mounted and cannot issue a product receipt. #909 background acquisition bridge is absent on this branch. To close the product Goal, link a real supervised and authorized Windows service to staff/device identity, actual patient confirmation, a canonical SQLCipher transaction storing ClinicalAsset receipt/audit/outbox, persisted idempotency/ACK-loss and recovery, verified ACL/DPAPI under installed service, and a true desktop FUE on ONE HEAD. Check Alembic chain and rollback before any schema change; physical scanner/driver FUE stays in LOT10.4. No forced merge of diverged histories.

**Gates:** `READY_TO_MERGE=false`; `PRODUCT_READY=false`; `CLINICAL_GO=false`. No master merge, Vercel, cabinet installation or patient data authorized.
