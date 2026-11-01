# LOT06 C05B-03K — supervised HotFolder to SQLCipher, isolated synthetic integration

Date: 2026-11-01. Child of [PR #1179](https://github.com/hraaaaf/Digital_crown/pull/1179) at `05584a9d534ef2d0632ada76d40a31750c8aa528`. Selective source import from [PR #909](https://github.com/hraaaaf/Digital_crown/pull/909) at `78c7983de911854ebddc7526d7461ee3a2e8a8df`. No broad git merge; no existing backend file overwritten.

## Exact design

- Retain original disabled-by-default HotFolder collector, PNG structural validation, spool encryption, Windows confinement helpers, owner lock and supervised process from #909 **without editing backend/main.py**.
- Run a dedicated isolated synthetic FUE crossing the actual byte boundary: ready-manifest PNG → HotFolder two stable scans → encrypted spool → authenticated decrypt → existing scoped Patient + required staff confirmation preflight → new AES-GCM ClinicalAsset in file-backed SQLCipher → pre-approved synthetic device/staff/station ledger → immutable receipt/audit/outbox transaction and idem replay. This proves actual media bytes, **not** automatic production device enrollment or human consent.
- The existing C05B03E synthetic approval fixture is explicitly reused. Its pre-approval is not a UI action or production attestation. Isolated SQLCipher receipt is a LAB result, not product ACK.
- Negative tests: tenant/patient/device/digest claims, SQL rollback after audit, spool ciphertext tamper, non-TEST guard, duplicate HotFolder capture after restart, repeated receipt after lost ACK, supervised synthetic child startup/stop.
- CI also reruns the established FastAPI TestClient/JWT/SQLCipher FUE on the same candidate SHA. These are separate tests of actual HTTP routes in an isolated app and **do not** wire HotFolder to a production API.

## Required boundaries

`backend/main.py` and existing application routers unchanged. New modules in `tools/imaging_gateway/` remain opt-in under `ENVIRONMENT=test`, `DIGITALCROWN_ISOLATED_RUNTIME=true` and fixture marker/temp root. No routes mounted, no installer, hardware, clinic database migration or patient data. The copied HotFolder's Local SQLite ledger is **not** the authority for clinical ACK: SQLCipher server-side receipt is decisive, and the client-local state deliberately stays PENDING_CONFIRMATION even after the synthetic receipt. Transport reconciliation/ack mapping remains to be engineered.

This is only FUE-0/I (LAB), not an automatically deployed product. Production integration needs server-owned device enrollment, actual user/session authentication in *the same request path*, Windows SCM service security on exact SHA, explicit Patient/RDV confirmation, persisted authorization/revocation, migration and recovery from crashes/power loss, independent reviewers and human GO. Physical scanner/driver belongs LOT10.4.

**Gates: READY_TO_MERGE=false, PRODUCT_READY=false, CLINICAL_GO=false.** No merge/deploy authorized.
