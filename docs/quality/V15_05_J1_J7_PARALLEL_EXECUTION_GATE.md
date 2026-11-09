# Digital Crown — V1.5 LOT05 — seven coordinated jalons, single integrated gate

**Date:** 2026-11-09. **Decision:** execute J1–J7 concurrently in isolated, reproducible FAKE-only validation lanes, sharing a single decision and final clinical NO-GO. The seven jobs MAY all succeed as a synthetic lab without implying clinical import is ready.

## Current master truth, not a new plan masquerading as delivery

- The original SQL Migration Wizard preparation 05.1–05.6 was merged as [PR #890](https://github.com/hraaaaf/Digital_crown/pull/890), validated with the [post-merge PostgreSQL/Windows run #38591351010](https://github.com/hraaaaf/Digital_crown/actions/runs/38591351010). That scope includes the inspector, explicit mapping draft, synthetic 100-patient/200-appointment rehearsal, owner-facing Mapping Studio and **disabled** import control.
- [PR #1240](https://github.com/hraaaaf/Digital_crown/pull/1240) read-only lab was merged. It does not install Open Dental or produce a GUI clinical CSV.
- Open Dental is an **optional legacy compatibility example**, not a prerequisite or the core of LOT05. [#1243](https://github.com/hraaaaf/Digital_crown/pull/1243) is documentation-only DRAFT.
- UI theme [PR #1242](https://github.com/hraaaaf/Digital_crown/pull/1242) is parked: OWNER NO-GO on Dark logo. It is not in this LOT05 branch.

## Seven concurrent tracks — one risk-ordered integration contract

| Track | Goal / observed success condition on the synthetic lab | Still required for a true clinical-ready claim |
|---|---|---|
| **J1 Inspection** | Existing **05.1** inspector reads a real, cold SQLite fake-source file in staging, SHA matched, only metadata enumerated, zero import | Native PostgreSQL / MySQL / MariaDB dump adapters and real export schemas permitted by contract |
| **J2 Mapping** | Existing **05.2** immutable MappingDraft contains explicit decisions, UNMAPPED origin marker, exact source/target SHA revalidation, forged approval rejected | Actual Digital Crown ORM/physical schema coverage; authenticated owner-reviewed transformation decisions |
| **J3 Dry-run** | Real 100 fake patients + 2 practitioners + 200 RDV/acts/payments + 40 fake assets counted; orphan source, financial divergence and source mutation cause refusal; no target writes | Domain-complete, real-vendor-source, full collision/unknown-code report + privacy safe presentation |
| **J4 Identity** | 100 artificial patients + 2 artificial practitioners inserted **only** into a disposable local SQLite scratch target with tenant/legacy-ID key, duplicate collision rejects | Real tenant ACL, local target commit protocol, human deduplication adjudication and clinical schema migration |
| **J5 RDV/acts/finances** | 200 synthetic appointments and 200 acts and 200 payments satisfy SQL FK, source amounts verified (2,000,000 charged vs 1,000,000 paid cents), orphan/overpayment rejected | Actual clinical accounting, historical payments/act codes and administrator reconciliation approval |
| **J6 Docs/media** | 20 fake documents + 20 fake image blobs have verified SHA, relative allowlisted paths, no symlink/hardlink, scratch-vault copy verified; tamper refused | Real local media archive/manifest permissions and patient attachment reconciliation |
| **J7 Recovery** | True on-disk scratch SQLite backup, simulated crash mid-transaction rollback, artificial batch import, verified scratch media copy, then SQL DB + vault restore to original state and source preservation | Real BackupService + encrypted SQLCipher/WAL/production-equivalent PostgreSQL, multi-process crash/restoration, owner authorization for clinical rollout |

**Test code:** `backend/tests/test_lot05_j1_j7_parallel_fue_v15.py` — seven methods; each creates and deletes its own `TemporaryDirectory`, **never accepts a path, database or patient record from the operator**. All source names are `FAKE_...`, files are fabricated binary strings and no real clinical records or files are used. Uses actual existing 05.1 / 05.2 modules, then a **test-only** scratch schema for J4–J7.

**Execution:** `.github/workflows/v15-05-seven-jalons-parallel-fake-lab.yml` — seven independent GitHub-hosted Ubuntu/Python 3.12 jobs executed with `max-parallel: 7` (not seven claims from one test). Exact PR HEAD checked before any job, no frontend, API, migration or deployment steps. Each job uploads a *zero-PHI* verdict JSON. One final fail-closed aggregate job requires seven SUCCESS results.

**Non-negotiable flags:** all successful test verdicts must still state `clinical_import_permitted=false`, `cabinet_database_accessed=false`, `deployment=false`. No path to activate the real Import button; no clinical data read/write; no production config, Vercel, EULA or install action.

## Human GO/NO-GO sequence after seven lab lanes

1. Require all seven jobs **SUCCESS on the exact branch SHA**, inspect the actual jobs and JSON, and review negative tests. No skipped J task counts as success.
2. Independently review the J1–J7 fake-only implementation for mistakes, overstatement and unsafe file paths.
3. Keep all product import gates FALSE. Before any actual source data, separately validate source rights/format, authenticated owner identity, full ORM + physical schema and tenant reconciliation.
4. Before any cabinet mutation, demonstrate tested backup/restore of the actual local encrypted database, WAL, attachments and media; rollback and post-crash idempotency; sample-level clinician approval.
5. Merge only proven fake-only integration under owner approval; NO clinical activation and NO deployment by inference.

**STOP:** If one of seven synthetic jobs fails or if patient/production paths are involved, correct the failing lane and rerun exact-HEAD. Never hide a failed lane behind the other six.
