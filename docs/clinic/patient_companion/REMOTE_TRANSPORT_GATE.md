# Patient Companion — REMOTE TRANSPORT GATE — E2E Opaque Relay

Status: APPROVED ARCHITECTURE — IMPLEMENTATION FOUNDATION IN PROGRESS
Decision date: 2026-09-19

## Goal

Enable PC-02+ remote patient actions without exposing Digital Crown's cabinet database to the Internet and without giving the relay access to clinical plaintext.

Canonical topology:

Patient encrypted vault
→ TLS
→ opaque relay mailbox
→ TLS
→ Digital Crown cabinet

The relay stores and forwards ciphertext only. The cabinet remains the clinical source of truth.

## Success

The gate is closed only when all of these are evidenced:

1. relay-visible envelopes contain no patient ID, tenant ID, appointment ID, clinical resource ID, message type or clinical payload;
2. clinical/application payload is signed by the sender then encrypted to the recipient;
3. replayed or expired messages are rejected by the recipient;
4. remote write commands are idempotent and remain cabinet-authoritative;
5. relay access uses random least-privilege mailbox capabilities stored only as hashes by the relay;
6. patient and cabinet cryptographic private keys never transit through or reside in the relay;
7. key compromise/revocation/rotation behavior is specified and testable;
8. relay downtime cannot corrupt cabinet truth; queued patient actions are never presented as confirmed before cabinet acknowledgement;
9. the relay has no route, credential or network path to cabinet SQLite/PostgreSQL/media storage;
10. exact-head CI and adversarial review pass before PC-02 is allowed to merge.

## Decision

Selected family: **B — end-to-end encrypted opaque relay**.

Rejected as canonical remote plane:
- direct public exposure of the cabinet API;
- Firebase/SaaS plaintext clinical storage;
- WhatsApp as clinical transport;
- direct database/media exposure.

## Threat model

Protected against:
- honest-but-curious relay operator;
- relay database disclosure;
- relay application compromise that exposes stored blobs/capability hashes;
- passive network observer when TLS is correctly enforced;
- replay/reordering/duplication by the relay;
- cross-mailbox access with a stolen capability from another mailbox.

Not protected against:
- a fully compromised cabinet host;
- a fully compromised patient browser/origin/device while keys are usable there;
- denial of service by the relay/network;
- traffic-analysis metadata: relay can observe mailbox identifiers, source IPs, timestamps, approximate message sizes and polling cadence.

No claim of metadata anonymity is permitted.

## Cryptographic protocol

Do not design a bespoke cipher or bespoke key-agreement algorithm.

Application message protection is **sign-then-encrypt**:

1. canonical JSON application payload;
2. JWS using ES256 (ECDSA P-256 / SHA-256);
3. resulting JWS encrypted as JWE using ECDH-ES+A256KW;
4. JWE content encryption: A256GCM.

Standards:
- RFC 7515 — JSON Web Signature;
- RFC 7516 — JSON Web Encryption;
- RFC 7518 — JSON Web Algorithms.

Implementation rule:
- use a maintained JOSE implementation;
- do not hand-roll ECDH, Concat KDF, AES-GCM framing, JOSE serialization or ECDSA encoding;
- pin algorithm allowlists during verify/decrypt; never accept algorithm negotiation from untrusted input.

The JWS is inside the JWE, therefore sender identity/key metadata is encrypted. The JWE protected header may expose only protocol/algorithm data and an opaque recipient key identifier.

## Key separation

Every endpoint has independent keys for:
- signing/authenticity;
- encryption/key agreement.

Never reuse a signing private key for ECDH.

Patient:
- keypairs generated on the patient device;
- private keys non-exportable where the platform allows;
- public JWKs enrolled during a trusted local pairing/re-key ceremony;
- private keys never sent to cabinet or relay.

Cabinet:
- installation-level or scoped relay keypairs;
- private material stored with an OS-bound protected-key mechanism, not plaintext DB/source/env;
- public keys pinned to the patient device during trusted pairing.

Key IDs are random opaque identifiers.

## Key lifecycle

- immediate revoke/rotate on suspected compromise;
- explicit active/retired/revoked states;
- recipient may retain retired decryption keys only for the bounded outstanding-message window;
- signing private keys are not escrowed;
- cryptoperiod is reviewed at least annually and must remain within the application's threat model;
- every message records the opaque signing/encryption key IDs inside protected JOSE headers/payload as appropriate.

NIST SP 800-57 Part 1 Rev.5 is the key-lifecycle baseline.

## Relay mailbox model

Relay knows only random mailboxes and capabilities.

For each Patient Companion access, provision two independent mailboxes:
- patient inbox;
- cabinet inbox.

Each mailbox has independent random 256-bit capabilities:
- read/delete capability;
- write capability.

Relay stores only SHA-256 capability hashes.

Provision the two mailboxes independently so the relay does not need an explicit patient↔cabinet pair relation.

Never put these in relay-visible metadata:
- patient_id;
- employer_id / tenant_id;
- access_id;
- appointment/document/media IDs;
- patient/cabinet names;
- clinical message type.

## Relay envelope

Outer relay-visible object is intentionally dumb:

- envelope_id: random UUID;
- blob: compact JWE string;
- relay-created timestamp;
- relay expiry.

Nothing else is required for routing.

Maximum v1 blob size: 256 KiB.
Maximum relay retention: 7 days.
PC-02 appointment commands use a much shorter signed application expiry: 15 minutes maximum.

Future large media transfer (PC-07) requires a separate chunked encrypted-object design; do not raise the message limit casually.

## Capabilities and relay authorization

Authorization header uses a high-entropy mailbox capability.

Properties:
- 256 random bits;
- scope is exactly one mailbox + one privilege class;
- compare hashed values in constant-time;
- rotate by replacing the mailbox/capability, not by extending privilege;
- rate-limit by mailbox/IP without decoding content;
- all relay transport remains TLS even though blobs are E2E encrypted.

Bootstrap/provisioning credentials are cabinet-only infrastructure credentials and are never embedded in the patient app.

## Signed inner application envelope

After JWE decryption and JWS verification, recipient validates:

- protocol_version;
- message_id;
- access_id (inside ciphertext only);
- sent_at;
- expires_at;
- idempotency_key;
- operation;
- payload.

Receiver checks:
1. signature key is pinned and active;
2. access is active and belongs to expected cabinet/patient context;
3. now <= expires_at;
4. message_id has not been processed before;
5. idempotency_key has not already produced another server-authoritative mutation.

Only then may domain validation execute.

## Replay / ordering / idempotency

Relay ordering is never trusted.

Recipient keeps a bounded processed-message ledger.

Duplicate message_id:
- reject as replay;
- do not repeat side effects.

Duplicate idempotency_key for a write:
- return/reuse the original cabinet result where safe;
- never create a second appointment/action.

A patient-side queued command is displayed as:
- pending transmission;
- delivered to cabinet;
- accepted/rejected by cabinet.

It is never displayed as a confirmed appointment before a signed cabinet acknowledgement.

## Revocation

Access revoke:
- cabinet immediately refuses future application messages for that access;
- cabinet stops sending new patient messages;
- relay mailbox capabilities are rotated/decommissioned;
- patient retains already-held offline data; no remote-delete claim.

Key revoke:
- messages signed with a revoked sender key are rejected according to revocation effective time/policy;
- new outbound messages use the replacement recipient key.

## Logging / observability

Relay logs:
- envelope ID;
- mailbox opaque ID;
- byte size;
- created/expired/deleted timestamps;
- status/rate-limit outcome.

Relay must not log:
- blob body;
- capability/token;
- decrypted content;
- patient/tenant/access IDs.

Cabinet audit log records clinical command outcome after verified decryption/signature checks.

## Deployment boundary

Relay is a separate deployment unit.

It must not import cabinet models or mount cabinet routers.
It receives no cabinet DB credentials and no media filesystem credentials.

No Vercel deployment is authorized by this gate.

## PC-02 contract

PC-02 may start only on this basis:
- remote action is an encrypted command, not a direct remote DB mutation;
- cabinet validates slot/conflict/business rules after decrypt+verify;
- response is a separately signed+encrypted acknowledgement;
- offline/pending state is explicit;
- failed/expired request remains unconfirmed.

## References

- RFC 7515 — JSON Web Signature: https://www.rfc-editor.org/rfc/rfc7515
- RFC 7516 — JSON Web Encryption: https://www.rfc-editor.org/rfc/rfc7516
- RFC 7518 — JSON Web Algorithms: https://www.rfc-editor.org/rfc/rfc7518
- NIST SP 800-57 Part 1 Rev.5 — Recommendation for Key Management
- OWASP Cryptographic Storage Cheat Sheet
- OWASP Key Management Cheat Sheet
