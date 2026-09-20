# Patient Companion — Remote Transport Gate B — Adversarial Review

Status: VERIFIED for code/test candidate `6843f4ccd0ca40afe372a96ba7bfee92598ef098` — Remote Gate `35504753520`, CI `35504753506`, Alembic `35504753494` and every triggered regression gate passed. This closeout commit is docs-only; its exact HEAD must pass the same required gates before merge.

Cross-check: RFC 7515 requires protected algorithm/signature verification and describes unique integrity-protected message IDs as replay defense; OWASP recommends authenticated encryption, separate keys by purpose, maintained libraries and protected key storage. The implemented fixed allowlists, ES256, A256GCM, separate signing/encryption keys, replay ledger, WebCrypto non-extractable patient keys and Windows DPAPI cabinet keys are consistent with those principles. This is not a legal-compliance or deployment certification.

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

Status: remediated; verified on candidate `6843f4ccd...`.

### F-02 — Relay-visible clinical routing metadata
Severity: blocker

Risk:
patient_id, tenant/employer_id, access_id, resource IDs or operation type would let relay correlate clinical activity even without plaintext.

Remediation:
RelayEnvelopeCreate is extra=forbid and contains only envelope_id, blob and ttl_seconds. Negative tests attempt forbidden clinical fields and require 422/rejection.

Status: implemented; verified on candidate `6843f4ccd...`.

### F-03 — Raw mailbox capabilities persisted by relay
Severity: blocker

Risk:
relay DB leak would directly grant mailbox access.

Remediation:
256-bit random read/write capabilities are returned only at provisioning. Relay stores SHA-256 hashes and uses constant-time comparison. Test inspects relay DB and verifies raw capabilities are absent.

Status: implemented; verified on candidate `6843f4ccd...`.

### F-04 — Read/write privilege confusion
Severity: high

Risk:
a patient/cabinet capability stolen for one direction could become full mailbox access.

Remediation:
independent read and write capabilities. Read cannot write; write cannot read/delete. Cross-mailbox capability test added.

Status: implemented; verified on candidate `6843f4ccd...`.

### F-05 — Duplicate/replayed relay envelopes
Severity: high

Remediation:
envelope_id is unique; duplicate insertion returns 409. Recipient-side signed message_id replay ledger and idempotency_key remain mandatory before domain mutation.

Status: verified on candidate `6843f4ccd...`; persistent message_id + idempotency ledger and allow-listed worker passed the dedicated gate.

### F-06 — Expired queued messages
Severity: high

Remediation:
relay TTL bounded to maximum 7 days; expired rows are filtered; test forces expiry and proves they are not returned. PC-02 appointment command signed expiry is capped by architecture at 15 minutes.

Status: verified on candidate `6843f4ccd...`; inner command TTL is capped at 15 minutes and future clock skew over 5 minutes is rejected.

### F-07 — Cache/CORS leakage
Severity: medium

Remediation:
capability and envelope responses use Cache-Control: no-store. CORS is disabled by default and can only be enabled with explicit allowed origins; no wildcard credentials.

Status: implemented; verified on candidate `6843f4ccd...`.

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

Status: verified on candidate `6843f4ccd...`. Python uses pinned jwcrypto 1.6.1; browser uses pinned jose 6.2.12. Dedicated run `35504753520` passed cross-runtime Python→JS and JS→Python interoperability and Windows current-user DPAPI.

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

Status: remediated; verified on candidate `6843f4ccd...`.

### F-12 — Access revocation left active remote keyset
Severity: high

Risk:
A server-revoked Patient Companion access could leave its E2E keyset marked ACTIVE, creating ambiguous future reactivation semantics.

Remediation:
The staff access-revocation flow now marks the active remote keyset REVOKED in the same cabinet transaction. Re-enabling remote transport therefore requires fresh key enrollment.

Status: implemented and regression-tested; verified on candidate `6843f4ccd...`.

### F-13 — Concurrent cabinet key creation
Severity: high

Risk:
Two simultaneous first remote pairings for the same cabinet could both observe no ACTIVE cabinet key and race on the partial unique index.

Remediation:
Cabinet key creation now uses a nested transaction/savepoint. The DB unique index remains authoritative; the loser re-queries and reuses the committed ACTIVE key instead of surfacing an uncontrolled 500.

Status: implemented; verified on candidate `6843f4ccd...`.

### F-14 — ACK operation could exceed protocol bound
Severity: medium

Risk:
A maximum-length inbound operation (64 chars) followed by the old `.result` suffix could make ACK construction fail after domain handling.

Remediation:
ACK operation is now the fixed bounded value `command.result`; the original operation is carried inside the signed/encrypted payload as `request_operation`. Regression test uses a 64-character request operation.

Status: implemented; verified on candidate `6843f4ccd...`.

## Verified certification evidence

Candidate: `6843f4ccd0ca40afe372a96ba7bfee92598ef098`

- Remote Transport Gate `35504753520` — SUCCESS (Linux JOSE interoperability + Windows DPAPI).
- CI `35504753506` — SUCCESS.
- PostgreSQL/Alembic `35504753494` — SUCCESS.
- T2 `35504753499`, P7 `35504753473`, UX1-C `35504753513`, PC-00 Visual `35504753543`, Agenda `35504753550`, Portability `35504753538`, Windows Build `35504753532`, Catalog `35504753461`, Marketplace `35504753528`, Media `35504753516` — SUCCESS.

External standards review: RFC 7515/7516/8725, NIST SP 800-57 Part 1 Rev.5 and OWASP cryptographic storage/key-management guidance were cross-checked. Fixed algorithm allowlists, authenticated encryption, separate signing/encryption keys, protected private-key storage and replay controls are consistent with those principles. This is not a legal-compliance or production-deployment certification.

Remaining: certify this docs-inclusive exact HEAD, then ready/merge #638 and post-merge verification.

No deployment performed.
