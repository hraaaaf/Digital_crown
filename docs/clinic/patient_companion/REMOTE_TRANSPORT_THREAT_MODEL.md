# Patient Companion E2E Relay — Adversarial Threat Model

Status: GATE REVIEW IN PROGRESS

## Assets

Highest-value:
- clinical plaintext;
- patient/cabinet signing private keys;
- patient/cabinet encryption private keys;
- relay mailbox capabilities;
- cabinet source-of-truth mutation authority.

## Trust boundaries

1. Patient device/browser origin.
2. Public Internet/TLS transport.
3. Opaque relay.
4. Cabinet transport worker.
5. Cabinet domain/API/database.

Relay is explicitly outside the clinical trust boundary.

## Adversary cases

### Relay database leak

Expected result:
- attacker gets ciphertext, opaque mailbox IDs, timestamps/sizes and hashed capabilities;
- no clinical plaintext/private keys.

### Relay code execution compromise

Expected result:
- attacker may observe future incoming blobs and traffic metadata and may deny/reorder/replay them;
- recipient signature, expiry, replay and idempotency checks prevent trusted clinical mutation from forged/replayed ciphertext;
- confidentiality still depends on endpoint private keys remaining uncompromised.

### Stolen write capability

Expected result:
- attacker can inject arbitrary blobs into one mailbox and consume quota;
- cannot create a valid signed clinical command without sender private signing key;
- rate limits/size quotas bound DoS.

### Stolen read capability

Expected result:
- attacker can copy ciphertext from one mailbox;
- cannot decrypt without recipient private key;
- capability is rotated when compromise is suspected.

### Ciphertext replay

Expected result:
- duplicate message_id is rejected before domain side effects;
- duplicate idempotency_key cannot create a second write.

### Message reordering

Expected result:
- application timestamps/expiry and domain version/conflict checks decide validity;
- relay order is never treated as causal truth.

### Patient device loss

Expected result:
- cabinet revokes Patient Companion access + associated relay capabilities/keys;
- future commands/sync rejected;
- no claim that already-stored offline data can be remotely erased.

### Cabinet offline

Expected result:
- relay may hold encrypted request until expiry;
- patient UI says pending, never confirmed;
- once cabinet reconnects it verifies freshness/signature/access before processing.

### Malicious or compromised patient origin

Expected result:
- browser code able to invoke non-exportable CryptoKey operations may act as that patient device;
- non-exportable keys do not make an XSS-compromised origin safe;
- CSP/dependency controls and origin hardening remain required.

### Compromised cabinet

Expected result:
- out of scope for E2E relay confidentiality because cabinet is the clinical endpoint/source of truth;
- incident response/key rotation/backups/audit are separate controls.

## Explicit residual risks

- traffic analysis;
- IP address exposure to relay;
- message-size correlation;
- endpoint compromise;
- relay denial of service;
- cryptographic library supply-chain risk;
- loss of decrypt keys can make queued encrypted messages unrecoverable.

## Required negative tests

- extra patient_id/employer_id/access_id in relay envelope rejected;
- blob >256 KiB rejected;
- retention >7 days rejected;
- wrong mailbox capability rejected;
- read capability cannot write;
- write capability cannot read/delete;
- duplicate envelope ID rejected;
- expired envelope not returned;
- JOSE algorithm outside allowlist rejected at endpoint;
- expired inner message rejected;
- duplicate message_id rejected;
- duplicate idempotency_key cannot repeat mutation;
- revoked access/key rejects command;
- malformed/undecryptable blob never reaches domain handler.
