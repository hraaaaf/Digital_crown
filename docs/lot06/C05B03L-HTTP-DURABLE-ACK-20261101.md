# LOT06 C05B-03L — Loopback HTTP + durable signed ACK (TEST ONLY)

Date: 2026-11-01. Parent [#1180](https://github.com/hraaaaf/Digital_crown/pull/1180) at `1fe4eb24caa7720681ad6fb423d10df80db7ddc6`. This is NOT a product API route or an installed Windows service.

## Change, kept deliberately narrow

- `isolated_fue_lot06c/test_c05b03l_http_durable_ack_v15.py`: actual 127.0.0.1 TCP HTTP request with bytes read from the #909 HotFolder encrypted spool. A dedicated isolated FastAPI app calls **real backend** `auth.get_current_user` (JWT, Station cookie, active user), SQLCipher backed staff+device+explicit patient+synthetic preapproved capture authority, then AES-GCM ClinicalAsset storage and immutable SQLCipher receipt/audit/outbox. It reads the media stream and verifies structure and approved digest **before** writing any asset. The workstation/user/device approval is rechecked under SQLCipher `BEGIN IMMEDIATE`. Server never updates or creates approval records from the request.
- `tools/imaging_gateway/http_ack_lab_v15.py`: gate `ENVIRONMENT=test`, `DIGITALCROWN_ISOLATED_RUNTIME=true`, `DC_V15_06_HTTP_ACK_LAB=1`, exact marked TEMP fixture. Reject unsigned responses, wrong patient/capture/device/media, arbitrary receipt fields. **Server-only Ed25519 private signing key**, pinned public verification key held independently by collector; local device token is *not* the signing key. After the real spool passes AES-GCM authenticated readback, one local SQLite WAL transaction writes `c05b03l_lab_acks`, `LAB_ACK_CONFIRMED` and an audit event, with strict idempotent readback/conflict refusal.
- Simulate HTTP response loss after server SQLCipher commit: local item stays `PENDING_CONFIRMATION`; restart agent; POST identical verified bytes to real local HTTP again; same receipt/only 1 receipt+audit+outbox; verify server signature then write local ACK once; restart and prove durable LAB-only confirmation.
- Negative checks: expired/missing auth via existing G tests; new missing JWT, wrong Station cookie, wrong device token, mismatched media/patient, forged signature, wrong expected patient, production/flag-off ACK refusal, Station revoked. Existing K/G FUE re-run on exact SHA.

## Non-negotiable truth & security limits

The HTTP socket binds **127.0.0.1** without TLS strictly in CI TEST. This does NOT validate TLS/mTLS/network threat model, product device enrollment, real clinician confirmation, approval issuance, Windows Service Control Manager, DACLs, power-cut durability, cabinet database schema migration or cross-filesystem crash atomicity. The signing key and pinned public key are generated per disposable test fixture, not production PKI provisioning; local state is named **LAB_ACK_CONFIRMED**, never `CONFIRMED` or clinical authorization. Fixture staff/device/approval are synthetic, although the actual backend user/workstation authorization code is used. SQLCipher content, SQL receipt and local SQLite ACK are intentionally two independent transactions with post-commit retry/idempotence, NOT a distributed transaction. `backend/main.py`, application routers, Alembic and production service entrypoints remain untouched.

`READY_TO_MERGE=false`
`PRODUCT_READY=false`
`CLINICAL_GO=false`

Next: real on-prem authenticated route and independent device/server identity provisioning, UI-supported human approval, signed ACK reconciliation under clinic policies, live Windows service + ACL validation and failure injections, separate owner merge/deploy approval. Physical scanners in LOT10.4.
