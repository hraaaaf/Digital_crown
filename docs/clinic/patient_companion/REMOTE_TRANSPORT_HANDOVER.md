# HANDOVER — Digital Crown Patient Companion — Remote Transport Gate B

Updated: 2026-09-19

## Goal

Option B: end-to-end encrypted opaque relay for PC-02+.

Cabinet remains source of truth. Relay stores/forwards ciphertext only.

## Current verified repository state

Repo: hraaaaf/Digital_crown
Base master includes:
- PC-00 merge 2a402e7d3bb232e90db7f9cd78b4e07cb393375b
- PC-01 merge 4dfa3b88cc516f79a99f3b30810ed39df3b0d841

Branch: feature/patient-companion-e2e-relay-gate
PR: #638 draft
Latest head before this handover commit: 5ce6b396354087587bf6c2a00ed1e55aea4f4383
PR mergeable: true
Exact-head CI: queued/pending at last check.

## Done

- architecture decision B recorded;
- threat model;
- sign-then-encrypt JOSE protocol locked;
- separate signing/encryption keys required;
- opaque mailbox model;
- 256-bit read/write capabilities;
- hashes only persisted;
- no clinical metadata in relay envelope;
- 256 KiB blob max;
- 7 day retention max;
- duplicate envelope rejection;
- mailbox revocation;
- explicit CORS allowlist only;
- Cache-Control no-store;
- separate relay schema migration;
- relay package statically forbidden from cabinet backend imports;
- unit/service negative tests.

## Deliberately not claimed complete

- no endpoint JOSE implementation yet;
- no cross-runtime JS/Python interoperability proof yet;
- no patient remote public-key enrollment yet;
- no cabinet worker replay/idempotency ledger yet;
- no production relay deployment;
- no Vercel deployment.

## Next exact

Read PR #638 exact-head CI. If red: diagnose/fix. If green: implement trusted key enrollment + JOSE interoperability proof without hand-written crypto.

## Remaining sequence

CI relay foundation
→ key enrollment contract
→ maintained JOSE libraries
→ cross-runtime crypto vectors
→ receiver replay/idempotency persistence
→ adversarial re-review
→ exact-head certification
→ update canonical/Notion/handover
→ merge #638
→ PC-02 Self-Service Agenda.

No deployment authorized.
