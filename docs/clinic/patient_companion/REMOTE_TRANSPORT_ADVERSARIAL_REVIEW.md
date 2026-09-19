# Patient Companion — Remote Transport Gate B — Adversarial Review

Status: IN PROGRESS — exact-head CI and crypto endpoint interoperability still pending.

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

Status: relay layer implemented; endpoint replay ledger belongs to PC-02 transport worker and is not yet certified.

### F-06 — Expired queued messages
Severity: high

Remediation:
relay TTL bounded to maximum 7 days; expired rows are filtered; test forces expiry and proves they are not returned. PC-02 appointment command signed expiry is capped by architecture at 15 minutes.

Status: relay side implemented; endpoint signed-expiry enforcement not yet implemented.

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

Status: DESIGN LOCKED; runtime endpoint implementation/interoperability pending.

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

## Remaining gates

1. exact-head CI for relay contract/service tests;
2. endpoint key enrollment design in trusted local pairing;
3. maintained JOSE library selected/pinned for browser + cabinet;
4. cross-runtime sign/encrypt/decrypt/verify interoperability vectors;
5. receiver replay ledger + idempotency persistence;
6. cabinet worker integration proving no direct remote domain mutation;
7. update canonical/Notion/handover;
8. only then mark Remote Transport Gate VERIFIED and allow PC-02 merge.

No deployment performed.
