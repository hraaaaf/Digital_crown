# HANDOVER — Digital Crown Patient Companion — Remote Transport Gate B

Updated: 2026-09-20

## Goal

Close the mandatory pre-PC-02 gate with an end-to-end encrypted opaque relay. Cabinet stays clinical source of truth; relay stores/forwards ciphertext only.

## Verified repository state

Repo: hraaaaf/Digital_crown
Branch: feature/patient-companion-e2e-relay-gate
PR: #638 — draft, mergeable at last check
Base: master
Code/test HEAD before final documentation freeze: eeec66468b95d49c2fe01dc135663ceed8695b31

No merge. No Vercel deployment.

## Implemented

- option B architecture + threat model;
- isolated relay package with no cabinet backend import;
- opaque envelopes only: envelope_id, ciphertext blob, TTL;
- 256-bit read/write mailbox capabilities; hashes persisted only;
- bounded blob size, retention, quota, duplicate rejection and mailbox revocation;
- JWS ES256 -> JWE ECDH-ES+A256KW/A256GCM;
- pinned Python jwcrypto 1.6.1 and browser jose 6.2.12;
- patient P-256 signing/encryption keys generated in WebCrypto; private keys non-extractable;
- cabinet P-256 private keys protected with Windows current-user DPAPI;
- atomic remote key enrollment inside one-time QR/manual pairing;
- cabinet/public keysets versioned in DB;
- one ACTIVE keyset per access and one ACTIVE cabinet key per tenant/use enforced by DB indexes;
- command freshness: max 15 min TTL, max 5 min future clock skew;
- persistent replay/idempotency receipt ledger;
- cabinet remote worker: decrypt -> verify -> replay/idempotency -> allow-listed handler -> transactional commit/rollback -> signed+encrypted ACK;
- access revoke also revokes active remote keyset;
- concurrent first-pair cabinet-key creation is savepoint/unique-index race-safe;
- ACK uses bounded `command.result` and carries the original operation inside ciphertext;
- browser erase deletes the full Patient Companion IndexedDB, including remote private CryptoKeys;
- dedicated Linux JOSE interoperability + Windows DPAPI workflow;
- stale competing remote-key route/test removed.

## Exact failures diagnosed from old HEAD 6dd85ae...

These were concrete harness/integration failures, not a proven crypto break:

1. Remote Transport Linux job: missing email-validator in focused test dependencies.
2. Remote Transport Windows job: pytest loaded full backend conftest and failed before DPAPI.
3. General frontend build: JsonWebKey TypeScript type rejected JOSE kid/use metadata.
4. PostgreSQL/Alembic: backend runtime head still declared ojf20000008 instead of pcrt0000009.

All four causes were corrected before current checkpoint.

## Current certification state

Code/test candidate `6843f4ccd0ca40afe372a96ba7bfee92598ef098` is VERIFIED: Remote Gate `35504753520`, CI `35504753506`, Alembic `35504753494`, T2 `35504753499`, P7 `35504753473`, UX1-C `35504753513`, PC-00 Visual `35504753543`, Agenda `35504753550`, Portability `35504753538`, Windows Build `35504753532`, Catalog `35504753461`, Marketplace `35504753528`, Media `35504753516` — all SUCCESS. This closeout is docs-only and its new exact HEAD must be certified before merge.

Final VERIFIED requires the same exact HEAD to have:
- Patient Companion Remote Transport Gate: Linux + Windows SUCCESS;
- CI SUCCESS;
- PostgreSQL Alembic SUCCESS;
- any triggered Patient P7 / Media C4 / Catalog / Marketplace gates SUCCESS;
- adversarial review updated with exact run IDs.

## Deliberately not claimed

- no production relay deployment;
- no Vercel deployment;
- no PC-02 appointment handler enabled;
- no hardware-backed/Secure-Enclave claim for browser WebCrypto;
- no retroactive remote deletion of already-downloaded patient data;
- relay metadata anonymity is not claimed.

## Next exact

1. Read exact-head runs after the documentation checkpoint.
2. Diagnose/correct any red job.
3. If green, record exact run IDs in adversarial review + canonical + Notion.
4. Mark PR ready only after final review.
5. Merge #638 with expected-head guard.
6. Verify post-merge master/workflows.
7. Start PC-02 only after gate closeout.

## Remaining sequence

exact-head CI -> fix red if any -> adversarial closeout -> canonical/Notion -> ready/merge #638 -> post-merge -> PC-02 Self-Service Agenda.
