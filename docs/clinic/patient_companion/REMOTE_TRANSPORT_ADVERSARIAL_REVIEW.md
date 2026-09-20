# Patient Companion — Remote Transport Gate B — Adversarial Review

Status: IN PROGRESS — implementation substantially complete; final exact-head certification still pending.

## Candidate

Repo: hraaaaf/Digital_crown
Branch: feature/patient-companion-e2e-relay-gate
PR: #638
Base: master@4dfa3b88cc516f79a99f3b30810ed39df3b0d841

## Goal

Establish an end-to-end encrypted opaque relay for PC-02+ without exposing cabinet clinical data or cabinet storage to the relay.

## Findings

### F-01 — Relay package imported cabinet backend module
Severity: architecture blocker

Observed:
Initial relay service imported the protocol contract from backend.services.

Risk:
Deployment coupling could accidentally drag cabinet code/dependencies into the relay boundary.

Remediation:
Protocol contract moved into relay/contract.py. Relay package now has a static negative test forbidding backend imports, cabinet models and get_db.

Status: remediated; exact-head CI pending.

### F-02 — Relay-visible clinical routing metadata
Severity: blocker

Risk:
patient_id, tenant/employer_id, access_id, resource IDs or operation type would let relay correlate clinical activity even without plaintext.

Remediation:
RelayEnvelopeCreate is extra=forbid and contains only envelope_id, blob and ttl_seconds. Negative tests attempt forbidden clinical fields and require 422/rejection.

Status: implemented; CI pending.

### F-03 — Raw mailbox capabilities persisted by relay
Severity: blocker

Risk:
relay DB leak would directly grant mailbox access.

Remediation:
256-bit random read/write capabilities are returned only at provisioning. Relay stores SHA-256 hashes and uses constant-time comparison. Test inspects relay DB and verifies raw capabilities are absent.

Status: implemented; CI pending.

### F-04 — Read/write privilege confusion
Severity: high

Risk:
a patient/cabinet capability stolen for one direction could become full mailbox access.

Remediation:
independent read and write capabilities. Read cannot write; write cannot read/delete. Cross-mailbox capability test added.

Status: implemented; CI pending.

### F-05 — Duplicate/replayed relay envelopes
Severity: high

Remediation:
envelope_id is unique; duplicate insertion returns 409. Recipient-side signed message_id replay ledger and idempotency_key remain mandatory before domain mutation.

Status: implemented. Cabinet-side persistent message_id + idempotency ledger and allow-listed worker are present; exact-head certification pending.

### F-06 — Expired queued messages
Severity: high

Remediation:
relay TTL bounded to maximum 7 days; expired rows are filtered; test forces expiry and proves they are not returned. PC-02 appointment command signed expiry is capped by architecture at 15 minutes.

Status: implemented. Inner command TTL is capped at 15 minutes and future clock skew over 5 minutes is rejected; exact-head certification pending.

### F-07 — Cache/CORS leakage
Severity: medium

Remediation:
capability and envelope responses use Cache-Control: no-store. CORS is disabled by default and can only be enabled with explicit allowed origins; no wildcard credentials.

Status: implemented; CI pending.

### F-08 — Silent production schema mutation
Severity: medium

Risk:
automatic create_all in production bypasses migration governance.

Remediation:
schema creation is opt-in test-only. Separate relay/migrations/001_init.sql is canonical v1 schema.

Status: remediated.

### F-09 — Cryptography implementation risk
Severity: blocker before clinical remote writes

Decision:
JWS ES256 -> JWE ECDH-ES+A256KW / A256GCM. Separate signing and encryption keys. Algorithm allowlist fixed in executable contract.

Critical restriction:
No hand-written JOSE implementation. Endpoint crypto must use a maintained JOSE library and must pass cross-runtime interoperability vectors before PC-02 merge.

Status: implemented, not yet finally certified. Python uses pinned jwcrypto 1.6.1; browser uses pinned jose 6.2.12. Cross-runtime Python→JS and JS→Python certification workflow is present. Patient private keys are generated non-extractable in WebCrypto; cabinet private keys use Windows current-user DPAPI.

### F-10 — Relay metadata/DoS residual risk
Severity: accepted residual / operational

Relay can still observe:
mailbox IDs, IPs, timestamps, sizes and polling cadence.

Relay cannot prevent all DoS. Current service bounds blob size, retention and active-envelope quota. Deployment ingress must also enforce request/IP rate limiting and TLS.

Status: documented residual; deployment gate remains separate.

## External standard cross-check

- RFC 7515: ES256 JWS.
- RFC 7516: JWE.
- RFC 7518: ECDH-ES+A256KW and A256GCM are registered/recommended JOSE algorithms.
- NIST SP 800-57 Part 1 Rev.5: key lifecycle/cryptoperiod baseline.
- OWASP Cryptographic Storage + Key Management: threat-model first, authenticated encryption, key separation/lifecycle, no custom cryptographic algorithms.

### F-11 — Competing remote-key architecture residue
Severity: high

Observed:
An earlier parallel implementation left a second remote-key route/test family after the canonical QR-bound design had been selected.

Remediation:
The stale route and stale enrollment test were removed. Canonical enrollment occurs atomically inside the one-time QR/manual pairing ceremony.

Status: remediated; exact-head CI pending.

### F-12 — Access revocation left active remote keyset
Severity: high

Risk:
A server-revoked Patient Companion access could leave its E2E keyset marked ACTIVE, creating ambiguous future reactivation semantics.

Remediation:
The staff access-revocation flow now marks the active remote keyset REVOKED in the same cabinet transaction. Re-enabling remote transport therefore requires fresh key enrollment.

Status: implemented with regression test; exact-head CI pending.

### F-13 — Concurrent cabinet key creation
Severity: high

Risk:
Two simultaneous first remote pairings for the same cabinet could both observe no ACTIVE cabinet key and race on the partial unique index.

Remediation:
Cabinet key creation now uses a nested transaction/savepoint. The DB unique index remains authoritative; the loser re-queries and reuses the committed ACTIVE key instead of surfacing an uncontrolled 500.

Status: implemented; exact-head certification pending.

### F-14 — ACK operation could exceed protocol bound
Severity: medium

Risk:
A maximum-length inbound operation (64 chars) followed by the old `.result` suffix could make ACK construction fail after domain handling.

Remediation:
ACK operation is now the fixed bounded value `command.result`; the original operation is carried inside the signed/encrypted payload as `request_operation`. Regression test uses a 64-character request operation.

Status: implemented; exact-head certification pending.

## Remaining gates

1. exact-head dedicated Remote Transport Gate green on Linux and Windows;
2. exact-head general CI + PostgreSQL/Alembic green;
3. Patient/Media/Catalog/Marketplace gates green if triggered by this branch;
4. inspect failures rather than infer common cause;
5. update this review with exact run IDs and only then mark VERIFIED;
6. update canonical + Notion + handover;
7. merge #638 with expected-head guard;
8. post-merge master verification;
9. only then open PC-02 implementation.

No deployment performed.
