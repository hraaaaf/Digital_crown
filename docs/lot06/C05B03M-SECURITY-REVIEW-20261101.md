# LOT06 C05B-03M — Security gate review, on-prem identity and human confirmation

**Date:** 2026-11-01. Parent [#1181](https://github.com/hraaaaf/Digital_crown/pull/1181) exact SHA `f55ba41bed7898750146553d0540521412955035`. This is an **internal automated security review** and synthetic contract FUE, **NOT** independent penetration testing, scanner certification or production authorization.

## Audit findings (severity / status / proof)

| Risk | Severity | Status | Evidence and boundary |
| --- | --- | --- | --- |
| Device bearer token copied from USB / local process can be reused to pretend scanner | P0 for cabinet activation | LAB MITIGATION; PRODUCT OPEN | Added independent Ed25519 device signing key, pinned public key in file-backed SQLCipher TEST, signature binds tenant + device + capture + patient + staff + station + generation + version + sha256 + byte size + server challenge. FUE wrong signing key, cross-patient, wrong generation, device revoked. Still no Windows hardware-backed enrollment or mTLS on cabinet. |
| A preapproved Python fixture is confused with genuine explicit clinical staff confirmation | P0 | LAB CONTRACT only; PRODUCT OPEN | Independent `record_staff_review_fixture()` event checks actual active staff/role/WorkstationMode; upload alone cannot mint review; review expiry, contradictory identity and invalid actor rejected. No UI consent screen or proof of real human click; must be implemented and tested with human FUE. |
| Device/approval consumed before receipt commit, then ACK network loss | P1 | LAB MITIGATED | `TestOnlyMediaAuthority.consume` invoked as `_issue(... locked_authorize=...)` inside same SQLCipher `BEGIN IMMEDIATE` as receipt/audit/outbox. Failure after audit rolls back consumption. Replay only after same immutable receipt exists. Distinct local SQLite ACK remains another commit, handled by retry. |
| Signed server ACK could be client-forged using symmetric device token | P0 | LAB MITIGATED in 03L | Server Ed25519 private signing key, agent separately pins public key, no symmetric MAC. This is still ephemeral LAB key without production provisioning, revocation or secure key rotation. |
| HTTP media transport susceptible to local interception, client/server impersonation or secret leakage | P0 | OPEN | Current test binds unencrypted 127.0.0.1 only, test credentials. Product must choose OS-bound local IPC with explicit Windows SID/DACL and secure peer authentication OR HTTPS/mTLS when traffic can cross machine; never simply expose 03L route to LAN. |
| SQLCipher ClinicalAsset bytes persisted before receipt authority/commit | P1 | OPEN | 03L two independent server transactions: storage metadata and ciphertext are committed before `_issue`, so failed approval or SQL receipt can leave unattached encrypted content / metadata. Product needs crash-consistent staging + receipt transaction / garbage-collection and proof of no dossier publication until committed. |
| Restart, power-loss, Windows SCM virtual account, WAL/DACL, physical scanning | P0/P1 | OPEN LOT10.4 | Synthetic Linux subprocess tests do not prove real Windows install, impersonation, privilege separation, power cut, restore, or third-party driver. |
| SQLCipher migration / audited installation / data provenance | P0 | OPEN | Tests create schema dynamically and manufacture synthetic approval; there is no production Alembic migration or clinical trust root. |

## TEST-only proof implemented here

- `isolated_fue_lot06c/c05b03m_security_gate_lab.py` has file-backed SQLCipher test tables `c05b03m_lab_device_identity`, `c05b03m_lab_review`, and `c05b03m_lab_review_audit`; not imported in any product runtime. Explicit env `ENVIRONMENT=test`, `DIGITALCROWN_ISOLATED_RUNTIME=true`, `DC06C05B03M_TEST_ONLY=1`, actual SQLCipher `cipher_version`.
- New optional `security_gate` on **disposable** FastAPI endpoint in isolated 03L FUE checks signed device claim **before** storing media. A separate synthetic staff approval action checks existing active User, tenant, permissions, station revision; server upload is never allowed to mint its own approval or enroll a device.
- `_issue` existing `locked_authorize` invokes one-time review consumption under the same SQLCipher write lock and SQL transaction as receipt/audit/outbox. After lost reply, exact same device proof can replay **only** when identical immutable receipt already exists. Failpoint rolls back consumption and receipts together.
- New 03M tests exercise genuine 127.0.0.1 HTTP and actual HotFolder decrypted PNG, device signature wrong, cross-patient, missing review, expiration, generation/key rotation, revoked staff/device, atomic rollback, reboot/lost ACK, forged ACK blocked by pinned server key, TEST gate hard stop.
- Re-run prior 03K/03L, JWT/WorkstationMode, and J contracts on the exact same candidate SHA. No real workstation installer or patient data.

## Required on-prem product design (decision needed before next implementation)

1. **Local trust root and key lifecycle**: server-owned Ed25519 signing private key in Windows DPAPI/CNG or credential-protected platform store, opaque pin pre-provisioned to authorized cabinet device with audited key rotation; each device holds non-exportable private key or secure keystore, identity enrolled by human administrator on an authenticated local channel, tenant-bound certificates/claims, revocation before every receipt and replay.
2. **Human review UI and audit**: only authenticated staff with `patients` permission, live WorkstationMode, server-issued short-lived capture context can view verified patient identifiers (not filename heuristics), select explicit patient and RDV or coded reason, confirm a captured hash/device before signing; server persists actor/session/workstation/reason/challenge/expiry with immutable audit, then consumes once. Changes to patient scope or revocation invalidate proof.
3. **Transport**: on-machine isolated IPC with OS principal ACL; across machines TLS 1.3 with device mTLS and certificate pin / rotation. Reject proxy-forwarded local requests, DNS rebinding and host spoof; local IP alone is not authentication. No raw bearer-token HTTP on external interfaces.
4. **Crash and rollback FUE**: power kill between AES write, SQL metadata, SQL receipt, response signing, client ACK, WAL fsync; test replay 1 receipt / 1 audit / 1 outbox and cleanup of orphan ciphertext; preserve original files until confirmed.
5. **Real product API + migrations**: build only after independent security sign-off and owner approval; never port LAB fixture approval enrollment, hardcoded test keys, temporary directory guards or test-only signing key directly into production.

`READY_TO_MERGE=false`
`PRODUCT_READY=false`
`CLINICAL_GO=false`

**Expected next:** C05B-03N = independent security review, owner arbitration on transport/key provisioning + real staff UI workflow; only then engineering gated product integration. Physical Windows device remains LOT10.4.
